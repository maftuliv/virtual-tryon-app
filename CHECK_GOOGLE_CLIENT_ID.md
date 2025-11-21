# 🔍 Проверка Client ID в Google Cloud Console

## ❌ Проблема: Error 401: invalid_client

Google возвращает ошибку `The OAuth client was not found` для Client ID:
```
558131336096-bpdufj7dj1240r45k3feulft6tvfudpi.apps.googleusercontent.com
```

---

## ✅ Что проверить в Google Cloud Console

### Шаг 1: Откройте Google Cloud Console

1. Перейдите: https://console.cloud.google.com/
2. **ВАЖНО:** Убедитесь, что выбран правильный проект: **Tap to look Virtual Try-On**

### Шаг 2: Проверьте OAuth Client

1. Перейдите: **APIs & Services** → **Credentials**
2. Найдите OAuth 2.0 Client ID: `558131336096-bpdufj7dj1240r45k3feulft6tvfudpi.apps.googleusercontent.com`

**Проверьте:**

#### ✅ Client ID существует?
- Если **НЕ НАЙДЕН** → Client ID был удален или находится в другом проекте
- **Решение:** Создайте новый OAuth Client ID (см. ниже)

#### ✅ Client ID активен?
- Проверьте статус Client ID
- Если деактивирован → активируйте его

#### ✅ Правильный проект?
- Убедитесь, что Client ID находится в проекте **Tap to look Virtual Try-On**
- Если Client ID в другом проекте → либо переключитесь на правильный проект, либо создайте новый

#### ✅ Redirect URI добавлен?
- В настройках OAuth Client проверьте **Authorized redirect URIs**
- Должен быть точно такой URI:
  ```
  https://testbackendvirtualtryon-production.up.railway.app/api/auth/google/callback
  ```

---

## 🔧 Если Client ID не найден: Создайте новый

### Шаг 1: Создайте OAuth Client ID

1. В Google Cloud Console: **APIs & Services** → **Credentials**
2. Нажмите **+ CREATE CREDENTIALS** → **OAuth client ID**

**Если видите предупреждение о OAuth consent screen:**
- Нажмите **CONFIGURE CONSENT SCREEN**
- Выберите **External**
- Заполните обязательные поля и сохраните

### Шаг 2: Настройте OAuth Client

1. **Application type:** `Web application`
2. **Name:** `Virtual Try-On Test Environment`
3. **Authorized JavaScript origins:**
   ```
   https://testbackendvirtualtryon-production.up.railway.app
   ```
4. **Authorized redirect URIs:**
   ```
   https://testbackendvirtualtryon-production.up.railway.app/api/auth/google/callback
   ```
5. Нажмите **CREATE**

### Шаг 3: Скопируйте новые credentials

После создания вы увидите:
- **Your Client ID:** `123456789-abc...xyz.apps.googleusercontent.com`
- **Your Client Secret:** `GOCSPX-...`

**ВАЖНО:** Скопируйте оба значения!

### Шаг 4: Обновите переменные в Railway

1. Railway Dashboard → `test_backend_virtual_tryon` → Variables
2. Обновите:
   - `GOOGLE_CLIENT_ID` = новый Client ID
   - `GOOGLE_CLIENT_SECRET` = новый Client Secret
3. Railway автоматически перезапустит сервис

---

## 🔍 Альтернативная проверка

### Проверка через Google OAuth Playground

1. Откройте: https://developers.google.com/oauthplayground/
2. Нажмите на иконку настроек (⚙️) в правом верхнем углу
3. Введите ваш Client ID и Client Secret
4. Попробуйте получить authorization code

**Если это работает:**
- Значит проблема в конфигурации приложения, а не в Google

**Если не работает:**
- Значит проблема в Client ID/Secret - создайте новые

---

## 📋 Чеклист

- [ ] Открыл Google Cloud Console
- [ ] Проверил правильный проект (Tap to look Virtual Try-On)
- [ ] Проверил существование Client ID `558131336096-...`
- [ ] Проверил статус Client ID (активен)
- [ ] Проверил Redirect URI в Console
- [ ] Если Client ID не найден - создал новый
- [ ] Обновил переменные в Railway (если создал новый)
- [ ] Подождал 1-2 минуты после изменений
- [ ] Протестировал вход через Google снова

---

*Инструкция для проверки и исправления ошибки 401: invalid_client*



