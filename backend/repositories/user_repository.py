"""User repository - wraps AuthManager for user operations."""

from typing import Dict, List, Optional

from backend.auth import AuthManager
from backend.logger import get_logger

logger = get_logger(__name__)


class UserRepository:
    """
    User data access layer.

    Wraps backend.auth.AuthManager to provide consistent repository interface.
    All user-related database operations go through this repository.
    """

    def __init__(self, auth_manager: Optional[AuthManager] = None):
        """
        Initialize repository with AuthManager.

        Args:
            auth_manager: AuthManager instance (None if auth unavailable)
        """
        self.auth_manager = auth_manager

    def is_available(self) -> bool:
        """Check if authentication system is available."""
        return self.auth_manager is not None

    def create_user(
        self, email: str, password: str, full_name: str, provider: str = "email"
    ) -> Dict:
        """
        Register new user.

        Args:
            email: User email address
            password: User password (will be hashed)
            full_name: User's full name
            provider: Auth provider (default: "email", also: "google")

        Returns:
            Dictionary with user data:
            {
                'success': bool,
                'user': {
                    'id': int,
                    'email': str,
                    'full_name': str,
                    'provider': str,
                    'is_premium': bool,
                    'role': str,
                    'created_at': datetime
                },
                'token': str  # JWT token
            }

        Raises:
            ValueError: If email already exists or validation fails
            RuntimeError: If auth system unavailable
        """
        if not self.is_available():
            raise RuntimeError("Authentication system is not available")

        try:
            result = self.auth_manager.register_user(email, password, full_name, provider)
            return result

        except Exception as e:
            logger.error(f"Error creating user {email}: {e}", exc_info=True)
            raise

    def authenticate(self, email: str, password: str) -> Optional[Dict]:
        """
        Verify credentials and return user with token.

        Args:
            email: User email
            password: User password

        Returns:
            Dictionary with user and token if authenticated:
            {
                'success': bool,
                'user': {...},
                'token': str
            }
            Returns None if authentication fails.

        Raises:
            RuntimeError: If auth system unavailable
        """
        if not self.is_available():
            raise RuntimeError("Authentication system is not available")

        try:
            result = self.auth_manager.login_user(email, password)
            return result

        except Exception as e:
            logger.error(f"Error authenticating user {email}: {e}", exc_info=True)
            return None

    def get_by_id(self, user_id: int) -> Optional[Dict]:
        """
        Get user by ID.

        Args:
            user_id: User ID

        Returns:
            User dictionary or None if not found
        """
        if not self.is_available():
            return None

        try:
            user = self.auth_manager.get_user_by_id(user_id)
            return user

        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}", exc_info=True)
            return None

    def get_by_token(self, token: str) -> Optional[Dict]:
        """
        Validate JWT token and return user.

        Args:
            token: JWT token string

        Returns:
            User dictionary or None if token invalid
        """
        if not self.is_available():
            return None

        try:
            user = self.auth_manager.validate_token(token)
            return user

        except Exception as e:
            logger.error(f"Error validating token: {e}", exc_info=True)
            return None

    def check_daily_limit(self, user_id: int) -> Dict:
        """
        Check user's daily generation limit.

        Args:
            user_id: User ID

        Returns:
            Dictionary with limit info:
            {
                'can_generate': bool,
                'used': int,
                'limit': int,
                'remaining': int
            }

        Raises:
            RuntimeError: If auth system unavailable
        """
        if not self.is_available():
            raise RuntimeError("Authentication system is not available")

        try:
            # AuthManager returns tuple: (can_generate, used, limit)
            can_generate, used, limit = self.auth_manager.check_daily_limit(user_id)

            # Convert to dict format expected by service layer
            remaining = max(0, limit - used) if limit > 0 else -1  # -1 for unlimited

            return {
                "can_generate": can_generate,
                "used": used,
                "limit": limit,
                "remaining": remaining,
            }

        except Exception as e:
            logger.error(f"Error checking limit for user {user_id}: {e}", exc_info=True)
            raise

    def increment_daily_limit(self, user_id: int, increment: int = 1) -> Dict:
        """
        Increment user's generation counter.

        Args:
            user_id: User ID
            increment: Amount to increment (default: 1)

        Returns:
            Updated limit info dictionary

        Raises:
            RuntimeError: If auth system unavailable
        """
        if not self.is_available():
            raise RuntimeError("Authentication system is not available")

        try:
            limit_info = self.auth_manager.increment_daily_limit(user_id, increment)
            return limit_info

        except Exception as e:
            logger.error(f"Error incrementing limit for user {user_id}: {e}", exc_info=True)
            raise

    def list_all_users(self) -> List[Dict]:
        """
        Get all users with generation counts (admin operation).

        Returns:
            List of user dictionaries with metadata:
            [
                {
                    'id': int,
                    'email': str,
                    'full_name': str,
                    'provider': str,
                    'is_premium': bool,
                    'premium_until': datetime,
                    'role': str,
                    'created_at': datetime,
                    'generation_count': int
                },
                ...
            ]

        Raises:
            RuntimeError: If auth system unavailable
        """
        if not self.is_available():
            raise RuntimeError("Authentication system is not available")

        try:
            # AuthManager doesn't have this method yet, will need to add it
            # For now, return empty list
            logger.warning("list_all_users not yet implemented in AuthManager")
            return []

        except Exception as e:
            logger.error(f"Error listing users: {e}", exc_info=True)
            raise

    def toggle_premium(self, user_id: int, enable: bool, days: int = 30) -> Dict:
        """
        Grant or revoke premium status.

        Args:
            user_id: User ID
            enable: True to grant premium, False to revoke
            days: Number of days to grant premium (default: 30)

        Returns:
            Updated user dictionary

        Raises:
            RuntimeError: If auth system unavailable
            ValueError: If user not found
        """
        if not self.is_available():
            raise RuntimeError("Authentication system is not available")

        try:
            # AuthManager doesn't have this method yet, will need to add it
            logger.warning("toggle_premium not yet implemented in AuthManager")
            user = self.get_by_id(user_id)
            if not user:
                raise ValueError(f"User {user_id} not found")
            return user

        except Exception as e:
            logger.error(f"Error toggling premium for user {user_id}: {e}", exc_info=True)
            raise
