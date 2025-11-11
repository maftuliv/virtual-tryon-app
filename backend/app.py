import os
import time
import base64
import requests
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from PIL import Image
import io

# Configuration for static files
FRONTEND_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend')

app = Flask(__name__,
            static_folder=FRONTEND_FOLDER,
            static_url_path='')
CORS(app)

# Configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
RESULTS_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'results')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Create folders if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULTS_FOLDER'] = RESULTS_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# API configurations
FASHN_API_KEY = os.environ.get('FASHN_API_KEY', '').strip()  # FASHN AI token
FASHN_BASE_URL = "https://api.fashn.ai/v1"

# Nano Banana API (Google Gemini 2.5 Flash) - Official API
# Try multiple environment variable names as Railway might use different naming
NANOBANANA_API_KEY = (
    os.environ.get('NANOBANANA_API_KEY', '') or
    os.environ.get('NANOBANANA_API_KEY'.lower(), '') or
    os.environ.get('nanobanana_api_key', '')
).strip()
NANOBANANA_BASE_URL = "https://api.nanobananaapi.ai/api/v1/nanobanana"  # Base URL without /generate

# ==================== DIAGNOSTICS (runs on import, works with gunicorn) ====================
print("=" * 80)
print("🔍 RAILWAY ENVIRONMENT DIAGNOSTICS")
print("=" * 80)

# Show ALL environment variables containing "NANO", "BANANA", or "API"
print("\n[ENV VARS] All variables containing 'NANO', 'BANANA', or 'API':")
found_vars = False
for key, value in sorted(os.environ.items()):
    if any(keyword in key.upper() for keyword in ['NANO', 'BANANA', 'API']):
        found_vars = True
        # Show preview of value (hide sensitive info)
        if len(value) > 20:
            preview = f"{value[:10]}...{value[-6:]}"
        else:
            preview = value if len(value) <= 12 else f"{value[:8]}...{value[-4:]}"
        print(f"  ✓ {key} = {preview} (length: {len(value)})")

if not found_vars:
    print("  ⚠️  NO variables found containing 'NANO', 'BANANA', or 'API'!")

# Show loaded API key status
print("\n[API KEYS] Loaded values in Python:")
print(f"  FASHN_API_KEY: {'✅ SET' if FASHN_API_KEY else '❌ MISSING'} (length: {len(FASHN_API_KEY)})")
print(f"  NANOBANANA_API_KEY: {'✅ SET' if NANOBANANA_API_KEY else '❌ MISSING'} (length: {len(NANOBANANA_API_KEY)})")

if NANOBANANA_API_KEY:
    print(f"  NANOBANANA_API_KEY preview: {NANOBANANA_API_KEY[:8]}...{NANOBANANA_API_KEY[-4:]}")
else:
    print("  ⚠️  NANOBANANA_API_KEY is EMPTY or MISSING!")
    print("  ℹ️  Checked: NANOBANANA_API_KEY, nanobanana_api_key")

print("=" * 80)
print()
# ==================== END DIAGNOSTICS ====================

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def preprocess_image(image_path, max_height=2000, quality=95):
    """
    Preprocess image according to FASHN best practices:
    - Resize to max_height if larger (maintaining aspect ratio)
    - Convert to JPEG format with quality setting
    - Use LANCZOS resampling for quality preservation

    Returns: path to preprocessed image
    """
    try:
        img = Image.open(image_path)

        # Convert RGBA to RGB if needed
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')

        # Resize if height exceeds max_height
        width, height = img.size
        if height > max_height:
            ratio = max_height / height
            new_width = int(width * ratio)
            img = img.resize((new_width, max_height), Image.Resampling.LANCZOS)
            print(f"[PREPROCESS] Resized from {width}x{height} to {new_width}x{max_height}")

        # Save as optimized JPEG
        output_path = image_path.rsplit('.', 1)[0] + '_optimized.jpg'
        img.save(output_path, 'JPEG', quality=quality, optimize=True)

        print(f"[PREPROCESS] Optimized image saved to {output_path}")
        return output_path

    except Exception as e:
        print(f"[PREPROCESS WARNING] Failed to preprocess {image_path}: {e}")
        # Return original path if preprocessing fails
        return image_path

