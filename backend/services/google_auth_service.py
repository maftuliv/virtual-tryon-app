"""
Google OAuth 2.0 Authentication Service.

Handles Google OAuth flow: authorization URL generation, token exchange,
user profile retrieval, and user creation/login.
"""

import secrets
from typing import Dict, Optional, Tuple
from urllib.parse import urlencode

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow

from backend.auth import AuthManager
from backend.config import Settings
from backend.logger import get_logger

logger = get_logger(__name__)


class GoogleAuthService:
    """
    Service for Google OAuth 2.0 authentication.

    Provides methods for:
    - Generating authorization URLs with state validation
    - Exchanging authorization codes for tokens
    - Retrieving user profile from Google
    - Creating/finding users in the database
    """

    # Google OAuth 2.0 scopes (minimal required permissions)
    SCOPES = [
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
    ]

    def __init__(
        self,
        settings: Settings,
        auth_manager: Optional[AuthManager] = None,
    ):
        """
        Initialize Google OAuth service.

        Args:
            settings: Application settings with Google OAuth config
            auth_manager: AuthManager for user database operations
        """
        self.settings = settings
        self.auth_manager = auth_manager
        self.logger = get_logger(__name__)

        # Validate configuration
        if not settings.google_oauth_enabled:
            self.logger.warning("[GOOGLE-AUTH] Google OAuth is disabled in settings")
            self.enabled = False
            return

        if not settings.google_client_id or not settings.google_client_secret:
            self.logger.error(
                "[GOOGLE-AUTH] Google OAuth enabled but credentials missing. "
                "Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET"
            )
            self.enabled = False
            return

        if not settings.google_redirect_uri:
            self.logger.error(
                "[GOOGLE-AUTH] Google OAuth enabled but GOOGLE_REDIRECT_URI not set"
            )
            self.enabled = False
            return

        self.enabled = True
        self.logger.info("[GOOGLE-AUTH] Google OAuth 2.0 service initialized")
        self.logger.info(f"[GOOGLE-AUTH] Redirect URI: {settings.google_redirect_uri}")

    def is_enabled(self) -> bool:
        """
        Check if Google OAuth is properly configured and enabled.

        Returns:
            True if Google OAuth is ready, False otherwise
        """
        return self.enabled

    def generate_authorization_url(self) -> Tuple[str, str]:
        """
        Generate Google OAuth authorization URL with state token.

        Returns:
            Tuple of (authorization_url, state_token)
            - authorization_url: URL to redirect user to Google login
            - state_token: Random state token for CSRF protection (store in session)

        Raises:
            RuntimeError: If Google OAuth is not enabled
        """
        if not self.is_enabled():
            raise RuntimeError("Google OAuth is not enabled or misconfigured")

        # Generate random state for CSRF protection
        state = secrets.token_urlsafe(32)

        try:
            # Create OAuth 2.0 flow
            flow = Flow.from_client_config(
                client_config={
                    "web": {
                        "client_id": self.settings.google_client_id,
                        "client_secret": self.settings.google_client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [self.settings.google_redirect_uri],
                    }
                },
                scopes=self.SCOPES,
                state=state,
            )

            flow.redirect_uri = self.settings.google_redirect_uri

            # Generate authorization URL
            authorization_url, _ = flow.authorization_url(
                access_type="offline",  # Request refresh token
                include_granted_scopes="true",
                prompt="consent",  # Force consent screen to ensure refresh token
            )

            self.logger.info(f"[GOOGLE-AUTH] Generated authorization URL (state={state[:8]}...)")

            return authorization_url, state

        except Exception as e:
            self.logger.error(f"[GOOGLE-AUTH] Error generating authorization URL: {e}", exc_info=True)
            raise RuntimeError(f"Failed to generate Google authorization URL: {e}")

    def exchange_code_for_token(
        self, authorization_code: str, state: str, expected_state: str
    ) -> Dict:
        """
        Exchange authorization code for access token and ID token.

        Args:
            authorization_code: Authorization code from Google callback
            state: State token from callback
            expected_state: Expected state token (from session)

        Returns:
            Dictionary with token information:
            {
                'access_token': str,
                'refresh_token': str (optional),
                'id_token': str,
                'expires_in': int,
                'token_type': str
            }

        Raises:
            ValueError: If state validation fails or token exchange fails
        """
        if not self.is_enabled():
            raise RuntimeError("Google OAuth is not enabled or misconfigured")

        # Validate state (CSRF protection)
        if state != expected_state:
            self.logger.error(
                f"[GOOGLE-AUTH] State mismatch: received={state[:8]}..., "
                f"expected={expected_state[:8]}..."
            )
            raise ValueError("Invalid state token (CSRF protection)")

        try:
            # Create OAuth 2.0 flow
            flow = Flow.from_client_config(
                client_config={
                    "web": {
                        "client_id": self.settings.google_client_id,
                        "client_secret": self.settings.google_client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [self.settings.google_redirect_uri],
                    }
                },
                scopes=self.SCOPES,
                state=state,
            )

            flow.redirect_uri = self.settings.google_redirect_uri

            # Exchange code for token
            flow.fetch_token(code=authorization_code)

            # Get credentials
            credentials = flow.credentials

            token_data = {
                "access_token": credentials.token,
                "refresh_token": credentials.refresh_token,
                "id_token": credentials.id_token,
                "expires_in": credentials.expiry.timestamp() if credentials.expiry else None,
                "token_type": getattr(credentials, "token_type", "Bearer"),
            }

            self.logger.info("[GOOGLE-AUTH] Successfully exchanged code for tokens")
            self.logger.info(
                f"[GOOGLE-AUTH] Token: {token_data['access_token'][:10]}... "
                f"(has_refresh: {bool(token_data['refresh_token'])})"
            )

            return token_data

        except Exception as e:
            self.logger.error(f"[GOOGLE-AUTH] Token exchange failed: {e}", exc_info=True)
            raise ValueError(f"Failed to exchange authorization code: {e}")

    def get_user_info(self, id_token_str: str) -> Dict:
        """
        Extract user information from Google ID token.

        Args:
            id_token_str: ID token string from Google

        Returns:
            Dictionary with user information:
            {
                'google_id': str,
                'email': str,
                'email_verified': bool,
                'full_name': str,
                'given_name': str,
                'family_name': str,
                'picture': str (avatar URL)
            }

        Raises:
            ValueError: If ID token is invalid or verification fails
        """
        if not self.is_enabled():
            raise RuntimeError("Google OAuth is not enabled or misconfigured")

        try:
            # Verify and decode ID token
            id_info = id_token.verify_oauth2_token(
                id_token_str,
                google_requests.Request(),
                self.settings.google_client_id,
            )

            # Extract user information
            user_info = {
                "google_id": id_info.get("sub"),
                "email": id_info.get("email"),
                "email_verified": id_info.get("email_verified", False),
                "full_name": id_info.get("name"),
                "given_name": id_info.get("given_name"),
                "family_name": id_info.get("family_name"),
                "picture": id_info.get("picture"),
            }

            # Validate required fields
            if not user_info["google_id"] or not user_info["email"]:
                raise ValueError("Missing required fields in ID token")

            if not user_info["email_verified"]:
                raise ValueError("Email not verified by Google")

            self.logger.info(
                f"[GOOGLE-AUTH] Retrieved user info: email={user_info['email']}, "
                f"name={user_info['full_name']}"
            )

            return user_info

        except ValueError as e:
            self.logger.error(f"[GOOGLE-AUTH] ID token verification failed: {e}")
            raise ValueError(f"Invalid ID token: {e}")
        except Exception as e:
            self.logger.error(f"[GOOGLE-AUTH] Error extracting user info: {e}", exc_info=True)
            raise ValueError(f"Failed to get user information: {e}")

    def find_or_create_user(self, user_info: Dict) -> Dict:
        """
        Find existing user or create new user from Google profile.

        Args:
            user_info: User information from Google (from get_user_info)

        Returns:
            Dictionary with user data and JWT token:
            {
                'success': bool,
                'user': {
                    'id': int,
                    'email': str,
                    'full_name': str,
                    'provider': 'google',
                    'is_premium': bool,
                    'avatar_url': str,
                    ...
                },
                'token': str  # JWT token for authentication
            }

        Raises:
            RuntimeError: If AuthManager is not available
            ValueError: If user creation fails
        """
        if not self.auth_manager:
            raise RuntimeError("AuthManager not available - cannot create/find users")

        try:
            # Use AuthManager's find_or_create_oauth_user method
            result = self.auth_manager.find_or_create_oauth_user(
                email=user_info["email"],
                full_name=user_info["full_name"],
                avatar_url=user_info.get("picture"),
                provider="google",
                provider_id=user_info["google_id"],
            )

            if result["success"]:
                self.logger.info(
                    f"[GOOGLE-AUTH] User authenticated: user_id={result['user']['id']}, "
                    f"email={result['user']['email']}"
                )
            else:
                self.logger.error(f"[GOOGLE-AUTH] User authentication failed: {result.get('error')}")

            return result

        except Exception as e:
            self.logger.error(f"[GOOGLE-AUTH] Error finding/creating user: {e}", exc_info=True)
            raise ValueError(f"Failed to create or find user: {e}")

    def handle_oauth_callback(
        self, authorization_code: str, state: str, expected_state: str
    ) -> Dict:
        """
        Complete OAuth flow: exchange code, get user info, create/find user.

        This is a convenience method that combines all OAuth callback steps.

        Args:
            authorization_code: Authorization code from Google callback
            state: State token from callback
            expected_state: Expected state token (from session)

        Returns:
            Dictionary with user data and JWT token (same as find_or_create_user)

        Raises:
            ValueError: If any step in the OAuth flow fails
            RuntimeError: If Google OAuth is not properly configured
        """
        if not self.is_enabled():
            raise RuntimeError("Google OAuth is not enabled or misconfigured")

        self.logger.info("[GOOGLE-AUTH] Starting OAuth callback handling...")

        # Step 1: Exchange code for tokens
        token_data = self.exchange_code_for_token(authorization_code, state, expected_state)

        # Step 2: Extract user info from ID token
        user_info = self.get_user_info(token_data["id_token"])

        # Step 3: Find or create user in database
        result = self.find_or_create_user(user_info)

        self.logger.info("[GOOGLE-AUTH] OAuth callback completed successfully")

        return result
