"""
Script to apply migration 005: Create admin_sessions table
"""

import sys
import psycopg2

# Import centralized database configuration
try:
    from backend.db_config import parse_database_url
except ImportError:
    print("Error: Cannot import backend.db_config")
    print("Make sure you're running from the project root directory")
    sys.exit(1)


def apply_migration():
    try:
        print("\nApplying migration: 005_create_admin_sessions.sql")
        print("=" * 70)

        conn = psycopg2.connect(**parse_database_url())
        cursor = conn.cursor()

        # Read and execute migration
        with open('backend/migrations/005_create_admin_sessions.sql', 'r', encoding='utf-8') as f:
            sql = f.read()

        cursor.execute(sql)
        conn.commit()

        print("\nMigration applied successfully!")
        print("\nVerifying results:")

        # Check table exists
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = 'admin_sessions'
        """)
        table = cursor.fetchone()
        if table:
            print(f"   [OK] Table 'admin_sessions' created")
        else:
            print("   [ERROR] Table 'admin_sessions' not found!")
            return False

        # Check columns
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'admin_sessions'
            ORDER BY ordinal_position
        """)
        columns = cursor.fetchall()
        print(f"\n   [OK] {len(columns)} columns:")
        for col in columns:
            nullable = "NULL" if col[2] == "YES" else "NOT NULL"
            print(f"      - {col[0]} ({col[1]}) {nullable}")

        # Check indexes
        cursor.execute("""
            SELECT indexname
            FROM pg_indexes
            WHERE tablename = 'admin_sessions'
            ORDER BY indexname
        """)
        indexes = cursor.fetchall()
        print(f"\n   [OK] {len(indexes)} indexes:")
        for idx in indexes:
            print(f"      - {idx[0]}")

        # Check foreign key constraint
        cursor.execute("""
            SELECT conname, contype
            FROM pg_constraint
            WHERE conrelid = 'admin_sessions'::regclass
            AND contype = 'f'
        """)
        fk = cursor.fetchone()
        if fk:
            print(f"\n   [OK] Foreign key constraint: {fk[0]}")

        print("\n" + "=" * 70)
        print("\n[SUCCESS] Admin sessions table created successfully!")

        cursor.close()
        conn.close()

        return True

    except ValueError as exc:
        print(f"\n❌ Configuration error: {exc}")
        print("Make sure DATABASE_URL is set in your environment or .env file")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR]: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    success = apply_migration()
    sys.exit(0 if success else 1)

