"""Google OAuth 2.0 API endpoints."""

from urllib.parse import urlencode

from flask import Blueprint, jsonify, redirect, request, session

from backend.logger import get_logger
from backend.services.google_auth_service import GoogleAuthService

logger = get_logger(__name__)


def create_google_auth_blueprint(google_auth_service: GoogleAuthService) -> Blueprint:
    """
    Create blueprint for Google OAuth endpoints.

    Args:
        google_auth_service: GoogleAuthService instance

    Returns:
        Configured Blueprint with Google OAuth routes
    """
    google_auth_bp = Blueprint("google_auth", __name__)

    @google_auth_bp.route("/api/auth/google/login", methods=["GET"])
    def google_login():
        """
        Initiate Google OAuth 2.0 flow.

        Returns:
            JSON with authorization URL:
            {
                "authorization_url": "https://accounts.google.com/o/oauth2/auth?...",
                "success": true
            }

        Error responses:
            503: Google OAuth not enabled or misconfigured
            500: Internal server error
        """
        try:
            # Check if Google OAuth is enabled
            if not google_auth_service.is_enabled():
                logger.warning("[GOOGLE-AUTH-API] OAuth attempt but service is disabled")
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "Google OAuth не настроен. Обратитесь к администратору.",
                            "hint": "Установите GOOGLE_OAUTH_ENABLED=true и добавьте учетные данные OAuth.",
                        }
                    ),
                    503,  # Service Unavailable
                )

            # Generate authorization URL with state token
            authorization_url, state = google_auth_service.generate_authorization_url()

            # Store state in session for validation (CSRF protection)
            session["google_oauth_state"] = state

            logger.info(f"[GOOGLE-AUTH-API] Generated auth URL (state={state[:8]}...)")

            return (
                jsonify(
                    {
                        "success": True,
                        "authorization_url": authorization_url,
                    }
                ),
                200,
            )

        except Exception as e:
            logger.error(f"[GOOGLE-AUTH-API] Login initiation failed: {e}", exc_info=True)
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f"Не удалось инициировать вход через Google: {str(e)}",
                    }
                ),
                500,
            )

    @google_auth_bp.route("/api/auth/google/callback", methods=["GET"])
    def google_callback():
        """
        Handle Google OAuth 2.0 callback.

        Query parameters:
            code: Authorization code from Google
            state: State token for CSRF validation
            error: Error code (if authorization failed)

        Returns:
            Redirect to frontend with token in URL hash:
            - Success: /?#google_auth_success&token=<jwt_token>
            - Error: /?#google_auth_error&message=<error_message>

        Note: Redirects to frontend, not JSON response
        """
        try:
            # Check if Google OAuth is enabled
            if not google_auth_service.is_enabled():
                logger.error("[GOOGLE-AUTH-API] Callback received but OAuth is disabled")
                fragment = urlencode({"google_auth_error": "1", "message": "OAuth не настроен. Обратитесь к администратору"})
                return redirect(f"/#{fragment}")

            # Check for error in callback
            error = request.args.get("error")
            if error:
                error_description = request.args.get("error_description", "Unknown error")
                logger.warning(f"[GOOGLE-AUTH-API] OAuth error: {error} - {error_description}")
                fragment = urlencode({"google_auth_error": "1", "message": f"{error} - {error_description}"})
                return redirect(f"/#{fragment}")

            # Get authorization code and state
            authorization_code = request.args.get("code")
            state = request.args.get("state")

            if not authorization_code or not state:
                logger.error("[GOOGLE-AUTH-API] Missing code or state in callback")
                fragment = urlencode({"google_auth_error": "1", "message": "Missing authorization code or state"})
                return redirect(f"/#{fragment}")

            # Get expected state from session
            expected_state = session.get("google_oauth_state")
            if not expected_state:
                logger.error("[GOOGLE-AUTH-API] No state found in session")
                fragment = urlencode({"google_auth_error": "1", "message": "Invalid session state"})
                return redirect(f"/#{fragment}")

            # Clear state from session (one-time use)
            session.pop("google_oauth_state", None)

            # Handle OAuth callback: exchange code, get user info, create/login user
            result = google_auth_service.handle_oauth_callback(
                authorization_code=authorization_code,
                state=state,
                expected_state=expected_state,
            )

            if not result.get("success"):
                error_msg = result.get("error", "Authentication failed")
                logger.error(f"[GOOGLE-AUTH-API] Authentication failed: {error_msg}")
                fragment = urlencode({"google_auth_error": "1", "message": error_msg})
                return redirect(f"/#{fragment}")

            # Get JWT token from result
            token = result.get("token")
            user = result.get("user", {})

            if not token:
                logger.error("[GOOGLE-AUTH-API] No token in authentication result")
                fragment = urlencode({"google_auth_error": "1", "message": "Failed to generate token"})
                return redirect(f"/#{fragment}")

            logger.info(
                f"[GOOGLE-AUTH-API] User authenticated: user_id={user.get('id')}, "
                f"email={user.get('email')}"
            )

            # Redirect to frontend with token in URL hash (URL-encoded to preserve +, /, = chars)
            # Frontend will extract token and store it
            fragment = urlencode({"google_auth_success": "1", "token": token})
            return redirect(f"/#{fragment}")

        except ValueError as e:
            # Validation error (state mismatch, invalid token, etc.)
            logger.error(f"[GOOGLE-AUTH-API] Validation error: {e}")
            fragment = urlencode({"google_auth_error": "1", "message": f"Validation failed: {str(e)}"})
            return redirect(f"/#{fragment}")

        except Exception as e:
            # Unexpected error
            logger.error(f"[GOOGLE-AUTH-API] Callback failed: {e}", exc_info=True)
            fragment = urlencode({"google_auth_error": "1", "message": f"Internal error: {str(e)}"})
            return redirect(f"/#{fragment}")

    @google_auth_bp.route("/api/auth/google/status", methods=["GET"])
    def google_status():
        """
        Check if Google OAuth is enabled and configured.

        Returns:
            JSON with OAuth status:
            {
                "enabled": bool,
                "configured": bool,
                "redirect_uri": str (if configured)
            }
        """
        try:
            is_enabled = google_auth_service.is_enabled()

            response = {
                "enabled": is_enabled,
                "configured": is_enabled,
            }

            if is_enabled:
                # Return redirect URI for debugging (not sensitive)
                response["redirect_uri"] = google_auth_service.settings.google_redirect_uri

            return jsonify(response), 200

        except Exception as e:
            logger.error(f"[GOOGLE-AUTH-API] Status check failed: {e}", exc_info=True)
            return jsonify({"enabled": False, "configured": False, "error": str(e)}), 500

    return google_auth_bp
