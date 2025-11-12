# PostgreSQL Setup for Feedback Storage

## 🎯 Зачем нужна база данных?

**Проблема:** Файлы отзывов хранятся в папке `feedback/` которая удаляется при каждом деплое на Railway (ephemeral filesystem).

**Решение:** PostgreSQL - постоянное хранилище которое НЕ удаляется при редеплоях.

## ✅ Преимущества PostgreSQL

- ✅ **Отзывы никогда не теряются** - даже после редеплоя
- ✅ **Отслеживание статуса Telegram** - можно увидеть какие отзывы не отправились
- ✅ **Возможность retry** - повторная отправка неудачных уведомлений
- ✅ **Аналитика** - средняя оценка, количество отзывов за период
- ✅ **Бесплатно** - Railway предоставляет PostgreSQL бесплатно (до 1GB)

---

## 📋 Пошаговая настройка

### Шаг 1: Создать PostgreSQL базу данных в Railway

1. Откройте Railway Dashboard: https://railway.app/dashboard
2. Откройте ваш проект `virtual-tryon-app`
3. Нажмите кнопку **"+ New"** (справа вверху)
4. Выберите **"Database"** → **"Add PostgreSQL"**
5. Railway создаст новую базу данных

### Шаг 2: Подключить базу данных к сервису

1. Кликните на карточку PostgreSQL которую только что создали
2. Перейдите на вкладку **"Connect"** или **"Variables"**
3. Скопируйте переменную **DATABASE_URL** (она уже готова)
4. Вернитесь к вашему основному сервису (web/backend)
5. Перейдите в **Settings** → **Reference Variables**
6. Найдите базу данных в списке и нажмите **"Add reference"**
7. Railway автоматически добавит переменную `DATABASE_URL`

**Альтернативный способ:**
- Переменная `DATABASE_URL` может быть добавлена автоматически если вы свяжете (link) базу данных с сервисом через Railway UI

### Шаг 3: Redeploy сервиса

1. Railway автоматически начнёт Redeploy после добавления переменной
2. Если нет - вручную нажмите **"Deploy"** или **"Redeploy"**
3. Дождитесь завершения деплоя (2-5 минут)

### Шаг 4: Проверить подключение

1. Откройте **Deploy Logs** последнего деплоя
2. Найдите строки:
   ```
   🔗 Connecting to PostgreSQL database...
   ================================================================================
   ✅ Database connection successful!
   ✅ Database tables initialized
   ✅ PostgreSQL is ready for feedback storage
   ```

3. Если видите эти строки - **всё работает!** ✅

4. Если видите ошибку - проверьте что `DATABASE_URL` добавлена в Variables

---

## 🧪 Тестирование

### Тест 1: Отправить отзыв

1. Откройте ваш сайт
2. Нажмите кнопку **"🧪 Тест формы отзыва"**
3. Заполните форму и отправьте
4. Проверьте логи Railway - должны увидеть:
   ```
   [FEEDBACK] 💾 Saving to PostgreSQL database...
   [DATABASE] ✅ Saved feedback to PostgreSQL: ID=1, rating=5
   [TELEGRAM] ✅ SUCCESS on attempt 1: Message ID 123
   [DATABASE] ✅ Updated telegram status for feedback 1: sent=True
   ```

### Тест 2: Просмотреть отзывы из базы данных

Откройте в браузере:
```
https://ваш-домен.railway.app/api/feedback/list
```

Должен вернуть JSON:
```json
{
  "success": true,
  "source": "database",
  "count": 1,
  "feedbacks": [
    {
      "id": 1,
      "rating": 5,
      "comment": "Отлично работает!",
      "timestamp": "2025-01-11T20:00:00",
      "telegram_sent": true,
      "telegram_error": null
    }
  ]
}
```

---

## 🔍 Просмотр данных в Railway

### Способ 1: Railway Web UI (Data tab)

1. Railway Dashboard → PostgreSQL → вкладка **"Data"**
2. Выберите таблицу `feedback`
3. Просмотр всех записей в таблице

### Способ 2: psql (терминал)

1. Railway Dashboard → PostgreSQL → вкладка **"Connect"**
2. Скопируйте команду подключения:
   ```bash
   psql postgresql://postgres:password@hostname:port/database
   ```
