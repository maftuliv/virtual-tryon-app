"""
Data access layer (repositories).

Repositories handle all database and file storage operations:
- CRUD operations
- Query building
- Connection management
- Data mapping to domain models

No business logic should exist in repositories.
"""

from backend.repositories.device_limit_repository import DeviceLimitRepository
from backend.repositories.feedback_repository import FeedbackRepository
from backend.repositories.generation_repository import GenerationRepository

# UserRepository imports AuthManager which has emoji in print statements
# This causes UnicodeEncodeError on Windows cp1251 encoding
# Import it explicitly when needed: from backend.repositories.user_repository import UserRepository
# Works fine on Railway (Linux UTF-8)

__all__ = [
    "DeviceLimitRepository",
    "GenerationRepository",
    "FeedbackRepository",
    # "UserRepository",  # Import explicitly to avoid Windows emoji issues
]
