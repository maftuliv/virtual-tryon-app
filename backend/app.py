import os
import time
import base64
import json
import requests
import psycopg2
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

# Auth imports
# Dummy decorator for when auth is not available
def dummy_auth_decorator(f):
    """Decorator that returns 503 when auth is not available"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        return jsonify({'error': 'Auth not available'}), 503
    return decorated_function

db_conn = None

try:
    from backend.auth import AuthManager, create_auth_decorator
    print("[AUTH] ✅ Auth module loaded successfully")

    # Initialize PostgreSQL connection for auth
    DATABASE_URL = os.getenv('DATABASE_URL')
    if DATABASE_URL:
        db_conn = psycopg2.connect(DATABASE_URL)
        auth_manager = AuthManager(db_conn)
        require_auth, require_admin = create_auth_decorator(auth_manager)
        auth_available = True
        print("[AUTH] ✅ Auth manager initialized")
    else:
        auth_available = False
        require_auth = dummy_auth_decorator
        require_admin = dummy_auth_decorator
        print("[AUTH] ⚠️ DATABASE_URL not found, auth disabled")
except Exception as e:
    print(f"[AUTH] ⚠️ Auth module not available: {e}")
    auth_available = False
    require_auth = dummy_auth_decorator
    require_admin = dummy_auth_decorator

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

# Anonymous generation daily limit per device/IP
FREE_DEVICE_LIMIT = 3

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

ENABLE_STARTUP_DIAGNOSTICS = os.getenv('ENABLE_STARTUP_DIAGNOSTICS') == '1'

def log_masked_value(value):
    """Return a masked version of a secret for safe logging."""
    if not value:
        return "(empty)"
    if len(value) <= 6:
        return "***"
    return f"{value[:3]}...{value[-3:]}"


# ==================== DIAGNOSTICS (optional) ====================
if ENABLE_STARTUP_DIAGNOSTICS:
    print("=" * 80)
    print("🔍 RAILWAY ENVIRONMENT DIAGNOSTICS")
    print("=" * 80)

    print("\n[ENV VARS] All variables containing 'NANO', 'BANANA', 'API', or 'TELEGRAM':")
    found_vars = False
    for key, value in sorted(os.environ.items()):
        if any(keyword in key.upper() for keyword in ['NANO', 'BANANA', 'API', 'TELEGRAM']):
            found_vars = True
            print(f"  ✓ {key} = {log_masked_value(value)} (length: {len(value)})")

    if not found_vars:
        print("  ⚠️  NO variables found containing 'NANO', 'BANANA', or 'API'!")

    print("\n[API KEYS] Loaded values in Python:")
    print(f"  NANOBANANA_API_KEY: {'✅ SET' if NANOBANANA_API_KEY else '❌ MISSING'}")

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
    print(f"  TELEGRAM_BOT_TOKEN: {'✅ SET' if TELEGRAM_BOT_TOKEN_CHECK else '❌ MISSING'}")
    if TELEGRAM_BOT_TOKEN_CHECK:
        print(f"  TELEGRAM_BOT_TOKEN preview: {log_masked_value(TELEGRAM_BOT_TOKEN_CHECK)}")
    print(f"  TELEGRAM_CHAT_ID: {'✅ SET' if TELEGRAM_CHAT_ID_CHECK else '❌ MISSING'}")

    print(f"\n[TELEGRAM] Checking all variations:")
    for var_name in ['TELEGRAM_BOT_TOKEN', 'TELEGRAM_BOT_TOKEN'.lower(), 'telegram_bot_token']:
        value = os.environ.get(var_name, '')
        if value:
            print(f"  Found: {var_name} = {log_masked_value(value)} (length: {len(value)})")

    if not TELEGRAM_BOT_TOKEN_CHECK:
        print(f"  ⚠️  TELEGRAM_BOT_TOKEN not found in environment variables")
        print(f"  💡 Make sure variable is added in Railway Variables and redeploy is done")
    if not TELEGRAM_CHAT_ID_CHECK:
        print(f"  ℹ️  TELEGRAM_CHAT_ID not set (will be auto-detected from bot messages)")
    if not TELEGRAM_BOT_TOKEN_CHECK:
        print(f"  ⚠️  Telegram notifications will be disabled until TELEGRAM_BOT_TOKEN is set")

    if NANOBANANA_API_KEY:
        print(f"  NANOBANANA_API_KEY preview: {log_masked_value(NANOBANANA_API_KEY)}")
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


def get_client_ip():
    """Return client IP, respecting X-Forwarded-For."""
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if client_ip and ',' in client_ip:
        client_ip = client_ip.split(',')[0].strip()
    return client_ip or 'unknown'


def ensure_device_limit_service():
    if not db_conn:
        raise RuntimeError('Device limit service not configured')


def ensure_device_limit_record(device_fingerprint, client_ip, user_agent):
    """Ensure device record exists for current day and reset if needed."""
    ensure_device_limit_service()
    cursor = db_conn.cursor()
    today = datetime.now().date()
    cursor.execute("""
        SELECT id, limit_date
        FROM device_limits
        WHERE device_fingerprint = %s
    """, (device_fingerprint,))
    record = cursor.fetchone()

    if record:
        record_id, limit_date = record
        if limit_date < today:
            cursor.execute("""
                UPDATE device_limits
                SET generations_used = 0,
                    limit_date = %s,
                    last_used_at = NOW(),
                    updated_at = NOW(),
                    ip_address = %s,
                    user_agent = %s
                WHERE id = %s
            """, (today, client_ip, user_agent, record_id))
            db_conn.commit()
    else:
        cursor.execute("""
            INSERT INTO device_limits (device_fingerprint, generations_used, limit_date, ip_address, user_agent)
            VALUES (%s, 0, %s, %s, %s)
        """, (device_fingerprint, today, client_ip, user_agent))
        db_conn.commit()

    cursor.close()


def calculate_device_usage(device_fingerprint, client_ip):
    """Return total generations used for fingerprint or IP today."""
    ensure_device_limit_service()
    cursor = db_conn.cursor()
    today = datetime.now().date()
    cursor.execute("""
        SELECT COALESCE(SUM(generations_used), 0)
        FROM device_limits
        WHERE (device_fingerprint = %s OR ip_address = %s)
        AND limit_date = %s
    """, (device_fingerprint, client_ip, today))
    total_used = cursor.fetchone()[0]
    cursor.close()
    remaining = max(0, FREE_DEVICE_LIMIT - total_used)
    return {
        'can_generate': total_used < FREE_DEVICE_LIMIT,
        'used': total_used,
        'remaining': remaining,
        'limit': FREE_DEVICE_LIMIT
    }


def get_device_limit_status(device_fingerprint, client_ip, user_agent):
    """Ensure record exists and return current limit usage."""
    ensure_device_limit_record(device_fingerprint, client_ip, user_agent)
    return calculate_device_usage(device_fingerprint, client_ip)


def increment_device_usage(device_fingerprint, client_ip, user_agent, increment=1):
    """Increment limit counter for fingerprint and return updated totals."""
    ensure_device_limit_record(device_fingerprint, client_ip, user_agent)
    today = datetime.now().date()
    cursor = db_conn.cursor()
    cursor.execute("""
        UPDATE device_limits
        SET generations_used = generations_used + %s,
            last_used_at = NOW(),
            updated_at = NOW(),
            ip_address = %s,
            user_agent = %s
        WHERE device_fingerprint = %s
        AND limit_date = %s
        RETURNING generations_used
    """, (increment, client_ip, user_agent, device_fingerprint, today))
    result = cursor.fetchone()

    if not result:
        # Record might have been reset between calls; ensure and retry once
        cursor.close()
        ensure_device_limit_record(device_fingerprint, client_ip, user_agent)
        cursor = db_conn.cursor()
        cursor.execute("""
            UPDATE device_limits
            SET generations_used = generations_used + %s,
                last_used_at = NOW(),
                updated_at = NOW(),
                ip_address = %s,
                user_agent = %s
            WHERE device_fingerprint = %s
            AND limit_date = %s
            RETURNING generations_used
        """, (increment, client_ip, user_agent, device_fingerprint, today))
        result = cursor.fetchone()

    db_conn.commit()
    cursor.close()
    return calculate_device_usage(device_fingerprint, client_ip)


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
                    result_filename = f'taptolook.net_result_{timestamp}.png'
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
        timestamp = int(time.time())

        for idx, person_file in enumerate(person_files):
            if person_file and allowed_file(person_file.filename):
                filename = secure_filename(f'person_{timestamp}_{idx}.{person_file.filename.rsplit(".", 1)[1].lower()}')
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                person_file.save(filepath)
                person_paths.append(filepath)

                # Validate image quality
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

@app.route('/api/check-device-limit', methods=['POST'])
def check_device_limit():
    """
    Check generation limit for anonymous users using device fingerprint + IP
    Multi-factor protection: tracks both fingerprint AND IP address
    Prevents bypass via incognito mode, browser switching, etc.
    Expects JSON: {device_fingerprint: "abc123"}
    Returns: {can_generate: bool, used: int, remaining: int, limit: int}
    """
    try:
        data = request.get_json()
        device_fingerprint = data.get('device_fingerprint')

        if not device_fingerprint:
            return jsonify({'error': 'device_fingerprint required'}), 400

        client_ip = get_client_ip()
        user_agent = request.headers.get('User-Agent', '')

        limit_info = get_device_limit_status(device_fingerprint, client_ip, user_agent)

        print(f"[DEVICE-LIMIT] FP: {device_fingerprint[:16]}... IP: {client_ip} Total: {limit_info['used']}/{limit_info['limit']}")

        return jsonify(limit_info), 200

    except RuntimeError as e:
        return jsonify({'error': str(e)}), 503
    except Exception as e:
        print(f"[DEVICE-LIMIT] Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/increment-device-limit', methods=['POST'])
def increment_device_limit():
    """
    Increment generation counter for device fingerprint + IP tracking
    Multi-factor protection: increments for this fingerprint but returns total across IP
    Expects JSON: {device_fingerprint: "abc123"}
    Returns: {success: bool, used: int, remaining: int}
    """
    try:
        data = request.get_json()
        device_fingerprint = data.get('device_fingerprint')

        if not device_fingerprint:
            return jsonify({'error': 'device_fingerprint required'}), 400

        client_ip = get_client_ip()
        user_agent = request.headers.get('User-Agent', '')

        updated_limit = increment_device_usage(device_fingerprint, client_ip, user_agent)

        print(f"[DEVICE-LIMIT] Incremented: FP {device_fingerprint[:16]}... IP {client_ip} Total: {updated_limit['used']}/{updated_limit['limit']}")

        return jsonify({
            'success': True,
            **updated_limit
        }), 200

    except RuntimeError as e:
        return jsonify({'error': str(e)}), 503
    except Exception as e:
        if db_conn:
            db_conn.rollback()
        print(f"[DEVICE-LIMIT] Increment error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/tryon', methods=['POST'])
def virtual_tryon():
    """
    Perform virtual try-on using NanoBanana API (synchronous)
    Expects JSON: {person_images: [], garment_image: "", garment_category: "auto"}
    Returns: {success: true, results: [...]}
    Authentication is optional - allows 3 free generations without login
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Missing request body'}), 400

        # Check if user is authenticated (optional)
        user_id = None
        auth_header = request.headers.get('Authorization', '')

        if auth_available and auth_header.startswith('Bearer '):
            token = auth_header.replace('Bearer ', '')
            user_id = auth_manager.verify_token(token)

        # Check daily limit only for authenticated users
        if user_id and auth_available:
            can_generate, used, limit = auth_manager.check_daily_limit(user_id)

            if not can_generate:
                return jsonify({
                    'error': 'LIMIT_EXCEEDED',
                    'message': f'Вы исчерпали дневной лимит генераций ({limit}/день). Перейдите на Premium для безлимитного доступа!',
                    'used': used,
                    'remaining': 0,
                    'limit': limit
                }), 403

            remaining = limit - used if limit >= 0 else -1
            print(f"[TRYON] User {user_id} - Limit check: {used}/{limit} used, {remaining} remaining")
        else:
            # Enforce anonymous device limit
            device_fingerprint = data.get('device_fingerprint')
            if not device_fingerprint:
                return jsonify({
                    'error': 'DEVICE_FINGERPRINT_REQUIRED',
                    'message': 'Обновите страницу или включите JavaScript, чтобы мы могли проверить бесплатный лимит.'
                }), 400

            client_ip = get_client_ip()
            user_agent = request.headers.get('User-Agent', '')

            try:
                anonymous_limit = get_device_limit_status(device_fingerprint, client_ip, user_agent)
            except RuntimeError as e:
                return jsonify({
                    'error': 'LIMIT_SERVICE_UNAVAILABLE',
                    'message': 'Не удалось проверить лимит устройства. Повторите попытку позже или войдите в аккаунт.'
                }), 503

            if not anonymous_limit['can_generate']:
                return jsonify({
                    'error': 'ANON_LIMIT_EXCEEDED',
                    'message': 'Вы использовали все бесплатные генерации. Зарегистрируйтесь, чтобы продолжить.',
                    **anonymous_limit
                }), 403

            print(f"[TRYON] Anonymous user - {anonymous_limit['used']}/{anonymous_limit['limit']} used")

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
                    'result_image': f'data:image/png;base64,{img_data}',
                    'result_url': result_url,  # Add URL for mobile download
                    'result_filename': result_filename  # Add filename for download
                })
                
                # Send result to Telegram if configured
                try:
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
                    
                    if telegram_bot_token and telegram_chat_id:
                        # Get IP address for caption
                        from flask import has_request_context, request as flask_request
                        ip_address = 'Unknown'
                        if has_request_context():
                            ip_address = flask_request.remote_addr or flask_request.headers.get('X-Forwarded-For', 'Unknown')
                        
                        # Create caption with result info
                        caption = f"🎨 <b>Новый результат примерки</b>\n\n"
                        caption += f"📸 Оригинал: {os.path.basename(person_image)}\n"
                        caption += f"👕 Категория: {garment_category}\n"
                        caption += f"🌐 IP: {ip_address}\n"
                        caption += f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                        
                        # Send photo to Telegram
                        success, error = send_telegram_photo_with_retry(
                            telegram_bot_token,
                            telegram_chat_id,
                            result_path,
                            caption
                        )
                        if success:
                            print(f"[TELEGRAM] ✅ Result photo sent successfully")
                        else:
                            print(f"[TELEGRAM] ⚠️ Failed to send result photo: {error}")
                    else:
                        print(f"[TELEGRAM] ⚠️ Telegram not configured (missing token or chat_id)")
                except Exception as e:
                    print(f"[TELEGRAM] ⚠️ Error sending result to Telegram: {e}")
                    # Don't fail the whole request if Telegram send fails
            except Exception as e:
                print(f"Error processing {person_image}: {e}")
                import traceback
                traceback.print_exc()
                results.append({
                    'original': os.path.basename(person_image),
                    'error': str(e)
                })

        # Increment daily limit counter after successful generation (only for authenticated users)
        successful_results = [r for r in results if 'error' not in r]

        if auth_available and user_id and successful_results:
            try:
                auth_manager.increment_daily_limit(user_id)
                print(f"[TRYON] Daily limit incremented for user {user_id}")
            except Exception as e:
                print(f"[TRYON] Warning: Failed to increment daily limit: {e}")

        anonymous_limit_update = None
        if not user_id and successful_results:
            try:
                anonymous_limit_update = increment_device_usage(
                    device_fingerprint,
                    client_ip,
                    request.headers.get('User-Agent', ''),
                    increment=1
                )
                print(f"[TRYON] Anonymous device limit incremented: {anonymous_limit_update['used']}/{anonymous_limit_update['limit']}")
            except RuntimeError:
                pass
            except Exception as e:
                print(f"[TRYON] Warning: Failed to increment anonymous limit: {e}")

        # Get updated limit info (only for authenticated users)
        updated_limit = {'can_generate': True, 'used': -1, 'remaining': -1, 'limit': -1}
        if auth_available and user_id:
            try:
                can_gen, used_count, lim = auth_manager.check_daily_limit(user_id)
                rem = lim - used_count if lim >= 0 else -1
                updated_limit = {'can_generate': can_gen, 'used': used_count, 'remaining': rem, 'limit': lim}
            except Exception as e:
                print(f"[TRYON] Warning: Failed to get updated limit: {e}")

        response_payload = {
            'success': True,
            'results': results,
            'daily_limit': updated_limit
        }

        if not user_id:
            response_payload['anonymous_limit'] = anonymous_limit_update

        return jsonify(response_payload), 200

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
            
            # Generate a better filename for download
            # Remove any special characters and ensure .png extension
            safe_filename = filename.rsplit('.', 1)[0]  # Get name without extension
            download_filename = f"tap-to-look-{safe_filename}.png"
            
            # Ensure filename is safe for HTTP headers
            import urllib.parse
            encoded_filename = urllib.parse.quote(download_filename)
            
            print(f"[RESULT] Serving result image: {filename} ({mimetype}) as {download_filename}")
            
            # Create response with proper headers for download
            # Use as_attachment=True to force download instead of display
            response = send_file(file_path, mimetype=mimetype, as_attachment=True)
            
            # Set Content-Disposition header for proper download on mobile devices
            # This ensures the file downloads with the correct name, especially on iOS and Telegram browser
            # Use both filename and filename* for maximum compatibility
            response.headers['Content-Disposition'] = (
                f'attachment; filename="{download_filename}"; '
                f'filename*=UTF-8\'\'{encoded_filename}'
            )
            
            # Set Content-Type explicitly
            response.headers['Content-Type'] = mimetype
            
            # Allow CORS if needed
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
            
            return response
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

