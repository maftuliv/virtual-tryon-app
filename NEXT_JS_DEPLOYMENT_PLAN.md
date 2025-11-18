# Next.js Deployment Plan - Railway Setup

## ПРОБЛЕМА

**Почему дизайн не обновляется:**
- Railway деплоит ТОЛЬКО бэкенд (Python Flask)
- Бэкенд статически серверит старую папку `/frontend` через `send_from_directory`
- Новый Next.js проект в `/app-next` не деплоится - он только в Git

## РЕШЕНИЕ

Создать **отдельный сервис на Railway** для Next.js frontend.

---

## ШАГ 1: Создать новый Railway Service для Next.js

### 1.1 В Railway Dashboard:

1. Открыть проект: https://railway.app/project/{your-project-id}
2. Нажать "+ New Service"
3. Выбрать "GitHub Repo"
4. Выбрать репозиторий: `maftuliv/virtual-tryon-app`
5. Branch: `staging`

### 1.2 Настроить Root Directory:

**КРИТИЧЕСКИ ВАЖНО:**
```
Settings → Build → Root Directory: app-next
```

Это говорит Railway билдить именно папку `app-next/`, а не корень репозитория.

### 1.3 Настроить Environment Variables:

```bash
NEXT_PUBLIC_API_URL=https://your-backend-service.up.railway.app
```

**Где взять Backend URL:**
- Открыть существующий Backend service в Railway
- Settings → Networking → Public Domain
- Скопировать URL (например: `https://virtual-tryon-backend-production.up.railway.app`)

### 1.4 Verify Build Settings:

Railway автоматически определит Next.js и использует:
- Build Command: `npm run build`
- Start Command: `npm start`

Если нет, установить вручную:
```
Settings → Build → Build Command: npm run build
Settings → Deploy → Start Command: npm start
```

---

## ШАГ 2: Обновить Backend CORS

Бэкенд должен разрешить запросы от нового фронтенда.

### 2.1 В Railway Backend Service:

Добавить Environment Variable:
```bash
FRONTEND_URL=https://your-frontend-service.up.railway.app
```

### 2.2 Обновить backend/app_factory.py (если нужно):

```python
from flask_cors import CORS

# В create_app():
CORS(app, origins=[
    os.getenv('FRONTEND_URL'),  # Production Next.js
    'http://localhost:3000',     # Local development
], supports_credentials=True)
```

---

## ШАГ 3: Настроить Custom Domain (опционально)

### 3.1 Frontend Domain:
```
Settings → Networking → Custom Domain
Example: app.taptolook.com
```

### 3.2 Backend Domain:
```
Settings → Networking → Custom Domain
Example: api.taptolook.com
```

### 3.3 Обновить DNS записи:

В Cloudflare/ваш DNS провайдер:
```
Type: CNAME
Name: app
Value: {railway-frontend-domain}.up.railway.app

Type: CNAME
Name: api
Value: {railway-backend-domain}.up.railway.app
```

---

## ШАГ 4: Проверка деплоя

### 4.1 Check Frontend Build Logs:

В Railway Frontend Service:
```
Deployments → Latest → Build Logs
```

Должно быть:
```
✓ Creating optimized production build
✓ Compiled successfully
✓ Linting and checking validity of types
✓ Collecting page data
✓ Generating static pages
✓ Finalizing page optimization
```

### 4.2 Check Frontend Runtime:

```
Deployments → Latest → Deploy Logs
```

Должно быть:
```
> next start
ready - started server on 0.0.0.0:3000
```

### 4.3 Открыть сайт:

```
https://your-frontend-service.up.railway.app
```

Должен показать новый дизайн из `app-next/`.

---

## ШАГ 5: Переключить Staging/Production

### 5.1 Staging Environment:

1. Создать новый Environment в Railway: `Staging`
2. Создать Frontend Service в Staging
3. Root Directory: `app-next`
4. Branch: `staging`

### 5.2 Production Environment:

1. Создать Frontend Service в Production
2. Root Directory: `app-next`
3. Branch: `main`

---

## ИТОГОВАЯ АРХИТЕКТУРА

### Старая архитектура (❌ проблема):
```
Railway Service: Backend (Python)
  ├── Serves: /frontend (старый HTML/CSS/JS)
  └── Problem: app-next не деплоится
```

### Новая архитектура (✅ решение):
```
Railway Project
  ├── Backend Service (Python Flask)
  │     ├── Branch: staging/main
  │     ├── Port: 5000
  │     └── Serves: API only
  │
  └── Frontend Service (Next.js)
        ├── Root Directory: app-next/
        ├── Branch: staging/main
        ├── Port: 3000
        └── Serves: Static + SSR pages
```

---

## TROUBLESHOOTING

### Problem: "Module not found: Can't resolve 'react'"

**Solution:**
```bash
# В Settings → Deploy:
Install Command: npm ci
```

### Problem: "Error: listen EADDRINUSE: address already in use :::3000"

**Solution:** Railway автоматически назначает PORT. Проверить, что используется `process.env.PORT`:

```javascript
// next.config.js
module.exports = {
  // ...
}
```

Next.js автоматически читает `process.env.PORT`.

### Problem: API requests fail with CORS

**Solution:** Проверить:
1. Backend CORS настроен на фронтенд URL
2. Frontend использует правильный `NEXT_PUBLIC_API_URL`
3. Credentials включены в запросах (withCredentials: true)

### Problem: Build succeeds but page shows 404

**Solution:** Проверить Root Directory в Settings → Build.

---

## ЧЕКЛИСТ ДЕПЛОЯ

- [ ] Создан Frontend Service в Railway
- [ ] Root Directory установлен: `app-next`
- [ ] Branch выбран: `staging`
- [ ] Environment Variable: `NEXT_PUBLIC_API_URL`
- [ ] Backend CORS обновлён
- [ ] Build успешный (check logs)
- [ ] Deploy успешный (check logs)
- [ ] Сайт открывается
- [ ] Новый дизайн виден
- [ ] API запросы работают
- [ ] Авторизация работает
- [ ] Генерация работает

---

## СЛЕДУЮЩИЕ ШАГИ

1. ✅ Закоммитить изменения в staging
2. ✅ Создать Frontend Service в Railway
3. ✅ Настроить Root Directory
4. ✅ Добавить Environment Variables
5. ✅ Проверить деплой
6. ✅ Протестировать функционал
7. ✅ Повторить для production

---

## КОНТАКТЫ И ПОМОЩЬ

**Railway Documentation:**
- https://docs.railway.app/guides/deployments
- https://docs.railway.app/guides/services

**Next.js Deployment:**
- https://nextjs.org/docs/deployment

**Если нужна помощь:**
- Railway Discord: https://discord.gg/railway
- Railway Support: support@railway.app
