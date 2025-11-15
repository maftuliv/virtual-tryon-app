"""
Centralized database configuration module.
All database utilities should import from here instead of hardcoding credentials.
"""
import os
from urllib.parse import urlparse


def get_database_url():
    """
    Get DATABASE_URL from environment variables with proper fallback.

    Priority:
    1. DATABASE_URL environment variable
    2. Raise error if not found (fail-safe approach)

    Returns:
        str: PostgreSQL connection URL

    Raises:
        ValueError: If DATABASE_URL is not configured
    """
    db_url = os.getenv('DATABASE_URL')

    if not db_url:
        raise ValueError(
            "DATABASE_URL environment variable is not set. "
            "Please configure it in .env file or Railway settings."
        )

    return db_url


def parse_database_url(db_url=None):
    """
    Parse PostgreSQL URL into connection parameters.

    Args:
        db_url: Database URL (if None, will get from environment)

    Returns:
        dict: Connection parameters for psycopg2
    """
    if db_url is None:
        db_url = get_database_url()

    parsed = urlparse(db_url)

    if parsed.scheme not in ("postgresql", "postgres"):
        raise ValueError(f"Unsupported database scheme: {parsed.scheme}")

    if not parsed.hostname:
        raise ValueError("Database URL must include hostname")

    return {
        "dbname": parsed.path.lstrip("/"),
        "user": parsed.username,
        "password": parsed.password,
        "host": parsed.hostname,
        "port": parsed.port or 5432,
        "sslmode": "require",
        "connect_timeout": 10,
    }
