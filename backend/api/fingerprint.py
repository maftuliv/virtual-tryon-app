"""Device fingerprint API endpoints."""

from flask import Blueprint, jsonify, request

from backend.logger import get_logger
from backend.services.device_fingerprint_service import DeviceFingerprintService

logger = get_logger(__name__)

fingerprint_bp = Blueprint("fingerprint", __name__)


def create_fingerprint_blueprint(service: DeviceFingerprintService) -> Blueprint:
    """Create blueprint for secure device fingerprint generation."""

    @fingerprint_bp.route("/api/fingerprint/generate", methods=["POST"])
    def generate_fingerprint():
        payload = request.get_json(silent=True) or {}
        stable_components = payload.get("stable_components")

        if not isinstance(stable_components, dict) or not stable_components:
            return jsonify({"error": "stable_components must be a non-empty object"}), 400

        try:
            fingerprint = service.generate_fingerprint(stable_components)
            return jsonify({"fingerprint": fingerprint})
        except ValueError as exc:
            logger.warning("Invalid fingerprint payload: %s", exc)
            return jsonify({"error": str(exc)}), 400
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Fingerprint generation failed: %s", exc, exc_info=True)
            return jsonify({"error": "Failed to generate fingerprint"}), 500

    return fingerprint_bp


__all__ = ["create_fingerprint_blueprint"]

