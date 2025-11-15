"""
Utility script to reset anonymous device limits (free quota) in PostgreSQL.

Usage:
    python reset_device_limits.py

Requires DATABASE_URL environment variable to be set.
"""

import sys
import psycopg2

# Import centralized database configuration
try:
    from backend.db_config import get_database_url, parse_database_url
except ImportError:
    print("Error: Cannot import backend.db_config")
    print("Make sure you're running from the project root directory")
    sys.exit(1)


def reset_limits():
    print("Connecting to database...")
    conn = psycopg2.connect(**parse_database_url())
    cur = conn.cursor()

    # Get today's date
    from datetime import date
    today = date.today()

    # Option 1: Reset ONLY today's records to 0 (keeps history)
    cur.execute("""
        UPDATE device_limits
        SET generations_used = 0, updated_at = NOW()
        WHERE limit_date = %s
        RETURNING id
    """, (today,))

    updated_count = cur.rowcount
    conn.commit()

    # Show stats
    cur.execute("SELECT COUNT(*) FROM device_limits WHERE limit_date = %s", (today,))
    total_today = cur.fetchone()[0]

    cur.close()
    conn.close()

    print(f"✅ Reset complete!")
    print(f"   Updated {updated_count} records for today ({today})")
    print(f"   Total records for today: {total_today}")
    print(f"   Free quota (3 generations) restored for all devices")


if __name__ == "__main__":
    try:
        reset_limits()
    except ValueError as exc:
        print(f"❌ Configuration error: {exc}")
        print("Make sure DATABASE_URL is set in your environment or .env file")
        sys.exit(1)
    except Exception as exc:
        print(f"❌ Failed to reset limits: {exc}")
        sys.exit(1)

