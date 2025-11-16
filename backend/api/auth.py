"""Authentication API endpoints."""

from typing import Optional

from flask import Blueprint, jsonify, make_response, request

from backend.auth import (
    ADMIN_SESSION_COOKIE,
    clear_admin_session_cookie,
    clear_auth_cookie,
    get_token_from_request,
    set_admin_session_cookie,
    set_auth_cookie,
)
from backend.logger import get_logger
from backend.services.admin_session_service import AdminSessionService
from backend.services.auth_service import AuthService

logger = get_logger(__name__)

# Blueprint will be created by factory function
auth_bp = Blueprint("auth", __name__)


def create_auth_blueprint(
    auth_service: AuthService, admin_session_service: Optional[AdminSessionService] = None
) -> Blueprint:
    """
    Factory function to create auth blueprint with injected dependencies.

    Args:
        auth_service: AuthService instance

    Returns:
        Configured Blueprint
    """

    def _extract_admin_user(user: dict) -> Optional[dict]:
        """
        Normalize user payload from AuthService/AuthManager.

        Depending on the layer, `user` can be either:
        - flat dict with fields: id, email, role, token, ...
        - wrapped dict: { success, user: {...}, token }
        """
        if not isinstance(user, dict):
            return None

        # Flat format
        if user.get("role") == "admin":
            return user

        # Wrapped format from AuthManager.register_user/login_user
        inner = user.get("user")
        if isinstance(inner, dict) and inner.get("role") == "admin":
            return inner

        return None

    def _activate_admin_session(response, user):
        """Create admin session for admin users after login/registration."""
        if not admin_session_service or not admin_session_service.is_available():
            return

        admin_user = _extract_admin_user(user)
        if not admin_user:
            # Not an admin (or malformed payload) → no admin session
            logger.info("[ADMIN-SESSION] Skipping admin session: user is not admin or payload invalid")
            return

        session_id = admin_session_service.create_session(
            user_id=admin_user["id"],
            ip_address=request.remote_addr,
            user_agent=request.headers.get("User-Agent"),
        )
        if session_id:
            set_admin_session_cookie(response, session_id)

    def _clear_admin_session(response):
        if not admin_session_service or not admin_session_service.is_available():
            return
        session_id = request.cookies.get(ADMIN_SESSION_COOKIE)
        if session_id:
            admin_session_service.delete_session(session_id)
        clear_admin_session_cookie(response)

    @auth_bp.route("/api/auth/register", methods=["POST"])
    def register():
        """
        Register new user.

        Request JSON:
        {
            "email": "user@example.com",
            "password": "password123",
            "full_name": "John Doe"
        }

        Response:
        {
            "success": true,
            "message": "User registered successfully",
            "user": {
                "id": 1,
                "email": "user@example.com",
                "full_name": "John Doe",
                "is_premium": false,
                "provider": "email",
                "role": "user",
                "token": "eyJ...",
                "created_at": "2025-01-15T12:00:00"
            }
        }
        """
        if not auth_service.is_available():
            return jsonify({"error": "Authentication not available"}), 503

        try:
            data = request.get_json()

            if not data:
                return jsonify({"error": "No data provided"}), 400

            # Extract fields
            email = data.get("email", "").strip()
            password = data.get("password", "")
            full_name = data.get("full_name", "").strip()

            logger.info(f"Registration request: email={email}")

            # Register via service
            user = auth_service.register(email=email, password=password, full_name=full_name)

            # Create response with auth cookie
            response = make_response(
                jsonify({"success": True, "message": "User registered successfully", "user": user}),
                201
            )
            set_auth_cookie(response, user["token"])
            _activate_admin_session(response, user)
            logger.info(f"[AUTH] Registration successful, cookie set for {email}")

            return response

        except ValueError as e:
            logger.warning(f"Registration validation failed: {e}")
            return jsonify({"error": str(e)}), 400

        except Exception as e:
            logger.error(f"Registration failed: {e}", exc_info=True)
            return jsonify({"error": str(e)}), 500

    @auth_bp.route("/api/auth/login", methods=["POST"])
    def login():
        """
        Authenticate user and return token.

        Request JSON:
        {
            "email": "user@example.com",
            "password": "password123"
        }

        Response:
        {
            "success": true,
            "message": "Login successful",
            "user": {
                "id": 1,
                "email": "user@example.com",
                "full_name": "John Doe",
                "is_premium": false,
                "provider": "email",
                "role": "user",
                "token": "eyJ...",
                "daily_limit": {
                    "can_generate": true,
                    "used": 0,
                    "remaining": 10,
                    "limit": 10
                }
            }
        }
        """
        if not auth_service.is_available():
            return jsonify({"error": "Authentication not available"}), 503

        try:
            data = request.get_json()

            if not data:
                return jsonify({"error": "No data provided"}), 400

            # Extract fields
            email = data.get("email", "").strip()
            password = data.get("password", "")

            logger.info(f"Login request: email={email}")

            # Login via service
            user = auth_service.login(email=email, password=password)

            if not user:
                logger.warning(f"Login failed: invalid credentials for {email}")
                return jsonify({"error": "Invalid email or password"}), 401

            # Create response with auth cookie
            response = make_response(
                jsonify({"success": True, "message": "Login successful", "user": user}),
                200
            )
            set_auth_cookie(response, user["token"])
            _activate_admin_session(response, user)
            logger.info(f"[AUTH] Login successful, cookie set for {email}")

            return response

        except ValueError as e:
            logger.warning(f"Login validation failed: {e}")
            return jsonify({"error": str(e)}), 400

        except Exception as e:
            logger.error(f"Login failed: {e}", exc_info=True)
            return jsonify({"error": str(e)}), 500

    @auth_bp.route("/api/auth/me", methods=["GET"])
    def get_current_user():
        """
        Get current user info from token.

        Headers:
        - Authorization: Bearer <token>

        Response:
        {
            "user": {
                "id": 1,
                "email": "user@example.com",
                "full_name": "John Doe",
                "is_premium": false,
                "provider": "email",
                "role": "user"
            }
        }
        """
        if not auth_service.is_available():
            return jsonify({"error": "Authentication not available"}), 503

        try:
            token = get_token_from_request()

            if not token:
                return jsonify({"error": "Authorization required"}), 401

            logger.info("Current user request with token")

            # Validate token via service
            user = auth_service.get_user_by_token(token)

            if not user:
                logger.warning("Invalid or expired token")
                return jsonify({"error": "Invalid or expired token"}), 401

            return jsonify({"user": user}), 200

        except Exception as e:
            logger.error(f"Get current user failed: {e}", exc_info=True)
            return jsonify({"error": str(e)}), 500

    @auth_bp.route("/api/auth/check-limit", methods=["GET"])
    def check_limit():
        """
        Check user's daily generation limit.

        Headers:
        - Authorization: Bearer <token>

        Response:
        {
            "can_generate": true,
            "used": 3,
            "remaining": 7,
            "limit": 10
        }
        """
        if not auth_service.is_available():
            return jsonify({"error": "Authentication not available"}), 503

        try:
            token = get_token_from_request()

            if not token:
                return jsonify({"error": "Authorization required"}), 401

            # Validate token and get user
            user = auth_service.get_user_by_token(token)

            if not user:
                return jsonify({"error": "Invalid or expired token"}), 401

            user_id = user["id"]

            logger.info(f"Check limit request: user_id={user_id}")

            # Check limit via service
            limit_status = auth_service.check_daily_limit(user_id)

            return jsonify(limit_status), 200

        except Exception as e:
            logger.error(f"Check limit failed: {e}", exc_info=True)
            return jsonify({"error": str(e)}), 500

    @auth_bp.route("/api/auth/admin/session", methods=["GET"])
    def admin_session_status():
        if not admin_session_service or not admin_session_service.is_available():
            return jsonify({"error": "Admin sessions unavailable"}), 503

        session_id = request.cookies.get(ADMIN_SESSION_COOKIE)
        if not session_id:
            return jsonify({"error": "Admin session not found"}), 401

        admin_user = admin_session_service.get_session_user(session_id)
        if not admin_user:
            response = make_response(jsonify({"error": "Admin session expired"}), 401)
            clear_admin_session_cookie(response)
            return response

        return jsonify({"user": admin_user}), 200

    @auth_bp.route("/api/auth/logout", methods=["POST"])
    def logout():
        """
        Logout user by clearing auth cookie.

        This endpoint clears the HTTP-only auth_token cookie.
        Client should also clear localStorage token.

        Response:
        {
            "success": true,
            "message": "Logged out successfully"
        }
        """
        try:
            response = make_response(
                jsonify({"success": True, "message": "Logged out successfully"}),
                200
            )
            clear_auth_cookie(response)
            _clear_admin_session(response)
            logger.info("[AUTH] User logged out, cookie cleared")

            return response

        except Exception as e:
            logger.error(f"Logout failed: {e}", exc_info=True)
            return jsonify({"error": str(e)}), 500

    return auth_bp
