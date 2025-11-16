# Authentication & Admin Panel Best Practices

## 🎯 Основные принципы

### Безопасность превыше всего
- Серверная проверка роли ПЕРЕД отдачей HTML
- HTTP-only cookies для защиты от XSS
- Двойная проверка токенов (header + cookie)
- Audit logging всех административных действий

---

## 🔐 Cookie-Based Authentication

### Правильная настройка cookies

```python
# ✅ ПРАВИЛЬНО - условная настройка Secure
from flask import request

def set_auth_cookie(response, token):
    is_localhost = request.host.startswith("localhost") or request.host.startswith("127.0.0.1")

    response.set_cookie(
        "auth_token",
        value=token,
        max_age=7 * 24 * 60 * 60,  # 7 дней
        secure=not is_localhost,    # HTTPS только на production
        httponly=True,              # Защита от XSS
        samesite="Strict",          # Защита от CSRF
        path="/",
    )
    return response

# ❌ НЕПРАВИЛЬНО - всегда Secure=True
response.set_cookie("auth_token", value=token, secure=True)
# Блокирует cookies на localhost (HTTP)
```

### Очистка cookies при logout

```python
# ✅ ПРАВИЛЬНО
def clear_auth_cookie(response):
    response.delete_cookie("auth_token", path="/")
    return response

# Endpoint
@app.route("/api/auth/logout", methods=["POST"])
def logout():
    response = make_response(jsonify({"success": True}))
    clear_auth_cookie(response)
    return response
```

---

## 🌐 CORS для Credentials

### Правильная настройка CORS

```python
# ✅ ПРАВИЛЬНО - конкретные origins
from flask_cors import CORS

allowed_origins = [
    "http://localhost:5000",
    "http://127.0.0.1:5000",
    "https://taptolook.net",
    "https://www.taptolook.net",
]

CORS(app, resources={
    r"/*": {
        "origins": allowed_origins,              # НЕ "*"
        "methods": ["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True,            # Разрешить cookies
    }
})

# ❌ НЕПРАВИЛЬНО - wildcard с credentials
CORS(app, resources={
    r"/*": {
        "origins": "*",                          # Конфликт!
        "supports_credentials": True,            # Не будет работать
    }
})
```

**Почему:**
- `supports_credentials=True` требует явных origins
- Браузеры блокируют `*` + credentials по соображениям безопасности

---

## 🎨 Frontend: Fetch с Credentials

### Правильные запросы к API

```javascript
// ✅ ПРАВИЛЬНО - включаем credentials
async apiCall(endpoint, options = {}) {
    const token = localStorage.getItem('auth_token');

    const response = await fetch(`/api${endpoint}`, {
        ...options,
        credentials: 'include',  // КРИТИЧНО! Отправляет cookies
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
            ...options.headers,
        },
    });

    return response.json();
}

// ❌ НЕПРАВИЛЬНО - без credentials
const response = await fetch('/api/admin/users', {
    headers: {'Authorization': `Bearer ${token}`}
});
// Cookies НЕ отправляются!
```

### Logout на клиенте

```javascript
// ✅ ПРАВИЛЬНО - вызов сервера для очистки cookie
async logout() {
    try {
        await fetch('/api/auth/logout', {
            method: 'POST',
            credentials: 'include',  // Важно!
        });
    } catch (error) {
        console.error('Logout error:', error);
    }

    // Очистка локального состояния
    this.token = null;
    this.user = null;
    localStorage.removeItem('auth_token');
}

// ❌ НЕПРАВИЛЬНО - только локальная очистка
logout() {
    localStorage.removeItem('auth_token');
    // Cookie остаётся в браузере!
}
```

---

## 🛡️ Защита Admin Routes

### Server-Side Protection (HTML)

```python
# ✅ ПРАВИЛЬНО - проверка роли перед отдачей HTML
from backend.auth import require_admin_page

@app.route("/admin")
@require_admin_page
def serve_admin(current_user):
    """
    Серверная проверка: только admin может получить HTML.
    Неавторизованные → редирект на /.
    """
    response = send_from_directory("frontend", "admin.html")
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Robots-Tag"] = "noindex, nofollow"
    return response

# ❌ НЕПРАВИЛЬНО - публичный доступ к HTML
@app.route("/admin")
def serve_admin():
    return send_from_directory("frontend", "admin.html")
    # Любой может скачать HTML!
```

