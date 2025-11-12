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

# Database imports
try:
    from database import (
        db_available,
        save_feedback_to_db,
        get_unsent_telegram_feedbacks,
        mark_telegram_sent
    )
    print("[DATABASE] ✅ Database module loaded successfully")
except ImportError as e:
    print(f"[DATABASE] ⚠️ Database module not available: {e}")
    db_available = False

# Configuration for static files
FRONTEND_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend')

app = Flask(__name__,
            static_folder=FRONTEND_FOLDER,
            static_url_path='')
# CORS configuration - allow all origins (since we're serving frontend from same domain)
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

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

# Hugging Face API Key (for person detection)
HUGGINGFACE_API_KEY = (
    os.environ.get('HUGGINGFACE_API_KEY', '') or
    os.environ.get('HF_API_KEY', '') or
    os.environ.get('HF_TOKEN', '')
).strip()

# ==================== DIAGNOSTICS (runs on import, works with gunicorn) ====================
print("=" * 80)
print("🔍 RAILWAY ENVIRONMENT DIAGNOSTICS")
print("=" * 80)

# Show ALL environment variables containing "NANO", "BANANA", "API", or "TELEGRAM"
print("\n[ENV VARS] All variables containing 'NANO', 'BANANA', 'API', or 'TELEGRAM':")
found_vars = False
for key, value in sorted(os.environ.items()):
    if any(keyword in key.upper() for keyword in ['NANO', 'BANANA', 'API', 'TELEGRAM']):
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

# Check Telegram variables - try multiple variations
TELEGRAM_BOT_TOKEN_CHECK = (
    os.environ.get('TELEGRAM_BOT_TOKEN', '').strip() or
    os.environ.get('TELEGRAM_BOT_TOKEN'.lower(), '').strip() or
    os.environ.get('telegram_bot_token', '').strip()
)
TELEGRAM_CHAT_ID_CHECK = (
    os.environ.get('TELEGRAM_CHAT_ID', '').strip() or
    os.environ.get('TELEGRAM_CHAT_ID'.lower(), '').strip() or
    os.environ.get('telegram_chat_id', '').strip()
)

print(f"\n[TELEGRAM] Configuration check:")
print(f"  TELEGRAM_BOT_TOKEN: {'✅ SET' if TELEGRAM_BOT_TOKEN_CHECK else '❌ MISSING'} (length: {len(TELEGRAM_BOT_TOKEN_CHECK)})")
if TELEGRAM_BOT_TOKEN_CHECK:
    print(f"  TELEGRAM_BOT_TOKEN preview: {TELEGRAM_BOT_TOKEN_CHECK[:15]}...{TELEGRAM_BOT_TOKEN_CHECK[-5:]}")
print(f"  TELEGRAM_CHAT_ID: {'✅ SET' if TELEGRAM_CHAT_ID_CHECK else '❌ MISSING'} (value: {TELEGRAM_CHAT_ID_CHECK})")

# Check all possible variations
print(f"\n[TELEGRAM] Checking all variations:")
for var_name in ['TELEGRAM_BOT_TOKEN', 'TELEGRAM_BOT_TOKEN'.lower(), 'telegram_bot_token']:
    value = os.environ.get(var_name, '')
    if value:
        print(f"  Found: {var_name} = {value[:15]}... (length: {len(value)})")

if not TELEGRAM_BOT_TOKEN_CHECK:
    print(f"  ⚠️  TELEGRAM_BOT_TOKEN not found in environment variables")
    print(f"  💡 Make sure variable is added in Railway Variables and redeploy is done")
if not TELEGRAM_CHAT_ID_CHECK:
    print(f"  ℹ️  TELEGRAM_CHAT_ID not set (will be auto-detected from bot messages)")
if not TELEGRAM_BOT_TOKEN_CHECK:
    print(f"  ⚠️  Telegram notifications will be disabled until TELEGRAM_BOT_TOKEN is set")

if NANOBANANA_API_KEY:
    print(f"  NANOBANANA_API_KEY preview: {NANOBANANA_API_KEY[:8]}...{NANOBANANA_API_KEY[-4:]}")
else:
    print("  ⚠️  NANOBANANA_API_KEY is EMPTY or MISSING!")
    print("  ℹ️  Checked: NANOBANANA_API_KEY, nanobanana_api_key")

