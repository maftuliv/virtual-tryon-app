# 🔍 Результаты диагностики Google OAuth (тестовое окружение)

**Дата проверки:** Сейчас  
**Окружение:** Тестовое (staging)  
**Backend URL:** https://testbackendvirtualtryon-production.up.railway.app

---

## ✅ Результаты проверки

### 1. Endpoint `/api/auth/google/status` - ✅ РАБОТАЕТ

**Ответ:**
```json
{
  "enabled": true,
  "configured": true,
  "client_id_format_valid": true,
  "client_id_masked": "2786633510....com",
  "redirect_uri": "https://testbackendvirtualtryon-production.up.railway.app/api/auth/google/callback",
  "config_issues": []
}
```

**Вывод:** Конфигурация OAuth правильная, проблем не обнаружено.

### 2. Endpoint `/api/auth/google/login` - ✅ РАБОТАЕТ

**Ответ:**
```json
{
  "success": true,
  "authorization_url": "https://accounts.google.com/o/oauth2/auth?response_type=code&client_id=278663351028-qcrgf8j2d1lpce6kjamb4vtejq82mcg5.apps.googleusercontent.com&redirect_uri=https%3A%2F%2Ftestbackendvirtualtryon-production.up.railway.app%2Fapi%2Fauth%2Fgoogle%2Fcallback&scope=openid+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fuserinfo.email+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fuserinfo.profile&state=...&access_type=offline&include_granted_scopes=true&prompt=consent"
}
```

**Вывод:** Authorization URL генерируется правильно.

**Извлеченные параметры:**
- **Client ID:** `278663351028-qcrgf8j2d1lpce6kjamb4vtejq82mcg5.apps.googleusercontent.com`
- **Redirect URI:** `https://testbackendvirtualtryon-production.up.railway.app/api/auth/google/callback`
- **Scopes:** `openid`, `userinfo.email`, `userinfo.profile`

---

## 🔍 Следующие шаги для диагностики ошибки 401: invalid_client

### Шаг 1: Проверка Google Cloud Console

