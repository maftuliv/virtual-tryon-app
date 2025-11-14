# План Реализации Системы Авторизации и Premium

## 📋 Обзор

Реализация полноценной системы авторизации с поддержкой:
- Email/пароль регистрация
- Google OAuth 2.0
- VK OAuth (опционально)
- Telegram Auth (опционально)
- Premium подписки
- Лимиты для бесплатных пользователей

---

## 🗄️ Этап 1: База Данных

### Таблица `users`
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE,
    password_hash VARCHAR(255),  -- NULL для OAuth пользователей
    full_name VARCHAR(255),
    avatar_url TEXT,
    provider VARCHAR(50) DEFAULT 'email',  -- 'email', 'google', 'vk', 'telegram'
    provider_id VARCHAR(255),  -- ID от провайдера (для OAuth)
    is_premium BOOLEAN DEFAULT FALSE,
    premium_until TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP
);
```

### Таблица `generations`
```sql
CREATE TABLE generations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    session_id VARCHAR(255),
    person_image_url TEXT,
    garment_image_url TEXT,
    result_image_url TEXT,
    category VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Таблица `daily_limits`
```sql
CREATE TABLE daily_limits (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    date DATE DEFAULT CURRENT_DATE,
    generations_count INTEGER DEFAULT 0,
    UNIQUE(user_id, date)
);
```

---

## 🔐 Этап 2: Backend API (Flask)

### Новые endpoints

#### 1. Регистрация через Email
```
POST /api/auth/register
Body: {
    "email": "user@example.com",
    "password": "secure_password",
    "full_name": "Иван Иванов"
}
Response: {
    "success": true,
    "user": {...},
    "token": "jwt_token_here"
}
```

#### 2. Вход через Email
```
POST /api/auth/login
Body: {
    "email": "user@example.com",
    "password": "password"
}
Response: {
    "success": true,
    "user": {...},
    "token": "jwt_token_here"
}
```

#### 3. Google OAuth
```
GET /api/auth/google
→ Редирект на Google OAuth

GET /api/auth/google/callback
→ Обработка callback от Google
→ Редирект на фронтенд с токеном
```

#### 4. Проверка статуса пользователя
```
GET /api/auth/me
Headers: Authorization: Bearer <token>
Response: {
    "user": {
        "id": 1,
        "email": "user@example.com",
        "is_premium": false,
        "daily_limit": 3,
        "used_today": 1
    }
}
```

#### 5. Проверка лимита генераций
```
GET /api/auth/check-limit
Headers: Authorization: Bearer <token>
Response: {
    "can_generate": true,
    "remaining": 2,
    "limit": 3
}
```

---

## 🎨 Этап 3: Frontend UI

### Модальные окна

#### 1. Модальное окно авторизации
```html
<div id="authModal" class="auth-modal">
    <div class="auth-modal-content">
        <!-- Табы: Вход | Регистрация -->
        <div class="auth-tabs">
            <button class="auth-tab active">Вход</button>
            <button class="auth-tab">Регистрация</button>
        </div>

        <!-- Форма входа -->
        <form id="loginForm">
            <input type="email" placeholder="Email" required>
            <input type="password" placeholder="Пароль" required>
            <button type="submit">Войти</button>
        </form>

        <!-- Разделитель -->
        <div class="auth-divider">или войти через</div>

        <!-- Социальные сети -->
        <div class="social-auth">
            <button class="social-btn google">
                <img src="google-icon.svg"> Google
            </button>
            <button class="social-btn vk">
                <img src="vk-icon.svg"> ВКонтакте
            </button>
        </div>
    </div>
</div>
```

#### 2. Профиль пользователя (в header)
```html
<div class="user-profile">
    <img src="avatar.jpg" class="user-avatar">
    <div class="user-info">
        <span class="user-name">Иван Иванов</span>
        <span class="user-status">Free</span> <!-- или Premium -->
    </div>
    <div class="user-menu">
        <a href="#profile">Профиль</a>
        <a href="#history">История</a>
        <a href="#upgrade">Upgrade to Premium</a>
        <a href="#logout">Выход</a>
    </div>
</div>
```