def image_to_base64(image_path):
    """Convert image file to base64 string"""
    with open(image_path, 'rb') as img_file:
        img_data = base64.b64encode(img_file.read()).decode('utf-8')
    return img_data

def validate_image(image_path):
    """
    Validate image quality and provide recommendations
    Returns: (is_valid, warnings_list)
    """
    warnings = []

    try:
        img = Image.open(image_path)
        width, height = img.size

        # Check minimum resolution
        if width < 512 or height < 512:
            warnings.append("Низкое разрешение - рекомендуется минимум 512px")

        # Check if image is too large
        if height > 2000 or width > 2000:
            warnings.append("Изображение будет автоматически уменьшено до 2000px")

        # Check aspect ratio
        aspect_ratio = width / height
        supported_ratios = {
            "1:1": 1.0, "3:4": 0.75, "4:3": 1.33, "9:16": 0.56,
            "16:9": 1.78, "2:3": 0.67, "3:2": 1.5, "4:5": 0.8, "5:4": 1.25
        }

        # Find closest supported ratio
        closest_ratio = min(supported_ratios.values(), key=lambda x: abs(x - aspect_ratio))
        if abs(aspect_ratio - closest_ratio) > 0.15:
            warnings.append("Необычное соотношение сторон - может повлиять на качество")

        # Check brightness (simple histogram analysis)
        grayscale = img.convert('L')
        histogram = grayscale.histogram()
        pixels = sum(histogram)
        brightness = sum(i * histogram[i] for i in range(256)) / pixels

        if brightness < 80:
            warnings.append("Изображение слишком темное - улучшите освещение")
        elif brightness > 200:
            warnings.append("Изображение слишком яркое - проверьте экспозицию")

        print(f"[VALIDATION] Image: {width}x{height}, brightness: {brightness:.1f}, warnings: {len(warnings)}")

        return True, warnings

    except Exception as e:
        print(f"[VALIDATION ERROR] Failed to validate {image_path}: {e}")
        return False, ["Не удалось проанализировать изображение"]

def save_base64_image(base64_string, output_path):
    """Save base64 image to file"""
    # Remove data URL prefix if present
    if ',' in base64_string:
        base64_string = base64_string.split(',', 1)[1]

    img_data = base64.b64decode(base64_string)
    with open(output_path, 'wb') as img_file:
        img_file.write(img_data)
    return output_path

