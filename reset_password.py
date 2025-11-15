"""
Script to reset user password
"""

import sys
import psycopg2
from werkzeug.security import generate_password_hash

# Import centralized database configuration
try:
    from backend.db_config import parse_database_url
except ImportError:
    print("Error: Cannot import backend.db_config")
    print("Make sure you're running from the project root directory")
    sys.exit(1)


def reset_password(email, new_password):
    """Reset user password"""
    try:
        print(f"\n🔐 Сброс пароля для пользователя: {email}")
        print("=" * 70)

        conn = psycopg2.connect(**parse_database_url())
        cursor = conn.cursor()

        # Check if user exists
        cursor.execute("""
            SELECT id, email, full_name
            FROM users
            WHERE email = %s
        """, (email,))

        user = cursor.fetchone()
        if not user:
            print(f"❌ Пользователь с email {email} не найден")
            return

        user_id, user_email, full_name = user

        print(f"\n👤 Найден пользователь:")
        print(f"   Имя: {full_name}")
        print(f"   Email: {user_email}")
        print(f"   ID: {user_id}")
        print()

        # Generate password hash
        password_hash = generate_password_hash(new_password, method='pbkdf2:sha256')

        # Update password
        cursor.execute("""
            UPDATE users
            SET password_hash = %s
            WHERE id = %s
        """, (password_hash, user_id))

        conn.commit()

        print(f"✅ Пароль успешно изменён!")
        print(f"   Новый пароль: {new_password}")
        print(f"   Теперь можете войти с этим паролем")
        print("=" * 70)
        print()

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        print("\n" + "=" * 70)
        print("   СБРОС ПАРОЛЯ ПОЛЬЗОВАТЕЛЯ")
        print("=" * 70)

        email = input("\nВведите email пользователя: ").strip()
        new_password = input("Введите новый пароль (минимум 6 символов): ").strip()

        if len(new_password) < 6:
            print("\n❌ Пароль должен быть минимум 6 символов!")
        else:
            confirm = input(f"\n⚠️  Вы уверены что хотите сбросить пароль для {email}? (y/n): ").strip().lower()
            if confirm == 'y':
                reset_password(email, new_password)
            else:
                print("\n❌ Отменено")

        input("\n\nНажмите Enter для выхода...")

    except ValueError as exc:
        print(f"\n❌ Configuration error: {exc}")
        print("Make sure DATABASE_URL is set in your environment or .env file")
        input("\n\nНажмите Enter для выхода...")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Прервано пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        input("\n\nНажмите Enter для выхода...")
