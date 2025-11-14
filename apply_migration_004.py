import psycopg2
import os

DATABASE_URL = "postgresql://postgres:rrQVBIrrzIFcRJlZCfjyrqYCmKSDfiKk@gondola.proxy.rlwy.net:15018/railway"

def apply_migration():
    try:
        print("\nApplying migration: 004_update_device_limits_for_ip.sql")
        print("=" * 70)

        conn = psycopg2.connect(DATABASE_URL)
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

    except Exception as e:
        print(f"\n[ERROR]: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    apply_migration()
