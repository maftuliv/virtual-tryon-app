# 🗄️ Применение миграции 005 через Railway Dashboard

## Быстрый способ применения миграции

### Шаг 1: Откройте Railway Dashboard

1. Перейдите на: https://railway.app/dashboard
2. Войдите в ваш аккаунт
3. Выберите проект с вашим приложением

### Шаг 2: Откройте базу данных PostgreSQL

1. В списке сервисов найдите **PostgreSQL** базу данных
2. Кликните на неё
3. Перейдите на вкладку **"Query"** (или "Data" → "Query")

### Шаг 3: Выполните SQL миграцию

Скопируйте и вставьте следующий SQL код в редактор запросов:

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

4. Нажмите кнопку **"Run"** или **"Execute"**

### Шаг 4: Проверка результата

Выполните запрос для проверки:

```sql
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'admin_sessions'
ORDER BY ordinal_position;
```

**Ожидаемый результат:**
- Таблица `admin_sessions` должна существовать
- 6 столбцов: session_id, user_id, ip_address, user_agent, created_at, expires_at
- 2 индекса: idx_admin_sessions_user_id, idx_admin_sessions_expires_at

### Готово! ✅

После применения миграции:
- Админ-сессии будут работать автоматически
- Администраторы смогут входить в админ-панель
- Серверные сессии будут храниться в базе данных

---

## Альтернативный способ: через Railway Service Shell

Если у вас есть доступ к shell контейнера:

1. В Railway Dashboard → ваш сервис → "Deployments"
2. Выберите последний deployment → "Connect" → "Shell"
3. Выполните:
   ```bash
   python apply_migration_005.py
   ```

---

## Проверка после применения

После применения миграции проверьте:

1. **Логин администратора:**
   - Войдите как администратор через `/api/auth/login` или Google OAuth
   - В cookies должен появиться `admin_session`
   
2. **Доступ к админ-панели:**
   - Откройте `/admin`
   - Должна открыться админ-панель без ошибок

3. **API эндпоинты:**
   - `GET /api/auth/admin/session` должен вернуть данные администратора
   - `GET /api/admin/summary` должен работать с админ-сессией

---

**Если возникли проблемы:** Проверьте логи в Railway Dashboard → Deployments → View Logs

