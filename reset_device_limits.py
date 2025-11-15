"""
Utility script to reset anonymous device limits (free quota) in PostgreSQL.

Usage:
    python reset_device_limits.py

Requires DATABASE_URL environment variable to be set.
"""

import os
import sys
from urllib.parse import urlparse

import psycopg2
from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()


def get_db_connection_params():
    """Get database connection parameters from DATABASE_URL."""
    db_url = os.getenv("DATABASE_URL")

    if not db_url:
        raise ValueError(
            "DATABASE_URL environment variable is not set. "
            "Please configure it in .env file or set it in your environment."
        )

    # Parse the URL
    parsed = urlparse(db_url)

    if parsed.scheme not in ("postgresql", "postgres"):
        raise ValueError(f"Unsupported database scheme: {parsed.scheme}")

    return {
        "dbname": parsed.path.lstrip("/"),
        "user": parsed.username,
        "password": parsed.password,
        "host": parsed.hostname,
        "port": parsed.port or 5432,
        "sslmode": "require",
        "connect_timeout": 10,
    }


def reset_limits():
    """Reset device limits for today to restore free quota."""
    from datetime import date

    print("Connecting to database...")
    conn = psycopg2.connect(**get_db_connection_params())
    cur = conn.cursor()

    # Get today's date
    today = date.today()

    # Reset ONLY today's records to 0 (keeps history)
    cur.execute(
        """
        UPDATE device_limits
        SET generations_used = 0, updated_at = NOW()
        WHERE limit_date = %s
        RETURNING id
    """,
        (today,),
    )

    updated_count = cur.rowcount
    conn.commit()

    # Show stats
    cur.execute("SELECT COUNT(*) FROM device_limits WHERE limit_date = %s", (today,))
    total_today = cur.fetchone()[0]

    cur.close()
    conn.close()

    print("[OK] Reset complete!")
    print(f"   Updated {updated_count} records for today ({today})")
    print(f"   Total records for today: {total_today}")
    print("   Free quota (3 generations) restored for all devices")


if __name__ == "__main__":
    try:
        reset_limits()
    except ValueError as exc:
        print(f"[ERROR] Configuration error: {exc}")
        print("Make sure DATABASE_URL is set in your environment or .env file")
        sys.exit(1)
    except Exception as exc:
        print(f"[ERROR] Failed to reset limits: {exc}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

