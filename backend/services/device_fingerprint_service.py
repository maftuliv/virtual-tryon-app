"""Device fingerprint service."""

import hashlib
import hmac
from typing import Dict

from backend.logger import get_logger

logger = get_logger(__name__)


class DeviceFingerprintService:
    """Generate secure device fingerprints on the server using a secret pepper."""

    def __init__(self, secret: str):
        if not secret:
            raise ValueError("Device fingerprint secret is required")
        self.secret = secret.encode("utf-8")

    def generate_fingerprint(self, stable_components: Dict[str, str]) -> str:
        """
        Generate fingerprint hash using stable device components.

        Args:
            stable_components: Dict of stable strings from client (gpu, screen, tz, etc.)

        Returns:
            Hex digest fingerprint string
        """
        if not stable_components:
            raise ValueError("stable_components must not be empty")

        # Sort keys to ensure deterministic ordering
        sorted_items = sorted(stable_components.items())
        canonical_string = "|".join(f"{key}:{value}" for key, value in sorted_items)

        digest = hmac.new(self.secret, canonical_string.encode("utf-8"), hashlib.sha256).hexdigest()
        logger.debug("Device fingerprint generated for keys: %s", ",".join(stable_components.keys()))
        return digest


__all__ = ["DeviceFingerprintService"]

