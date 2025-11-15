"""
API route handlers (thin layer).

Each module registers a Flask Blueprint with route handlers that:
- Parse HTTP requests
- Call appropriate service methods
- Format HTTP responses
- Handle HTTP errors

No business logic should exist in this layer.
"""

__all__ = []
