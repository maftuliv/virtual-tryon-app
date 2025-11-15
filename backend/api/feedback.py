"""Feedback API endpoints."""

from flask import Blueprint, jsonify, request

from backend.logger import get_logger
from backend.services.feedback_service import FeedbackService
from backend.utils.request_helpers import get_client_ip

logger = get_logger(__name__)

# Blueprint will be created by factory function
feedback_bp = Blueprint("feedback", __name__)


def create_feedback_blueprint(feedback_service: FeedbackService) -> Blueprint:
    """
    Factory function to create feedback blueprint with injected dependencies.

    Args:
        feedback_service: FeedbackService instance

    Returns:
        Configured Blueprint
    """

    @feedback_bp.route("/api/feedback", methods=["POST"])
    def submit_feedback():
        """
        Save user feedback (rating and comment).

        Request JSON:
        {
            "rating": 5,  // 1-5 (required)
            "comment": "Great app!",  // optional
            "session_id": "123456",  // optional
            "timestamp": "2025-01-15T12:00:00"  // optional
        }

        Response:
        {
            "success": true,
            "message": "Feedback saved successfully",
            "feedback_id": 123,
            "saved_to": "database",
            "db_saved": true,
            "telegram_sent": true
        }

        Saves to database (primary) and JSON file (backup).
        Optionally sends to Telegram if configured.
        """
        try:
            data = request.get_json()

            if not data:
                return jsonify({"error": "No data provided"}), 400

            # Extract fields
            rating_raw = data.get("rating")
            comment = data.get("comment", "")
            session_id = data.get("session_id")

            # Parse rating (handles int, string, list)
            try:
                rating = feedback_service.parse_rating(rating_raw)
            except ValueError as e:
                logger.warning(f"Invalid rating: {e}")
                return jsonify({"error": "Invalid rating. Must be 1-5"}), 400

            # Get client IP
            ip_address = get_client_ip(request)

            logger.info(f"Feedback submission: rating={rating}/5, ip={ip_address}")

            # Submit via service
            result = feedback_service.submit_feedback(
                rating=rating, comment=comment, session_id=session_id, ip_address=ip_address
            )

            return jsonify(result), 200

        except ValueError as e:
            logger.error(f"Feedback validation failed: {e}")
            return jsonify({"error": str(e)}), 400

        except Exception as e:
            logger.error(f"Feedback submission failed: {e}", exc_info=True)
            return jsonify({"error": str(e)}), 500

    @feedback_bp.route("/api/feedback/list", methods=["GET"])
    def list_feedback():
        """
        Retrieve all feedback (admin-only in production).

        Query params:
        - limit: Maximum number of records (default: 100)

        Response:
        {
            "source": "database",
            "count": 42,
            "feedback": [
                {
                    "id": 1,
                    "rating": 5,
                    "comment": "Great app!",
                    "session_id": "123",
                    "ip_address": "1.2.3.4",
                    "telegram_sent": true,
                    "created_at": "2025-01-15T12:00:00"
                }
            ]
        }
        """
        try:
            # Get limit from query params
            limit = request.args.get("limit", default=100, type=int)

            # Validate limit
            if limit < 1 or limit > 1000:
                return jsonify({"error": "Limit must be between 1 and 1000"}), 400

            logger.info(f"Feedback list request: limit={limit}")

            # Get feedback via service
            result = feedback_service.list_feedback(limit=limit)

            return jsonify(result), 200

        except Exception as e:
            logger.error(f"Feedback list retrieval failed: {e}", exc_info=True)
            return jsonify({"error": str(e)}), 500

    @feedback_bp.route("/api/feedback/retry-telegram", methods=["POST"])
    def retry_telegram_notifications():
        """
        Retry failed Telegram notifications for feedback (admin-only).

        Response:
        {
            "attempted": 5,
            "succeeded": 3,
            "failed": 2,
            "errors": ["Feedback 1: Connection timeout", ...]
        }
        """
        try:
            logger.info("Retrying failed Telegram notifications...")

            result = feedback_service.retry_failed_telegram_notifications()

            return jsonify(result), 200

        except Exception as e:
            logger.error(f"Telegram retry failed: {e}", exc_info=True)
            return jsonify({"error": str(e)}), 500

    return feedback_bp
