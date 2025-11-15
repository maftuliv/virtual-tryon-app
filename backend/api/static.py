"""Static file serving endpoints."""

import os

from flask import Blueprint, jsonify, send_from_directory
from werkzeug.utils import secure_filename

from backend.logger import get_logger

logger = get_logger(__name__)

# Blueprint will be created by factory function
static_bp = Blueprint("static", __name__)


def create_static_blueprint(
    upload_folder: str, result_folder: str, frontend_folder: str
) -> Blueprint:
    """
    Factory function to create static file blueprint with injected dependencies.

    Args:
        upload_folder: Path to uploads folder
        result_folder: Path to results folder
        frontend_folder: Path to frontend build folder

    Returns:
        Configured Blueprint
    """

    @static_bp.route("/uploads/<path:filename>", methods=["GET"])
    def serve_upload(filename):
        """
        Serve uploaded images publicly (needed for NanoBanana API).

        This includes both original and optimized (_optimized.jpg) files.
        """
        try:
            # Security: prevent directory traversal
            filename = secure_filename(filename)
            file_path = os.path.join(upload_folder, filename)

            # Additional security check
            if not os.path.abspath(file_path).startswith(os.path.abspath(upload_folder)):
                logger.warning(f"Security check failed for: {filename}")
                return jsonify({"error": "Invalid file path"}), 403

            if not os.path.exists(file_path):
                logger.warning(f"File not found: {filename}")
                return jsonify({"error": "File not found"}), 404

            logger.info(f"Serving upload: {filename} ({os.path.getsize(file_path)} bytes)")

            return send_from_directory(upload_folder, filename)

        except Exception as e:
            logger.error(f"Error serving upload {filename}: {e}", exc_info=True)
            return jsonify({"error": "File not found"}), 404

    @static_bp.route("/api/result/<filename>", methods=["GET"])
    def get_result(filename):
        """
        Retrieve result image.
        """
        try:
            # Security: prevent directory traversal
            filename = secure_filename(filename)
            file_path = os.path.join(result_folder, filename)

            # Additional security check
            if not os.path.abspath(file_path).startswith(os.path.abspath(result_folder)):
                logger.warning(f"Security check failed for result: {filename}")
                return jsonify({"error": "Invalid file path"}), 403

            if not os.path.exists(file_path):
                logger.warning(f"Result file not found: {filename}")
                return jsonify({"error": "Result not found"}), 404

            logger.info(f"Serving result: {filename} ({os.path.getsize(file_path)} bytes)")

            return send_from_directory(result_folder, filename)

        except Exception as e:
            logger.error(f"Error serving result {filename}: {e}", exc_info=True)
            return jsonify({"error": "File not found"}), 404

    @static_bp.route("/", methods=["GET"])
    def serve_frontend():
        """
        Serve frontend index.html.
        """
        try:
            response = send_from_directory(frontend_folder, "index.html")
            response.headers["Cache-Control"] = "no-cache, must-revalidate"
            return response
        except Exception as e:
            logger.error(f"Error serving frontend: {e}", exc_info=True)
            return jsonify({"error": "Frontend not found"}), 404

    @static_bp.route("/<path:path>", methods=["GET"])
    def serve_static(path):
        """
        Serve static frontend files (SPA fallback).
        """
        # Avoid conflicts with API routes
        if path.startswith("api/"):
            return jsonify({"error": "Not found"}), 404

        try:
            response = send_from_directory(frontend_folder, path)

            # Add caching headers for static assets
            if path.endswith(
                (".js", ".css", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".woff", ".woff2", ".ttf", ".eot")
            ):
                response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
            else:
                response.headers["Cache-Control"] = "no-cache, must-revalidate"

            return response

        except Exception:
            # If file not found, serve index.html (SPA fallback)
            try:
                response = send_from_directory(frontend_folder, "index.html")
                response.headers["Cache-Control"] = "no-cache, must-revalidate"
                return response
            except Exception as e:
                logger.error(f"Error serving static file {path}: {e}", exc_info=True)
                return jsonify({"error": "Not found"}), 404

    @static_bp.route("/api/health", methods=["GET"])
    def health_check():
        """
        Health check endpoint.
        """
        import time

        return jsonify({"status": "healthy", "timestamp": time.time()}), 200

    return static_bp