print("=" * 80)
print()
# ==================== END DIAGNOSTICS ====================

# ==================== ENVIRONMENT VALIDATION ====================
def validate_environment():
    """
    Validate all required environment variables on startup
    Critical variables will cause warnings but won't stop the app
    """
    REQUIRED_ENV_VARS = {
        'TELEGRAM_BOT_TOKEN': {
            'description': 'Telegram Bot API token for feedback notifications',
            'instruction': 'Get from https://t.me/BotFather',
            'critical': False  # App can work without it, but feedback won't be sent to Telegram
        },
        'TELEGRAM_CHAT_ID': {
            'description': 'Telegram Chat ID to send notifications to',
            'instruction': 'Send /start to your bot, then use getUpdates API',
            'critical': False  # Can be auto-detected
        },
        'FASHN_API_KEY': {
            'description': 'FASHN AI API key for virtual try-on',
            'instruction': 'Get from FASHN dashboard',
            'critical': False  # Optional if using only Nano Banana
        },
        'NANOBANANA_API_KEY': {
            'description': 'Nano Banana API key for virtual try-on',
            'instruction': 'Get from https://nanobananaapi.ai/api-key',
            'critical': False  # Optional if using only FASHN
        }
    }

    missing_vars = []
    warnings = []

    print("\n" + "=" * 80)
    print("🔍 ENVIRONMENT VARIABLES VALIDATION")
    print("=" * 80)

    for var_name, var_info in REQUIRED_ENV_VARS.items():
        # Try multiple variations of variable name
        value = (
            os.environ.get(var_name, '').strip() or
            os.environ.get(var_name.lower(), '').strip()
        )

        status = "✅ SET" if value else "❌ MISSING"
        length_info = f"(length: {len(value)})" if value else ""

        print(f"{status} {var_name} {length_info}")
        print(f"     → {var_info['description']}")

        if not value:
            if var_info['critical']:
                missing_vars.append({
                    'name': var_name,
                    'instruction': var_info['instruction']
                })
            else:
                warnings.append({
                    'name': var_name,
                    'instruction': var_info['instruction']
                })

    print("=" * 80)

    # Show critical errors
    if missing_vars:
        print("\n🚨 CRITICAL: Missing required environment variables!")
        print("=" * 80)
        for var in missing_vars:
            print(f"❌ {var['name']}")
            print(f"   How to fix: {var['instruction']}")
        print("=" * 80)
        print("⚠️  Application may not work correctly!")
        print("⚠️  Add variables in Railway Dashboard → Variables → Redeploy\n")

    # Show warnings
    if warnings:
        print("\n⚠️  WARNING: Optional environment variables not set")
        print("=" * 80)
        for var in warnings:
            print(f"⚠️  {var['name']}")
            print(f"   Impact: Some features will be disabled")
            print(f"   How to fix: {var['instruction']}")
        print("=" * 80)
        print("💡 Application will continue but some features may not work\n")

    if not missing_vars and not warnings:
        print("\n✅ All environment variables are properly configured!\n")

    return len(missing_vars) == 0

# Run validation on module import (works with gunicorn)
validate_environment()

