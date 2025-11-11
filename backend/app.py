import os
import time
import base64
import json
import requests
from datetime import datetime
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
FEEDBACK_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'feedback')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Create folders if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)
os.makedirs(FEEDBACK_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULTS_FOLDER'] = RESULTS_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Removed: Task storage system - using simple synchronous processing instead

# API configurations
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
print(f"  NANOBANANA_API_KEY: {'✅ SET' if NANOBANANA_API_KEY else '❌ MISSING'} (length: {len(NANOBANANA_API_KEY)})")

# Check Telegram variables
TELEGRAM_BOT_TOKEN_CHECK = os.environ.get('TELEGRAM_BOT_TOKEN', '').strip()
TELEGRAM_CHAT_ID_CHECK = os.environ.get('TELEGRAM_CHAT_ID', '').strip()
print(f"\n[TELEGRAM] Configuration check:")
print(f"  TELEGRAM_BOT_TOKEN: {'✅ SET' if TELEGRAM_BOT_TOKEN_CHECK else '❌ MISSING'} (length: {len(TELEGRAM_BOT_TOKEN_CHECK)})")
print(f"  TELEGRAM_CHAT_ID: {'✅ SET' if TELEGRAM_CHAT_ID_CHECK else '❌ MISSING'} (value: {TELEGRAM_CHAT_ID_CHECK})")
if not TELEGRAM_BOT_TOKEN_CHECK or not TELEGRAM_CHAT_ID_CHECK:
    print(f"  ⚠️  Telegram notifications will be disabled until variables are set")

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
    Preprocess image for optimal quality:
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
    Pricing: $0.02 per image
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

        # Create optimized prompt for virtual try-on
        # NanoBanana API works best with clear, direct instructions for outfit editing
        category_map = {
            'auto': 'garment',
            'tops': 'top',
            'bottoms': 'bottom',
            'one-pieces': 'full outfit'
        }
        garment_type = category_map.get(category, 'garment')

        # Optimized prompt for virtual try-on (based on NanoBanana outfit editing best practices)
        prompt = f"Put the {garment_type} from the second image onto the person in the first image. The garment should fit naturally on the person's body, maintaining their original pose and proportions. Keep the garment's exact color, pattern, and style. Ensure realistic lighting, shadows, and fabric texture."

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

                # Extract data object (API wraps response in 'data' field)
                data_obj = status_data.get('data', {})
                if not isinstance(data_obj, dict):
                    print(f"[NANOBANANA WARNING] Invalid data structure, continuing...")
                    continue

                # Handle successFlag - can be int or string, located in data.successFlag
                success_flag_raw = data_obj.get('successFlag', 0)
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
                    
                    # resultImageUrl is in data.response.resultImageUrl
                    result_image_url = None
                    response_obj = data_obj.get('response', {})
                    
                    if isinstance(response_obj, dict):
                        result_image_url = response_obj.get('resultImageUrl') or response_obj.get('result_image_url')
                    
                    # Fallback: check top-level (shouldn't happen but just in case)
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
                    error_msg = data_obj.get('errorMessage') or status_data.get('msg', 'Task creation failed')
                    raise ValueError(f"Task creation failed: {error_msg}")
                elif success_flag == 3:
                    error_msg = data_obj.get('errorMessage') or status_data.get('msg', 'Generation failed')
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

# FASHN AI removed - using only NanoBanana API

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
    Perform virtual try-on using NanoBanana API (synchronous)
    Expects JSON: {person_images: [], garment_image: "", garment_category: "auto"}
    Returns: {success: true, results: [...]}
    """
    try:
        data = request.get_json()

        if not data or 'person_images' not in data or 'garment_image' not in data:
            return jsonify({'error': 'Missing required data'}), 400

        person_images = data['person_images']
        garment_image = data['garment_image']
        garment_category = data.get('garment_category', 'auto')

        if not person_images or not garment_image:
            return jsonify({'error': 'Invalid image paths'}), 400

        print(f"[TRYON] Processing with category: {garment_category}, AI model: nanobanana")

        # Validate Nano Banana API key
        if not NANOBANANA_API_KEY or NANOBANANA_API_KEY.strip() == '':
            return jsonify({
                'error': 'NANOBANANA_API_KEY_MISSING',
                'message': '🍌 Nano Banana API ключ не настроен\n\n'
                          'Пожалуйста, добавьте NANOBANANA_API_KEY в Railway Variables:\n'
                          '1. Зайдите на https://nanobananaapi.ai/api-key\n'
                          '2. Создайте API ключ\n'
                          '3. Добавьте его в Railway Dashboard → Variables'
            }), 400

        # Process each person image with the garment using NanoBanana
        results = []

        for person_image in person_images:
            if not os.path.exists(person_image):
                continue

            try:
                # Always use NanoBanana API
                result_path = process_with_nanobanana(person_image, garment_image, garment_category)

                # Generate public URL for result image
                result_filename = os.path.basename(result_path)
                railway_url = os.environ.get('RAILWAY_PUBLIC_DOMAIN', 'taptolook.up.railway.app')
                result_url = f"https://{railway_url}/api/result/{result_filename}"

                # Read result image and encode to base64 for frontend
                with open(result_path, 'rb') as img_file:
                    img_data = base64.b64encode(img_file.read()).decode('utf-8')

                results.append({
                    'original': os.path.basename(person_image),
                    'result_path': result_path,
                    'result_image': f'data:image/png;base64,{img_data}'
                })
            except Exception as e:
                print(f"Error processing {person_image}: {e}")
                import traceback
                traceback.print_exc()
                results.append({
                    'original': os.path.basename(person_image),
                    'error': str(e)
                })

        return jsonify({
            'success': True,
            'results': results
        }), 200

    except Exception as e:
        print(f"[TRYON ERROR] {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/result/<filename>', methods=['GET'])
def get_result(filename):
    """
    Retrieve result image
    """
    try:
        # Security: prevent directory traversal
        filename = secure_filename(filename)
        file_path = os.path.join(app.config['RESULTS_FOLDER'], filename)
        
        # Additional security check
        if not os.path.abspath(file_path).startswith(os.path.abspath(app.config['RESULTS_FOLDER'])):
            return jsonify({'error': 'Invalid file path'}), 403
        
        if os.path.exists(file_path):
            # Determine MIME type from extension
            ext = filename.rsplit('.', 1)[-1].lower()
            mimetype_map = {
                'png': 'image/png',
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg'
            }
            mimetype = mimetype_map.get(ext, 'image/png')
            
            print(f"[RESULT] Serving result image: {filename} ({mimetype})")
            return send_file(file_path, mimetype=mimetype)
        else:
            print(f"[RESULT] File not found: {filename}")
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        print(f"[RESULT ERROR] {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    """
    Save user feedback (rating and comment)
    Saves to JSON file and optionally sends to Telegram if configured
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        rating = data.get('rating')
        comment = data.get('comment', '')
        timestamp = data.get('timestamp', datetime.now().isoformat())
        session_id = data.get('session_id')
        
        if not rating or not isinstance(rating, int) or rating < 1 or rating > 5:
            return jsonify({'error': 'Invalid rating. Must be 1-5'}), 400
        
        # Prepare feedback data
        feedback_data = {
            'rating': rating,
            'comment': comment,
            'timestamp': timestamp,
            'session_id': session_id,
            'ip_address': request.remote_addr
        }
        
        # Save to JSON file
        feedback_file = os.path.join(FEEDBACK_FOLDER, f'feedback_{int(time.time())}.json')
        try:
            with open(feedback_file, 'w', encoding='utf-8') as f:
                json.dump(feedback_data, f, ensure_ascii=False, indent=2)
            
            # Verify file was saved
            if os.path.exists(feedback_file):
                file_size = os.path.getsize(feedback_file)
                print(f"[FEEDBACK] ✅ Saved feedback: rating={rating}, comment_length={len(comment)}")
                print(f"[FEEDBACK] ✅ File saved to: {feedback_file} (size: {file_size} bytes)")
            else:
                print(f"[FEEDBACK] ❌ ERROR: File was not created: {feedback_file}")
        except Exception as e:
            print(f"[FEEDBACK] ❌ ERROR saving file: {e}")
            import traceback
            traceback.print_exc()
            raise
        
        # Optional: Send to Telegram if configured
        telegram_bot_token = os.environ.get('TELEGRAM_BOT_TOKEN', '').strip()
        telegram_chat_id = os.environ.get('TELEGRAM_CHAT_ID', '').strip()
        
        print(f"[FEEDBACK] Telegram config check:")
        print(f"  TELEGRAM_BOT_TOKEN: {'✅ SET' if telegram_bot_token else '❌ MISSING'} (length: {len(telegram_bot_token)})")
        print(f"  TELEGRAM_CHAT_ID: {'✅ SET' if telegram_chat_id else '❌ MISSING'} (value: {telegram_chat_id})")
        
        # If only token is set, automatically get chat_id from last message
        if telegram_bot_token and not telegram_chat_id:
            print(f"[FEEDBACK] 🔍 Auto-detecting Chat ID from bot messages...")
            try:
                # Get updates with offset=0 to get all pending updates
                updates_url = f"https://api.telegram.org/bot{telegram_bot_token}/getUpdates"
                updates_params = {
                    'offset': 0,  # Get all pending updates
                    'timeout': 10
                }
                updates_response = requests.get(updates_url, params=updates_params, timeout=15)
                
                print(f"[FEEDBACK] getUpdates response status: {updates_response.status_code}")
                
                if updates_response.status_code == 200:
                    updates_data = updates_response.json()
                    print(f"[FEEDBACK] getUpdates response: ok={updates_data.get('ok')}, result_count={len(updates_data.get('result', []))}")
                    
                    if updates_data.get('ok'):
                        updates_result = updates_data.get('result', [])
                        
                        if updates_result:
                            # Get the most recent message (last in array)
                            last_update = updates_result[-1]
                            print(f"[FEEDBACK] Last update keys: {list(last_update.keys())}")
                            
                            message = last_update.get('message') or last_update.get('edited_message') or last_update.get('channel_post')
                            
                            if message:
                                chat = message.get('chat', {})
                                print(f"[FEEDBACK] Chat object: {chat}")
                                
                                # Chat ID can be int or str, but Telegram API accepts both
                                chat_id_value = chat.get('id')
                                if chat_id_value:
                                    telegram_chat_id = str(chat_id_value)  # Convert to string for consistency
                                    print(f"[FEEDBACK] ✅ Auto-detected Chat ID: {telegram_chat_id}")
                                    print(f"[FEEDBACK] 📱 Chat info: {chat.get('first_name', '')} {chat.get('last_name', '')} (@{chat.get('username', 'N/A')})")
                                else:
                                    print(f"[FEEDBACK] ⚠️  Could not extract Chat ID from message")
                                    print(f"[FEEDBACK] Message structure: {message}")
                            else:
                                print(f"[FEEDBACK] ⚠️  No message found in last update")
                                print(f"[FEEDBACK] Update structure: {last_update}")
                        else:
                            print(f"[FEEDBACK] ⚠️  No messages found. Please send a message to your bot first!")
                            print(f"[FEEDBACK] 💡 Tip: Write any message to your bot in Telegram, then try again")
                            print(f"[FEEDBACK] Full response: {updates_data}")
                    else:
                        error_desc = updates_data.get('description', 'Unknown error')
                        error_code = updates_data.get('error_code', 'N/A')
                        print(f"[FEEDBACK] ❌ Telegram API error: {error_code} - {error_desc}")
                        print(f"[FEEDBACK] Full error response: {updates_data}")
                else:
                    print(f"[FEEDBACK] ❌ Failed to get updates: HTTP {updates_response.status_code}")
                    print(f"[FEEDBACK] Response: {updates_response.text[:500]}")
                    
            except Exception as e:
                print(f"[FEEDBACK] ❌ Could not auto-detect Chat ID: {e}")
                import traceback
                traceback.print_exc()
        
        if telegram_bot_token and telegram_chat_id:
            try:
                # Format message for Telegram (using HTML format - simpler and more reliable)
                stars = '⭐' * rating + '☆' * (5 - rating)
                message = f"📊 <b>Новый отзыв</b>\n\n"
                message += f"⭐ Оценка: {stars} ({rating}/5)\n"
                if comment:
                    # Escape HTML special characters in comment
                    safe_comment = comment.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    message += f"💬 Комментарий: {safe_comment}\n"
                message += f"🕐 Время: {timestamp}\n"
                if session_id:
                    message += f"🆔 Session: {session_id[:8]}...\n"
                
                telegram_url = f"https://api.telegram.org/bot{telegram_bot_token}/sendMessage"
                
                # Chat ID should be integer or string - try integer first (Telegram API accepts both)
                try:
                    chat_id_int = int(telegram_chat_id)
                except (ValueError, TypeError):
                    chat_id_int = telegram_chat_id
                
                telegram_data = {
                    'chat_id': chat_id_int,  # Use integer format (Telegram prefers this)
                    'text': message,
                    'parse_mode': 'HTML'  # Use HTML instead of MarkdownV2 (simpler, no escaping needed)
                }
                
                print(f"[FEEDBACK] Sending to Telegram: chat_id={chat_id_int}, message_length={len(message)}")
                
                telegram_response = requests.post(telegram_url, json=telegram_data, timeout=10)
                if telegram_response.status_code == 200:
                    response_data = telegram_response.json()
                    if response_data.get('ok'):
                        print(f"[FEEDBACK] ✅ Sent to Telegram successfully")
                        print(f"[FEEDBACK] Message ID: {response_data.get('result', {}).get('message_id', 'N/A')}")
                    else:
                        print(f"[FEEDBACK] ❌ Telegram API error: {response_data.get('description', 'Unknown')}")
                else:
                    print(f"[FEEDBACK] ❌ Telegram HTTP error: {telegram_response.status_code}")
                    try:
                        error_data = telegram_response.json()
                        print(f"[FEEDBACK] Error details: {error_data}")
                    except:
                        print(f"[FEEDBACK] Response text: {telegram_response.text[:500]}")
            except Exception as e:
                print(f"[FEEDBACK] ❌ Telegram error (non-critical): {e}")
                import traceback
                traceback.print_exc()
        else:
            if not telegram_bot_token:
                print(f"[FEEDBACK] ⚠️ TELEGRAM_BOT_TOKEN not set - skipping Telegram notification")
            if not telegram_chat_id:
                print(f"[FEEDBACK] ⚠️ TELEGRAM_CHAT_ID not set - skipping Telegram notification")
        
        return jsonify({
            'success': True,
            'message': 'Feedback saved successfully'
        }), 200
        
    except Exception as e:
        print(f"[FEEDBACK ERROR] {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/feedback/list', methods=['GET'])
def list_feedback():
    """
    List all saved feedback files (for debugging)
    """
    try:
        feedback_files = []
        if os.path.exists(FEEDBACK_FOLDER):
            for filename in os.listdir(FEEDBACK_FOLDER):
                if filename.endswith('.json'):
                    filepath = os.path.join(FEEDBACK_FOLDER, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            feedback_files.append({
                                'filename': filename,
                                'rating': data.get('rating'),
                                'comment': data.get('comment', '')[:50] + '...' if len(data.get('comment', '')) > 50 else data.get('comment', ''),
                                'timestamp': data.get('timestamp'),
                                'size': os.path.getsize(filepath)
                            })
                    except Exception as e:
                        feedback_files.append({
                            'filename': filename,
                            'error': str(e)
                        })
        
        return jsonify({
            'success': True,
            'count': len(feedback_files),
            'files': feedback_files,
            'folder': FEEDBACK_FOLDER
        }), 200
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

    # Diagnostic: Show ALL environment variables containing "NANO" or "BANANA"
    print("[DIAGNOSTICS] All Environment Variables containing 'NANO' or 'BANANA':")
    for key, value in os.environ.items():
        if 'NANO' in key.upper() or 'BANANA' in key.upper():
            preview = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else value
            print(f"  {key}: {preview} (length: {len(value)})")
    print("=" * 60)

    # Diagnostic: Show API key status
    print("[DIAGNOSTICS] API Keys Status:")
    print(f"  NANOBANANA_API_KEY: {'✅ SET' if NANOBANANA_API_KEY else '❌ MISSING'} (length: {len(NANOBANANA_API_KEY) if NANOBANANA_API_KEY else 0})")

    if NANOBANANA_API_KEY:
        print(f"  NANOBANANA_API_KEY preview: {NANOBANANA_API_KEY[:8]}...{NANOBANANA_API_KEY[-4:]}")
    else:
        print("  ⚠️ WARNING: NANOBANANA_API_KEY not set! Nano Banana will not work.")
        print(f"  ℹ️ Checked variables: NANOBANANA_API_KEY, nanobanana_api_key")

    print("=" * 60)

    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
