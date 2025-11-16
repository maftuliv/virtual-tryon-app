#!/usr/bin/env python3
"""Check if generations table exists and has data."""

import sys
sys.path.insert(0, '.')

from backend.config import Settings
import psycopg2

def main():
    print("=== Checking generations table ===\n")

    config = Settings()
    conn = psycopg2.connect(str(config.database_url))
    cursor = conn.cursor()

    # Check if table exists
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_name = 'generations'
        )
    """)
    table_exists = cursor.fetchone()[0]
    print(f"Table 'generations' exists: {table_exists}")

    if not table_exists:
        print("\n[ERROR] Table 'generations' does not exist!")
        print("You need to apply migration: 001_create_auth_tables.sql")
        return

    # Check table structure
    cursor.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'generations'
        ORDER BY ordinal_position
    """)
    columns = cursor.fetchall()
    print(f"\nTable structure ({len(columns)} columns):")
    for col_name, col_type in columns:
        print(f"  - {col_name}: {col_type}")

    # Count total generations
    cursor.execute("SELECT COUNT(*) FROM generations")
    total = cursor.fetchone()[0]
    print(f"\nTotal generations: {total}")

    # Count today's generations
    cursor.execute("SELECT COUNT(*) FROM generations WHERE DATE(created_at) = CURRENT_DATE")
    today = cursor.fetchone()[0]
    print(f"Generations today: {today}")

    # Show recent generations
    cursor.execute("""
        SELECT id, user_id, category, status, created_at
        FROM generations
        ORDER BY created_at DESC
        LIMIT 10
    """)
    recent = cursor.fetchall()
    print(f"\nRecent generations (last 10):")
    if recent:
        for gen in recent:
            print(f"  ID={gen[0]}, user_id={gen[1]}, category={gen[2]}, status={gen[3]}, created_at={gen[4]}")
    else:
        print("  No generations found!")

    cursor.close()
    conn.close()

if __name__ == '__main__':
    main()
