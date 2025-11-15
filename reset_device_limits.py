"""
Utility script to reset anonymous device limits (free quota) in PostgreSQL.

Usage:
    python reset_device_limits.py

If DATABASE_URL is not set in the environment, edit DEFAULT_DB_URL below.
"""

import os
import psycopg2

DEFAULT_DB_URL = "postgresql://postgres:rrQVBIrrzIFcRJlZCfjyrqYCmKSDfiKk@gondola.proxy.rlwy.net:15018/railway"


def reset_limits():
    db_url = os.getenv("DATABASE_URL", DEFAULT_DB_URL)
    print(f"Connecting to database: {db_url}")
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    cur.execute("TRUNCATE TABLE device_limits RESTART IDENTITY CASCADE;")
    conn.commit()
    cur.close()
    conn.close()
    print("✅ device_limits table truncated. Free quota reset.")


if __name__ == "__main__":
    reset_limits()