#### 3. Баннер лимита
```html
<div class="limit-banner" v-if="!isPremium && remainingGenerations <= 1">
    ⚠️ Осталось генераций сегодня: {{ remainingGenerations }}/3
    <button onclick="showUpgradeModal()">Перейти на Premium</button>
</div>
```

---

## 💎 Этап 4: Premium Функции

### Бесплатный тариф (Free)
- ✅ 3 генерации в день
- ✅ Стандартное качество
- ✅ Водяной знак на результате
- ❌ Без истории
- ❌ Без скачивания в HD

### Premium тариф ($4.99/мес)
- ✅ Безлимитные генерации
- ✅ HD качество
- ✅ Без водяных знаков
- ✅ История всех генераций
- ✅ Приоритетная обработка
- ✅ Скачивание результатов

### Проверка лимитов в коде
```python
# backend/auth.py
def check_daily_limit(user_id):
    # Premium пользователи - безлимит
    if is_premium_user(user_id):
        return True, -1  # -1 означает безлимит

    # Бесплатные пользователи - 3 в день
    today = datetime.now().date()
    limit = db.query(
        "SELECT generations_count FROM daily_limits WHERE user_id = ? AND date = ?",
        [user_id, today]
    )

    if not limit:
        return True, 3  # Первая генерация

    if limit[0] >= 3:
        return False, 0  # Лимит исчерпан

    return True, 3 - limit[0]  # Осталось генераций
```

---

## 🔒 Этап 5: Безопасность

### JWT Токены
```python
import jwt
from datetime import datetime, timedelta

SECRET_KEY = os.getenv('JWT_SECRET_KEY')

def generate_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

def verify_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload['user_id']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
```

### Защита паролей
```python
from werkzeug.security import generate_password_hash, check_password_hash

# При регистрации
password_hash = generate_password_hash(password, method='pbkdf2:sha256')

# При входе
is_valid = check_password_hash(stored_hash, entered_password)
```

### Middleware для защиты endpoints
```python
from functools import wraps

def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        user_id = verify_token(token)

        if not user_id:
            return jsonify({'error': 'Unauthorized'}), 401

        request.user_id = user_id
        return f(*args, **kwargs)

    return decorated_function

# Использование
@app.route('/api/tryon', methods=['POST'])
@require_auth
def tryon():
    user_id = request.user_id
    # Проверить лимит
    can_generate, remaining = check_daily_limit(user_id)
    if not can_generate:
        return jsonify({'error': 'Daily limit exceeded'}), 403
    # ...
```

---

## 🌐 Этап 6: Google OAuth Setup

