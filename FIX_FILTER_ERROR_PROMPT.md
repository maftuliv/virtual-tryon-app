# Исправление ошибки "a.filter is not a function" после входа через Google OAuth

## Проблема

После успешного входа через Google OAuth на staging окружении возникала критическая ошибка в браузере:
```
Uncaught TypeError: a.filter is not a function
```

Ошибка происходила в компонентах `UserGreeting.tsx` и `LikedItems.tsx` при попытке вызвать метод `.filter()` на переменной `tryons`.

## Корневая причина

**Несоответствие формата данных между Backend API и Frontend ожиданиями:**

1. **Backend API** (`/api/user/tryons`) возвращает объект с вложенным массивом:
   ```json
   {
     "success": true,
     "tryons": [...],
     "total": 10,
     "limit": 50,
     "offset": 0,
     "has_more": false
   }
   ```

2. **Frontend** ожидал получить массив напрямую, но получал объект:
   ```typescript
   // ❌ НЕПРАВИЛЬНО (было):
   async getUserTryons(): Promise<UserTryon[]> {
     return api.get('api/user/tryons').json(); // Возвращает объект, а не массив!
   }
   ```

3. **Компоненты** пытались вызвать `.filter()` на объекте:
   ```typescript
   // UserGreeting.tsx:13
   const favoritesCount = tryons?.filter((t) => t.is_favorite).length || 0;
   // ❌ Ошибка: tryons это объект {success, tryons, total...}, а не массив
   ```

## Решение

Исправлена функция `getUserTryons()` в `app-next/src/lib/api.ts`:

```typescript
// ✅ ПРАВИЛЬНО (стало):
async getUserTryons(): Promise<UserTryon[]> {
  const response = await api.get('api/user/tryons').json<{
    success: boolean;
    tryons: UserTryon[];
    total: number;
    limit: number;
    offset: number;
    has_more: boolean;
  }>();
  return response.tryons || []; // Извлекаем массив из ответа
}
```

## Что было изменено

**Файл:** `app-next/src/lib/api.ts`
- **Строки:** 130-141
- **Изменение:** Добавлена типизация ответа API и извлечение массива `tryons` из объекта ответа
- **Результат:** Теперь функция возвращает массив `UserTryon[]`, как и ожидают компоненты

## Урок для будущего

**Важно:** Всегда проверяйте формат ответа API на бэкенде и убеждайтесь, что фронтенд правильно обрабатывает структуру данных.

**Паттерн для проверки:**
1. Посмотрите, что возвращает Backend endpoint (в `backend/api/user_tryons.py`)
2. Проверьте, что Frontend API функция (`app-next/src/lib/api.ts`) правильно парсит ответ
3. Убедитесь, что типы TypeScript соответствуют реальной структуре данных

**Красные флаги:**
- Если API возвращает объект с данными внутри (например, `{success: true, data: [...]}`), а функция ожидает массив напрямую
- Если TypeScript типы не соответствуют реальной структуре ответа
- Если используются методы массивов (`.filter()`, `.map()`, `.length`) на переменных, которые могут быть объектами

## Статус

✅ **Исправлено и задеплоено на staging**
- Коммит: `7004a30` - "Fix: Extract tryons array from API response to fix filter error"
- Ветка: `staging` (production/main не затронута)

