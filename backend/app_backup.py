import os
import time
import base64
import requests
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
from PIL import Image
import io

app = Flask(__name__)
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

# Hugging Face API configuration
HF_API_URL = "https://api-inference.huggingface.co/models/yisol/IDM-VTON"
HF_API_TOKEN = os.environ.get('HF_API_TOKEN', '')  # Set your token in environment

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_with_idm_vton(person_image_path, garment_image_path):
    """
    Process virtual try-on using IDM-VTON via Hugging Face API
    """
    try:
        # Read images
        with open(person_image_path, 'rb') as person_file:
            person_image = person_file.read()

        with open(garment_image_path, 'rb') as garment_file:
            garment_image = garment_file.read()

        # Prepare request for Hugging Face API
        headers = {
            "Authorization": f"Bearer {HF_API_TOKEN}"
        }

        # Method 1: Try using the Gradio client approach
        try:
            from gradio_client import Client, handle_file

            client = Client("yisol/IDM-VTON")
            result = client.predict(
                dict={"background": handle_file(person_image_path), "layers": [], "composite": None},
                garm_img=handle_file(garment_image_path),
                garment_des="A clothing item",
                is_checked=True,
                is_checked_crop=False,
                denoise_steps=30,
                seed=42,
                api_name="/tryon"
            )

            # Result is a tuple with the output image path
            if result and len(result) > 0:
                output_path = result[0]
                return output_path

        except Exception as e:
            print(f"Gradio client method failed: {e}")

            # Method 2: Fallback to local processing simulation
            # For demo purposes, we'll create a composite image
            person_img = Image.open(person_image_path).convert('RGB')
            garment_img = Image.open(garment_image_path).convert('RGB')

            # Resize images to standard size
            person_img = person_img.resize((768, 1024))
            garment_img = garment_img.resize((768, 1024))

            # Create a simple composite (in production, this would be the model output)
            result_img = Image.blend(person_img, garment_img, alpha=0.3)

            # Save result
            timestamp = int(time.time())
            result_filename = f'result_{timestamp}.png'
            result_path = os.path.join(app.config['RESULTS_FOLDER'], result_filename)
            result_img.save(result_path)

            return result_path

    except Exception as e:
        print(f"Error in process_with_idm_vton: {e}")
        raise

@app.route('/')
def index():
    return jsonify({
        "status": "running",
        "message": "Virtual Try-On API Server",
        "version": "1.0.0"
    })

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
                result_path = process_with_idm_vton(person_image, garment_image)

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
