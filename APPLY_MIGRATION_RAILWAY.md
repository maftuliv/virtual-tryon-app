# 🗄️ Применение миграции на Railway

## 📋 Способы применения миграции `005_create_admin_sessions.sql`

Есть **3 способа** применить миграцию на Railway. Выберите наиболее удобный для вас.

---

## ✅ Способ 1: Через Railway CLI (Рекомендуется)

### Шаг 1: Установить Railway CLI (если ещё не установлен)

**Windows (PowerShell):**
```powershell
# Скачать и установить через winget
winget install --id Railway.Railway

# Или через npm (если установлен Node.js)
npm i -g @railway/cli
```

**Проверка установки:**
```bash
railway --version
```

### Шаг 2: Авторизоваться в Railway

```bash
railway login
```

Откроется браузер для авторизации через GitHub.

### Шаг 3: Подключиться к проекту

```bash
# Перейти в директорию проекта
cd C:\Users\ivmaf\virtual-tryon-app

# Связать проект с Railway
railway link
```

Выберите ваш проект `virtual-tryon-app` из списка.

### Шаг 4: Применить миграцию

```bash
# Запустить скрипт миграции в окружении Railway
railway run python apply_migration_005.py
```

Вы должны увидеть:
```
Applying migration: 005_create_admin_sessions.sql
======================================================================
Migration applied successfully!

Verifying results:
   [OK] Table 'admin_sessions' created
   [OK] 6 columns: ...
   [OK] 3 indexes: ...
   [OK] Foreign key constraint: admin_sessions_user_id_fkey

[SUCCESS] Admin sessions table created successfully!
```

---

## ✅ Способ 2: Через Railway Web UI (Data Tab)

### Шаг 1: Открыть Railway Dashboard

1. Перейдите на https://railway.app/dashboard
2. Откройте ваш проект `virtual-tryon-app`
3. Кликните на карточку **PostgreSQL** (база данных)

### Шаг 2: Открыть вкладку "Data"

1. В карточке PostgreSQL нажмите на вкладку **"Data"**
2. Нажмите кнопку **"Query"** или **"New Query"**

### Шаг 3: Выполнить SQL миграцию

Скопируйте и вставьте весь SQL из файла `backend/migrations/005_create_admin_sessions.sql`:

```sql
-- Migration: Create admin_sessions table for server-side admin sessions

CREATE TABLE IF NOT EXISTS admin_sessions (
    session_id VARCHAR(128) PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    ip_address TEXT,
    user_agent TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_admin_sessions_user_id ON admin_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_admin_sessions_expires_at ON admin_sessions(expires_at);
```

3. Нажмите **"Run"** или **"Execute"**

### Шаг 4: Проверить результат

Выполните проверочный запрос:
```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_name = 'admin_sessions';
```

Должна вернуться строка с `admin_sessions`.

---

## ✅ Способ 3: Через psql (Терминал)

### Шаг 1: Получить строку подключения

1. Railway Dashboard → PostgreSQL → вкладка **"Connect"**
2. Скопируйте строку подключения (Connection String):
   ```
   postgresql://postgres:password@hostname:port/database
   ```

### Шаг 2: Подключиться через psql

**Windows (если установлен PostgreSQL):**
```powershell
# Используйте скопированную строку подключения
psql "postgresql://postgres:password@hostname:port/database"
```

**Или через Railway CLI:**
```bash
railway connect postgres
```

### Шаг 3: Выполнить миграцию

```sql
-- Скопируйте SQL из backend/migrations/005_create_admin_sessions.sql
CREATE TABLE IF NOT EXISTS admin_sessions (
    session_id VARCHAR(128) PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    ip_address TEXT,
    user_agent TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_admin_sessions_user_id ON admin_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_admin_sessions_expires_at ON admin_sessions(expires_at);
```

### Шаг 4: Проверить

```sql
-- Проверить таблицу
\dt admin_sessions

-- Проверить структуру
\d admin_sessions

-- Выйти
\q
```

---

## 🔍 Проверка успешного применения

После применения миграции любым способом, проверьте:

### 1. Через Railway Web UI

1. Railway Dashboard → PostgreSQL → **"Data"** → таблица `admin_sessions`
2. Должна отображаться таблица с колонками:
   - `session_id` (VARCHAR, PRIMARY KEY)
   - `user_id` (INTEGER, FOREIGN KEY)
   - `ip_address` (TEXT)
   - `user_agent` (TEXT)
   - `created_at` (TIMESTAMPTZ)
   - `expires_at` (TIMESTAMPTZ)

### 2. Через SQL запрос

```sql
-- Проверить таблицу
SELECT COUNT(*) FROM admin_sessions;

-- Проверить индексы
SELECT indexname 
FROM pg_indexes 
WHERE tablename = 'admin_sessions';

-- Должно вернуть:
-- admin_sessions_pkey
-- idx_admin_sessions_user_id
-- idx_admin_sessions_expires_at
```

### 3. Через работу админ-панели

1. Войдите как администратор на сайте
2. Перейдите на `/admin`
3. Если админ-панель открывается без ошибок — миграция применена успешно ✅

---

## ⚠️ Важные замечания

1. **Миграция безопасна**: Используется `CREATE TABLE IF NOT EXISTS`, поэтому повторное выполнение не вызовет ошибок.

2. **Внешний ключ**: Таблица `admin_sessions` ссылается на `users(id)`, поэтому убедитесь, что таблица `users` уже существует.

3. **Индексы**: Индексы создаются автоматически для оптимизации запросов по `user_id` и `expires_at`.

4. **Очистка**: Старые сессии автоматически удаляются при проверке (через `AdminSessionService.cleanup_expired()`).

---

## 🆘 Проблемы и решения

### Ошибка: "relation 'users' does not exist"

**Причина:** Таблица `users` ещё не создана.

**Решение:** Сначала примените миграцию `001_create_auth_tables.sql`:
```bash
railway run python apply_migration.py
```

### Ошибка: "permission denied"

**Причина:** Недостаточно прав для создания таблиц.

**Решение:** Убедитесь, что используете правильные учётные данные из Railway (не локальные).

### Ошибка: "table already exists"

**Причина:** Миграция уже применена ранее.

**Решение:** Это нормально! `CREATE TABLE IF NOT EXISTS` предотвращает ошибку. Можно игнорировать.

---

## 📝 После применения миграции

После успешного применения миграции:

1. ✅ Админ-панель будет работать через серверные сессии
2. ✅ Сессии будут храниться в базе данных (надёжнее, чем cookies)
3. ✅ Автоматическая очистка истёкших сессий
4. ✅ Лучшая безопасность для админ-доступа

**Готово!** 🎉