# ==================== END VALIDATION ====================

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def preprocess_image(image_path, max_dimension=2000, quality=95):
    """
    Preprocess image for optimal quality:
    - Resize if ANY dimension exceeds max_dimension (maintaining aspect ratio)
    - Convert to JPEG format with quality setting
    - Use LANCZOS resampling for quality preservation
    
    Important: API requires BOTH width AND height to be <= 2000 pixels

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

        # Resize if ANY dimension exceeds max_dimension
        width, height = img.size
        original_size = (width, height)
        
        if width > max_dimension or height > max_dimension:
            # Calculate ratio to fit within max_dimension
            ratio = min(max_dimension / width, max_dimension / height)
            new_width = int(width * ratio)
            new_height = int(height * ratio)
            
            # Ensure both dimensions are within limit
            if new_width > max_dimension:
                new_width = max_dimension
            if new_height > max_dimension:
                new_height = max_dimension
            
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            print(f"[PREPROCESS] Resized from {original_size[0]}x{original_size[1]} to {new_width}x{new_height}")
            
            # Double-check dimensions after resize
            final_width, final_height = img.size
            if final_width > max_dimension or final_height > max_dimension:
                print(f"[PREPROCESS] ⚠️ WARNING: Final size {final_width}x{final_height} still exceeds {max_dimension}!")
        else:
            print(f"[PREPROCESS] Image size {width}x{height} is within limits (max: {max_dimension})")

        # Save as optimized JPEG
        output_path = image_path.rsplit('.', 1)[0] + '_optimized.jpg'
        img.save(output_path, 'JPEG', quality=quality, optimize=True)
        
        # Verify final dimensions
        final_img = Image.open(output_path)
        final_width, final_height = final_img.size
        print(f"[PREPROCESS] ✅ Optimized image saved: {output_path} (final size: {final_width}x{final_height})")
        
        if final_width > max_dimension or final_height > max_dimension:
            raise ValueError(f"Final image dimensions {final_width}x{final_height} exceed maximum {max_dimension} pixels!")
        
        return output_path

    except Exception as e:
        print(f"[PREPROCESS ERROR] Failed to preprocess {image_path}: {e}")
        import traceback
        traceback.print_exc()
        # Return original path if preprocessing fails (but this might cause API errors)
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

def detect_person_with_huggingface(image_path):
    """
    Detect if there is a person in the image using Hugging Face Inference API
    Uses DETR (DEtection TRansformer) model trained on COCO dataset
    Returns: dict with detection results

    If Hugging Face API key is not set, falls back to simple heuristic validation
    """
    try:
        print(f"[PERSON DETECTION] 🔍 Analyzing image: {image_path}")

        # Check if Hugging Face API key is available
        if not HUGGINGFACE_API_KEY:
            print(f"[PERSON DETECTION] ⚠️ No Hugging Face API key - using simple validation")
            # Fallback: simple heuristic validation (assume photo is valid)
            img = Image.open(image_path)
            width, height = img.size

            # Basic checks
            warnings = []
            is_vertical = height > width
            if not is_vertical:
                warnings.append("⚠️ Рекомендуется вертикальное фото для лучшего результата")

            # Assume person is present (no AI validation)
            return {
                "person_detected": True,
                "confidence": 0.5,  # Neutral confidence
                "is_full_body": is_vertical,
                "height_ratio": 0.8 if is_vertical else 0.5,
                "width_ratio": 0.6,
                "warnings": warnings,
                "critical": False,
                "ai_validated": False,  # Flag to indicate no AI was used
                "validation_method": "heuristic"
            }

        # Read and encode image to base64
        with open(image_path, 'rb') as img_file:
            img_data = img_file.read()

        # Hugging Face Inference API endpoint (updated 2025)
        API_URL = "https://router.huggingface.co/hf-inference/models/facebook/detr-resnet-50"

        # Make request to Hugging Face API with authentication
        headers = {
            "Authorization": f"Bearer {HUGGINGFACE_API_KEY}",
            "Content-Type": "application/octet-stream"
        }

        print(f"[PERSON DETECTION] Sending request to Hugging Face API with auth...")
        response = requests.post(API_URL, headers=headers, data=img_data, timeout=30)

        if response.status_code != 200:
            print(f"[PERSON DETECTION ERROR] API returned status {response.status_code}: {response.text[:200]}")
            # Fallback to simple validation on API error
            print(f"[PERSON DETECTION] ⚠️ API error - falling back to simple validation")
            img = Image.open(image_path)
            width, height = img.size
            is_vertical = height > width
            return {
                "person_detected": True,
                "confidence": 0.5,
                "is_full_body": is_vertical,
                "height_ratio": 0.8 if is_vertical else 0.5,
                "width_ratio": 0.6,
                "warnings": ["⚠️ AI-валидация временно недоступна"] if not is_vertical else [],
                "critical": False,
                "ai_validated": False,
                "validation_method": "heuristic_fallback"
            }

        detections = response.json()
        print(f"[PERSON DETECTION] Received {len(detections)} detections")

        # Find all "person" detections
        person_detections = [d for d in detections if d['label'] == 'person']

        if not person_detections:
            print(f"[PERSON DETECTION] ❌ No person detected")
            return {
                "person_detected": False,
                "confidence": 0.0,
                "total_objects": len(detections),
                "warnings": ["❌ Человек не обнаружен на фото"],
                "critical": True
            }

        # Get best person detection (highest confidence)
        best_person = max(person_detections, key=lambda x: x['score'])
        confidence = best_person['score']

        print(f"[PERSON DETECTION] ✅ Person detected with confidence: {confidence:.2%}")

        # Analyze detection quality
        warnings = []
        is_full_body = False

        # Check bounding box to estimate if it's full body
        box = best_person['box']
        box_height = box['ymax'] - box['ymin']
        box_width = box['xmax'] - box['xmin']

        # Get image dimensions
        img = Image.open(image_path)
        img_width, img_height = img.size

        # Calculate what percentage of image height the person occupies
        height_ratio = box_height / img_height
        width_ratio = box_width / img_width

        # If person occupies >60% of image height, likely full body
        if height_ratio > 0.6:
            is_full_body = True
            print(f"[PERSON DETECTION] ✅ Detected as full-body photo (height ratio: {height_ratio:.2%})")
        else:
            warnings.append("⚠️ Возможно, это не фото в полный рост")
            print(f"[PERSON DETECTION] ⚠️ May not be full-body (height ratio: {height_ratio:.2%})")

        # Check confidence thresholds
        if confidence < 0.5:
            warnings.append("⚠️ Низкая уверенность в детекции человека")
        elif confidence < 0.7:
            warnings.append("⚠️ Средняя уверенность детекции")

        # Check if person is too small in frame
        if width_ratio < 0.2 or height_ratio < 0.3:
            warnings.append("⚠️ Человек занимает слишком мало места в кадре")

        result = {
            "person_detected": True,
            "confidence": round(confidence, 3),
            "is_full_body": is_full_body,
            "box": box,
            "height_ratio": round(height_ratio, 3),
            "width_ratio": round(width_ratio, 3),
            "warnings": warnings,
            "critical": False,
            "total_persons": len(person_detections),
            "ai_validated": True,
            "validation_method": "huggingface_detr"
        }

        print(f"[PERSON DETECTION] ✅ AI validation successful - Result: {result}")
        return result

    except requests.exceptions.Timeout:
        print(f"[PERSON DETECTION ERROR] Request timeout - using fallback validation")
        # Fallback to simple validation
        img = Image.open(image_path)
        width, height = img.size
        is_vertical = height > width
        return {
            "person_detected": True,
            "confidence": 0.5,
            "is_full_body": is_vertical,
            "height_ratio": 0.8 if is_vertical else 0.5,
            "width_ratio": 0.6,
            "warnings": ["⚠️ Время ожидания AI-проверки истекло"],
            "critical": False,
            "ai_validated": False,
            "validation_method": "timeout_fallback"
        }
    except Exception as e:
        print(f"[PERSON DETECTION ERROR] {e}")
        import traceback
        traceback.print_exc()
        # Fallback to simple validation
        try:
            img = Image.open(image_path)
            width, height = img.size
            is_vertical = height > width
            return {
                "person_detected": True,
                "confidence": 0.5,
                "is_full_body": is_vertical,
                "height_ratio": 0.8 if is_vertical else 0.5,
                "width_ratio": 0.6,
                "warnings": ["⚠️ Ошибка AI-проверки, используется упрощенная валидация"],
                "critical": False,
                "ai_validated": False,
                "validation_method": "error_fallback"
            }
        except:
            # Last resort: assume valid
            return {
                "person_detected": True,
                "confidence": 0.5,
                "is_full_body": True,
                "warnings": [],
                "critical": False,
                "ai_validated": False,
                "validation_method": "minimal_fallback"
            }

def save_base64_image(base64_string, output_path):
    """Save base64 image to file"""
    # Remove data URL prefix if present
    if ',' in base64_string:
        base64_string = base64_string.split(',', 1)[1]

    img_data = base64.b64decode(base64_string)
    with open(output_path, 'wb') as img_file:
        img_file.write(img_data)
    return output_path

def get_public_image_url(image_path, request_obj=None):
    """
    Get public URL for image (NanoBanana API requires URLs, not base64)

    Strategy:
    1. Use Railway public URL to serve the uploaded file directly
    2. Fallback: Try ImgBB if IMGBB_API_KEY is set
    3. Auto-detect domain from request if available
    """
    filename = os.path.basename(image_path)

    # Try to get domain from request first (most reliable)
    domain = None
    if request_obj:
        try:
            # Get host from request headers (works with custom domains)
            host = request_obj.headers.get('Host', '')
            if host:
                # Remove port if present
                domain = host.split(':')[0]
                print(f"[IMAGE URL] Detected domain from request: {domain}")
        except Exception as e:
            print(f"[IMAGE URL] Could not get domain from request: {e}")

    # Fallback to environment variable or default
    if not domain:
        domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN', 'taptolook.net')
        print(f"[IMAGE URL] Using domain from environment/default: {domain}")

    # Construct public URL for the uploaded file
    public_url = f"https://{domain}/uploads/{filename}"

    print(f"[IMAGE URL] Generated public URL: {public_url}")

    # Verify file exists before generating URL
    if not os.path.exists(image_path):
        print(f"[IMAGE URL] ⚠️ WARNING: Image file does not exist: {image_path}")

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

        # Preprocess images - ensure BOTH width and height are <= 2000 pixels
        print(f"[NANOBANANA] Preprocessing images...")
        person_image_optimized = preprocess_image(person_image_path, max_dimension=2000, quality=95)
        garment_image_optimized = preprocess_image(garment_image_path, max_dimension=2000, quality=95)

        # NanoBananaAPI requires image URLs, not base64
        # Generate public URLs for uploaded images (served via Railway)
        print(f"[NANOBANANA] Generating public URLs for images...")

        # Try to get request object from Flask context (if available)
        from flask import has_request_context, request as flask_request
        request_obj = flask_request if has_request_context() else None

        person_image_url = get_public_image_url(person_image_optimized, request_obj)
        garment_image_url = get_public_image_url(garment_image_optimized, request_obj)
        
        # Verify URLs are accessible (quick check)
        print(f"[NANOBANANA] Verifying image URLs are accessible...")
        try:
            # Quick HEAD request to check if URLs are accessible
            person_check = requests.head(person_image_url, timeout=5, allow_redirects=True)
            garment_check = requests.head(garment_image_url, timeout=5, allow_redirects=True)
            
            if person_check.status_code != 200:
                print(f"[NANOBANANA] ⚠️ WARNING: Person image URL returned {person_check.status_code}: {person_image_url}")
            else:
                print(f"[NANOBANANA] ✅ Person image URL is accessible")
                
            if garment_check.status_code != 200:
                print(f"[NANOBANANA] ⚠️ WARNING: Garment image URL returned {garment_check.status_code}: {garment_image_url}")
            else:
                print(f"[NANOBANANA] ✅ Garment image URL is accessible")
        except Exception as e:
            print(f"[NANOBANANA] ⚠️ Could not verify URL accessibility: {e}")
            print(f"[NANOBANANA] Continuing anyway - API will handle errors...")

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
        # More explicit prompt to ensure the API actually modifies the image
        prompt = f"Replace the clothing on the person in the first image with the {garment_type} shown in the second image. The {garment_type} must be placed accurately on the person's body, matching their pose and body shape. Preserve the exact colors, patterns, textures, and style of the {garment_type} from the second image. Ensure the {garment_type} fits naturally with realistic shadows, lighting, and fabric draping. The result should show the person wearing the {garment_type}, not just the original image."

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
                            file_size = len(img_response.content)
                            print(f"[NANOBANANA] ✅ Result saved: {result_path} ({file_size} bytes)")
                            
                            # Verify the result image is valid
                            try:
                                result_img = Image.open(result_path)
                                result_width, result_height = result_img.size
                                print(f"[NANOBANANA] ✅ Result image verified: {result_width}x{result_height} pixels")
                            except Exception as e:
                                print(f"[NANOBANANA] ⚠️ WARNING: Could not verify result image: {e}")
                            
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
    response = send_from_directory(FRONTEND_FOLDER, 'index.html')
    response.headers['Cache-Control'] = 'no-cache, must-revalidate'
    return response

@app.route('/<path:path>')
def serve_static(path):
    # Avoid conflicts with API routes
    if path.startswith('api/'):
        return jsonify({"error": "Not found"}), 404
    try:
        response = send_from_directory(FRONTEND_FOLDER, path)
        # Add caching headers for static assets
        if path.endswith(('.js', '.css', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.woff', '.woff2', '.ttf', '.eot')):
            response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
        else:
            response.headers['Cache-Control'] = 'no-cache, must-revalidate'
        return response
    except:
        # If file not found, serve index.html (SPA fallback)
        response = send_from_directory(FRONTEND_FOLDER, 'index.html')
        response.headers['Cache-Control'] = 'no-cache, must-revalidate'
        return response

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
    This includes both original and optimized (_optimized.jpg) files
    """
    try:
        # Security: prevent directory traversal
        filename = secure_filename(filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        
        # Additional security check
        if not os.path.abspath(file_path).startswith(os.path.abspath(UPLOAD_FOLDER)):
            print(f"[UPLOADS] ⚠️ Security check failed for: {filename}")
            return jsonify({"error": "Invalid file path"}), 403
        
        if not os.path.exists(file_path):
            print(f"[UPLOADS] ⚠️ File not found: {filename} (path: {file_path})")
            # List available files for debugging
            if os.path.exists(UPLOAD_FOLDER):
                available_files = [f for f in os.listdir(UPLOAD_FOLDER) if os.path.isfile(os.path.join(UPLOAD_FOLDER, f))]
                print(f"[UPLOADS] Available files in uploads folder: {available_files[:10]}...")  # Show first 10
            return jsonify({"error": "File not found"}), 404
        
        print(f"[UPLOADS] ✅ Serving file: {filename} ({os.path.getsize(file_path)} bytes)")
        return send_from_directory(UPLOAD_FOLDER, filename)
    except Exception as e:
        print(f"[UPLOADS] ❌ Error serving file {filename}: {e}")
        import traceback
        traceback.print_exc()
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
        person_detection_results = []
        timestamp = int(time.time())

        for idx, person_file in enumerate(person_files):
            if person_file and allowed_file(person_file.filename):
                filename = secure_filename(f'person_{timestamp}_{idx}.{person_file.filename.rsplit(".", 1)[1].lower()}')
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                person_file.save(filepath)
                person_paths.append(filepath)

                # Validate image quality
                is_valid, warnings = validate_image(filepath)

                # Detect person using Hugging Face API
                detection_result = detect_person_with_huggingface(filepath)
                detection_result['image_index'] = idx

                # Combine quality warnings with detection warnings
                all_warnings = warnings + detection_result.get('warnings', [])

                if all_warnings:
                    person_warnings.append({
                        'image_index': idx,
                        'warnings': all_warnings
                    })

                # Store detection result for response
                person_detection_results.append(detection_result)

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
            'session_id': timestamp,
            'person_detection': person_detection_results
        }

        # Add warnings if any
        if person_warnings or garment_warnings:
            response_data['validation_warnings'] = {
                'person_images': person_warnings,
                'garment_image': garment_warnings
            }

        # Check if any person image has critical errors (no person detected)
        has_critical_error = any(result.get('critical', False) for result in person_detection_results)
        response_data['can_proceed'] = not has_critical_error

        if has_critical_error:
            print(f"[UPLOAD] ❌ Critical validation error - person not detected in one or more images")

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
                # Always use NanoBanana API (pass request for domain detection)
                result_path = process_with_nanobanana(person_image, garment_image, garment_category)

                # Generate public URL for result image (use same domain detection logic)
                result_filename = os.path.basename(result_path)
                # Try to get domain from request
                from flask import has_request_context, request as flask_request
                if has_request_context():
                    host = flask_request.headers.get('Host', '')
                    if host:
                        domain = host.split(':')[0]
                    else:
                        domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN', 'taptolook.net')
                else:
                    domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN', 'taptolook.net')
                result_url = f"https://{domain}/api/result/{result_filename}"

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

