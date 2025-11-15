"""Virtual try-on API endpoints."""

import os
from typing import Optional

from flask import Blueprint, jsonify, request

from backend.logger import get_logger
from backend.services.tryon_service import TryonService
from backend.utils.request_helpers import get_client_ip

logger = get_logger(__name__)

# Blueprint will be created by factory function
tryon_bp = Blueprint("tryon", __name__)


def create_tryon_blueprint(tryon_service: TryonService, auth_service=None) -> Blueprint:
    """
    Factory function to create try-on blueprint with injected dependencies.

    Args:
        tryon_service: TryonService instance
        auth_service: Optional AuthService for authentication

    Returns:
        Configured Blueprint
    """

    @tryon_bp.route("/api/tryon", methods=["POST"])
    def virtual_tryon():
        """
        Perform virtual try-on using NanoBanana API (synchronous).

        Request JSON:
        {
            "person_images": ["path1", "path2"],
            "garment_image": "path",
            "garment_category": "auto",  // optional
            "device_fingerprint": "abc123"  // required for anonymous users
        }

        Response:
        {
            "success": true,
            "results": [
                {
                    "original": "person_1.jpg",
                    "result_path": "/results/result_1.jpg",
                    "result_image": "data:image/png;base64,...",
                    "result_url": "https://domain/api/result/result_1.jpg",
                    "result_filename": "result_1.jpg"
                }
            ],
            "daily_limit": {
                "can_generate": true,
                "used": 1,
                "remaining": 2,
                "limit": 3
            }
        }

        Authentication is optional - allows 3 free generations without login.
        """
        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": "Missing request body"}), 400

            # Extract authentication (optional)
            user_id = None
            auth_header = request.headers.get("Authorization", "")

            if auth_service and auth_service.is_available() and auth_header.startswith("Bearer "):
                token = auth_header.replace("Bearer ", "")
                try:
                    user = auth_service.get_user_by_token(token)
                    if user:
                        user_id = user["id"]
                        logger.info(f"Authenticated request: user_id={user_id}")
                except Exception as e:
                    logger.warning(f"Token validation failed: {e}")

            # Extract request data
            person_images = data.get("person_images", [])
            garment_image = data.get("garment_image")
            garment_category = data.get("garment_category", "auto")
            device_fingerprint = data.get("device_fingerprint")

            # Validate required fields
            if not person_images or not garment_image:
                return jsonify({"error": "Missing required data: person_images and garment_image"}), 400

            # For anonymous users, require device fingerprint
            if not user_id and not device_fingerprint:
                return (
                    jsonify(
                        {
                            "error": "DEVICE_FINGERPRINT_REQUIRED",
                            "message": "Обновите страницу или включите JavaScript, чтобы мы могли проверить бесплатный лимит.",
                        }
                    ),
                    400,
                )

            # Get client info for anonymous users
            client_ip = get_client_ip(request) if not user_id else None
            user_agent = request.headers.get("User-Agent", "") if not user_id else None

            logger.info(
                f"Try-on request: {len(person_images)} images, category={garment_category}, "
                f"user_id={user_id if user_id else 'anonymous'}"
            )

            # Process try-on via service
            try:
                result = tryon_service.process_tryon(
                    person_images=person_images,
                    garment_image=garment_image,
                    garment_category=garment_category,
                    user_id=user_id,
                    device_fingerprint=device_fingerprint,
                    ip_address=client_ip,
                    user_agent=user_agent,
                    request_obj=request,
                )

                return jsonify(result), 200

            except ValueError as e:
                error_msg = str(e)

                # Handle limit exceeded errors
                if "LIMIT_EXCEEDED" in error_msg:
                    if user_id:
                        return (
                            jsonify(
                                {
                                    "error": "LIMIT_EXCEEDED",
                                    "message": "Вы исчерпали дневной лимит генераций. Перейдите на Premium для безлимитного доступа!",
                                }
                            ),
                            403,
                        )
                    else:
                        return (
                            jsonify(
                                {
                                    "error": "ANON_LIMIT_EXCEEDED",
                                    "message": "Вы использовали все бесплатные генерации. Зарегистрируйтесь, чтобы продолжить.",
                                }
                            ),
                            403,
                        )

                # Other validation errors
                return jsonify({"error": error_msg}), 400

        except Exception as e:
            logger.error(f"Try-on request failed: {e}", exc_info=True)
            return jsonify({"error": str(e)}), 500

    @tryon_bp.route("/api/check-device-limit", methods=["POST"])
    def check_device_limit():
        """
        Check generation limit for anonymous users using device fingerprint + IP.

        Request JSON:
        {
            "device_fingerprint": "abc123"
        }

        Response:
        {
            "can_generate": true,
            "used": 1,
            "remaining": 2,
            "limit": 3
        }
        """
        try:
            data = request.get_json()
            device_fingerprint = data.get("device_fingerprint")

            if not device_fingerprint:
                return jsonify({"error": "device_fingerprint required"}), 400

            client_ip = get_client_ip(request)
            user_agent = request.headers.get("User-Agent", "")

            logger.info(f"Device limit check: fingerprint={device_fingerprint[:16]}..., ip={client_ip}")

            # Use tryon_service.limit_service to check limit
            limit_info = tryon_service.limit_service.check_device_limit(
                device_fingerprint=device_fingerprint, ip_address=client_ip, user_agent=user_agent
            )

            return jsonify(limit_info), 200

        except Exception as e:
            logger.error(f"Device limit check failed: {e}", exc_info=True)
            return jsonify({"error": str(e)}), 500

    @tryon_bp.route("/api/increment-device-limit", methods=["POST"])
    def increment_device_limit():
        """
        Increment generation counter for device fingerprint + IP tracking.

        Request JSON:
        {
            "device_fingerprint": "abc123"
        }

        Response:
        {
            "success": true,
            "used": 2,
            "remaining": 1,
            "limit": 3
        }
        """
        try:
            data = request.get_json()
            device_fingerprint = data.get("device_fingerprint")

            if not device_fingerprint:
                return jsonify({"error": "device_fingerprint required"}), 400

            client_ip = get_client_ip(request)
            user_agent = request.headers.get("User-Agent", "")

            logger.info(f"Device limit increment: fingerprint={device_fingerprint[:16]}..., ip={client_ip}")

            # Use tryon_service.limit_service to increment
            updated_limit = tryon_service.limit_service.increment_device_limit(
                device_fingerprint=device_fingerprint, ip_address=client_ip, user_agent=user_agent
            )

            return jsonify({"success": True, **updated_limit}), 200

        except Exception as e:
            logger.error(f"Device limit increment failed: {e}", exc_info=True)
            return jsonify({"error": str(e)}), 500

    return tryon_bp
