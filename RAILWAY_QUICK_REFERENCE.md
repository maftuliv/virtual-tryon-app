# 🚀 RAILWAY - БЫСТРАЯ ШПАРГАЛКА

## ⚡ ЗА 5 МИНУТ

### 1. Загрузите на GitHub (2 минуты)
```bash
cd C:\Users\ivmaf\virtual-tryon-app
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/ваш-username/virtual-tryon-app.git
git push -u origin main
```

### 2. Разверните на Railway (3 минуты)
1. Откройте: https://railway.app
2. Login with GitHub
3. New Project → Deploy from GitHub repo
4. Выберите: virtual-tryon-app
5. Подождите 3-5 минут
6. Settings → Generate Domain
7. Готово!

---

## 📋 ОСНОВНЫЕ КОМАНДЫ

### Git команды
```bash
# Первая настройка (один раз)
git config --global user.name "Ваше Имя"
git config --global user.email "email@example.com"

# Сохранение изменений
git add .
git commit -m "Описание"
git push

# Проверка статуса
git status
```

### Обновление приложения
```bash
# 1. Измените код
# 2. Сохраните в Git
git add .
git commit -m "Update"
git push
# 3. Railway автоматически обновит!
```

---

## 🔍 ПРОВЕРКА

### Что проверить:
- ✅ https://ваш-url.up.railway.app - главная страница
- ✅ https://ваш-url.up.railway.app/api/health - API

### Где смотреть логи:
Railway → Deployments → View Logs

### Где смотреть использование:
Railway → Account Settings → Usage

---

## 🆘 ЧАСТЫЕ ПРОБЛЕМЫ

### Application Error
→ Проверьте логи в Railway
→ Убедитесь что Procfile правильный

### 502 Bad Gateway
→ Увеличьте timeout в Procfile до 180
→ Перезапустите: Deployments → Redeploy

### Файлы не загружаются
→ Проверьте Flask-CORS в requirements.txt
→ Проверьте API_URL в frontend/app.js

### Медленно работает
→ Добавьте HF_API_TOKEN в Variables
→ Оптимизируйте размер изображений

---

## 💰 СТОИМОСТЬ

- Первый месяц: БЕСПЛАТНО ($5 кредитов)
- Дальше: ~$5/месяц
- Контроль: Settings → Usage Limits

---

## 🌐 СВОЙ ДОМЕН

1. Купите домен на Namecheap/Reg.ru
2. Railway: Settings → Custom Domain
3. Добавьте CNAME запись в DNS:
   ```
   www → ваш-url.up.railway.app
   ```
4. Подождите 30-60 минут
5. Готово!

---

## 📱 ПОЛЕЗНЫЕ ССЫЛКИ

- Railway: https://railway.app/dashboard
- Docs: https://docs.railway.app
- GitHub: https://github.com/ваш-username
- Подробная инструкция: RAILWAY_DETAILED_GUIDE.md

---

**Всё! Приложение работает в интернете! 🎉**
