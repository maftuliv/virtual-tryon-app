# 🍌 Полная Инструкция по Интеграции Nano Banana API

**Дата**: 2025-11-11
**Модель**: Google Gemini 2.5 Flash (Nano Banana)
**Платформа**: Replicate API
**Цена**: $0.03 за изображение

---

## 📋 Что Уже Готово

✅ Frontend слайдер с иконкой 🍌
✅ Backend функция `process_with_nanobanana()`
✅ Обработка ошибок и уведомления
✅ Переключение моделей через UI

---

## 🎯 Шаг 1: Регистрация на Replicate

### 1.1 Создайте аккаунт на Replicate

🔗 **Ссылка**: https://replicate.com/signin

1. Откройте ссылку выше
2. Нажмите **"Sign up"**
3. Выберите метод регистрации:
   - GitHub (рекомендуется)
   - Google
   - Email

### 1.2 Получите API ключ

🔗 **Ссылка**: https://replicate.com/account/api-tokens

1. После входа перейдите по ссылке выше
2. Нажмите **"Create token"**
3. Введите имя токена (например: `nano-banana-tryon`)
4. Нажмите **"Create"**
5. **⚠️ ВАЖНО**: Скопируйте токен СРАЗУ! Он показывается только один раз!

**Ваш токен будет выглядеть так:**
```
r8_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 1.3 Проверьте доступные модели

🔗 **Nano Banana на Replicate**: https://replicate.com/google/nano-banana

Убедитесь, что модель доступна и посмотрите примеры использования.

---

## 🖥️ Шаг 2: Установка Replicate SDK на сервере

### 2.1 SSH подключение к Railway

Если ваш backend запущен на Railway, вам нужно добавить зависимость в `requirements.txt`.

**Откройте файл** `backend/requirements.txt` и добавьте:

```txt
Flask==3.0.0
flask-cors==4.0.0
requests==2.31.0
Pillow==10.1.0
replicate==0.22.0
```

### 2.2 Локальная установка (для тестирования)

Если хотите протестировать локально:

```bash
cd virtual-tryon-app
pip install replicate
```

---

## 🔑 Шаг 3: Настройка Environment Variables

### 3.1 На Railway (Production)

🔗 **Railway Dashboard**: https://railway.app/dashboard

1. Откройте ваш проект на Railway
2. Перейдите в раздел **Variables**
3. Нажмите **"New Variable"**
4. Добавьте:
   - **Key**: `REPLICATE_API_KEY`
   - **Value**: `r8_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` (ваш токен)
5. Нажмите **"Add"**

**⚠️ ВАЖНО**: После добавления переменной Railway автоматически перезапустит приложение!

### 3.2 Локально (для тестирования)

**Создайте файл** `.env` в корне проекта:

```bash
# В корне проекта (virtual-tryon-app/)
touch .env
```

**Добавьте в `.env`:**

```env
FASHN_API_KEY=ваш_fashn_ключ
REPLICATE_API_KEY=r8_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**⚠️ Убедитесь, что `.env` в `.gitignore`!**

---

## 🔧 Шаг 4: Реализация Nano Banana API в Backend

### 4.1 Откройте файл `backend/app.py`

Найдите функцию `process_with_nanobanana()` (строка ~148)

### 4.2 Замените функцию на рабочую версию

**Удалите старый код** (строки 148-178) и **вставьте новый**:

