"""
Script to view all users and their info
"""

import psycopg2

# DATABASE_URL из Railway
DATABASE_URL = "postgresql://postgres:rrQVBIrrzIFcRJlZCfjyrqYCmKSDfiKk@gondola.proxy.rlwy.net:15018/railway"

def view_all_users():
    """View all registered users"""
    try:
        print("\n👥 СПИСОК ВСЕХ ПОЛЬЗОВАТЕЛЕЙ")
        print("=" * 100)

        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        # Get all users
        cursor.execute("""
            SELECT id, email, full_name, is_premium, provider, created_at
            FROM users
            ORDER BY created_at DESC
        """)

        users = cursor.fetchall()

        if not users:
            print("\n❌ Пользователей не найдено")
            return

        print(f"\nВсего пользователей: {len(users)}\n")

        for i, (user_id, email, full_name, is_premium, provider, created_at) in enumerate(users, 1):
            premium_badge = "✨ Premium" if is_premium else "Free"
            print(f"{i}. ID: {user_id}")
            print(f"   📧 Email: {email}")
            print(f"   👤 Имя: {full_name}")
            print(f"   💎 Статус: {premium_badge}")
            print(f"   🔐 Способ входа: {provider}")
            print(f"   📅 Регистрация: {created_at}")

            # Get generation count for user
            cursor.execute("""
                SELECT COUNT(*) FROM generations WHERE user_id = %s
            """, (user_id,))
            gen_count = cursor.fetchone()[0]
            print(f"   🎨 Всего генераций: {gen_count}")

            if i < len(users):
                print()

        print("\n" + "=" * 100)
        print("\nℹ️  Пароли хранятся в хешированном виде и не могут быть просмотрены.")
        print("   Используйте reset_password.py для сброса пароля пользователя.")
        print()

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        view_all_users()
        input("\n\nНажмите Enter для выхода...")
    except KeyboardInterrupt:
        print("\n\n⚠️  Прервано пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        input("\n\nНажмите Enter для выхода...")
