"""
Utility script to reset anonymous device limits (free quota) in PostgreSQL.

Usage:
    python reset_device_limits.py [optional_database_url]

Priority of DB URL:
1. Command-line argument
2. Environment variable DATABASE_URL
3. DEFAULT_DB_URL in this file
"""

import os
import sys
import psycopg2
from urllib.parse import urlparse

DEFAULT_DB_URL = "postgresql://postgres:rrQVBIrrzIFcRJlZCfjyrqYCmKSDfiKk@gondola.proxy.rlwy.net:15018/railway"


def parse_db_url(db_url: str) -> dict:
    parsed = urlparse(db_url)
    if parsed.scheme not in ("postgresql", "postgres"):
        raise ValueError(f"Unsupported scheme in DATABASE_URL: {parsed.scheme}")
    if not parsed.hostname:
        raise ValueError("DATABASE_URL must include hostname")

    port = parsed.port or 5432
    return {
        "dbname": parsed.path.lstrip("/"),
        "user": parsed.username,
        "password": parsed.password,
        "host": parsed.hostname,
        "port": port,
        "sslmode": "require",
        "connect_timeout": 10,
    }


def reset_limits(db_url: str):
    print(f"Connecting to database...")
    conn = psycopg2.connect(**parse_db_url(db_url))
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
    db_url = (
        sys.argv[1]
        if len(sys.argv) > 1
        else os.getenv("DATABASE_URL", DEFAULT_DB_URL)
    )
    try:
        reset_limits(db_url)
    except Exception as exc:
        print(f"❌ Failed to reset limits: {exc}")
        sys.exit(1)

