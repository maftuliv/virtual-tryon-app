# Исправление проблемы с Google OAuth логином на staging

## Проблема

При нажатии на кнопку "Войти" через Google OAuth на staging окружении:
- В браузере отображался JSON ответ вместо редиректа на Google
- JSON содержал: `{"authorization_url": "...", "success": true}`
- Пользователь не перенаправлялся на страницу авторизации Google

## Корневая причина

**Неправильный паттерн инициализации OAuth flow:**

В `app-next/src/components/LandingPage.tsx` использовался прямой редирект:
```typescript
// ❌ НЕПРАВИЛЬНО (было):
const handleLoginClick = () => {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';
  window.location.href = `${apiUrl}/api/auth/google/login`;
};
```

**Почему это не работало:**
1. `window.location.href` делает GET запрос на backend
2. Backend endpoint `/api/auth/google/login` возвращает **JSON**, а не HTTP редирект
3. Браузер показывает JSON ответ вместо перенаправления на Google
4. OAuth flow не инициируется

## Решение

Изменил логику на правильный паттерн: **fetch → получить URL → редирект**

```typescript
// ✅ ПРАВИЛЬНО (стало):
const handleLoginClick = async () => {
  try {
    // 1. Делаем fetch запрос к backend
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';
    const response = await fetch(`${apiUrl}/api/auth/google/login`);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    // 2. Получаем JSON с authorization_url
    const data = await response.json();
    
    // 3. Проверяем успешность и наличие URL
    if (data.success && data.authorization_url) {
      // 4. Редиректим на Google OAuth
      window.location.href = data.authorization_url;
    } else {
      alert('Не удалось получить URL для входа через Google. Попробуйте еще раз.');
    }
  } catch (error) {
    console.error('Ошибка при инициализации Google OAuth:', error);
    alert('Ошибка при входе через Google. Попробуйте еще раз.');
  }
};
```

## Правильный OAuth Flow

Теперь flow работает корректно:

1. **Пользователь нажимает "Войти"**
   - Frontend вызывает `handleLoginClick()`

2. **Frontend делает fetch запрос**
   - `GET /api/auth/google/login`
   - Backend генерирует state token и authorization URL

3. **Backend возвращает JSON**
   ```json
   {
     "success": true,
     "authorization_url": "https://accounts.google.com/o/oauth2/auth?..."
   }
   ```

4. **Frontend редиректит на Google**
   - `window.location.href = data.authorization_url`
   - Пользователь видит страницу авторизации Google

5. **Google редиректит обратно на backend**
   - `GET /api/auth/google/callback?code=...&state=...`
   - Backend обменивает code на токен, создает/логинит пользователя

6. **Backend редиректит на frontend с токеном**
   - `https://testtaptolooknet-production.up.railway.app/#google_auth_success=1&token=<jwt>`

7. **Frontend обрабатывает токен**
   - `GoogleOAuthHandler` компонент (в `ClientProviders`) читает hash
   - Вызывает `authApi.me(token)` для получения данных пользователя
   - Сохраняет токен и пользователя в `authStore`

## Что было изменено

**Файл:** `app-next/src/components/LandingPage.tsx`
- **Строки:** 20-24 (было) → 20-38 (стало)
- **Изменение:** 
  - Добавлен `async/await` для асинхронной обработки
  - Добавлен `fetch()` запрос к backend
  - Добавлена обработка JSON ответа
  - Добавлена проверка `data.success` и `data.authorization_url`
  - Добавлена обработка ошибок с try/catch
  - Редирект на Google происходит только после получения `authorization_url`

## Урок для будущего

**Важно:** Всегда проверяйте формат ответа API endpoint перед использованием.

**Паттерн для OAuth инициализации:**
1. ❌ **НЕ используйте** прямой `window.location.href` на API endpoint, который возвращает JSON
2. ✅ **Используйте** `fetch()` для получения данных от API
3. ✅ **Проверяйте** формат ответа (JSON vs HTTP redirect)
4. ✅ **Делайте редирект** только после получения нужных данных

**Красные флаги:**
- Если API endpoint возвращает JSON, а не HTTP redirect (302/301)
- Если используется `window.location.href` на endpoint, который возвращает JSON
- Если в браузере показывается JSON вместо ожидаемого редиректа

**Правильный паттерн для OAuth:**
```typescript
// ✅ Правильно:
const response = await fetch('/api/auth/google/login');
const data = await response.json();
if (data.authorization_url) {
  window.location.href = data.authorization_url;
}

// ❌ Неправильно:
window.location.href = '/api/auth/google/login'; // Покажет JSON!
```

## Статус

✅ **Исправлено и задеплоено на staging**
- Коммит: `c620d31` - "fix: Use fetch to get Google OAuth authorization URL before redirect"
- Ветка: `staging` (production/main не затронута)

## Дополнительные проверки

После деплоя убедитесь:
1. ✅ Backend endpoint `/api/auth/google/login` возвращает JSON с `authorization_url`
2. ✅ Frontend правильно обрабатывает ответ и редиректит на Google
3. ✅ Google OAuth callback работает (проверено ранее)
4. ✅ `GoogleOAuthHandler` компонент подключен в `ClientProviders` (проверено)
5. ✅ `FRONTEND_URL` в backend config указывает на правильный frontend URL для staging