3. Выполните в терминале
4. Запросы SQL:
   ```sql
   -- Все отзывы
   SELECT * FROM feedback ORDER BY timestamp DESC;

   -- Отзывы без Telegram
   SELECT * FROM feedback WHERE telegram_sent = false;

   -- Средняя оценка
   SELECT AVG(rating) as average_rating FROM feedback;

   -- Количество по оценкам
   SELECT rating, COUNT(*) as count FROM feedback GROUP BY rating;
   ```

---

## 🛠️ Устранение проблем

### Проблема: "DATABASE_URL not found in environment"

**Причина:** Переменная не добавлена или не применилась

**Решение:**
1. Проверьте что PostgreSQL база данных создана
2. Проверьте что сервис связан (linked) с базой данных
3. Проверьте Variables - должна быть `DATABASE_URL`
4. Сделайте Redeploy

### Проблема: "Database connection failed"

**Причина:** Неверная строка подключения или база данных недоступна

**Решение:**
1. Проверьте что PostgreSQL сервис запущен (статус "Active")
2. Проверьте значение `DATABASE_URL` - должно начинаться с `postgresql://`
3. Railway автоматически исправляет `postgres://` на `postgresql://`
4. Проверьте логи PostgreSQL сервиса

### Проблема: Отзывы сохраняются только в файлы

**Причина:** База данных недоступна, приложение использует fallback

**Решение:**
1. Проверьте логи при старте - должно быть "✅ Database connection successful"
2. Если видите "Database not available" - проверьте DATABASE_URL
3. Если видите "Database connection failed" - проверьте логи PostgreSQL

---

## 📊 Структура таблицы

```sql
CREATE TABLE feedback (
    id SERIAL PRIMARY KEY,
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    timestamp TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    session_id VARCHAR(100),
    ip_address VARCHAR(50),
    telegram_sent BOOLEAN NOT NULL DEFAULT FALSE,
    telegram_error TEXT
);
```

**Поля:**
- `id` - уникальный идентификатор (автоинкремент)
- `rating` - оценка от 1 до 5
- `comment` - текстовый комментарий (необязательно)
- `timestamp` - дата и время отзыва
- `session_id` - ID сессии пользователя (для отслеживания)
- `ip_address` - IP адрес пользователя
- `telegram_sent` - был ли отправлен в Telegram (`true`/`false`)
- `telegram_error` - ошибка отправки в Telegram (если была)

---

## 🔄 Миграция существующих отзывов из файлов

Если у вас уже есть отзывы в файлах, можно их импортировать в базу данных:

```python
# Создайте скрипт migrate_feedback.py
import os
import json
from database import save_feedback_to_db

feedback_folder = 'feedback'
for filename in os.listdir(feedback_folder):
    if filename.endswith('.json'):
        filepath = os.path.join(feedback_folder, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            save_feedback_to_db(
                rating=data['rating'],
                comment=data.get('comment', ''),
                timestamp=data['timestamp'],
                session_id=data.get('session_id'),
                ip_address=data.get('ip_address'),
                telegram_sent=True  # Assume already sent
            )
            print(f"Imported: {filename}")
```

Запустить:
```bash
cd backend
python migrate_feedback.py
```

---

## 💡 Дополнительные возможности

### Автоматическая повторная отправка в Telegram

Можно создать cron job который периодически проверяет неотправленные отзывы и пытается отправить снова:

```python
from database import get_unsent_telegram_feedbacks

# Получить все неотправленные
unsent = get_unsent_telegram_feedbacks()

for feedback in unsent:
    # Попробовать отправить снова
    success, error = send_telegram_notification_with_retry(...)
    if success:
        mark_telegram_sent(feedback.id, success=True)
```

### Экспорт данных

```python
from database import SessionLocal, Feedback
import pandas as pd

db = SessionLocal()
feedbacks = db.query(Feedback).all()
df = pd.DataFrame([fb.to_dict() for fb in feedbacks])
df.to_csv('feedbacks_export.csv', index=False)
```

---

## ✅ Готово!

После выполнения всех шагов:
- ✅ Отзывы сохраняются в PostgreSQL (постоянно)
- ✅ Fallback на файлы если БД недоступна
- ✅ Отслеживание статуса Telegram отправки
- ✅ Возможность просмотра отзывов через API
- ✅ Никогда не потеряете отзывы при редеплое

---

## 🆘 Нужна помощь?

- Документация Railway PostgreSQL: https://docs.railway.app/databases/postgresql
- SQLAlchemy документация: https://docs.sqlalchemy.org/
- Проверьте логи в Railway Dashboard → Deployments → View Logs
