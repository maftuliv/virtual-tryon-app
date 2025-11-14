# Инструкции по Завершению Авторизации

## ✅ УЖЕ СОЗДАНО:

1. **SQL миграция**: `backend/migrations/001_create_auth_tables.sql`
2. **Auth модуль**: `backend/auth.py`
3. **План реализации**: `AUTH_IMPLEMENTATION_PLAN.md`

---

## 📝 СЛЕДУЮЩИЕ ШАГИ:

### 1. Обновить requirements.txt

Добавьте в `backend/requirements.txt`:
```
PyJWT==2.8.0
google-auth==2.25.2
google-auth-oauthlib==1.2.0
```

### 2. Применить SQL миграцию

```bash
# Подключитесь к вашей PostgreSQL базе
psql $DATABASE_URL -f backend/migrations/001_create_auth_tables.sql
```

### 3. Добавить Auth Endpoints в app.py

В `backend/app.py` добавьте:

```python
from auth import AuthManager, create_auth_decorator

# Инициализация
auth_manager = AuthManager(db_connection)
require_auth = create_auth_decorator(auth_manager)

# Регистрация
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json
    result = auth_manager.register_user(
        data['email'],
        data['password'],
        data['full_name']
    )
    return jsonify(result), 200 if result['success'] else 400

# Логин
@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    result = auth_manager.login_user(data['email'], data['password'])
    return jsonify(result), 200 if result['success'] else 400

# Получить текущего пользователя
@app.route('/api/auth/me', methods=['GET'])
@require_auth
def get_current_user():
    user = auth_manager.get_user_by_id(request.user_id)
    if user:
        can_generate, remaining, limit = auth_manager.check_daily_limit(request.user_id)
        user['daily_limit'] = {
            'can_generate': can_generate,
            'remaining': remaining,
            'limit': limit
        }
        return jsonify({'user': user})
    return jsonify({'error': 'User not found'}), 404

# Проверить лимит
@app.route('/api/auth/check-limit', methods=['GET'])
@require_auth
def check_limit():
    can_generate, remaining, limit = auth_manager.check_daily_limit(request.user_id)
    return jsonify({
        'can_generate': can_generate,
        'remaining': remaining,
        'limit': limit
    })

# Защитить endpoint генерации
@app.route('/api/tryon', methods=['POST'])
@require_auth  # Добавить эту строку!
def tryon():
    # Проверить лимит
    can_generate, remaining, limit = auth_manager.check_daily_limit(request.user_id)
    if not can_generate:
        return jsonify({
            'error': 'Daily limit exceeded',
            'message': 'Вы исчерпали дневной лимит. Перейдите на Premium!'
        }), 403

    # Инкрементировать счетчик
    auth_manager.increment_daily_limit(request.user_id)

    # ... существующий код генерации ...

    # Сохранить в историю
    auth_manager.save_generation(
        request.user_id,
        person_image_url,
        garment_image_url,
        result_image_url,
        category,
        session_id
    )

    # Вернуть результат
    return jsonify(result)
```

### 4. Добавить переменные окружения

В Railway или `.env`:
```
JWT_SECRET_KEY=ваш-супер-секретный-ключ-измените-это
GOOGLE_CLIENT_ID=ваш-google-client-id
GOOGLE_CLIENT_SECRET=ваш-google-client-secret
```

### 5. Frontend - Создать auth.js

Полный код в `AUTH_IMPLEMENTATION_PLAN.md` (секция "Этап 7").

### 6. Frontend - UI модального окна

Добавьте в `index.html` перед закрывающим `</body>`:

```html
<!-- Auth Modal -->
<div id="authModal" class="auth-modal" style="display: none;">
    <div class="auth-modal-overlay" onclick="closeAuthModal()"></div>
    <div class="auth-modal-content">
        <button class="auth-modal-close" onclick="closeAuthModal()">&times;</button>

        <div class="auth-tabs">
            <button class="auth-tab active" onclick="switchAuthTab('login')">Вход</button>
            <button class="auth-tab" onclick="switchAuthTab('register')">Регистрация</button>
        </div>

        <!-- Login Form -->
        <form id="loginForm" class="auth-form" onsubmit="handleLogin(event)">
            <input type="email" id="loginEmail" placeholder="Email" required>
            <input type="password" id="loginPassword" placeholder="Пароль" required>
            <button type="submit" class="auth-submit-btn">Войти</button>
            <div class="auth-error" id="loginError"></div>
        </form>

        <!-- Register Form -->
        <form id="registerForm" class="auth-form" style="display: none;" onsubmit="handleRegister(event)">
            <input type="text" id="registerName" placeholder="Имя" required>
            <input type="email" id="registerEmail" placeholder="Email" required>
            <input type="password" id="registerPassword" placeholder="Пароль" required>
            <button type="submit" class="auth-submit-btn">Зарегистрироваться</button>
            <div class="auth-error" id="registerError"></div>
        </form>

        <div class="auth-divider">или войти через</div>

        <div class="social-auth">
            <button class="social-btn google" onclick="googleLogin()">
                <svg><!-- Google icon --></svg>
                Google
            </button>
        </div>
    </div>
</div>

<script src="auth.js"></script>
```

### 7. Добавить кнопку "Войти" в header

Замените в `index.html`:
```html
<div class="top-bar-right">
    <!-- Для неавторизованных -->
    <button id="authButton" class="auth-button" onclick="showAuthModal()">
        Войти
    </button>

    <!-- Для авторизованных (скрыто по умолчанию) -->
    <div id="userProfile" class="user-profile" style="display: none;">
        <img id="userAvatar" src="default-avatar.png" class="user-avatar">
        <div class="user-info">
            <span id="userName">User</span>
            <span id="userStatus" class="user-status-badge">Free</span>
        </div>
    </div>

    <a href="changelog.html">📜 История</a>
</div>
```

---

## 🚀 ТЕСТИРОВАНИЕ:

1. Перезапустите backend
2. Откройте сайт
3. Нажмите "Войти"
4. Зарегистрируйтесь
5. Попробуйте сгенерировать 3 раза
6. При 4-й попытке должна быть ошибка лимита

---

## 📂 ФАЙЛЫ ДЛЯ ИЗУЧЕНИЯ:

- `AUTH_IMPLEMENTATION_PLAN.md` - полный план с кодом
- `backend/auth.py` - все функции авторизации
- `backend/migrations/001_create_auth_tables.sql` - структура БД

Нужна помощь с конкретным шагом?