# ==================== SEND TELEGRAM PHOTO WITH RETRY ====================
def send_telegram_photo_with_retry(bot_token, chat_id, photo_path, caption=None, max_retries=3):
    """
    Send photo to Telegram with retry mechanism

    Args:
        bot_token: Telegram bot API token
        chat_id: Telegram chat ID to send to
        photo_path: Path to photo file
        caption: Optional caption text
        max_retries: Maximum number of retry attempts (default: 3)

    Returns:
        tuple: (success: bool, error_message: str or None)
    """
    telegram_url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"

    # Chat ID should be integer or string - try integer first
    try:
        chat_id_int = int(chat_id)
    except (ValueError, TypeError):
        chat_id_int = chat_id

    last_error = None

    for attempt in range(1, max_retries + 1):
        try:
            print(f"[TELEGRAM PHOTO] Attempt {attempt}/{max_retries}: Sending photo to chat_id={chat_id_int}")

            # Check if file exists
            if not os.path.exists(photo_path):
                last_error = f"Photo file not found: {photo_path}"
                print(f"[TELEGRAM PHOTO] ❌ {last_error}")
                return False, last_error

            # Prepare files and data for multipart/form-data
            with open(photo_path, 'rb') as photo_file:
                files = {'photo': (os.path.basename(photo_path), photo_file, 'image/png')}
                data = {'chat_id': chat_id_int}
                if caption:
                    data['caption'] = caption
                    data['parse_mode'] = 'HTML'

                # Use timeout for each request
                response = requests.post(telegram_url, files=files, data=data, timeout=30)

            if response.status_code == 200:
                response_data = response.json()
                if response_data.get('ok'):
                    message_id = response_data.get('result', {}).get('message_id', 'N/A')
                    print(f"[TELEGRAM PHOTO] ✅ SUCCESS on attempt {attempt}: Message ID {message_id}")
                    return True, None
                else:
                    error_desc = response_data.get('description', 'Unknown API error')
                    print(f"[TELEGRAM PHOTO] ❌ API error on attempt {attempt}: {error_desc}")
                    last_error = f"Telegram API error: {error_desc}"
            else:
                print(f"[TELEGRAM PHOTO] ❌ HTTP {response.status_code} on attempt {attempt}")
                try:
                    error_data = response.json()
                    error_desc = error_data.get('description', 'Unknown')
                    print(f"[TELEGRAM PHOTO] Error details: {error_desc}")
                    last_error = f"HTTP {response.status_code}: {error_desc}"
                except:
                    print(f"[TELEGRAM PHOTO] Response: {response.text[:200]}")
                    last_error = f"HTTP {response.status_code}: {response.text[:100]}"

            # If this wasn't the last attempt, wait before retrying
            if attempt < max_retries:
                # Exponential backoff: 1s, 2s, 4s
                delay = 2 ** (attempt - 1)
                print(f"[TELEGRAM PHOTO] ⏳ Retrying in {delay} seconds...")
                time.sleep(delay)

        except requests.exceptions.Timeout:
            print(f"[TELEGRAM PHOTO] ⏰ Timeout on attempt {attempt}")
            last_error = "Request timeout"
            if attempt < max_retries:
                delay = 2 ** (attempt - 1)
                print(f"[TELEGRAM PHOTO] ⏳ Retrying in {delay} seconds...")
                time.sleep(delay)

        except requests.exceptions.ConnectionError as e:
            print(f"[TELEGRAM PHOTO] 🔌 Connection error on attempt {attempt}: {e}")
            last_error = f"Connection error: {str(e)[:100]}"
            if attempt < max_retries:
                delay = 2 ** (attempt - 1)
                print(f"[TELEGRAM PHOTO] ⏳ Retrying in {delay} seconds...")
                time.sleep(delay)

        except Exception as e:
            print(f"[TELEGRAM PHOTO] ❌ Unexpected error on attempt {attempt}: {e}")
            import traceback
            traceback.print_exc()
            last_error = f"Unexpected error: {str(e)[:100]}"
            if attempt < max_retries:
                delay = 2 ** (attempt - 1)
                print(f"[TELEGRAM PHOTO] ⏳ Retrying in {delay} seconds...")
                time.sleep(delay)

    # All retries failed
    print(f"[TELEGRAM PHOTO] ❌ FAILED after {max_retries} attempts. Last error: {last_error}")
    return False, last_error

