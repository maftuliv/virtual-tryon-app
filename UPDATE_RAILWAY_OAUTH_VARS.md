# 🔧 Обновление OAuth переменных в Railway

## ✅ Проблема найдена!

В Google Cloud Console существует OAuth Client с ID:
```
558131336096-bpdufj7dj1240r45k3feulft6tvfudpi.apps.googleusercontent.com
```

Но в Railway используется неправильный Client ID:
```
278663351028-qcrgf8j2d1lpce6kjamb4vtejq82mcg5.apps.googleusercontent.com
```

---

## 🎯 Решение: Обновить переменные в Railway

### Шаг 1: Откройте Railway Dashboard

1. Перейдите: https://railway.app/
2. Войдите в свой аккаунт
3. Выберите проект
4. Выберите сервис: **test_backend_virtual_tryon**

### Шаг 2: Обновите переменные окружения

1. Перейдите в **Variables** tab
2. Найдите следующие переменные и обновите их:

#### ✅ GOOGLE_CLIENT_ID

**Старое значение (неправильное):**
```
278663351028-qcrgf8j2d1lpce6kjamb4vtejq82mcg5.apps.googleusercontent.com
```

**Новое значение (правильное):**
```
558131336096-bpdufj7dj1240r45k3feulft6tvfudpi.apps.googleusercontent.com
```

**Действия:**
- Нажмите на переменную `GOOGLE_CLIENT_ID`
- Замените значение на новый Client ID
- Нажмите **Save** или **Update**

#### ✅ GOOGLE_CLIENT_SECRET

**Новое значение:**
```
GOCSPX-TM1xiYZZAOjDS5SI76zkUoPcpGA
```

**Действия:**
- Нажмите на переменную `GOOGLE_CLIENT_SECRET`
- Замените значение на новый Client Secret
- Нажмите **Save** или **Update**

#### ✅ GOOGLE_REDIRECT_URI (проверьте)

**Должно быть:**
```
https://testbackendvirtualtryon-production.up.railway.app/api/auth/google/callback
```

**Проверьте:**
- Убедитесь, что значение точно такое (без trailing slash)
- Если отличается - обновите

---

### Шаг 3: Проверка переменных

После обновления переменных, убедитесь что:

- ✅ `GOOGLE_OAUTH_ENABLED=true`
- ✅ `GOOGLE_CLIENT_ID=558131336096-bpdufj7dj1240r45k3feulft6tvfudpi.apps.googleusercontent.com`
- ✅ `GOOGLE_CLIENT_SECRET=GOCSPX-TM1xiYZZAOjDS5SI76zkUoPcpGA`
- ✅ `GOOGLE_REDIRECT_URI=https://testbackendvirtualtryon-production.up.railway.app/api/auth/google/callback`

**Важно:**
- Нет лишних пробелов в начале/конце
- Значения НЕ в кавычках
- Client ID заканчивается на `.apps.googleusercontent.com`

---

### Шаг 4: Ожидание перезапуска

Railway автоматически перезапустит сервис после изменения переменных.

**Подождите 1-2 минуты** для:
- Применения переменных окружения
- Перезапуска сервиса
- Применения изменений

---

### Шаг 5: Проверка после обновления

#### 5.1 Проверка статуса

```bash
curl https://testbackendvirtualtryon-production.up.railway.app/api/auth/google/status
```

**Ожидаемый ответ:**
```json
{
  "enabled": true,
  "configured": true,
  "client_id_masked": "5581313360...udpi",
  "client_id_format_valid": true,
  "redirect_uri": "https://testbackendvirtualtryon-production.up.railway.app/api/auth/google/callback",
  "config_issues": []
}
```

**Проверьте:**
- `client_id_masked` должен начинаться с `5581313360...` (новый Client ID)
- `config_issues` должен быть пустым массивом

#### 5.2 Тестирование authorization URL

```bash
curl https://testbackendvirtualtryon-production.up.railway.app/api/auth/google/login
```

**Ожидаемый ответ:**
```json
{
  "success": true,
  "authorization_url": "https://accounts.google.com/o/oauth2/auth?client_id=558131336096-bpdufj7dj1240r45k3feulft6tvfudpi.apps.googleusercontent.com&..."
}
```

**Проверьте:**
- `authorization_url` должен содержать новый Client ID (`558131336096-...`)

#### 5.3 Открытие authorization URL в браузере

1. Скопируйте `authorization_url` из ответа
2. Откройте в браузере (режим инкогнито)
3. **Ожидаемый результат:**
   - ✅ Должен открыться экран разрешений Google (consent screen)
   - ❌ Если все еще ошибка 401 - проверьте еще раз переменные

---

## 📋 Чеклист обновления

- [ ] Открыл Railway Dashboard
- [ ] Выбрал сервис `test_backend_virtual_tryon`
- [ ] Обновил `GOOGLE_CLIENT_ID` на `558131336096-bpdufj7dj1240r45k3feulft6tvfudpi.apps.googleusercontent.com`
- [ ] Обновил `GOOGLE_CLIENT_SECRET` на `GOCSPX-TM1xiYZZAOjDS5SI76zkUoPcpGA`
- [ ] Проверил `GOOGLE_REDIRECT_URI` (должен быть правильным)
- [ ] Убедился, что нет лишних пробелов
- [ ] Подождал 1-2 минуты для перезапуска
- [ ] Проверил `/api/auth/google/status` - новый Client ID
- [ ] Протестировал authorization URL - открывается consent screen

---

## 🔍 Если после обновления все еще ошибка

### Проверка 1: Переменные правильно обновились?

1. Проверьте через `/api/auth/google/status`
2. Убедитесь, что `client_id_masked` начинается с `5581313360...`

### Проверка 2: Redirect URI в Google Console

В Google Cloud Console проверьте, что Redirect URI точно совпадает:
```
https://testbackendvirtualtryon-production.up.railway.app/api/auth/google/callback
```

### Проверка 3: Логи Railway

1. Откройте Railway → Deployments → последний deployment → Logs
2. Найдите логи с `[GOOGLE-AUTH]`
3. Проверьте, что Client ID правильный в логах

---

## ✅ После успешного обновления

Когда все заработает:
1. ✅ Authorization URL будет открывать consent screen Google
2. ✅ После разрешения будет редирект на callback
3. ✅ Пользователь будет авторизован

---

*Инструкция для обновления OAuth переменных в Railway*



