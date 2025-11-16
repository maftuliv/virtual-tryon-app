"""Authentication service wrapper."""

from typing import Dict, Optional

from backend.logger import get_logger

logger = get_logger(__name__)


class AuthService:
    """
    Service for authentication and user management.

    Thin wrapper around UserRepository (which wraps AuthManager).
    Provides consistent service interface for authentication operations.

    Responsibilities:
    - User registration
    - User login (email/password)
    - Token validation
    - User limit checking

    Note: This is a simple wrapper since AuthManager already handles
    most business logic. Main purpose is to provide consistent service
    interface and add logging/validation layer.
    """

    def __init__(self, user_repository=None):
        """
        Initialize authentication service.

        Args:
            user_repository: UserRepository instance (optional, may not be available)
        """
        self.user_repository = user_repository
        self.logger = get_logger(__name__)

    def is_available(self) -> bool:
        """
        Check if authentication is available.

        Returns:
            True if UserRepository is configured, False otherwise
        """
        return self.user_repository is not None

    def register(self, email: str, password: str, full_name: str, provider: str = "email") -> Dict:
        """
        Register new user.

        Args:
            email: User email address
            password: User password (will be hashed)
            full_name: User's full name
            provider: Authentication provider (default: "email")

        Returns:
            User dictionary with token:
            {
                'id': int,
                'email': str,
                'full_name': str,
                'is_premium': bool,
                'provider': str,
                'role': str,
                'token': str,
                'created_at': str
            }

        Raises:
            ValueError: If authentication not available or validation fails
        """
        if not self.user_repository:
            raise ValueError("Authentication not available")

        # Validate inputs
        if not email or not email.strip():
            raise ValueError("Email is required")

        if not password or len(password) < 6:
            raise ValueError("Password must be at least 6 characters")

        if not full_name or not full_name.strip():
            raise ValueError("Full name is required")

        self.logger.info(f"Registering new user: email={email}, provider={provider}")

        user = self.user_repository.create_user(
            email=email.strip(), password=password, full_name=full_name.strip(), provider=provider
        )

        self.logger.info(f"User registered successfully: id={user['id']}, email={user['email']}")

        return user

    def login(self, email: str, password: str) -> Optional[Dict]:
        """
        Authenticate user and return user data with token.

        Args:
            email: User email address
            password: User password

        Returns:
            User dictionary with token if successful, None if authentication failed:
            {
                'id': int,
                'email': str,
                'full_name': str,
                'is_premium': bool,
                'provider': str,
                'role': str,
                'token': str,
                'daily_limit': {
                    'can_generate': bool,
                    'used': int,
                    'remaining': int,
                    'limit': int
                }
            }

        Raises:
            ValueError: If authentication not available
        """
        if not self.user_repository:
            raise ValueError("Authentication not available")

        # Validate inputs
        if not email or not email.strip():
            raise ValueError("Email is required")

        if not password:
            raise ValueError("Password is required")

        self.logger.info(f"Login attempt: email={email}")

        result = self.user_repository.authenticate(email.strip(), password)

        if result and result.get("success"):
            user_data = result.get("user", {})
            token = result.get("token")
            # Merge token into user_data for convenience
            if user_data and token:
                user_data["token"] = token
            self.logger.info(f"Login successful: user_id={user_data.get('id')}, email={user_data.get('email')}")
            return user_data
        else:
            self.logger.warning(f"Login failed: invalid credentials for email={email}")
            return None

    def get_user_by_token(self, token: str) -> Optional[Dict]:
        """
        Validate token and return user data.

        Args:
            token: JWT token

        Returns:
            User dictionary if token is valid, None otherwise

        Raises:
            ValueError: If authentication not available
        """
        if not self.user_repository:
            raise ValueError("Authentication not available")

        if not token or not token.strip():
            return None

        self.logger.info("Validating token...")

        user = self.user_repository.get_by_token(token.strip())

        if user:
            self.logger.info(f"Token valid: user_id={user['id']}")
        else:
            self.logger.warning("Token invalid or expired")

        return user

    def check_daily_limit(self, user_id: int) -> Dict:
        """
        Check user's daily generation limit.

        Args:
            user_id: User ID

        Returns:
            Dictionary with limit status:
            {
                'can_generate': bool,
                'used': int,
                'remaining': int,
                'limit': int
            }

        Raises:
            ValueError: If authentication not available
        """
        if not self.user_repository:
            raise ValueError("Authentication not available")

        self.logger.info(f"Checking daily limit for user_id={user_id}")

        limit_status = self.user_repository.check_daily_limit(user_id)

        self.logger.info(
            f"User limit: user_id={user_id}, "
            f"used={limit_status['used']}/{limit_status['limit']}, "
            f"can_generate={limit_status['can_generate']}"
        )

        return limit_status

    def increment_daily_limit(self, user_id: int, increment: int = 1) -> Dict:
        """
        Increment user's daily generation counter.

        Args:
            user_id: User ID
            increment: How many generations to add (default: 1)

        Returns:
            Dictionary with updated limit status:
            {
                'can_generate': bool,
                'used': int,
                'remaining': int,
                'limit': int
            }

        Raises:
            ValueError: If authentication not available
        """
        if not self.user_repository:
            raise ValueError("Authentication not available")

        self.logger.info(f"Incrementing daily limit for user_id={user_id} by {increment}")

        updated_status = self.user_repository.increment_daily_limit(user_id, increment)

        self.logger.info(
            f"User limit incremented: user_id={user_id}, "
            f"used={updated_status['used']}/{updated_status['limit']}"
        )

        return updated_status