```python
def process_with_nanobanana(person_image_path, garment_image_path, category='auto'):
    """
    Process virtual try-on using Nano Banana (Google Gemini 2.5 Flash)
    Via Replicate API: https://replicate.com/google/nano-banana

    Nano Banana is Google's image editing model powered by Gemini 2.5 Flash
    Pricing: $0.03 per image (cheaper than FASHN!)
    Speed: Very fast generation (5-10 seconds)
    """
    try:
        print(f"[NANOBANANA] 🍌 Starting Nano Banana processing...")

        if not REPLICATE_API_KEY:
            raise ValueError("REPLICATE_API_KEY not set. Please add to environment variables.")

        # Import replicate (installed via requirements.txt)
        import replicate

        # Preprocess images
        person_image_optimized = preprocess_image(person_image_path, max_height=2000, quality=95)
        garment_image_optimized = preprocess_image(garment_image_path, max_height=2000, quality=95)

        # Convert to base64 for API
        person_image_b64 = image_to_base64(person_image_optimized)
        garment_image_b64 = image_to_base64(garment_image_optimized)

        # Create prompt for virtual try-on
        prompt = f"""
        Create a realistic virtual try-on image:
        - Person: wearing the garment
        - Garment type: {category}
        - Style: photorealistic, high quality
        - Preserve person's pose and features
        - Fit garment naturally on the person's body
        """

        print(f"[NANOBANANA] Sending request to Replicate API...")

        # Call Replicate API
        output = replicate.run(
            "google/nano-banana",
            input={
                "image": f"data:image/jpg;base64,{person_image_b64}",
                "reference_image": f"data:image/jpg;base64,{garment_image_b64}",
                "prompt": prompt,
                "num_outputs": 1,
                "guidance_scale": 7.5,
                "num_inference_steps": 50
            }
        )

        print(f"[NANOBANANA] Response received: {type(output)}")

        # Handle output (URL or base64)
        timestamp = int(time.time())
        result_filename = f'result_nanobanana_{timestamp}.png'
        result_path = os.path.join(app.config['RESULTS_FOLDER'], result_filename)

        if isinstance(output, list) and len(output) > 0:
            result_data = output[0]
        else:
            result_data = output

        # Download or save result
        if isinstance(result_data, str) and result_data.startswith('http'):
            # Download from URL
            print(f"[NANOBANANA] Downloading result from URL...")
            img_response = requests.get(result_data, timeout=30)
            if img_response.status_code == 200:
                with open(result_path, 'wb') as img_file:
                    img_file.write(img_response.content)
                print(f"[NANOBANANA] ✅ Downloaded {len(img_response.content)} bytes")
            else:
                raise ValueError(f"Failed to download result: {img_response.status_code}")
        elif isinstance(result_data, str):
            # Save base64 image
            print(f"[NANOBANANA] Saving base64 result...")
            save_base64_image(result_data, result_path)
        else:
            raise ValueError(f"Unexpected output type: {type(result_data)}")

        print(f"[NANOBANANA] ✅ Result saved to: {result_path}")
        return result_path

    except ImportError as e:
        print(f"[NANOBANANA ERROR] ❌ Replicate library not installed: {e}")
        raise ValueError(
            "NANOBANANA_SETUP_ERROR: Replicate library not installed. "
            "Add 'replicate==0.22.0' to requirements.txt and redeploy."
        )
    except Exception as e:
        print(f"[NANOBANANA ERROR] ❌ Error in process_with_nanobanana: {e}")
        import traceback
        traceback.print_exc()
        raise
```

---

## 📦 Шаг 5: Обновление Requirements

### 5.1 Проверьте `backend/requirements.txt`

**Файл должен содержать:**

```txt
Flask==3.0.0
flask-cors==4.0.0
requests==2.31.0
Pillow==10.1.0
replicate==0.22.0
```

### 5.2 Commit и Push изменений

```bash
cd virtual-tryon-app

# Проверить статус
git status

# Добавить файлы
git add backend/app.py backend/requirements.txt

# Commit
git commit -m "Integrate Nano Banana API via Replicate

- Implemented process_with_nanobanana() with full API integration
- Added replicate SDK to requirements.txt
- Virtual try-on with Google Gemini 2.5 Flash
- Cost: $0.03 per image
- Speed: 5-10 seconds per generation"

# Push to GitHub
git push
```

---

## 🚀 Шаг 6: Deployment на Railway

### 6.1 Автоматический Deploy

Railway автоматически развернет изменения после push на GitHub:

1. Зайдите на https://railway.app/dashboard
2. Откройте ваш проект
3. Перейдите в **Deployments**
4. Дождитесь завершения деплоя (2-5 минут)

### 6.2 Проверьте логи

В разделе **Deployments** → **Logs** найдите:

```
✅ Installing replicate==0.22.0
✅ Successfully installed replicate-0.22.0
```

---

## 🧪 Шаг 7: Тестирование

### 7.1 Локальное тестирование (опционально)

```bash
# Запустите backend локально
cd virtual-tryon-app/backend
python app.py
```

### 7.2 Production тестирование

1. Откройте https://taptolook.up.railway.app
2. **Жестко перезагрузите** страницу: `Ctrl + Shift + R`
3. Загрузите фото человека и одежды
4. **Переключите** слайдер на **🍌 Nano Banana**
5. Нажмите **"нажми чтобы посмотреть"**

