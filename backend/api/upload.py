"""File upload and validation API endpoints."""

import os
import time

from flask import Blueprint, jsonify, request
from werkzeug.utils import secure_filename

from backend.logger import get_logger
from backend.services.image_service import ImageService

logger = get_logger(__name__)

# Blueprint will be created by factory function
upload_bp = Blueprint("upload", __name__)


def create_upload_blueprint(image_service: ImageService, upload_folder: str) -> Blueprint:
    """
    Factory function to create upload blueprint with injected dependencies.

    Args:
        image_service: ImageService instance for validation
        upload_folder: Path to upload folder

    Returns:
        Configured Blueprint
    """

    @upload_bp.route("/api/validate", methods=["POST"])
    def validate_uploaded_image():
        """
        Validate image quality before processing.

        Returns warnings and recommendations.

        Form data:
        - image: Image file

        Response:
        {
            "success": true,
            "is_valid": true,
            "warnings": [
                "Низкое разрешение - рекомендуется минимум 512px",
                "Изображение слишком темное - улучшите освещение"
            ]
        }
        """
        try:
            if "image" not in request.files:
                return jsonify({"error": "No image provided"}), 400

            image_file = request.files["image"]

            if not image_file or not image_service.validate_file(image_file.filename):
                return jsonify({"error": "Invalid image file"}), 400

            # Save temporarily for validation
            timestamp = int(time.time())
            extension = image_file.filename.rsplit(".", 1)[1].lower()
            filename = secure_filename(f"temp_validate_{timestamp}.{extension}")
            filepath = os.path.join(upload_folder, filename)

            image_file.save(filepath)

            logger.info(f"Validating image: {filename}")

            # Validate image quality
            is_valid, warnings = image_service.validate_image_quality(filepath)

            # Clean up temp file
            try:
                os.remove(filepath)
            except Exception as e:
                logger.warning(f"Failed to remove temp file {filepath}: {e}")

            return jsonify({"success": True, "is_valid": is_valid, "warnings": warnings}), 200

        except Exception as e:
            logger.error(f"Image validation failed: {e}", exc_info=True)
            return jsonify({"error": str(e)}), 500

    @upload_bp.route("/api/upload", methods=["POST"])
    def upload_files():
        """
        Upload person images and garment image.

        Expected form data:
        - person_images[]: 1-4 person images
        - garment_image: 1 garment image

        Response:
        {
            "success": true,
            "person_images": ["/path/to/person1.jpg", "/path/to/person2.jpg"],
            "garment_image": "/path/to/garment.jpg",
            "session_id": 1234567890,
            "validation_warnings": {
                "person_images": [
                    {
                        "image_index": 0,
                        "warnings": ["Низкое разрешение"]
                    }
                ],
                "garment_image": []
            }
        }
        """
        try:
            # Check if files are present
            if "person_images" not in request.files:
                return jsonify({"error": "No person images provided"}), 400

            if "garment_image" not in request.files:
                return jsonify({"error": "No garment image provided"}), 400

            person_files = request.files.getlist("person_images")
            garment_file = request.files["garment_image"]

            # Validate person images count
            if len(person_files) < 1 or len(person_files) > 4:
                return jsonify({"error": "Please upload 1-4 person images"}), 400

            logger.info(f"Upload request: {len(person_files)} person images, 1 garment image")

            # Validate and save files
            person_paths = []
            person_warnings = []
            timestamp = int(time.time())

            for idx, person_file in enumerate(person_files):
                if not person_file or not image_service.validate_file(person_file.filename):
                    return jsonify({"error": f"Invalid person image file: {person_file.filename}"}), 400

                # Save person image
                extension = person_file.filename.rsplit(".", 1)[1].lower()
                filename = secure_filename(f"person_{timestamp}_{idx}.{extension}")
                filepath = os.path.join(upload_folder, filename)

                person_file.save(filepath)
                person_paths.append(filepath)

                logger.info(f"Saved person image: {filename}")

                # Validate image quality
                is_valid, warnings = image_service.validate_image_quality(filepath)

                if warnings:
                    person_warnings.append({"image_index": idx, "warnings": warnings})

            # Validate and save garment image
            if not garment_file or not image_service.validate_file(garment_file.filename):
                return jsonify({"error": "Invalid garment image file"}), 400

            garment_extension = garment_file.filename.rsplit(".", 1)[1].lower()
            garment_filename = secure_filename(f"garment_{timestamp}.{garment_extension}")
            garment_path = os.path.join(upload_folder, garment_filename)

            garment_file.save(garment_path)

            logger.info(f"Saved garment image: {garment_filename}")

            # Validate garment image
            is_valid, garment_warnings = image_service.validate_image_quality(garment_path)

            # Build response
            response_data = {
                "success": True,
                "person_images": person_paths,
                "garment_image": garment_path,
                "session_id": timestamp,
            }

            # Add warnings if any
            if person_warnings or garment_warnings:
                response_data["validation_warnings"] = {
                    "person_images": person_warnings,
                    "garment_image": garment_warnings,
                }

            return jsonify(response_data), 200

        except Exception as e:
            logger.error(f"File upload failed: {e}", exc_info=True)
            return jsonify({"error": str(e)}), 500

    return upload_bp
