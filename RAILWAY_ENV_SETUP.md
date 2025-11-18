# Railway Environment Variables Setup

## Проблема
Google OAuth не работает из-за отсутствия переменной окружения `NEXT_PUBLIC_API_URL` в Railway Frontend сервисе.

## Решение

### Шаг 1: Получить URL бэкенда

1. Открыть Railway Dashboard: https://railway.app
2. Выбрать проект `virtual-tryon-app`
3. Открыть **Backend Service** (Python/Flask)
4. Перейти в **Settings** → **Networking** → **Public Domain**
5. Скопировать URL (например: `https://testtaptolooknet-production.up.railway.app`)

### Шаг 2: Установить переменную окружения для Frontend

1. В том же проекте Railway открыть **Frontend Service** (Next.js)
2. Перейти в **Variables**
3. Нажать **New Variable**
4. Добавить:
   - **Variable Name:** `NEXT_PUBLIC_API_URL`
   - **Value:** URL бэкенда из Шага 1 (например: `https://testtaptolooknet-production.up.railway.app`)
5. Нажать **Add**

### Шаг 3: Проверка

После добавления переменной Railway автоматически пересоберет приложение.

Проверить что переменная установлена можно так:
1. Открыть frontend URL в браузере
2. Открыть DevTools Console (F12)
3. Ввести: `console.log(process.env.NEXT_PUBLIC_API_URL)`
4. Должен вывестись URL бэкенда

### Шаг 4: Тестирование Google OAuth

1. Открыть модальное окно авторизации
2. Нажать "Войти через Google"
3. Должен произойти редирект на Google OAuth страницу

## Что делает эта переменная?

`NEXT_PUBLIC_API_URL` используется в [next.config.js](app-next/next.config.js#L27) для настройки прокси:

```javascript
async rewrites() {
  const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';
  return [
    {
      source: '/api/:path*',
      destination: `${backendUrl}/api/:path*`,
    },
  ];
}
```

Все запросы к `/api/*` на фронтенде автоматически проксируются к бэкенду.

## Важно!

- Переменная должна начинаться с `NEXT_PUBLIC_` чтобы быть доступной в браузере
- После изменения переменных окружения Railway пересобирает приложение (3-5 минут)
- URL бэкенда НЕ должен заканчиваться на `/`

## Если проблема остается

Проверьте логи в Railway:
1. Frontend Service → Deployments → Latest → Deploy Logs
2. Backend Service → Deployments → Latest → Deploy Logs

Убедитесь что:
- Backend сервис запущен и доступен
- Frontend сервис успешно собрался
- Переменная `NEXT_PUBLIC_API_URL` установлена правильно
