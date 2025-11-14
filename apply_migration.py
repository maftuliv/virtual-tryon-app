"""
Script to apply SQL migration to Railway PostgreSQL database
"""

import psycopg2
import sys

# Замените этот URL на ваш из Railway (нажмите "show" и скопируйте)
DATABASE_URL = "postgresql://postgres:rrQVBIrrzIFcRJlZCfjyrqYCmKSDfiKk@gondola.proxy.rlwy.net:15018/railway"

def apply_migration():
    """Apply SQL migration to database"""
    try:
        print("🔌 Подключение к базе данных...")
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        print("📄 Чтение SQL файла...")
        with open('backend/migrations/001_create_auth_tables.sql', 'r', encoding='utf-8') as f:
            sql = f.read()

        print("🚀 Выполнение миграции...")
        cursor.execute(sql)
        conn.commit()

        print("✅ Миграция успешно применена!")

        # Проверка созданных таблиц
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN ('users', 'generations', 'daily_limits', 'sessions')
        """)
        tables = cursor.fetchall()

        print(f"\n📊 Созданные таблицы: {', '.join([t[0] for t in tables])}")

        cursor.close()
        conn.close()

        return True

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    success = apply_migration()
    sys.exit(0 if success else 1)