# ==================== END TELEGRAM PHOTO RETRY ====================
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
        
        # Безопасная обработка rating - может прийти как int, string, или list
        try:
            # Если rating это список, возьмем первый элемент
            if isinstance(rating, list) and len(rating) > 0:
                rating = rating[0]
            # Если rating это строка, преобразуем в int
            if isinstance(rating, str):
                rating = int(rating.strip())
            # Убедимся что rating это int
            if not isinstance(rating, int):
                rating = int(rating)
        except (ValueError, TypeError, IndexError) as e:
            print(f"[FEEDBACK] Error parsing rating: {e}, received: {rating}, type: {type(rating)}")
            return jsonify({'error': 'Invalid rating. Must be 1-5'}), 400
        
        if not rating or rating < 1 or rating > 5:
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
        
        # Always try to send to Telegram if credentials are available
        telegram_success = False
        telegram_error = None
        telegram_message = None
        
        if telegram_bot_token and telegram_chat_id:
            # Format message for Telegram (using HTML format - simpler and more reliable)
            stars = '⭐' * rating + '☆' * (5 - rating)
            telegram_message = f"📊 <b>Новый отзыв</b>\n\n"
            telegram_message += f"⭐ Оценка: {stars} ({rating}/5)\n"
            if comment:
                # Escape HTML special characters in comment
                safe_comment = comment.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                telegram_message += f"💬 Комментарий: {safe_comment}\n"
            else:
                telegram_message += f"💬 Комментарий: <i>нет комментария</i>\n"
            telegram_message += f"🕐 Время: {timestamp}\n"
            if session_id:
                telegram_message += f"🆔 Session: {session_id[:8]}...\n"
            telegram_message += f"🌐 IP: {request.remote_addr}\n"

            # Use retry mechanism for reliable delivery
            print(f"[FEEDBACK] 📤 Sending to Telegram with retry mechanism...")
            print(f"[FEEDBACK] Message preview: {telegram_message[:100]}...")
            telegram_success, telegram_error = send_telegram_notification_with_retry(
                bot_token=telegram_bot_token,
                chat_id=telegram_chat_id,
                message=telegram_message,
                max_retries=3
            )
            
            if telegram_success:
                print(f"[FEEDBACK] ✅ Telegram notification sent successfully!")
            else:
                print(f"[FEEDBACK] ❌ Telegram notification failed: {telegram_error}")

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

        # Prepare response
        response_data = {
            'success': True,
            'message': 'Feedback saved successfully',
            'saved_to': 'database' if db_saved else 'file',
            'feedback_id': feedback_id if db_saved else None
        }
        
        # Add Telegram status to response
        if telegram_bot_token and telegram_chat_id:
            response_data['telegram_sent'] = telegram_success
            if not telegram_success:
                response_data['telegram_error'] = telegram_error
        
        return jsonify(response_data), 200
        
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
                                'rating': data.get('rating'),
                                'comment': data.get('comment', ''),
                                'timestamp': data.get('timestamp'),
                                'session_id': data.get('session_id')
                            })
                    except Exception as e:
                        print(f"[FEEDBACK] Error reading {filename}: {e}")

        return jsonify({
            'success': True,
            'source': 'files',
            'count': len(feedback_files),
            'files': feedback_files
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

# ==================== AUTH ENDPOINTS ====================

@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register new user with email and password"""
    if not auth_available:
        return jsonify({'success': False, 'error': 'Auth not available'}), 503

    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        full_name = data.get('full_name')

        if not email or not password or not full_name:
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400

        result = auth_manager.register_user(email, password, full_name)

        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400

    except Exception as e:
        print(f"[AUTH] Register error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login user with email and password"""
    if not auth_available:
        return jsonify({'success': False, 'error': 'Auth not available'}), 503

    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({'success': False, 'error': 'Missing email or password'}), 400

        result = auth_manager.login_user(email, password)

        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 401

    except Exception as e:
        print(f"[AUTH] Login error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/auth/me', methods=['GET'])
@require_auth
def get_current_user():
    """Get current user profile"""
    if not auth_available:
        return jsonify({'error': 'Auth not available'}), 503

    try:
        user = auth_manager.get_user_by_id(request.user_id)

        if user:
            # Add daily limit info
            can_generate, used, limit = auth_manager.check_daily_limit(request.user_id)
            remaining = limit - used if limit >= 0 else -1
            user['daily_limit'] = {
                'can_generate': can_generate,
                'used': used,
                'remaining': remaining,
                'limit': limit
            }
            return jsonify({'user': user}), 200
        else:
            return jsonify({'error': 'User not found'}), 404

    except Exception as e:
        print(f"[AUTH] Get user error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/check-limit', methods=['GET'])
@require_auth
def check_limit():
    """Check user's daily generation limit"""
    if not auth_available:
        return jsonify({'error': 'Auth not available'}), 503

    try:
        can_generate, used, limit = auth_manager.check_daily_limit(request.user_id)
        remaining = limit - used if limit >= 0 else -1

        return jsonify({
            'can_generate': can_generate,
            'used': used,
            'remaining': remaining,
            'limit': limit
        }), 200

    except Exception as e:
        print(f"[AUTH] Check limit error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/google', methods=['GET'])
def google_auth():
    """Initiate Google OAuth flow"""
    if not auth_available:
        return jsonify({'error': 'Auth not available'}), 503

    try:
        # TODO: Implement Google OAuth
        # This requires google-auth-oauthlib setup
        return jsonify({'error': 'Google OAuth not implemented yet'}), 501

    except Exception as e:
        print(f"[AUTH] Google auth error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/google/callback', methods=['GET'])
def google_callback():
    """Handle Google OAuth callback"""
    if not auth_available:
        return jsonify({'error': 'Auth not available'}), 503

    try:
        # TODO: Implement Google OAuth callback
        return jsonify({'error': 'Google OAuth not implemented yet'}), 501

    except Exception as e:
        print(f"[AUTH] Google callback error: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== END AUTH ENDPOINTS ====================

# ==================== ADMIN ENDPOINTS ====================

@app.route('/api/admin/users', methods=['GET'])
@require_admin
def admin_get_users():
    """Get all users (admin only)"""
    try:
        if not auth_available:
            return jsonify({'error': 'Auth system not available'}), 503

        cursor = db_conn.cursor()
        cursor.execute("""
            SELECT u.id, u.email, u.full_name, u.is_premium, u.provider, u.role, u.created_at,
                   COUNT(g.id) as generation_count
            FROM users u
            LEFT JOIN generations g ON u.id = g.user_id
            GROUP BY u.id, u.email, u.full_name, u.is_premium, u.provider, u.role, u.created_at
            ORDER BY u.created_at DESC
        """)

        users_data = cursor.fetchall()
        cursor.close()

        users = []
        for user in users_data:
            users.append({
                'id': user[0],
                'email': user[1],
                'full_name': user[2],
                'is_premium': user[3],
                'provider': user[4],
                'role': user[5],
                'created_at': user[6].isoformat() if user[6] else None,
                'generation_count': user[7]
            })

        return jsonify({'users': users}), 200

    except Exception as e:
        print(f"[ADMIN] Get users error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/users/<int:user_id>/premium', methods=['POST'])
@require_admin
def admin_toggle_premium(user_id):
    """Toggle user premium status (admin only)"""
    try:
        if not auth_available:
            return jsonify({'error': 'Auth system not available'}), 503

        data = request.get_json()
        is_premium = data.get('is_premium', False)

        cursor = db_conn.cursor()

        if is_premium:
            # Set premium for 30 days
            from datetime import datetime, timedelta
            premium_until = datetime.now() + timedelta(days=30)
            cursor.execute("""
                UPDATE users
                SET is_premium = TRUE, premium_until = %s
                WHERE id = %s
            """, (premium_until, user_id))
        else:
            # Remove premium
            cursor.execute("""
                UPDATE users
                SET is_premium = FALSE, premium_until = NULL
                WHERE id = %s
            """, (user_id,))

        db_conn.commit()
        cursor.close()

        return jsonify({'success': True, 'is_premium': is_premium}), 200

    except Exception as e:
        db_conn.rollback()
        print(f"[ADMIN] Toggle premium error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/generations', methods=['GET'])
@require_admin
def admin_get_all_generations():
    """Get all generations with user info (admin only)"""
    try:
        if not auth_available:
            return jsonify({'error': 'Auth system not available'}), 503

        # Get optional user_id filter
        user_id = request.args.get('user_id', type=int)
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)

        cursor = db_conn.cursor()

        if user_id:
            # Get generations for specific user
            cursor.execute("""
                SELECT g.id, g.user_id, u.email, u.full_name, g.category, g.status,
                       g.person_image_url, g.garment_image_url, g.result_image_url,
                       g.created_at
                FROM generations g
                JOIN users u ON g.user_id = u.id
                WHERE g.user_id = %s
                ORDER BY g.created_at DESC
                LIMIT %s OFFSET %s
            """, (user_id, limit, offset))
        else:
            # Get all generations
            cursor.execute("""
                SELECT g.id, g.user_id, u.email, u.full_name, g.category, g.status,
                       g.person_image_url, g.garment_image_url, g.result_image_url,
                       g.created_at
                FROM generations g
                JOIN users u ON g.user_id = u.id
                ORDER BY g.created_at DESC
                LIMIT %s OFFSET %s
            """, (limit, offset))

        generations_data = cursor.fetchall()
        cursor.close()

        generations = []
        for gen in generations_data:
            generations.append({
                'id': gen[0],
                'user_id': gen[1],
                'user_email': gen[2],
                'user_name': gen[3],
                'category': gen[4],
                'status': gen[5],
                'person_image_url': gen[6],
                'garment_image_url': gen[7],
                'result_image_url': gen[8],
                'created_at': gen[9].isoformat() if gen[9] else None
            })

        return jsonify({'generations': generations, 'total': len(generations)}), 200

    except Exception as e:
        print(f"[ADMIN] Get generations error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/stats', methods=['GET'])
@require_admin
def admin_get_stats():
    """Get admin statistics (admin only)"""
    try:
        if not auth_available:
            return jsonify({'error': 'Auth system not available'}), 503

        cursor = db_conn.cursor()

        # Get user stats
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM users WHERE is_premium = TRUE")
        premium_users = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
        admin_users = cursor.fetchone()[0]

        # Get generation stats
        cursor.execute("SELECT COUNT(*) FROM generations")
        total_generations = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM generations WHERE DATE(created_at) = CURRENT_DATE")
        today_generations = cursor.fetchone()[0]

        cursor.execute("""
            SELECT category, COUNT(*) as count
            FROM generations
            GROUP BY category
            ORDER BY count DESC
        """)
        category_stats = cursor.fetchall()

        cursor.close()

        return jsonify({
            'users': {
                'total': total_users,
                'premium': premium_users,
                'free': total_users - premium_users,
                'admins': admin_users
            },
            'generations': {
                'total': total_generations,
                'today': today_generations,
                'by_category': [{'category': cat[0], 'count': cat[1]} for cat in category_stats]
            }
        }), 200

    except Exception as e:
        print(f"[ADMIN] Get stats error: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== END ADMIN ENDPOINTS ====================

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