def get_public_image_url(image_path):
    """
    Get public URL for image (NanoBanana API requires URLs, not base64)

    Strategy:
    1. Use Railway public URL to serve the uploaded file directly
    2. Fallback: Try ImgBB if IMGBB_API_KEY is set
    """
    filename = os.path.basename(image_path)

    # Get Railway public URL from environment or use default
    railway_url = os.environ.get('RAILWAY_PUBLIC_DOMAIN', 'taptolook.up.railway.app')

    # Construct public URL for the uploaded file
    public_url = f"https://{railway_url}/uploads/{filename}"

    print(f"[IMAGE URL] Generated public URL: {public_url}")

    # Optional: Try ImgBB if API key is explicitly set (not required)
    imgbb_key = os.environ.get('IMGBB_API_KEY', '')
    if imgbb_key and imgbb_key != '':
        try:
            print(f"[IMGBB] Attempting to upload to ImgBB as alternative...")
            image_b64 = image_to_base64(image_path)

            imgbb_url = "https://api.imgbb.com/1/upload"
            payload = {
                'key': imgbb_key,
                'image': image_b64,
                'expiration': 600  # Auto-delete after 10 minutes
            }

            response = requests.post(imgbb_url, data=payload, timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    imgbb_public_url = result['data']['url']
                    print(f"[IMGBB] Successfully uploaded: {imgbb_public_url}")
                    return imgbb_public_url
        except Exception as e:
            print(f"[IMGBB] Upload failed, using Railway URL: {e}")

    # Return Railway public URL
    return public_url

def process_with_nanobanana(person_image_path, garment_image_path, category='auto'):
    """
    Process virtual try-on using Nano Banana (Google Gemini 2.5 Flash)
    Via Official NanoBananaAPI.ai: https://nanobananaapi.ai/

    Nano Banana is Google's image editing model powered by Gemini 2.5 Flash
    Pricing: $0.02 per image (cheaper than FASHN!)
    Speed: Very fast generation (5-10 seconds)

    API Documentation: https://docs.nanobananaapi.ai/quickstart
    """
    try:
        print(f"[NANOBANANA] 🍌 Starting Nano Banana processing...")

        if not NANOBANANA_API_KEY:
            raise ValueError(
                "NANOBANANA_API_KEY not set. Please add to Railway environment variables.\n"
                "Get your API key from: https://nanobananaapi.ai/api-key"
            )

        # Preprocess images
        print(f"[NANOBANANA] Preprocessing images...")
        person_image_optimized = preprocess_image(person_image_path, max_height=2000, quality=95)
        garment_image_optimized = preprocess_image(garment_image_path, max_height=2000, quality=95)

        # NanoBananaAPI requires image URLs, not base64
        # Generate public URLs for uploaded images (served via Railway)
        print(f"[NANOBANANA] Generating public URLs for images...")

        person_image_url = get_public_image_url(person_image_optimized)
        garment_image_url = get_public_image_url(garment_image_optimized)

        print(f"[NANOBANANA] Person image URL: {person_image_url}")
        print(f"[NANOBANANA] Garment image URL: {garment_image_url}")

        # Create prompt for virtual try-on using Nano Banana's image editing
        category_map = {
            'auto': 'garment',
            'tops': 'top',
            'bottoms': 'bottom',
            'one-pieces': 'full outfit'
        }
        garment_type = category_map.get(category, category)

        prompt = f"""Edit this image to show the person wearing the {garment_type} from the reference image.
        Requirements:
        - Realistically fit the garment on the person's body
        - Preserve the person's pose, face, and body proportions
        - Match lighting and shadows naturally
        - Keep the garment's color, texture, and style exactly as shown
        - Photorealistic quality
        - Natural fabric draping and wrinkles
        """

        print(f"[NANOBANANA] Sending request to NanoBananaAPI.ai...")
        print(f"[NANOBANANA] Prompt: {prompt[:100]}...")

        # Prepare API request
        headers = {
            "Authorization": f"Bearer {NANOBANANA_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "prompt": prompt,
            "type": "IMAGETOIAMGE",  # Image editing mode (API has typo: IAMGE not IMAGE)
            "numImages": 1,
            "imageUrls": [person_image_url, garment_image_url],  # Input images
            "callBackUrl": ""  # We'll poll instead of using callback
        }

        # Submit generation task
        generate_url = f"{NANOBANANA_BASE_URL}/generate"
        print(f"[NANOBANANA] POST to: {generate_url}")
        response = requests.post(
            generate_url,
            headers=headers,
            json=payload,
            timeout=30
        )

        print(f"[NANOBANANA] API Response Status: {response.status_code}")

        if response.status_code != 200:
            error_msg = f"NanoBanana API error: {response.status_code} - {response.text}"
            print(f"[NANOBANANA ERROR] {error_msg}")
            raise ValueError(error_msg)

        result = response.json()
        print(f"[NANOBANANA] Initial response: {result}")

        if result.get('code') != 200:
            raise ValueError(f"NanoBanana API error: {result.get('msg', 'Unknown error')}")

        task_id = result.get('data', {}).get('taskId')
        if not task_id:
            raise ValueError("No taskId returned from NanoBanana API")

        print(f"[NANOBANANA] Task created: {task_id}")
        print(f"[NANOBANANA] Polling for completion...")

        # Poll for task completion (max 120 seconds - increased for reliability)
        max_attempts = 60  # Increased from 30 to 60
        poll_interval = 2  # seconds

        for attempt in range(max_attempts):
            # Sleep before check (except first attempt)
            if attempt > 0:
                time.sleep(poll_interval)

            status_url = f"{NANOBANANA_BASE_URL}/record-info?taskId={task_id}"
            print(f"[NANOBANANA] GET status check {attempt + 1}/{max_attempts}: {status_url}")
            
            try:
                status_response = requests.get(status_url, headers=headers, timeout=10)
            except requests.exceptions.RequestException as e:
                print(f"[NANOBANANA WARNING] Request failed: {e}")
                continue  # Continue polling on network errors

            if status_response.status_code == 200:
                try:
                    status_data = status_response.json()
                    print(f"[NANOBANANA] Status check {attempt + 1}/{max_attempts}: {status_data}")
                except ValueError as e:
                    print(f"[NANOBANANA WARNING] Failed to parse JSON: {e}, response: {status_response.text[:200]}")
                    continue

                # Handle successFlag - can be int or string
                success_flag_raw = status_data.get('successFlag', 0)
                # Convert to int if it's a string
                if isinstance(success_flag_raw, str):
                    try:
                        success_flag = int(success_flag_raw)
                    except (ValueError, TypeError):
                        success_flag = 0
                else:
                    success_flag = int(success_flag_raw) if success_flag_raw else 0

                print(f"[NANOBANANA] Parsed success_flag: {success_flag} (type: {type(success_flag)}, raw: {success_flag_raw})")

                if success_flag == 1:
                    # Task completed successfully
                    print(f"[NANOBANANA] ✅ Task completed! Extracting result URL...")
                    
                    # Try multiple possible paths for resultImageUrl
                    result_image_url = None
                    response_obj = status_data.get('response', {})
                    
                    if isinstance(response_obj, dict):
                        result_image_url = response_obj.get('resultImageUrl') or response_obj.get('result_image_url')
                    
                    # Also check top-level
                    if not result_image_url:
                        result_image_url = status_data.get('resultImageUrl') or status_data.get('result_image_url')
                    
                    print(f"[NANOBANANA] Result URL found: {result_image_url}")
                    
                    if not result_image_url:
                        print(f"[NANOBANANA ERROR] Full status_data structure: {status_data}")
                        raise ValueError("No result image URL in completed task. Check logs for full response structure.")

                    print(f"[NANOBANANA] ✅ Generation complete! Downloading result from: {result_image_url}")

                    # Download result image
                    timestamp = int(time.time())
                    result_filename = f'result_nanobanana_{timestamp}.png'
                    result_path = os.path.join(app.config['RESULTS_FOLDER'], result_filename)

                    try:
                        img_response = requests.get(result_image_url, timeout=30)
                        if img_response.status_code == 200:
                            with open(result_path, 'wb') as img_file:
                                img_file.write(img_response.content)
                            print(f"[NANOBANANA] ✅ Result saved: {result_path} ({len(img_response.content)} bytes)")
                            return result_path
                        else:
                            raise ValueError(f"Failed to download result: HTTP {img_response.status_code}")
                    except requests.exceptions.RequestException as e:
                        raise ValueError(f"Failed to download result image: {e}")

                elif success_flag == 2:
                    error_msg = status_data.get('msg', 'Task creation failed')
                    raise ValueError(f"Task creation failed: {error_msg}")
                elif success_flag == 3:
                    error_msg = status_data.get('msg', 'Generation failed')
                    raise ValueError(f"Generation failed: {error_msg}")
                # success_flag == 0 means still processing, continue polling
                else:
                    print(f"[NANOBANANA] Task still processing (successFlag={success_flag}), continuing...")

            elif status_response.status_code == 404:
                # 404 might mean task not found yet, continue polling
                print(f"[NANOBANANA WARNING] Status check returned 404 (task may not be ready yet), continuing...")
            else:
                print(f"[NANOBANANA WARNING] Status check failed: {status_response.status_code} - {status_response.text[:200]}")

        # Timeout
        raise ValueError(f"Task timed out after {max_attempts * poll_interval} seconds ({max_attempts} attempts)")

    except Exception as e:
        print(f"[NANOBANANA ERROR] ❌ Error in process_with_nanobanana: {e}")
        import traceback
        traceback.print_exc()
        raise

def process_with_fashn(person_image_path, garment_image_path, category='auto'):
    """
    Process virtual try-on using FASHN API
    Generates high-quality realistic results in 5-17 seconds

    Now includes:
    - Image preprocessing (resize, optimize)
    - Enhanced API parameters for better quality
    - Validation and warnings
    """
    try:
        if not FASHN_API_KEY:
            raise ValueError("FASHN_API_KEY not set. Please configure your API key in environment variables.")

        print(f"[FASHN] Starting image preprocessing...")

        # Preprocess images according to FASHN best practices
        person_image_optimized = preprocess_image(person_image_path, max_height=2000, quality=95)
        garment_image_optimized = preprocess_image(garment_image_path, max_height=2000, quality=95)

        # Convert images to base64
        model_image_b64 = image_to_base64(person_image_optimized)
        garment_image_b64 = image_to_base64(garment_image_optimized)

        # Prepare request payload with enhanced parameters
        input_data = {
            "model_name": "tryon-v1.6",
            "inputs": {
                "model_image": f"data:image/jpg;base64,{model_image_b64}",
                "garment_image": f"data:image/jpg;base64,{garment_image_b64}",
                "category": category,            # User-selected or auto category
                "garment_photo_type": "auto",    # Auto-detect flat-lay vs model
                "segmentation_free": True,       # Better for bulky garments
                "num_samples": 1,                # Generate 1 result per image
                "mode": "quality",               # Use quality mode for best results
                "output_format": "png",          # PNG for maximum quality
                "seed": 42                       # Reproducible results
            }
        }

        print(f"[FASHN] Using category: {category}")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {FASHN_API_KEY}"
        }

        print(f"[FASHN] Sending request to FASHN API...")
        print(f"[FASHN] API Key (first 10 chars): {FASHN_API_KEY[:10]}...")
        print(f"[FASHN] Model image size: {len(model_image_b64)} chars")
        print(f"[FASHN] Garment image size: {len(garment_image_b64)} chars")

        # POST to /run endpoint
        run_response = requests.post(f"{FASHN_BASE_URL}/run", json=input_data, headers=headers, timeout=60)

        print(f"[FASHN] Response status code: {run_response.status_code}")

        if run_response.status_code != 200:
            error_msg = f"FASHN API error: {run_response.status_code} - {run_response.text}"
            print(f"[FASHN ERROR] {error_msg}")
            raise ValueError(error_msg)

        run_data = run_response.json()
        print(f"[FASHN] Response data: {run_data}")

        prediction_id = run_data.get("id")

        if not prediction_id:
            error_detail = run_data.get("error", "No error message")
            raise ValueError(f"Failed to get prediction ID from FASHN API. Response: {error_detail}")

        print(f"[FASHN] Prediction started, ID: {prediction_id}")

        # Poll /status/<ID> until completion
        max_attempts = 40  # 40 attempts * 3 seconds = 2 minutes max
        attempt = 0

        while attempt < max_attempts:
            time.sleep(3)  # Wait 3 seconds between checks

            status_response = requests.get(f"{FASHN_BASE_URL}/status/{prediction_id}", headers=headers, timeout=30)

            if status_response.status_code != 200:
                print(f"Status check error: {status_response.status_code}")
                attempt += 1
                continue

            status_data = status_response.json()
            status = status_data.get("status")

            print(f"[FASHN] Attempt {attempt + 1}/{max_attempts} - Status: {status}")

            if status == "completed":
                # Get the output image
                output = status_data.get("output")

                if not output:
                    raise ValueError("No output image in completed response")

                print(f"[FASHN] Output type: {type(output)}, value: {output}")

                # FASHN API returns a list of images (even if num_samples=1)
                if isinstance(output, list):
                    if len(output) == 0:
                        raise ValueError("FASHN returned empty output list")
                    # Get the first image from the list
                    result_image_data = output[0]
                    print(f"[FASHN] Using first image from list, type: {type(result_image_data)}")
                elif isinstance(output, str):
                    result_image_data = output
                elif isinstance(output, dict) and "url" in output:
                    result_image_data = output["url"]
                elif isinstance(output, dict) and "image" in output:
                    result_image_data = output["image"]
                else:
                    raise ValueError(f"Unexpected output format: {type(output)}")

                # If result_image_data is a dict, extract the URL or image
                if isinstance(result_image_data, dict):
                    if "url" in result_image_data:
                        result_image_data = result_image_data["url"]
                    elif "image" in result_image_data:
                        result_image_data = result_image_data["image"]
                    else:
                        raise ValueError(f"Dict output missing 'url' or 'image' key: {result_image_data}")

                print(f"[FASHN] Final image data type: {type(result_image_data)}")
                if isinstance(result_image_data, str):
                    print(f"[FASHN] Image data starts with: {result_image_data[:100]}...")

                # Save result
                timestamp = int(time.time())
                result_filename = f'result_{timestamp}_{prediction_id[:8]}.png'
                result_path = os.path.join(app.config['RESULTS_FOLDER'], result_filename)

                # Download or save the image
                if isinstance(result_image_data, str) and result_image_data.startswith('http'):
                    # Download from URL
                    print(f"[FASHN] Downloading from URL: {result_image_data[:50]}...")
                    img_response = requests.get(result_image_data, timeout=30)
                    if img_response.status_code == 200:
                        with open(result_path, 'wb') as img_file:
                            img_file.write(img_response.content)
                        print(f"[FASHN] Downloaded {len(img_response.content)} bytes")
                    else:
                        raise ValueError(f"Failed to download result image: {img_response.status_code}")
                elif isinstance(result_image_data, str):
                    # Save base64 image
                    print(f"[FASHN] Saving base64 image...")
                    save_base64_image(result_image_data, result_path)
                else:
                    raise ValueError(f"Cannot process result_image_data of type: {type(result_image_data)}")

                print(f"[FASHN] ✅ Result saved to: {result_path}")
                return result_path

            elif status in ["starting", "in_queue", "processing"]:
                # Still processing, continue polling
                attempt += 1
                continue
            elif status == "failed":
                error = status_data.get("error", "Unknown error")
                error_str = str(error).lower()

                # Parse FASHN API specific errors and provide user-friendly messages
                if "imageloaderror" in error_str or "unable to load" in error_str:
                    raise ValueError("IMAGE_LOAD_ERROR: Не удалось загрузить изображение. Проверьте формат и качество фото.")
                elif "poseerror" in error_str or "unable to detect" in error_str or "pose" in error_str:
                    raise ValueError("POSE_ERROR: Не удалось определить позу человека на фото. Используйте четкое фото в полный рост с хорошо видимым телом.")
                elif "contentmoderation" in error_str or "prohibited content" in error_str:
                    raise ValueError("CONTENT_ERROR: Обнаружен запрещенный контент на изображении.")
                elif "invalid" in error_str or "format" in error_str:
                    raise ValueError("FORMAT_ERROR: Неверный формат изображения. Используйте JPG или PNG.")
                else:
                    raise ValueError(f"FASHN_ERROR: {error}")
            else:
                # Unknown status
                print(f"Unknown status: {status}")
                attempt += 1
                continue

        # Timeout
        raise TimeoutError(f"FASHN processing timed out after {max_attempts * 3} seconds")

    except Exception as e:
        print(f"[FASHN ERROR] ❌ Error in process_with_fashn: {e}")
        import traceback
        traceback.print_exc()
        raise

