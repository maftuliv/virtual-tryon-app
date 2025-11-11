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
FASHN_API_KEY = os.environ.get('FASHN_API_KEY', '')  # FASHN AI token
FASHN_BASE_URL = "https://api.fashn.ai/v1"

# Nano Banana API (Google Gemini 2.5 Flash) - Official API
NANOBANANA_API_KEY = os.environ.get('NANOBANANA_API_KEY', '')  # NanoBananaAPI.ai token
NANOBANANA_BASE_URL = "https://api.nanobananaapi.ai/api/v1/nanobanana"

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

def upload_image_to_imgbb(image_path):
    """
    Upload image to ImgBB to get a public URL (NanoBanana API requires URLs, not base64)
    Using free ImgBB API as temporary image hosting
    """
    try:
        # Convert image to base64
        image_b64 = image_to_base64(image_path)

        # ImgBB free API endpoint (no key needed for basic usage)
        imgbb_url = "https://api.imgbb.com/1/upload"

        # Use a public API key (or user can set their own IMGBB_API_KEY env var)
        imgbb_key = os.environ.get('IMGBB_API_KEY', '3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e')  # Placeholder

        payload = {
            'key': imgbb_key,
            'image': image_b64,
            'expiration': 600  # Auto-delete after 10 minutes
        }

        response = requests.post(imgbb_url, data=payload, timeout=30)
        response.raise_for_status()

        result = response.json()
        if result.get('success'):
            return result['data']['url']
        else:
            raise ValueError(f"ImgBB upload failed: {result.get('error', {}).get('message', 'Unknown error')}")

    except Exception as e:
        print(f"[IMGBB ERROR] Failed to upload to ImgBB: {e}")
        # Fallback: serve from our own server if Railway deployment is available
        # This assumes the backend is publicly accessible
        filename = os.path.basename(image_path)
        # Return relative path that frontend can access
        return f"/uploads/{filename}"

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
        # Option 1: Upload to temporary image host (ImgBB)
        # Option 2: Serve from our own publicly accessible server
        print(f"[NANOBANANA] Uploading images to get public URLs...")

        # For Railway deployment, images are already accessible via public URL
        # We'll use ImgBB as a fallback for local development
        try:
            person_image_url = upload_image_to_imgbb(person_image_optimized)
            garment_image_url = upload_image_to_imgbb(garment_image_optimized)
            print(f"[NANOBANANA] Image URLs obtained successfully")
        except Exception as upload_error:
            print(f"[NANOBANANA WARNING] ImgBB upload failed, trying alternative method: {upload_error}")
            # Fallback: use local server paths (works if backend is publicly accessible)
            person_image_url = f"https://taptolook.up.railway.app/uploads/{os.path.basename(person_image_optimized)}"
            garment_image_url = f"https://taptolook.up.railway.app/uploads/{os.path.basename(garment_image_optimized)}"

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
            "type": "IMAGETOIMAGE",  # Image editing mode
            "numImages": 1,
            "imageUrls": [person_image_url, garment_image_url],  # Input images
            "callBackUrl": ""  # We'll poll instead of using callback
        }

        # Submit generation task
        response = requests.post(
            NANOBANANA_BASE_URL,
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

        # Poll for task completion (max 60 seconds)
        max_attempts = 30
        poll_interval = 2  # seconds

        for attempt in range(max_attempts):
            time.sleep(poll_interval)

            status_url = f"{NANOBANANA_BASE_URL}/record-info?taskId={task_id}"
            status_response = requests.get(status_url, headers=headers, timeout=10)

            if status_response.status_code == 200:
                status_data = status_response.json()
                print(f"[NANOBANANA] Status check {attempt + 1}/{max_attempts}: {status_data}")

                success_flag = status_data.get('successFlag', 0)

                if success_flag == 1:
                    # Task completed successfully
                    result_image_url = status_data.get('response', {}).get('resultImageUrl')
                    if not result_image_url:
                        raise ValueError("No result image URL in completed task")

                    print(f"[NANOBANANA] ✅ Generation complete! Downloading result...")

                    # Download result image
                    timestamp = int(time.time())
                    result_filename = f'result_nanobanana_{timestamp}.png'
                    result_path = os.path.join(app.config['RESULTS_FOLDER'], result_filename)

                    img_response = requests.get(result_image_url, timeout=30)
                    if img_response.status_code == 200:
                        with open(result_path, 'wb') as img_file:
                            img_file.write(img_response.content)
                        print(f"[NANOBANANA] ✅ Result saved: {result_path} ({len(img_response.content)} bytes)")
                        return result_path
                    else:
                        raise ValueError(f"Failed to download result: {img_response.status_code}")

                elif success_flag == 2:
                    raise ValueError("Task creation failed")
                elif success_flag == 3:
                    raise ValueError("Generation failed")
                # success_flag == 0 means still processing, continue polling

            else:
                print(f"[NANOBANANA WARNING] Status check failed: {status_response.status_code}")

        # Timeout
        raise ValueError(f"Task timed out after {max_attempts * poll_interval} seconds")

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

    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