# ==================== TELEGRAM NOTIFICATION WITH RETRY ====================
def send_telegram_notification_with_retry(bot_token, chat_id, message, max_retries=3):
    """
    Send notification to Telegram with retry mechanism

    Args:
        bot_token: Telegram bot API token
        chat_id: Telegram chat ID to send to
        message: Message text to send
        max_retries: Maximum number of retry attempts (default: 3)

    Returns:
        tuple: (success: bool, error_message: str or None)
    """
    telegram_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    # Chat ID should be integer or string - try integer first
    try:
        chat_id_int = int(chat_id)
    except (ValueError, TypeError):
        chat_id_int = chat_id

    telegram_data = {
        'chat_id': chat_id_int,
        'text': message,
        'parse_mode': 'HTML'
    }

    last_error = None

    for attempt in range(1, max_retries + 1):
        try:
            print(f"[TELEGRAM] Attempt {attempt}/{max_retries}: Sending to chat_id={chat_id_int}")

            # Use timeout for each request
            response = requests.post(telegram_url, json=telegram_data, timeout=10)

            if response.status_code == 200:
                response_data = response.json()
                if response_data.get('ok'):
                    message_id = response_data.get('result', {}).get('message_id', 'N/A')
                    print(f"[TELEGRAM] ✅ SUCCESS on attempt {attempt}: Message ID {message_id}")
                    return True, None
                else:
                    error_desc = response_data.get('description', 'Unknown API error')
                    print(f"[TELEGRAM] ❌ API error on attempt {attempt}: {error_desc}")
                    last_error = f"Telegram API error: {error_desc}"
            else:
                print(f"[TELEGRAM] ❌ HTTP {response.status_code} on attempt {attempt}")
                try:
                    error_data = response.json()
                    error_desc = error_data.get('description', 'Unknown')
                    print(f"[TELEGRAM] Error details: {error_desc}")
                    last_error = f"HTTP {response.status_code}: {error_desc}"
                except:
                    print(f"[TELEGRAM] Response: {response.text[:200]}")
                    last_error = f"HTTP {response.status_code}: {response.text[:100]}"

            # If this wasn't the last attempt, wait before retrying
            if attempt < max_retries:
                # Exponential backoff: 1s, 2s, 4s
                delay = 2 ** (attempt - 1)
                print(f"[TELEGRAM] ⏳ Retrying in {delay} seconds...")
                time.sleep(delay)

        except requests.exceptions.Timeout:
            print(f"[TELEGRAM] ⏰ Timeout on attempt {attempt}")
            last_error = "Request timeout"
            if attempt < max_retries:
                delay = 2 ** (attempt - 1)
                print(f"[TELEGRAM] ⏳ Retrying in {delay} seconds...")
                time.sleep(delay)

        except requests.exceptions.ConnectionError as e:
            print(f"[TELEGRAM] 🔌 Connection error on attempt {attempt}: {e}")
            last_error = f"Connection error: {str(e)[:100]}"
            if attempt < max_retries:
                delay = 2 ** (attempt - 1)
                print(f"[TELEGRAM] ⏳ Retrying in {delay} seconds...")
                time.sleep(delay)

        except Exception as e:
            print(f"[TELEGRAM] ❌ Unexpected error on attempt {attempt}: {e}")
            import traceback
            traceback.print_exc()
            last_error = f"Unexpected error: {str(e)[:100]}"
            if attempt < max_retries:
                delay = 2 ** (attempt - 1)
                print(f"[TELEGRAM] ⏳ Retrying in {delay} seconds...")
                time.sleep(delay)

    # All retries failed
    print(f"[TELEGRAM] ❌ FAILED after {max_retries} attempts. Last error: {last_error}")
    return False, last_error

