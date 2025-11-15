"""
Script to check and manage user's daily limit status
"""

import sys
import psycopg2
from datetime import datetime

# Import centralized database configuration
try:
    from backend.db_config import parse_database_url
except ImportError:
    print("Error: Cannot import backend.db_config")
    print("Make sure you're running from the project root directory")
    sys.exit(1)


def check_user_limit(email):
    """Check user's limit and generation history"""
    conn = None
    cursor = None

    try:
        print(f"\n🔍 Проверка лимитов для пользователя: {email}")
        print("=" * 70)

        conn = psycopg2.connect(**parse_database_url())
        cursor = conn.cursor()

        # Get user info
        cursor.execute("""
            SELECT id, email, full_name, is_premium, created_at
            FROM users
            WHERE email = %s
        """, (email,))

        user = cursor.fetchone()
        if not user:
            print(f"❌ Пользователь с email {email} не найден")
            return

        user_id, user_email, full_name, is_premium, created_at = user

        print(f"\n👤 ИНФОРМАЦИЯ О ПОЛЬЗОВАТЕЛЕ")
        print(f"   Имя: {full_name}")
        print(f"   Email: {user_email}")
        print(f"   ID: {user_id}")
        print(f"   Premium: {'✅ Да' if is_premium else '❌ Нет'}")
        print(f"   Дата регистрации: {created_at}")
        print("=" * 70)

        # Get daily limit info for TODAY
        cursor.execute("""
            SELECT generations_count, date, created_at, updated_at
            FROM daily_limits
            WHERE user_id = %s AND date = CURRENT_DATE
        """, (user_id,))

        limit_info = cursor.fetchone()

        print(f"\n📊 ЛИМИТЫ НА СЕГОДНЯ")
        if limit_info:
            used_count, limit_date, created_at_limit, updated_at = limit_info
            remaining = 3 - used_count

            print(f"   Осталось генераций: {remaining}/3")
            print(f"   Использовано: {used_count}")
            print(f"   Дата лимита: {limit_date}")
            print(f"   Создан: {created_at_limit}")
            print(f"   Обновлён: {updated_at}")

            # Visual progress bar (показывает сколько осталось)
            bar_remaining = "█" * remaining
            bar_used = "░" * used_count
            print(f"   [{bar_remaining}{bar_used}] {remaining}/3 осталось")
        else:
            print(f"   ✅ Лимит не инициализирован")
            print(f"   Осталось генераций: 3/3")
            print(f"   Использовано: 0")
            print(f"   [███] 3/3 осталось")

        print("=" * 70)

        # Get generation history for today
        cursor.execute("""
            SELECT id, created_at, category, status, result_image_url
            FROM generations
            WHERE user_id = %s
            AND DATE(created_at) = CURRENT_DATE
            ORDER BY created_at DESC
        """, (user_id,))

        generations = cursor.fetchall()

        print(f"\n🎨 ИСТОРИЯ ГЕНЕРАЦИЙ СЕГОДНЯ")
        if generations:
            print(f"   Всего генераций: {len(generations)}")
            print()
            for i, (gen_id, gen_time, category, status, result_url) in enumerate(generations, 1):
                status_icon = "✅" if status == "completed" else "❌"
                print(f"   {i}. {status_icon} ID: {gen_id}")
                print(f"      Время: {gen_time}")
                print(f"      Категория: {category}")
                print(f"      Статус: {status}")
                if i < len(generations):
                    print()
        else:
            print(f"   ✅ Генераций сегодня не найдено (0)")

        print("=" * 70)

        # Offer to reset limit
        print(f"\n🔄 УПРАВЛЕНИЕ ЛИМИТАМИ")
        print(f"   Выберите действие:")
        print(f"   1. Сбросить лимит на 3/3 (восстановить все генерации)")
        print(f"   2. Удалить запись лимита (как новый пользователь)")
        print(f"   3. Ничего не делать")

        choice = input(f"\nВведите номер (1-3): ").strip()

        if choice == '1':
            # Reset to 0 used (update or insert)
            cursor.execute("""
                INSERT INTO daily_limits (user_id, date, generations_count, created_at, updated_at)
                VALUES (%s, CURRENT_DATE, 0, NOW(), NOW())
                ON CONFLICT (user_id, date)
                DO UPDATE SET
                    generations_count = 0,
                    updated_at = NOW()
            """, (user_id,))
            conn.commit()
            print("   ✅ Лимит сброшен! Теперь: 3/3 (доступны все 3 генерации)")

        elif choice == '2':
            # Delete limit record entirely
            cursor.execute("""
                DELETE FROM daily_limits
                WHERE user_id = %s AND date = CURRENT_DATE
            """, (user_id,))
            conn.commit()
            rows_deleted = cursor.rowcount
            if rows_deleted > 0:
                print("   ✅ Запись лимита удалена! Пользователь как новый (3/3)")
            else:
                print("   ℹ️  Записи лимита не было, ничего не удалено")

        elif choice == '3':
            print("   ℹ️  Никаких изменений не внесено")
        else:
            print("   ⚠️  Неверный выбор, пропускаем")

        print("=" * 70)
        print()

    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    try:
        check_user_limit("maftul4d@gmail.com")
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
