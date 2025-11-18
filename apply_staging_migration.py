#!/usr/bin/env python3
"""Apply database schema to staging environment."""

import psycopg2

DATABASE_URL = "postgresql://postgres:qrXaZGyZDlvaBbWjnLGaBMRuUasijLQe@centerbeam.proxy.rlwy.net:18275/railway"

# Read SQL file
with open('init_database_schema.sql', 'r', encoding='utf-8') as f:
    sql_script = f.read()

print("Connecting to staging database...")
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

print("Executing migration script...")
try:
    cursor.execute(sql_script)
    conn.commit()
    print("Migration completed successfully!")

    # Verify tables
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_type = 'BASE TABLE'
        ORDER BY table_name
    """)

    tables = cursor.fetchall()
    print(f"\nCreated {len(tables)} tables:")
    for table in tables:
        print(f"  - {table[0]}")

except Exception as e:
    print(f"Error: {e}")
    conn.rollback()
finally:
    cursor.close()
    conn.close()