# Serve frontend
@app.route('/')
def serve_frontend():
    return send_from_directory(FRONTEND_FOLDER, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    # Avoid conflicts with API routes
    if path.startswith('api/'):
        return jsonify({"error": "Not found"}), 404
    try:
        return send_from_directory(FRONTEND_FOLDER, path)
    except:
        # If file not found, serve index.html (SPA fallback)
        return send_from_directory(FRONTEND_FOLDER, 'index.html')

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "timestamp": time.time()
    })

@app.route('/uploads/<path:filename>', methods=['GET'])
def serve_upload(filename):
    """
    Serve uploaded images publicly (needed for NanoBanana API)
    """
    try:
        return send_from_directory(UPLOAD_FOLDER, filename)
    except Exception as e:
        print(f"[UPLOADS] Error serving file {filename}: {e}")
        return jsonify({"error": "File not found"}), 404

@app.route('/api/validate', methods=['POST'])
def validate_uploaded_image():
    """
    Validate image quality before processing
    Returns warnings and recommendations
    """
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400

        image_file = request.files['image']

        if not image_file or not allowed_file(image_file.filename):
            return jsonify({'error': 'Invalid image file'}), 400

        # Save temporarily for validation
        timestamp = int(time.time())
        filename = secure_filename(f'temp_validate_{timestamp}.{image_file.filename.rsplit(".", 1)[1].lower()}')
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image_file.save(filepath)

        # Validate image
        is_valid, warnings = validate_image(filepath)

        # Clean up temp file
        try:
            os.remove(filepath)
        except:
            pass

        return jsonify({
            'success': True,
            'is_valid': is_valid,
            'warnings': warnings
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload', methods=['POST'])
def upload_files():
    """
    Upload person images and garment image
    Expected: person_images[] (3-4 images), garment_image (1 image)
    Now includes automatic validation and warnings
    """
    try:
        # Check if files are present
        if 'person_images' not in request.files:
            return jsonify({'error': 'No person images provided'}), 400

        if 'garment_image' not in request.files:
            return jsonify({'error': 'No garment image provided'}), 400

        person_files = request.files.getlist('person_images')
        garment_file = request.files['garment_image']

        # Validate person images count
        if len(person_files) < 1 or len(person_files) > 4:
            return jsonify({'error': 'Please upload 1-4 person images'}), 400

        # Validate and save files
        person_paths = []
        person_warnings = []
        timestamp = int(time.time())

        for idx, person_file in enumerate(person_files):
            if person_file and allowed_file(person_file.filename):
                filename = secure_filename(f'person_{timestamp}_{idx}.{person_file.filename.rsplit(".", 1)[1].lower()}')
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                person_file.save(filepath)
                person_paths.append(filepath)

                # Validate each person image
                is_valid, warnings = validate_image(filepath)
                if warnings:
                    person_warnings.append({
                        'image_index': idx,
                        'warnings': warnings
                    })
            else:
                return jsonify({'error': f'Invalid person image file: {person_file.filename}'}), 400

        if garment_file and allowed_file(garment_file.filename):
            garment_filename = secure_filename(f'garment_{timestamp}.{garment_file.filename.rsplit(".", 1)[1].lower()}')
            garment_path = os.path.join(app.config['UPLOAD_FOLDER'], garment_filename)
            garment_file.save(garment_path)

            # Validate garment image
            is_valid, garment_warnings = validate_image(garment_path)
        else:
            return jsonify({'error': 'Invalid garment image file'}), 400

        response_data = {
            'success': True,
            'person_images': person_paths,
            'garment_image': garment_path,
            'session_id': timestamp
        }

        # Add warnings if any
        if person_warnings or garment_warnings:
            response_data['validation_warnings'] = {
                'person_images': person_warnings,
                'garment_image': garment_warnings
            }

        return jsonify(response_data), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tryon', methods=['POST'])
def virtual_tryon():
    """
    Perform virtual try-on
    Expects JSON: {person_images: [], garment_image: "", garment_category: "auto", ai_model: "fashn"}
    """
    try:
        data = request.get_json()

        if not data or 'person_images' not in data or 'garment_image' not in data:
            return jsonify({'error': 'Missing required data'}), 400

        person_images = data['person_images']
        garment_image = data['garment_image']
        garment_category = data.get('garment_category', 'auto')  # Get category, default to auto
        ai_model = data.get('ai_model', 'fashn')  # Get AI model, default to fashn

        if not person_images or not garment_image:
            return jsonify({'error': 'Invalid image paths'}), 400

        print(f"[TRYON] Processing with category: {garment_category}, AI model: {ai_model}")

        # Early validation for Nano Banana API key
        if ai_model == 'nanobanana':
            print(f"[TRYON] Nano Banana selected, checking API key...")
            print(f"[TRYON] NANOBANANA_API_KEY status: {'SET' if NANOBANANA_API_KEY else 'MISSING'} (length: {len(NANOBANANA_API_KEY) if NANOBANANA_API_KEY else 0})")

            if not NANOBANANA_API_KEY or NANOBANANA_API_KEY.strip() == '':
                print(f"[TRYON ERROR] NANOBANANA_API_KEY is empty or missing!")
                return jsonify({
                    'error': 'NANOBANANA_API_KEY_MISSING',
                    'message': '🍌 Nano Banana API ключ не настроен\n\n'
                              'Пожалуйста, добавьте NANOBANANA_API_KEY в Railway Variables:\n'
                              '1. Зайдите на https://nanobananaapi.ai/api-key\n'
                              '2. Создайте API ключ\n'
                              '3. Добавьте его в Railway Dashboard → Variables\n\n'
                              'Или используйте FASHN AI (переключите слайдер).'
                }), 400

            print(f"[TRYON] NANOBANANA_API_KEY validated successfully (preview: {NANOBANANA_API_KEY[:8]}...)")

        # Process each person image with the garment
        results = []

        for person_image in person_images:
            if not os.path.exists(person_image):
                continue

            try:
                # Choose processing method based on AI model
                if ai_model == 'nanobanana':
                    result_path = process_with_nanobanana(person_image, garment_image, garment_category)
                else:
                    result_path = process_with_fashn(person_image, garment_image, garment_category)

                # Read result image and encode to base64
                with open(result_path, 'rb') as img_file:
                    img_data = base64.b64encode(img_file.read()).decode('utf-8')

                results.append({
                    'original': os.path.basename(person_image),
                    'result_path': result_path,
                    'result_image': f'data:image/png;base64,{img_data}'
                })
            except Exception as e:
                print(f"Error processing {person_image}: {e}")
                results.append({
                    'original': os.path.basename(person_image),
                    'error': str(e)
                })

        return jsonify({
            'success': True,
            'results': results
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/result/<filename>', methods=['GET'])
def get_result(filename):
    """
    Retrieve result image
    """
    try:
        file_path = os.path.join(app.config['RESULTS_FOLDER'], filename)
        if os.path.exists(file_path):
            return send_file(file_path, mimetype='image/png')
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cleanup', methods=['POST'])
def cleanup():
    """
    Clean up old files
    """
    try:
        # Delete files older than 1 hour
        current_time = time.time()
        cleanup_count = 0

        for folder in [app.config['UPLOAD_FOLDER'], app.config['RESULTS_FOLDER']]:
            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                if os.path.isfile(file_path):
                    file_age = current_time - os.path.getmtime(file_path)
                    if file_age > 3600:  # 1 hour
                        os.remove(file_path)
                        cleanup_count += 1

        return jsonify({
            'success': True,
            'files_removed': cleanup_count
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("=" * 60)
    print("Virtual Try-On Server Starting...")
    print("=" * 60)
    print(f"Upload folder: {UPLOAD_FOLDER}")
    print(f"Results folder: {RESULTS_FOLDER}")
    print("=" * 60)

    # Diagnostic: Show ALL environment variables containing "NANO" or "API"
    print("[DIAGNOSTICS] All Environment Variables containing 'NANO' or 'API':")
    for key, value in os.environ.items():
        if 'NANO' in key.upper() or 'API' in key.upper():
            preview = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else value
            print(f"  {key}: {preview} (length: {len(value)})")
    print("=" * 60)

    # Diagnostic: Show API key status
    print("[DIAGNOSTICS] API Keys Status:")
    print(f"  FASHN_API_KEY: {'✅ SET' if FASHN_API_KEY else '❌ MISSING'} (length: {len(FASHN_API_KEY) if FASHN_API_KEY else 0})")
    print(f"  NANOBANANA_API_KEY: {'✅ SET' if NANOBANANA_API_KEY else '❌ MISSING'} (length: {len(NANOBANANA_API_KEY) if NANOBANANA_API_KEY else 0})")

    if NANOBANANA_API_KEY:
        print(f"  NANOBANANA_API_KEY preview: {NANOBANANA_API_KEY[:8]}...{NANOBANANA_API_KEY[-4:]}")
    else:
        print("  ⚠️ WARNING: NANOBANANA_API_KEY not set! Nano Banana will not work.")
        print(f"  ℹ️ Checked variables: NANOBANANA_API_KEY, nanobanana_api_key")

    print("=" * 60)

    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
