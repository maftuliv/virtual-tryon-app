"""
External API client wrappers.

Each client encapsulates communication with an external service:
- HTTP request handling
- Response parsing
- Retry logic
- Error mapping to domain exceptions

Clients return domain objects or DTOs, never raw API responses.
"""

__all__ = []
