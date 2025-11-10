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

# FASHN API configuration
FASHN_API_KEY = os.environ.get('FASHN_API_KEY', '')  # Set your token in environment
FASHN_BASE_URL = "https://api.fashn.ai/v1"

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def image_to_base64(image_path):
    """Convert image file to base64 string"""
    with open(image_path, 'rb') as img_file:
        img_data = base64.b64encode(img_file.read()).decode('utf-8')
    return img_data

def save_base64_image(base64_string, output_path):
    """Save base64 image to file"""
    # Remove data URL prefix if present
    if ',' in base64_string:
        base64_string = base64_string.split(',', 1)[1]

    img_data = base64.b64decode(base64_string)
    with open(output_path, 'wb') as img_file:
        img_file.write(img_data)
    return output_path

def process_with_fashn(person_image_path, garment_image_path):
    """
    Process virtual try-on using FASHN API
    Generates high-quality realistic results in 5-17 seconds
    """
    try:
        if not FASHN_API_KEY:
            raise ValueError("FASHN_API_KEY not set. Please configure your API key in environment variables.")

        # Convert images to base64
        model_image_b64 = image_to_base64(person_image_path)
        garment_image_b64 = image_to_base64(garment_image_path)

        # Prepare request payload
        input_data = {
            "model_name": "tryon-v1.6",
            "inputs": {
                "model_image": f"data:image/jpg;base64,{model_image_b64}",
                "garment_image": f"data:image/jpg;base64,{garment_image_b64}",
                "category": "auto",  # Auto-detect garment category
                "num_samples": 1,    # Generate 1 result per image
                "mode": "quality"    # Use quality mode for best results
            }
        }

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

                # Output is a URL or base64 image
                if isinstance(output, str):
                    result_image_data = output
                elif isinstance(output, dict) and "url" in output:
                    result_image_data = output["url"]
                elif isinstance(output, dict) and "image" in output:
                    result_image_data = output["image"]
                else:
                    raise ValueError(f"Unexpected output format: {type(output)}")

                # Save result
                timestamp = int(time.time())
                result_filename = f'result_{timestamp}_{prediction_id[:8]}.png'
                result_path = os.path.join(app.config['RESULTS_FOLDER'], result_filename)

                # Download or save the image
                if result_image_data.startswith('http'):
                    # Download from URL
                    img_response = requests.get(result_image_data, timeout=30)
                    if img_response.status_code == 200:
                        with open(result_path, 'wb') as img_file:
                            img_file.write(img_response.content)
                    else:
                        raise ValueError(f"Failed to download result image: {img_response.status_code}")
                else:
                    # Save base64 image
                    save_base64_image(result_image_data, result_path)

                print(f"[FASHN] ✅ Result saved to: {result_path}")
                return result_path

            elif status in ["starting", "in_queue", "processing"]:
                # Still processing, continue polling
                attempt += 1
                continue
            elif status == "failed":
                error = status_data.get("error", "Unknown error")
                raise ValueError(f"FASHN processing failed: {error}")
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

@app.route('/api/upload', methods=['POST'])
def upload_files():
    """
    Upload person images and garment image
    Expected: person_images[] (3-4 images), garment_image (1 image)
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
        timestamp = int(time.time())

        for idx, person_file in enumerate(person_files):
            if person_file and allowed_file(person_file.filename):
                filename = secure_filename(f'person_{timestamp}_{idx}.{person_file.filename.rsplit(".", 1)[1].lower()}')
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                person_file.save(filepath)
                person_paths.append(filepath)
            else:
                return jsonify({'error': f'Invalid person image file: {person_file.filename}'}), 400

        if garment_file and allowed_file(garment_file.filename):
            garment_filename = secure_filename(f'garment_{timestamp}.{garment_file.filename.rsplit(".", 1)[1].lower()}')
            garment_path = os.path.join(app.config['UPLOAD_FOLDER'], garment_filename)
            garment_file.save(garment_path)
        else:
            return jsonify({'error': 'Invalid garment image file'}), 400

        return jsonify({
            'success': True,
            'person_images': person_paths,
            'garment_image': garment_path,
            'session_id': timestamp
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tryon', methods=['POST'])
def virtual_tryon():
    """
    Perform virtual try-on
    Expects JSON: {person_images: [], garment_image: ""}
    """
    try:
        data = request.get_json()

        if not data or 'person_images' not in data or 'garment_image' not in data:
            return jsonify({'error': 'Missing required data'}), 400

        person_images = data['person_images']
        garment_image = data['garment_image']

        if not person_images or not garment_image:
            return jsonify({'error': 'Invalid image paths'}), 400

        # Process each person image with the garment
        results = []

        for person_image in person_images:
            if not os.path.exists(person_image):
                continue

            try:
                result_path = process_with_fashn(person_image, garment_image)

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
