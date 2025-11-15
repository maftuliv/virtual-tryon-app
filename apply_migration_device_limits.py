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
        print("\nApplying migration: 003_add_device_limits.sql")
        print("=" * 70)

        conn = psycopg2.connect(**parse_database_url())
        cursor = conn.cursor()

        # Read and execute migration
        with open('backend/migrations/003_add_device_limits.sql', 'r', encoding='utf-8') as f:
            sql = f.read()

        cursor.execute(sql)
        conn.commit()

        print("\nMigration applied successfully!")
        print("\nVerifying results:")

        # Check if table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'device_limits'
            );
        """)

        table_exists = cursor.fetchone()[0]
        if table_exists:
            print("   [OK] Table 'device_limits' created")

            # Get column count
            cursor.execute("""
                SELECT COUNT(*)
                FROM information_schema.columns
                WHERE table_name = 'device_limits'
            """)
            col_count = cursor.fetchone()[0]
            print(f"   [OK] Table has {col_count} columns")

            # Check indexes
            cursor.execute("""
                SELECT indexname
                FROM pg_indexes
                WHERE tablename = 'device_limits'
            """)
            indexes = cursor.fetchall()
            print(f"   [OK] {len(indexes)} indexes created:")
            for idx in indexes:
                print(f"      - {idx[0]}")

        print("\n" + "=" * 70)

        cursor.close()
        conn.close()

        input("\n\nPress Enter to exit...")

    except ValueError as exc:
        print(f"\n❌ Configuration error: {exc}")
        print("Make sure DATABASE_URL is set in your environment or .env file")
        input("\n\nPress Enter to exit...")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR]: {e}")
        import traceback
        traceback.print_exc()
        input("\n\nPress Enter to exit...")

if __name__ == "__main__":
    apply_migration()
