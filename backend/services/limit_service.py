"""Limit management service for device and user generation limits."""

from datetime import date
from typing import Dict, Optional

from backend.logger import get_logger
from backend.repositories.device_limit_repository import DeviceLimitRepository

logger = get_logger(__name__)


class LimitService:
    """
    Service for managing generation limits.

    Responsibilities:
    - Check device limits (anonymous users: 3/day per device fingerprint + IP)
    - Check user limits (authenticated users: from user profile)
    - Increment limit counters
    - Combine device and user limit logic

    Orchestrates DeviceLimitRepository and UserRepository (when available).
    """

    FREE_DAILY_LIMIT = 3  # Free generations per day for anonymous users

    def __init__(
        self,
        device_limit_repo: DeviceLimitRepository,
        user_repository=None,  # Optional: UserRepository (may not be available)
    ):
        """
        Initialize limit service.

        Args:
            device_limit_repo: Repository for device limit tracking
            user_repository: Optional UserRepository for authenticated users
        """
        self.device_limit_repo = device_limit_repo
        self.user_repository = user_repository
        self.logger = get_logger(__name__)

    def check_device_limit(
        self, device_fingerprint: str, ip_address: str, user_agent: str
    ) -> Dict[str, any]:
        """
        Check generation limit for anonymous user (device fingerprint + IP).

        Multi-factor protection: tracks both fingerprint AND IP address.
        Prevents bypass via incognito mode, browser switching, etc.

        Args:
            device_fingerprint: Browser fingerprint
            ip_address: Client IP address
            user_agent: Browser user agent string

        Returns:
            Dictionary with limit status:
            {
                'can_generate': bool,
                'used': int,
                'remaining': int,
                'limit': int
            }
        """
        today = date.today()

        # Ensure record exists (create or reset if date changed)
        self.device_limit_repo.create_or_reset_record(device_fingerprint, ip_address, user_agent, today)

        # Calculate total usage across this IP address
        total_used = self.device_limit_repo.calculate_total_usage(device_fingerprint, ip_address, today)

        can_generate = total_used < self.FREE_DAILY_LIMIT
        remaining = max(0, self.FREE_DAILY_LIMIT - total_used)

        self.logger.info(
            f"Device limit check: FP={device_fingerprint[:16]}... IP={ip_address} "
            f"Used={total_used}/{self.FREE_DAILY_LIMIT}"
        )

        return {
            "can_generate": can_generate,
            "used": total_used,
            "remaining": remaining,
            "limit": self.FREE_DAILY_LIMIT,
        }

    def increment_device_limit(
        self, device_fingerprint: str, ip_address: str, user_agent: str, increment: int = 1
    ) -> Dict[str, any]:
        """
        Increment generation counter for device.

        Multi-factor protection: increments for this fingerprint but returns total across IP.

        Args:
            device_fingerprint: Browser fingerprint
            ip_address: Client IP address
            user_agent: Browser user agent string
            increment: How many generations to add (default: 1)

        Returns:
            Dictionary with updated limit status:
            {
                'success': bool,
                'used': int,
                'remaining': int,
                'limit': int
            }
        """
        today = date.today()

        # Increment usage for this device
        updated_record = self.device_limit_repo.increment_usage(
            device_fingerprint, ip_address, today, increment
        )

        # Calculate total usage across all devices on this IP
        total_used = self.device_limit_repo.calculate_total_usage(device_fingerprint, ip_address, today)

        remaining = max(0, self.FREE_DAILY_LIMIT - total_used)

        self.logger.info(
            f"Device limit incremented: FP={device_fingerprint[:16]}... IP={ip_address} "
            f"Total={total_used}/{self.FREE_DAILY_LIMIT}"
        )

        return {
            "success": True,
            "used": total_used,
            "remaining": remaining,
            "limit": self.FREE_DAILY_LIMIT,
        }

    def check_user_limit(self, user_id: int) -> Dict[str, any]:
        """
        Check generation limit for authenticated user.

        Uses UserRepository (via AuthManager) to get user's daily limit.

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
            ValueError: If user repository not available
        """
        if not self.user_repository:
            raise ValueError("User repository not available - cannot check user limits")

        limit_status = self.user_repository.check_daily_limit(user_id)

        self.logger.info(
            f"User limit check: user_id={user_id} "
            f"Used={limit_status['used']}/{limit_status['limit']}"
        )

        return limit_status

    def increment_user_limit(self, user_id: int, increment: int = 1) -> Dict[str, any]:
        """
        Increment generation counter for authenticated user.

        Args:
            user_id: User ID
            increment: How many generations to add (default: 1)

        Returns:
            Dictionary with updated limit status:
            {
                'success': bool,
                'used': int,
                'remaining': int,
                'limit': int
            }

        Raises:
            ValueError: If user repository not available
        """
        if not self.user_repository:
            raise ValueError("User repository not available - cannot increment user limits")

        updated_status = self.user_repository.increment_daily_limit(user_id, increment)

        self.logger.info(
            f"User limit incremented: user_id={user_id} "
            f"Used={updated_status['used']}/{updated_status['limit']}"
        )

        return {
            "success": True,
            **updated_status,
        }

    def can_generate(
        self,
        user_id: Optional[int] = None,
        device_fingerprint: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Dict[str, any]:
        """
        Universal limit checker - works for both authenticated and anonymous users.

        If user_id is provided: check user limits
        Otherwise: check device limits

        Args:
            user_id: User ID (optional, for authenticated users)
            device_fingerprint: Browser fingerprint (required for anonymous)
            ip_address: Client IP address (required for anonymous)
            user_agent: Browser user agent (required for anonymous)

        Returns:
            Dictionary with limit status:
            {
                'can_generate': bool,
                'used': int,
                'remaining': int,
                'limit': int,
                'user_type': 'authenticated' | 'anonymous'
            }

        Raises:
            ValueError: If required parameters missing
        """
        if user_id:
            # Authenticated user
            if not self.user_repository:
                self.logger.warning("User repository not available, falling back to device limits")
                # Fallback to device limits
                if not all([device_fingerprint, ip_address, user_agent]):
                    raise ValueError("Device fingerprint, IP, and user agent required for anonymous users")
                result = self.check_device_limit(device_fingerprint, ip_address, user_agent)
                result["user_type"] = "anonymous"
                return result

            result = self.check_user_limit(user_id)
            result["user_type"] = "authenticated"
            return result
        else:
            # Anonymous user
            if not all([device_fingerprint, ip_address, user_agent]):
                raise ValueError("Device fingerprint, IP, and user agent required for anonymous users")

            result = self.check_device_limit(device_fingerprint, ip_address, user_agent)
            result["user_type"] = "anonymous"
            return result

    def increment_limit(
        self,
        user_id: Optional[int] = None,
        device_fingerprint: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        increment: int = 1,
    ) -> Dict[str, any]:
        """
        Universal limit incrementer - works for both authenticated and anonymous users.

        If user_id is provided: increment user limits
        Otherwise: increment device limits

        Args:
            user_id: User ID (optional, for authenticated users)
            device_fingerprint: Browser fingerprint (required for anonymous)
            ip_address: Client IP address (required for anonymous)
            user_agent: Browser user agent (required for anonymous)
            increment: How many generations to add (default: 1)

        Returns:
            Dictionary with updated limit status:
            {
                'success': bool,
                'used': int,
                'remaining': int,
                'limit': int,
                'user_type': 'authenticated' | 'anonymous'
            }

        Raises:
            ValueError: If required parameters missing
        """
        if user_id:
            # Authenticated user
            if not self.user_repository:
                self.logger.warning("User repository not available, falling back to device limits")
                # Fallback to device limits
                if not all([device_fingerprint, ip_address, user_agent]):
                    raise ValueError("Device fingerprint, IP, and user agent required for anonymous users")
                result = self.increment_device_limit(device_fingerprint, ip_address, user_agent, increment)
                result["user_type"] = "anonymous"
                return result

            result = self.increment_user_limit(user_id, increment)
            result["user_type"] = "authenticated"
            return result
        else:
            # Anonymous user
            if not all([device_fingerprint, ip_address, user_agent]):
                raise ValueError("Device fingerprint, IP, and user agent required for anonymous users")

            result = self.increment_device_limit(device_fingerprint, ip_address, user_agent, increment)
            result["user_type"] = "anonymous"
            return result
