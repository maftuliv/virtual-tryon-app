import sys
import psycopg2
import os

# Import centralized database configuration
try:
    from backend.db_config import parse_database_url
except ImportError:
    print("Error: Cannot import backend.db_config")
    print("Make sure you're running from the project root directory")
    sys.exit(1)


def apply_migration():
    try:
        print("\nApplying migration: 004_update_device_limits_for_ip.sql")
        print("=" * 70)

        conn = psycopg2.connect(**parse_database_url())
        cursor = conn.cursor()

        # Read and execute migration
        with open('backend/migrations/004_update_device_limits_for_ip.sql', 'r', encoding='utf-8') as f:
            sql = f.read()

        cursor.execute(sql)
        conn.commit()

        print("\nMigration applied successfully!")
        print("\nVerifying results:")

        # Check indexes
        cursor.execute("""
            SELECT indexname
            FROM pg_indexes
            WHERE tablename = 'device_limits'
            ORDER BY indexname
        """)
        indexes = cursor.fetchall()
        print(f"   [OK] {len(indexes)} indexes found:")
        for idx in indexes:
            print(f"      - {idx[0]}")

        # Check constraints
        cursor.execute("""
            SELECT conname, contype
            FROM pg_constraint
            WHERE conrelid = 'device_limits'::regclass
        """)
        constraints = cursor.fetchall()
        print(f"\n   [OK] {len(constraints)} constraints:")
        for con in constraints:
            print(f"      - {con[0]} (type: {con[1]})")

        print("\n" + "=" * 70)

        cursor.close()
        conn.close()

        print("\n[SUCCESS] Database updated for multi-factor IP protection!")

    except ValueError as exc:
        print(f"\n❌ Configuration error: {exc}")
        print("Make sure DATABASE_URL is set in your environment or .env file")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR]: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    apply_migration()
