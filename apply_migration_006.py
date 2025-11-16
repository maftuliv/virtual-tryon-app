#!/usr/bin/env python3
"""Apply migration 006: Add device_fingerprint to generations table."""

import sys
sys.path.insert(0, '.')

from backend.config import Settings
import psycopg2

def main():
    print("Applying migration: 006_add_device_fingerprint_to_generations.sql")
    print("=" * 70)

    config = Settings()
    conn = psycopg2.connect(str(config.database_url))
    cursor = conn.cursor()

    # Read and execute migration
    with open('backend/migrations/006_add_device_fingerprint_to_generations.sql', 'r') as f:
        migration_sql = f.read()

    try:
        cursor.execute(migration_sql)
        conn.commit()
        print("Migration applied successfully!")
    except Exception as e:
        conn.rollback()
        print(f"[ERROR] Migration failed: {e}")
        return

    # Verify columns were added
    cursor.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'generations'
        ORDER BY ordinal_position
    """)
    columns = [row[0] for row in cursor.fetchall()]

    print("\nVerifying results:")
    if 'device_fingerprint' in columns:
        print("   [OK] Column 'device_fingerprint' added")
    else:
        print("   [ERROR] Column 'device_fingerprint' NOT found")

    if 'updated_at' in columns:
        print("   [OK] Column 'updated_at' added")
    else:
        print("   [ERROR] Column 'updated_at' NOT found")

    # Check index
    cursor.execute("""
        SELECT indexname FROM pg_indexes WHERE tablename = 'generations'
    """)
    indexes = [row[0] for row in cursor.fetchall()]
    if 'idx_generations_device_fingerprint' in indexes:
        print("   [OK] Index 'idx_generations_device_fingerprint' created")
    else:
        print("   [WARNING] Index not found (may already exist)")

    print("\n[SUCCESS] Migration completed!")

    cursor.close()
    conn.close()

if __name__ == '__main__':
    main()
