"""
Apply migration 002_add_user_roles.sql
"""

import psycopg2

DATABASE_URL = "postgresql://postgres:rrQVBIrrzIFcRJlZCfjyrqYCmKSDfiKk@gondola.proxy.rlwy.net:15018/railway"

def apply_migration():
    try:
        print("\nApplying migration: 002_add_user_roles.sql")
        print("=" * 70)

        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        # Read SQL file
        with open('backend/migrations/002_add_user_roles.sql', 'r', encoding='utf-8') as f:
            sql = f.read()

        # Execute migration
        cursor.execute(sql)
        conn.commit()

        print("\nMigration applied successfully!")
        print("\nVerifying results:")

        # Check if role column exists
        cursor.execute("""
            SELECT column_name, data_type, column_default
            FROM information_schema.columns
            WHERE table_name = 'users' AND column_name = 'role'
        """)

        role_col = cursor.fetchone()
        if role_col:
            print(f"   [OK] Column 'role' added: {role_col[1]} DEFAULT {role_col[2]}")

        # Check admin user
        cursor.execute("""
            SELECT email, role
            FROM users
            WHERE role = 'admin'
        """)

        admins = cursor.fetchall()
        if admins:
            print(f"\nAdministrators ({len(admins)}):")
            for email, role in admins:
                print(f"   - {email} ({role})")
        else:
            print("\n[WARNING] No administrators found")

        # Count users by role
        cursor.execute("""
            SELECT role, COUNT(*)
            FROM users
            GROUP BY role
        """)

        stats = cursor.fetchall()
        print(f"\nStatistics:")
        for role, count in stats:
            print(f"   {role}: {count} users")

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