# ==================== END TELEGRAM RETRY ====================

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

        feedback_id = None
        db_saved = False

        # Save to PostgreSQL database (primary storage)
        if db_available:
            print(f"[FEEDBACK] 💾 Saving to PostgreSQL database...")
            success, feedback_id, error = save_feedback_to_db(
                rating=rating,
                comment=comment,
                timestamp=timestamp,
                session_id=session_id,
                ip_address=request.remote_addr,
                telegram_sent=False  # Will update after Telegram send
            )
            if success:
                db_saved = True
                print(f"[FEEDBACK] ✅ Saved to database with ID: {feedback_id}")
            else:
                print(f"[FEEDBACK] ⚠️ Database save failed: {error}")
                print(f"[FEEDBACK] ℹ️ Falling back to file storage...")

        # Fallback: Save to JSON file (temporary, will be lost on redeploy)
        if not db_saved:
            feedback_file = os.path.join(FEEDBACK_FOLDER, f'feedback_{int(time.time())}.json')
            try:
                with open(feedback_file, 'w', encoding='utf-8') as f:
                    json.dump(feedback_data, f, ensure_ascii=False, indent=2)

                # Verify file was saved
                if os.path.exists(feedback_file):
                    file_size = os.path.getsize(feedback_file)
                    print(f"[FEEDBACK] ✅ Saved to file: {feedback_file} (size: {file_size} bytes)")
                else:
                    print(f"[FEEDBACK] ❌ ERROR: File was not created: {feedback_file}")
            except Exception as e:
                print(f"[FEEDBACK] ❌ ERROR saving file: {e}")
                import traceback
                traceback.print_exc()
                # Continue anyway - at least try to send to Telegram

        # Optional: Send to Telegram if configured (even if file save failed)
        # Try multiple variations of variable names
        telegram_bot_token = (
            os.environ.get('TELEGRAM_BOT_TOKEN', '').strip() or
            os.environ.get('TELEGRAM_BOT_TOKEN'.lower(), '').strip() or
            os.environ.get('telegram_bot_token', '').strip()
        )
        telegram_chat_id = (
            os.environ.get('TELEGRAM_CHAT_ID', '').strip() or
            os.environ.get('TELEGRAM_CHAT_ID'.lower(), '').strip() or
            os.environ.get('telegram_chat_id', '').strip()
        )
        
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
                            print(f"[FEEDBACK] 💡 Also check bot settings: Group Privacy should be OFF for private messages")
                            print(f"[FEEDBACK] Full response: {updates_data}")
                            
                            # Try to get bot info to verify token is valid
                            try:
                                bot_info_url = f"https://api.telegram.org/bot{telegram_bot_token}/getMe"
                                bot_info_response = requests.get(bot_info_url, timeout=5)
                                if bot_info_response.status_code == 200:
                                    bot_info = bot_info_response.json()
                                    if bot_info.get('ok'):
                                        bot_data = bot_info.get('result', {})
                                        print(f"[FEEDBACK] ✅ Bot token is valid! Bot: @{bot_data.get('username', 'N/A')}")
                                        print(f"[FEEDBACK] Bot name: {bot_data.get('first_name', 'N/A')}")
                                    else:
                                        print(f"[FEEDBACK] ❌ Bot token validation failed: {bot_info.get('description', 'Unknown')}")
                                else:
                                    print(f"[FEEDBACK] ❌ Failed to validate bot token: HTTP {bot_info_response.status_code}")
                            except Exception as e:
                                print(f"[FEEDBACK] ⚠️  Could not validate bot token: {e}")
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

            # Use retry mechanism for reliable delivery
            print(f"[FEEDBACK] 📤 Sending to Telegram with retry mechanism...")
            telegram_success, telegram_error = send_telegram_notification_with_retry(
                bot_token=telegram_bot_token,
                chat_id=telegram_chat_id,
                message=message,
                max_retries=3
            )

            # Update database with Telegram delivery status
            if db_available and feedback_id:
                mark_telegram_sent(
                    feedback_id=feedback_id,
                    success=telegram_success,
                    error=telegram_error
                )

            if not telegram_success:
                print(f"[FEEDBACK] ⚠️ Warning: Telegram notification failed after retries: {telegram_error}")
                if db_saved:
                    print(f"[FEEDBACK] ℹ️ Feedback was saved to database (ID: {feedback_id}), but Telegram notification could not be sent")
                else:
                    print(f"[FEEDBACK] ℹ️ Feedback was saved to file, but Telegram notification could not be sent")
        else:
            if not telegram_bot_token:
                print(f"[FEEDBACK] ⚠️ TELEGRAM_BOT_TOKEN not set - skipping Telegram notification")
            if not telegram_chat_id:
                print(f"[FEEDBACK] ⚠️ TELEGRAM_CHAT_ID not set - skipping Telegram notification")

            # Mark as not sent in database
            if db_available and feedback_id:
                mark_telegram_sent(
                    feedback_id=feedback_id,
                    success=False,
                    error="Telegram credentials not configured"
                )

        return jsonify({
            'success': True,
            'message': 'Feedback saved successfully',
            'saved_to': 'database' if db_saved else 'file',
            'feedback_id': feedback_id if db_saved else None
        }), 200
        
    except Exception as e:
        print(f"[FEEDBACK ERROR] {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/feedback/list', methods=['GET'])
def list_feedback():
    """
    List all saved feedback (from database if available, otherwise from files)
    """
    try:
        # Try database first
        if db_available:
            from database import SessionLocal, Feedback as FeedbackModel
            db = SessionLocal()
            try:
                feedbacks = db.query(FeedbackModel).order_by(FeedbackModel.timestamp.desc()).all()
                feedback_list = [fb.to_dict() for fb in feedbacks]

                return jsonify({
                    'success': True,
                    'source': 'database',
                    'count': len(feedback_list),
                    'feedbacks': feedback_list
                }), 200
            finally:
                db.close()

        # Fallback: Read from files
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
            'source': 'files',
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
