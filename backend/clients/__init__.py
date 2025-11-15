"""
External API client wrappers.

Each client encapsulates communication with an external service:
- HTTP request handling
- Response parsing
- Retry logic
- Error mapping to domain exceptions

Clients return domain objects or DTOs, never raw API responses.
"""

from backend.clients.nanobanana_client import NanoBananaClient
from backend.clients.telegram_client import TelegramClient

__all__ = [
    "NanoBananaClient",
    "TelegramClient",
]