### API Protection

```python
# ✅ ПРАВИЛЬНО - проверка токена из header ИЛИ cookie
from backend.auth import require_admin

@app.route("/api/admin/users")
@require_admin
def get_users(current_user):
    """
    Декоратор проверяет:
    1. Authorization: Bearer <token>
    2. Cookie: auth_token=<token>

    Принимает любой валидный источник.
    """
    return jsonify({"users": [...]})

# ❌ НЕПРАВИЛЬНО - проверка только header
@app.route("/api/admin/users")
def get_users():
    token = request.headers.get("Authorization")
    # Игнорирует cookie!
```

---

## 🔧 Декораторы для Auth

### require_admin_page (для HTML)

```python
def require_admin_page(f):
    """
    Для страниц (HTML). Редиректит неавторизованных.
    Используется на /admin.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get("auth_token")

        if not token:
            return redirect("/")

        user = decode_token(token, require_admin=True)
        if not user:
            return redirect("/")

        return f(current_user=user, *args, **kwargs)

    return decorated
```

### require_admin (для API)

```python
def require_admin(f):
    """
    Для API endpoints. Возвращает JSON 401/403.
    Проверяет header ИЛИ cookie.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_token_from_request()  # Проверяет оба источника

        if not token:
            return jsonify({"error": "No token"}), 401

        user = decode_token(token, require_admin=True)
        if not user:
            return jsonify({"error": "Access denied"}), 403

        return f(current_user=user, *args, **kwargs)

    return decorated
```

### get_token_from_request (утилита)

```python
def get_token_from_request():
    """
    Извлекает токен из Authorization header ИЛИ cookie.
    Возвращает первый найденный.
    """
    # Приоритет: header
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header.replace("Bearer ", "").strip()

    # Fallback: cookie
    token = request.cookies.get("auth_token")
    if token:
        return token.strip()

    return None
```

---

## 📝 Login/Register Flow

### Backend: Установка cookie

```python
@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json()
    user = auth_service.login(data["email"], data["password"])

    if not user:
        return jsonify({"error": "Invalid credentials"}), 401

    # Создать ответ с cookie
    response = make_response(
        jsonify({"success": True, "user": user}),
        200
    )
    set_auth_cookie(response, user["token"])

    return response
```

### Frontend: Обработка ответа

```javascript
async login(email, password) {
    const response = await fetch('/api/auth/login', {
        method: 'POST',
        credentials: 'include',  // Получить cookie
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({email, password})
    });

    const data = await response.json();

    if (data.success) {
        // Сервер установил cookie автоматически
        this.token = data.user.token;
        this.user = data.user;
        localStorage.setItem('auth_token', this.token);
    }
}
```

---

## 🔍 Google OAuth Flow

### Backend: Callback с cookie

```python
@app.route("/api/auth/google/callback")
def google_callback():
    # ... обмен code на токен, получение user_info ...

    result = google_auth_service.handle_callback(code, state)
    token = result["token"]
    user = result["user"]

    # Редирект с cookie
    fragment = urlencode({"google_auth_success": "1", "token": token})
    response = make_response(redirect(f"/#{fragment}"))
    set_auth_cookie(response, token)

    return response
```

### Frontend: Обработка callback

```javascript
handleGoogleCallback() {
    const params = new URLSearchParams(window.location.hash.substring(1));

    if (params.has('google_auth_success')) {
        const token = params.get('token');

        // Сервер УЖЕ установил cookie
        this.token = token;
        localStorage.setItem('auth_token', token);

        // Получить данные пользователя
        this.checkAuth();
    }
}
```

---

## 🧪 Testing Checklist

### Перед деплоем админ-панели:

- [ ] `/admin` без авторизации → редирект на `/`
- [ ] `/admin` с user token → редирект на `/`
- [ ] `/admin` с admin token → показывает панель
- [ ] API `/api/admin/*` без токена → 401
- [ ] API `/api/admin/*` с user token → 403
- [ ] API `/api/admin/*` с admin token → 200
- [ ] Logout очищает cookie → `/admin` редиректит
- [ ] Cookies работают на HTTPS (production)
- [ ] Cookies работают на HTTP (localhost)
- [ ] CORS разрешает credentials
- [ ] `fetch()` включает `credentials: 'include'`

### После деплоя на production:

- [ ] Очистить cookies в браузере
- [ ] Войти через Google OAuth
- [ ] Проверить наличие cookie `auth_token` (F12 → Application)
- [ ] Открыть `/admin` → должна загрузиться панель
- [ ] Проверить Network tab → requests содержат cookie
- [ ] Выйти из системы → cookie удалена
- [ ] Попытка открыть `/admin` → редирект на `/`

---

## 🚨 Типичные ошибки

### 1. Secure=True на localhost
**Проблема:** Браузер блокирует cookie на HTTP
```python
# ❌ НЕПРАВИЛЬНО
response.set_cookie("auth_token", secure=True)
# Не работает на localhost!

# ✅ ПРАВИЛЬНО
is_localhost = request.host.startswith("localhost")
response.set_cookie("auth_token", secure=not is_localhost)
```

### 2. CORS wildcard с credentials
**Проблема:** Браузер блокирует запросы
```python
# ❌ НЕПРАВИЛЬНО
CORS(app, origins="*", supports_credentials=True)

# ✅ ПРАВИЛЬНО
CORS(app, origins=["https://taptolook.net"], supports_credentials=True)
```

### 3. Забыли credentials: 'include'
**Проблема:** Cookies не отправляются с запросами
```javascript
// ❌ НЕПРАВИЛЬНО
fetch('/api/admin/users')

// ✅ ПРАВИЛЬНО
fetch('/api/admin/users', {credentials: 'include'})
```

### 4. Только клиентская проверка admin
**Проблема:** HTML доступен всем, легко обойти
```python
# ❌ НЕПРАВИЛЬНО
@app.route("/admin")
def serve_admin():
    return send_file("admin.html")  # Публично!

# ✅ ПРАВИЛЬНО
@app.route("/admin")
@require_admin_page
def serve_admin(current_user):
    return send_file("admin.html")  # Защищено!
```

---

## 📚 Примеры из кода

### Полная реализация

- `backend/auth.py` - декораторы и утилиты
  - `decode_token()` - валидация JWT
  - `get_token_from_request()` - извлечение токена
  - `set_auth_cookie()` - установка cookie
  - `clear_auth_cookie()` - очистка cookie
  - `@require_admin_page` - защита HTML
  - `@require_admin` - защита API

- `backend/api/auth.py` - auth endpoints
  - `/api/auth/login` - устанавливает cookie
  - `/api/auth/register` - устанавливает cookie
  - `/api/auth/logout` - очищает cookie

- `backend/api/google_auth.py` - OAuth endpoints
  - `/api/auth/google/callback` - устанавливает cookie

- `backend/api/static.py` - HTML routes
  - `/admin` - защищён `@require_admin_page`

- `frontend/auth.js` - клиентская авторизация
  - `login()` - использует `credentials: 'include'`
  - `logout()` - вызывает `/api/auth/logout`

- `frontend/admin.js` - админ панель
  - `apiCall()` - использует `credentials: 'include'`

---

## 🎯 Ключевые выводы

1. **HTTP-only cookies** - основа безопасности
2. **Двойная проверка** - header ИЛИ cookie для надёжности
3. **Серверная защита** - роль проверяется ПЕРЕД отдачей HTML
4. **CORS credentials** - требует явных origins (не `*`)
5. **credentials: 'include'** - обязательно во всех fetch()
6. **Условный Secure** - True на production, False на localhost
7. **Logout на сервере** - очистка cookie, не только localStorage

**Production First:** Всегда проектируем для production (HTTPS), добавляем localhost совместимость потом.