1. Откройте [Google Cloud Console](https://console.cloud.google.com/)
2. Выберите проект: **Tap to look Virtual Try-On**
3. Перейдите: **APIs & Services** → **Credentials**

**Проверьте:**

#### ✅ Client ID существует?
- Найдите OAuth 2.0 Client ID: `278663351028-qcrgf8j2d1lpce6kjamb4vtejq82mcg5.apps.googleusercontent.com`
- Если НЕ НАЙДЕН → Client ID не существует или был удален
- **Решение:** Создайте новый OAuth Client ID

#### ✅ Client ID активен?
- Проверьте статус Client ID (должен быть "Active")
- Если деактивирован → активируйте его

#### ✅ Redirect URI добавлен?
- В настройках OAuth Client проверьте **Authorized redirect URIs**
- Должен быть точно такой URI:
  ```
  https://testbackendvirtualtryon-production.up.railway.app/api/auth/google/callback
  ```
- **КРИТИЧНО:** URI должен совпадать ТОЧНО (включая https, без trailing slash)

#### ✅ Правильный проект?
- Убедитесь, что Client ID принадлежит проекту **Tap to look Virtual Try-On**
- Если Client ID в другом проекте → используйте Client ID из правильного проекта

---

### Шаг 2: Тестирование authorization URL

1. Скопируйте authorization URL из ответа выше
2. Откройте его в браузере (в режиме инкогнито)
3. Посмотрите, что происходит:

**Если видите:**
- ✅ **Consent screen (экран разрешений Google)** → Client ID правильный, проблема в другом месте
- ❌ **Error 401: invalid_client** → Client ID не существует в Google Cloud Console

---

### Шаг 3: Проверка логов Railway

1. Откройте Railway Dashboard
2. Сервис: `test_backend_virtual_tryon`
3. Перейдите в **Deployments** → последний deployment → **Logs**
4. Найдите логи с префиксом `[GOOGLE-AUTH]`

**Что искать:**
```
[GOOGLE-AUTH] Google OAuth 2.0 service initialized
[GOOGLE-AUTH] Client ID: 2786633510...mcg5
[GOOGLE-AUTH] Redirect URI: https://testbackendvirtualtryon-production.up.railway.app/api/auth/google/callback
[GOOGLE-AUTH] Generating authorization URL with Client ID: 2786633510...mcg5, Redirect URI: ...
```

**Если есть ошибки:**
- `Client ID format may be incorrect` → проверьте формат
- `Error generating authorization URL` → проблема с конфигурацией

---

## 🎯 Наиболее вероятные причины ошибки 401: invalid_client

### Причина 1: Client ID не существует в Google Cloud Console ⚠️ (НАИБОЛЕЕ ВЕРОЯТНО)

**Симптомы:**
- Authorization URL генерируется правильно
- Но Google возвращает `401: invalid_client`

**Решение:**
1. Проверьте Google Cloud Console
2. Если Client ID не найден → создайте новый:
   - **APIs & Services** → **Credentials** → **Create Credentials** → **OAuth Client ID**
   - Тип: **Web application**
   - Name: `Virtual Try-On Test Environment`
   - Authorized redirect URIs: `https://testbackendvirtualtryon-production.up.railway.app/api/auth/google/callback`
   - Скопируйте новый Client ID и Secret
   - Обновите переменные в Railway:
     - `GOOGLE_CLIENT_ID` = новый Client ID
     - `GOOGLE_CLIENT_SECRET` = новый Client Secret
   - Railway автоматически перезапустит сервис

### Причина 2: Client ID в другом проекте Google Cloud

**Симптомы:**
- Client ID существует, но в другом проекте
- Google не может найти его в текущем проекте

**Решение:**
- Используйте Client ID из правильного проекта
- Или создайте новый Client ID в нужном проекте

### Причина 3: Redirect URI не добавлен в Google Cloud Console

**Симптомы:**
- Обычно ошибка `redirect_uri_mismatch`, но может проявляться как `invalid_client`

**Решение:**
- Добавьте Redirect URI в Google Cloud Console:
  - Откройте OAuth Client ID
  - В разделе **Authorized redirect URIs** добавьте:
    ```
    https://testbackendvirtualtryon-production.up.railway.app/api/auth/google/callback
    ```
  - Сохраните изменения
  - Подождите 1-2 минуты (Google может кэшировать изменения)

---

## 📋 Чеклист для исправления

- [ ] Проверил Google Cloud Console - Client ID существует
- [ ] Проверил статус Client ID - активен
- [ ] Проверил Redirect URI в Console - точно совпадает
- [ ] Проверил проект Google Cloud - правильный проект
- [ ] Протестировал authorization URL в браузере
- [ ] Проверил логи Railway - нет ошибок
- [ ] Если Client ID не найден - создал новый
- [ ] Обновил переменные в Railway (если создал новый Client ID)
- [ ] Подождал 1-2 минуты после изменений в Google Console

---

## 🔗 Полезные ссылки

- **Google Cloud Console:** https://console.cloud.google.com/
- **Тестовый Backend:** https://testbackendvirtualtryon-production.up.railway.app
- **Тестовый Frontend:** https://testtaptolooknet-production.up.railway.app
- **Status Endpoint:** https://testbackendvirtualtryon-production.up.railway.app/api/auth/google/status
- **Login Endpoint:** https://testbackendvirtualtryon-production.up.railway.app/api/auth/google/login

---

## 💡 Рекомендации

1. **Сначала проверьте Google Cloud Console** - это самая частая причина ошибки
2. **Убедитесь, что Redirect URI совпадает ТОЧНО** - даже один символ имеет значение
3. **Подождите 1-2 минуты** после изменений в Google Console - изменения могут применяться с задержкой
4. **Используйте режим инкогнито** для тестирования - чтобы избежать проблем с кэшем браузера

---

*Сгенерировано автоматически после проверки тестового окружения*


