"""Google OAuth 2.0 API endpoints."""

from urllib.parse import urlencode

from flask import Blueprint, jsonify, make_response, redirect, request, session

from backend.auth import set_admin_session_cookie, set_auth_cookie
from backend.logger import get_logger
from backend.services.admin_session_service import AdminSessionService
from backend.services.google_auth_service import GoogleAuthService

logger = get_logger(__name__)


def create_google_auth_blueprint(
    google_auth_service: GoogleAuthService, admin_session_service: AdminSessionService = None
) -> Blueprint:
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

            # Generate authorization URL with signed state token
            # State is signed, so no session storage needed (works across domains)
            authorization_url, signed_state = google_auth_service.generate_authorization_url()

            logger.info(f"[GOOGLE-AUTH-API] Generated auth URL (signed_state={signed_state[:20]}...)")

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
            # Get frontend URL from config (for redirect after OAuth)
            from flask import current_app
            frontend_url = current_app.config.get("SETTINGS").frontend_url
            if not frontend_url:
                # Fallback: try to detect from request origin or use default
                # Note: Origin header may be from Google, so use default test frontend URL
                frontend_url = "https://testtaptolooknet-production.up.railway.app"
            
            logger.info(f"[GOOGLE-AUTH-API] Using frontend URL for redirect: {frontend_url}")
            
            # Check if Google OAuth is enabled
            if not google_auth_service.is_enabled():
                logger.error("[GOOGLE-AUTH-API] Callback received but OAuth is disabled")
                fragment = urlencode({"google_auth_error": "1", "message": "OAuth не настроен. Обратитесь к администратору"})
                return redirect(f"{frontend_url}/#{fragment}")

            # Check for error in callback
            error = request.args.get("error")
            if error:
                error_description = request.args.get("error_description", "Unknown error")
                logger.warning(f"[GOOGLE-AUTH-API] OAuth error: {error} - {error_description}")
                fragment = urlencode({"google_auth_error": "1", "message": f"{error} - {error_description}"})
                return redirect(f"{frontend_url}/#{fragment}")

            # Get authorization code and signed state
            authorization_code = request.args.get("code")
            signed_state = request.args.get("state")

            if not authorization_code or not signed_state:
                logger.error("[GOOGLE-AUTH-API] Missing code or state in callback")
                fragment = urlencode({"google_auth_error": "1", "message": "Missing authorization code or state"})
                return redirect(f"{frontend_url}/#{fragment}")

            # Verify signed state token (no session needed - works across domains)
            state = google_auth_service._verify_state(signed_state)
            if not state:
                logger.error("[GOOGLE-AUTH-API] Invalid or expired state token")
                fragment = urlencode({"google_auth_error": "1", "message": "Invalid or expired state token"})
                return redirect(f"{frontend_url}/#{fragment}")

            # Handle OAuth callback: exchange code, get user info, create/login user
            # Note: state is already verified, so we pass it as both state and expected_state
            result = google_auth_service.handle_oauth_callback(
                authorization_code=authorization_code,
                state=state,
                expected_state=state,  # Already verified, so same value
            )

            if not result.get("success"):
                error_msg = result.get("error", "Authentication failed")
                logger.error(f"[GOOGLE-AUTH-API] Authentication failed: {error_msg}")
                fragment = urlencode({"google_auth_error": "1", "message": error_msg})
                return redirect(f"{frontend_url}/#{fragment}")

            # Get JWT token from result
            token = result.get("token")
            user = result.get("user", {})

            if not token:
                logger.error("[GOOGLE-AUTH-API] No token in authentication result")
                fragment = urlencode({"google_auth_error": "1", "message": "Failed to generate token"})
                return redirect(f"{frontend_url}/#{fragment}")

            logger.info(
                f"[GOOGLE-AUTH-API] User authenticated: user_id={user.get('id')}, "
                f"email={user.get('email')}"
            )

            # Create redirect response with auth cookie
            fragment = urlencode({"google_auth_success": "1", "token": token})
            response = make_response(redirect(f"{frontend_url}/#{fragment}"))
            set_auth_cookie(response, token)
            logger.info(f"[GOOGLE-AUTH-API] Cookie set for {user.get('email')}, redirecting to {frontend_url}")

            if admin_session_service and admin_session_service.is_available() and user.get("role") == "admin":
                session_id = admin_session_service.create_session(
                    user_id=user["id"],
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get("User-Agent"),
                )
                if session_id:
                    set_admin_session_cookie(response, session_id)

            return response

        except ValueError as e:
            # Validation error (state mismatch, invalid token, etc.)
            logger.error(f"[GOOGLE-AUTH-API] Validation error: {e}")
            from flask import current_app
            frontend_url = current_app.config.get("SETTINGS").frontend_url or "https://testtaptolooknet-production.up.railway.app"
            fragment = urlencode({"google_auth_error": "1", "message": f"Validation failed: {str(e)}"})
            return redirect(f"{frontend_url}/#{fragment}")

        except Exception as e:
            # Unexpected error
            logger.error(f"[GOOGLE-AUTH-API] Callback failed: {e}", exc_info=True)
            from flask import current_app
            frontend_url = current_app.config.get("SETTINGS").frontend_url or "https://testtaptolooknet-production.up.railway.app"
            fragment = urlencode({"google_auth_error": "1", "message": f"Internal error: {str(e)}"})
            return redirect(f"{frontend_url}/#{fragment}")

    @google_auth_bp.route("/api/auth/google/status", methods=["GET"])
    def google_status():
        """
        Check if Google OAuth is enabled and configured.

        Returns:
            JSON with OAuth status:
            {
                "enabled": bool,
                "configured": bool,
                "redirect_uri": str (if configured),
                "client_id_masked": str (masked for security),
                "client_id_format_valid": bool,
                "config_issues": list of strings (if any)
            }
        """
        try:
            is_enabled = google_auth_service.is_enabled()

            response = {
                "enabled": is_enabled,
                "configured": is_enabled,
            }

            if is_enabled:
                settings = google_auth_service.settings
                
                # Return redirect URI for debugging (not sensitive)
                response["redirect_uri"] = settings.google_redirect_uri
                
                # Mask Client ID for security
                client_id = settings.google_client_id
                if client_id:
                    if len(client_id) > 14:
                        client_id_masked = f"{client_id[:10]}...{client_id[-4:]}"
                    else:
                        client_id_masked = "***"
                    response["client_id_masked"] = client_id_masked
                    response["client_id_format_valid"] = client_id.endswith(".apps.googleusercontent.com")
                else:
                    response["client_id_masked"] = "NOT SET"
                    response["client_id_format_valid"] = False
                
                # Check for configuration issues
                config_issues = []
                if not settings.google_client_id or not settings.google_client_id.strip():
                    config_issues.append("GOOGLE_CLIENT_ID is empty or contains only whitespace")
                elif not settings.google_client_id.endswith(".apps.googleusercontent.com"):
                    config_issues.append("GOOGLE_CLIENT_ID format may be incorrect (should end with .apps.googleusercontent.com)")
                
                if not settings.google_client_secret or not settings.google_client_secret.strip():
                    config_issues.append("GOOGLE_CLIENT_SECRET is empty or contains only whitespace")
                
                if not settings.google_redirect_uri or not settings.google_redirect_uri.strip():
                    config_issues.append("GOOGLE_REDIRECT_URI is empty or contains only whitespace")
                
                if config_issues:
                    response["config_issues"] = config_issues
                else:
                    response["config_issues"] = []

            return jsonify(response), 200

        except Exception as e:
            logger.error(f"[GOOGLE-AUTH-API] Status check failed: {e}", exc_info=True)
            return jsonify({"enabled": False, "configured": False, "error": str(e)}), 500

    return google_auth_bp