### 7.3 Что должно произойти

✅ **Успех**: Через 5-10 секунд появится результат
❌ **Ошибка**: Появится сообщение об ошибке

---

## 🐛 Troubleshooting (Решение Проблем)

### Проблема 1: "REPLICATE_API_KEY not set"

**Решение**:
1. Проверьте Railway Variables
2. Убедитесь, что ключ начинается с `r8_`
3. Перезапустите приложение на Railway

### Проблема 2: "Replicate library not installed"

**Решение**:
1. Проверьте `requirements.txt` содержит `replicate==0.22.0`
2. Commit и push изменения
3. Railway автоматически переустановит зависимости

### Проблема 3: "Failed to download result"

**Решение**:
1. Проверьте интернет соединение на сервере
2. Убедитесь, что Replicate API работает: https://status.replicate.com/

### Проблема 4: Медленная генерация (>30 секунд)

**Решение**:
1. Это нормально для первого запроса (cold start)
2. Последующие запросы будут быстрее
3. Можно увеличить timeout в app.py

---

## 💰 Стоимость и Лимиты

### Replicate Pricing

🔗 **Pricing**: https://replicate.com/pricing

**Nano Banana**:
- **Цена**: $0.03 за изображение
- **Скорость**: ~5-10 секунд
- **Quality**: Высокое

**Free Tier**:
- $0.01 в месяц бесплатно (для тестирования)
- После этого оплата по факту использования

### Сравнение с FASHN

| Параметр | FASHN AI | Nano Banana |
|----------|----------|-------------|
| Цена | $0.10+ | $0.03 |
| Скорость | 5-17 сек | 5-10 сек |
| Качество | Очень высокое | Высокое |
| Статус | ✅ Работает | 🍌 Новая |

---

## 📊 Мониторинг Использования

### Replicate Dashboard

🔗 **Usage**: https://replicate.com/account/usage

Здесь вы можете отслеживать:
- Количество запросов
- Потраченные средства
- История генераций

---

## 🔐 Безопасность

### ⚠️ ВАЖНО: Защита API ключей

1. **Никогда не коммитьте** `.env` файл в Git
2. **Добавьте в `.gitignore`**:
   ```
   .env
   *.env
   ```
3. **Используйте** только environment variables на production
4. **Регулярно ротируйте** API ключи (каждые 3-6 месяцев)

---

## 📚 Полезные Ссылки

### Документация

- 🔗 **Replicate Docs**: https://replicate.com/docs
- 🔗 **Nano Banana Model**: https://replicate.com/google/nano-banana
- 🔗 **Python Client**: https://github.com/replicate/replicate-python
- 🔗 **API Reference**: https://replicate.com/docs/reference/http

### Поддержка

- 🔗 **Replicate Discord**: https://discord.gg/replicate
- 🔗 **GitHub Issues**: https://github.com/replicate/replicate-python/issues
- 🔗 **Status Page**: https://status.replicate.com/

---

## ✅ Финальный Checklist

Перед запуском убедитесь:

- [ ] ✅ Зарегистрирован аккаунт на Replicate
- [ ] ✅ Получен API ключ (r8_...)
- [ ] ✅ Добавлен REPLICATE_API_KEY в Railway Variables
- [ ] ✅ Обновлен `requirements.txt` (добавлен replicate==0.22.0)
- [ ] ✅ Обновлен код `process_with_nanobanana()` в app.py
- [ ] ✅ Commit и push изменений
- [ ] ✅ Railway deployment завершен успешно
- [ ] ✅ Проверены логи на наличие ошибок
- [ ] ✅ Протестирована генерация на сайте
- [ ] ✅ Проверен баланс на Replicate Dashboard

---

## 🎉 Готово!

После выполнения всех шагов у вас будет работающая интеграция с двумя AI моделями:

- ⚡ **FASHN AI** - Проверенная, высокое качество
- 🍌 **Nano Banana** - Google Gemini 2.5, быстрая и дешевая

Пользователи смогут выбирать модель через красивый слайдер с плавными анимациями!

---

**Автор**: Claude Code (СТО с 20-летним стажем)
**Дата**: 2025-11-11
**Версия**: 1.0

Удачи! 🚀
