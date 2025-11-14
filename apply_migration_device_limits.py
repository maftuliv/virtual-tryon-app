import psycopg2
import os

DATABASE_URL = "postgresql://postgres:rrQVBIrrzIFcRJlZCfjyrqYCmKSDfiKk@gondola.proxy.rlwy.net:15018/railway"

def apply_migration():
    try:
        print("\nApplying migration: 003_add_device_limits.sql")
        print("=" * 70)

        conn = psycopg2.connect(DATABASE_URL)
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

    except Exception as e:
        print(f"\n[ERROR]: {e}")
        import traceback
        traceback.print_exc()
        input("\n\nPress Enter to exit...")

if __name__ == "__main__":
    apply_migration()
