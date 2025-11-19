"""
Google OAuth 2.0 Authentication Service.

Handles Google OAuth flow: authorization URL generation, token exchange,
user profile retrieval, and user creation/login.
"""

import hmac
import hashlib
import secrets
import time
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
        
        # Log configuration (masked for security)
        client_id_masked = self._mask_sensitive(settings.google_client_id) if settings.google_client_id else "NOT SET"
        redirect_uri = settings.google_redirect_uri
        self.logger.info(f"[GOOGLE-AUTH] Client ID: {client_id_masked}")
        self.logger.info(f"[GOOGLE-AUTH] Redirect URI: {redirect_uri}")
        
        # Validate Client ID format
        if settings.google_client_id and not settings.google_client_id.endswith(".apps.googleusercontent.com"):
            self.logger.warning(
                f"[GOOGLE-AUTH] Client ID format may be incorrect. "
                f"Expected format: *.apps.googleusercontent.com, got: {client_id_masked}"
            )

    def is_enabled(self) -> bool:
        """
        Check if Google OAuth is properly configured and enabled.

        Returns:
            True if Google OAuth is ready, False otherwise
        """
        return self.enabled

    def _sign_state(self, state: str) -> str:
        """
        Sign state token with HMAC for CSRF protection.
        State is signed so it can be validated without session storage.
        
        Args:
            state: Random state token
            
        Returns:
            Signed state token (state.timestamp.signature)
        """
        timestamp = str(int(time.time()))
        secret = self.settings.jwt_secret_key.encode('utf-8')
        message = f"{state}.{timestamp}".encode('utf-8')
        signature = hmac.new(secret, message, hashlib.sha256).hexdigest()[:16]
        return f"{state}.{timestamp}.{signature}"
    
    def _verify_state(self, signed_state: str) -> Optional[str]:
        """
        Verify signed state token and extract original state.
        
        Args:
            signed_state: Signed state token (state.timestamp.signature)
            
        Returns:
            Original state token if valid, None otherwise
        """
        try:
            parts = signed_state.split('.')
            if len(parts) != 3:
                return None
            
            state, timestamp_str, signature = parts
            timestamp = int(timestamp_str)
            
            # Check expiration (5 minutes)
            if time.time() - timestamp > 300:
                self.logger.warning(f"[GOOGLE-AUTH] State token expired (age: {time.time() - timestamp}s)")
                return None
            
            # Verify signature
            secret = self.settings.jwt_secret_key.encode('utf-8')
            message = f"{state}.{timestamp_str}".encode('utf-8')
            expected_signature = hmac.new(secret, message, hashlib.sha256).hexdigest()[:16]
            
            if not hmac.compare_digest(signature, expected_signature):
                self.logger.warning("[GOOGLE-AUTH] State token signature invalid")
                return None
            
            return state
        except (ValueError, IndexError) as e:
            self.logger.warning(f"[GOOGLE-AUTH] State token verification failed: {e}")
            return None

    def generate_authorization_url(self) -> Tuple[str, str]:
        """
        Generate Google OAuth authorization URL with signed state token.

        Returns:
            Tuple of (authorization_url, signed_state_token)
            - authorization_url: URL to redirect user to Google login
            - signed_state_token: Signed state token for CSRF protection (includes in URL, no session needed)

        Raises:
            RuntimeError: If Google OAuth is not enabled
        """
        if not self.is_enabled():
            raise RuntimeError("Google OAuth is not enabled or misconfigured")

        # Generate random state for CSRF protection
        state = secrets.token_urlsafe(32)
        
        # Sign state token (so it can be validated without session)
        signed_state = self._sign_state(state)

        try:
            # Log configuration details for debugging (masked)
            client_id_masked = self._mask_sensitive(self.settings.google_client_id)
            self.logger.info(
                f"[GOOGLE-AUTH] Generating authorization URL with Client ID: {client_id_masked}, "
                f"Redirect URI: {self.settings.google_redirect_uri}"
            )
            
            # Validate Client ID format before making request
            if not self.settings.google_client_id or not self.settings.google_client_id.strip():
                raise ValueError("GOOGLE_CLIENT_ID is empty or contains only whitespace")
            
            if not self.settings.google_client_id.endswith(".apps.googleusercontent.com"):
                self.logger.warning(
                    f"[GOOGLE-AUTH] Client ID format may be incorrect: {client_id_masked}"
                )
            
            # Create OAuth 2.0 flow
            # Note: Use signed_state in Flow so it's included in the authorization URL
            flow = Flow.from_client_config(
                client_config={
                    "web": {
                        "client_id": self.settings.google_client_id.strip(),  # Strip whitespace
                        "client_secret": self.settings.google_client_secret.strip() if self.settings.google_client_secret else "",
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [self.settings.google_redirect_uri.strip()],
                    }
                },
                scopes=self.SCOPES,
                state=signed_state,  # Use signed state so it's included in URL
            )

            flow.redirect_uri = self.settings.google_redirect_uri.strip()

            # Generate authorization URL
            # The signed_state will be included in the URL as the 'state' parameter
            authorization_url, _ = flow.authorization_url(
                access_type="offline",  # Request refresh token
                include_granted_scopes="true",
                prompt="consent",  # Force consent screen to ensure refresh token
            )

            self.logger.info(
                f"[GOOGLE-AUTH] Generated authorization URL (state={state[:8]}...), "
                f"URL length: {len(authorization_url)} chars"
            )
            
            # Log first part of URL for debugging (before query params)
            url_base = authorization_url.split("?")[0] if "?" in authorization_url else authorization_url
            self.logger.debug(f"[GOOGLE-AUTH] Authorization URL base: {url_base}")

            return authorization_url, signed_state

        except ValueError as e:
            self.logger.error(f"[GOOGLE-AUTH] Validation error: {e}")
            raise RuntimeError(f"Invalid OAuth configuration: {e}")
        except Exception as e:
            self.logger.error(
                f"[GOOGLE-AUTH] Error generating authorization URL: {e}", 
                exc_info=True
            )
            self.logger.error(
                f"[GOOGLE-AUTH] Client ID (masked): {self._mask_sensitive(self.settings.google_client_id)}, "
                f"Redirect URI: {self.settings.google_redirect_uri}"
            )
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
            # Note: Use the same state that was in authorization URL (signed_state)
            # But we validate the state separately, so we can use the original state here
            flow = Flow.from_client_config(
                client_config={
                    "web": {
                        "client_id": self.settings.google_client_id.strip(),
                        "client_secret": self.settings.google_client_secret.strip() if self.settings.google_client_secret else "",
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [self.settings.google_redirect_uri.strip()],
                    }
                },
                scopes=self.SCOPES,
                state=state,  # Use validated state (already verified)
            )

            flow.redirect_uri = self.settings.google_redirect_uri.strip()

            # Log for debugging
            client_id_masked = self._mask_sensitive(self.settings.google_client_id)
            client_secret_masked = self._mask_sensitive(self.settings.google_client_secret) if self.settings.google_client_secret else "NOT SET"
            self.logger.info(
                f"[GOOGLE-AUTH] Exchanging code for token (state={state[:8]}..., "
                f"client_id={client_id_masked}, client_secret={client_secret_masked})"
            )
            self.logger.info(
                f"[GOOGLE-AUTH] Redirect URI: {self.settings.google_redirect_uri}"
            )

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

    def _mask_sensitive(self, value: Optional[str]) -> str:
        """
        Mask sensitive value for logging (shows first 10 and last 4 chars).
        
        Args:
            value: Value to mask
            
        Returns:
            Masked string or "NOT SET" if value is None/empty
        """
        if not value:
            return "NOT SET"
        value = value.strip()
        if len(value) <= 14:
            return "***" * len(value)
        return f"{value[:10]}...{value[-4:]}"

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

        if result.get("success"):
            self.logger.info("[GOOGLE-AUTH] OAuth callback completed successfully")
        else:
            self.logger.error(
                "[GOOGLE-AUTH] OAuth callback failed during user creation: %s",
                result.get("error"),
            )

        return result