### 1. Получить credentials
1. Перейти в [Google Cloud Console](https://console.cloud.google.com/)
2. Создать новый проект "Virtual Try-On"
3. Включить Google+ API
4. Создать OAuth 2.0 credentials
5. Добавить redirect URI: `https://taptolook.net/api/auth/google/callback`

### 2. Установить библиотеки
```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2
```

### 3. Реализация
```python
from google.oauth2 import id_token
from google.auth.transport import requests

@app.route('/api/auth/google')
def google_login():
    # Создать authorization URL
    flow = Flow.from_client_secrets_file(
        'client_secret.json',
        scopes=['openid', 'email', 'profile'],
        redirect_uri=url_for('google_callback', _external=True)
    )
    authorization_url, state = flow.authorization_url()
    session['state'] = state
    return redirect(authorization_url)

@app.route('/api/auth/google/callback')
def google_callback():
    flow = Flow.from_client_secrets_file(
        'client_secret.json',
        scopes=['openid', 'email', 'profile'],
        state=session['state'],
        redirect_uri=url_for('google_callback', _external=True)
    )
    flow.fetch_token(authorization_response=request.url)

    credentials = flow.credentials
    id_info = id_token.verify_oauth2_token(
        credentials.id_token,
        requests.Request(),
        GOOGLE_CLIENT_ID
    )

    # Создать или найти пользователя
    user = find_or_create_user(
        email=id_info['email'],
        full_name=id_info['name'],
        avatar_url=id_info['picture'],
        provider='google',
        provider_id=id_info['sub']
    )

    # Сгенерировать JWT токен
    token = generate_token(user.id)

    # Редирект на фронтенд с токеном
    return redirect(f'https://taptolook.net/?token={token}')
```

---

## 📱 Этап 7: Frontend JavaScript

### auth.js
```javascript
class AuthManager {
    constructor() {
        this.token = localStorage.getItem('auth_token');
        this.user = null;
    }

    async login(email, password) {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({email, password})
        });

        const data = await response.json();
        if (data.success) {
            this.token = data.token;
            this.user = data.user;
            localStorage.setItem('auth_token', this.token);
            this.updateUI();
        }
        return data;
    }

    async register(email, password, fullName) {
        const response = await fetch('/api/auth/register', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({email, password, full_name: fullName})
        });

        const data = await response.json();
        if (data.success) {
            this.token = data.token;
            this.user = data.user;
            localStorage.setItem('auth_token', this.token);
            this.updateUI();
        }
        return data;
    }

    async checkAuth() {
        if (!this.token) return false;

        const response = await fetch('/api/auth/me', {
            headers: {'Authorization': `Bearer ${this.token}`}
        });

        if (response.ok) {
            const data = await response.json();
            this.user = data.user;
            this.updateUI();
            return true;
        }

        this.logout();
        return false;
    }

    async checkLimit() {
        const response = await fetch('/api/auth/check-limit', {
            headers: {'Authorization': `Bearer ${this.token}`}
        });

        return await response.json();
    }

    logout() {
        this.token = null;
        this.user = null;
        localStorage.removeItem('auth_token');
        this.updateUI();
    }

    updateUI() {
        if (this.user) {
            document.getElementById('authButton').style.display = 'none';
            document.getElementById('userProfile').style.display = 'block';
            document.getElementById('userName').textContent = this.user.full_name;
            document.getElementById('userStatus').textContent = this.user.is_premium ? 'Premium' : 'Free';
        } else {
            document.getElementById('authButton').style.display = 'block';
            document.getElementById('userProfile').style.display = 'none';
        }
    }

    googleLogin() {
        window.location.href = '/api/auth/google';
    }
}

// Инициализация
const auth = new AuthManager();
auth.checkAuth();

// Перехватить генерацию
async function handleTryOn() {
    // Проверить авторизацию
    if (!auth.user) {
        showAuthModal();
        return;
    }

    // Проверить лимит
    const limit = await auth.checkLimit();
    if (!limit.can_generate) {
        showUpgradeModal('Вы исчерпали дневной лимит генераций. Перейдите на Premium для безлимитного доступа!');
        return;
    }

    // Показать оставшиеся генерации
    if (!auth.user.is_premium && limit.remaining <= 1) {
        showLimitWarning(`Осталось генераций сегодня: ${limit.remaining}`);
    }

    // Продолжить с генерацией...
    // (существующий код)
}
```

---

## 🎯 Приоритеты Реализации

### Фаза 1: MVP (1-2 дня)
1. ✅ Создать таблицы БД
2. ✅ Реализовать Email регистрацию/вход
3. ✅ JWT токены
4. ✅ Базовый UI авторизации
5. ✅ Проверка лимитов (3 в день для Free)

### Фаза 2: OAuth (1 день)
6. ✅ Google OAuth
7. ✅ UI для соц. входа

### Фаза 3: Premium (1 день)
8. ✅ Система Premium подписок
9. ✅ Различие функционала Free vs Premium
10. ✅ UI для Upgrade

---

## 🔧 Необходимые переменные окружения

```env
# JWT
JWT_SECRET_KEY=your_super_secret_key_here

# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# Database
DATABASE_URL=postgresql://user:pass@host:5432/dbname
```

---

## 📝 Следующие шаги

1. Создать миграции БД
2. Реализовать backend endpoints
3. Создать UI компоненты
4. Настроить Google OAuth
5. Тестирование
6. Деплой на Railway

Вы готовы начать? С какого этапа начнем?
