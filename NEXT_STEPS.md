# 🚀 Следующие Шаги для Завершения Авторизации

## ✅ УЖЕ СОЗДАНО:

1. ✅ SQL миграция (`backend/migrations/001_create_auth_tables.sql`)
2. ✅ Backend auth модуль (`backend/auth.py`)
3. ✅ Frontend auth JavaScript (`frontend/auth.js`)
4. ✅ Обновлен `requirements.txt` с PyJWT и Google Auth

---

## 📝 ЧТО ОСТАЛОСЬ СДЕЛАТЬ:

### 1. Применить SQL миграцию к БД

Подключитесь к PostgreSQL и выполните:
```bash
psql $DATABASE_URL -f backend/migrations/001_create_auth_tables.sql
```

### 2. Добавить Auth Endpoints в `backend/app.py`

В начале файла добавьте импорты:
```python
from auth import AuthManager, create_auth_decorator
import psycopg2
```

После инициализации Flask добавьте:
```python
# Database connection
db = psycopg2.connect(os.getenv('DATABASE_URL'))

# Auth manager
auth_manager = AuthManager(db)
require_auth = create_auth_decorator(auth_manager)
```

Добавьте endpoints (ПОЛНЫЙ КОД в AUTH_SETUP_INSTRUCTIONS.md, раздел 3)

### 3. Добавить UI в `frontend/index.html`

Найдите `.top-bar-right` и замените на:
```html
<div class="top-bar-right">
    <!-- Auth Button (для неавторизованных) -->
    <button id="authButton" class="auth-btn" onclick="showAuthModal()">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="2"/>
            <circle cx="12" cy="7" r="4" stroke="currentColor" stroke-width="2"/>
        </svg>
        Войти
    </button>

    <!-- User Profile (для авторизованных) -->
    <div id="userProfile" class="user-profile" style="display: none;">
        <img id="userAvatar" src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='32' height='32'%3E%3Ccircle cx='16' cy='16' r='16' fill='%23ec4899'/%3E%3C/svg%3E" class="user-avatar" alt="User">
        <div class="user-info">
            <span id="userName" class="user-name">User</span>
            <span id="userStatus" class="user-status-badge free">Free</span>
        </div>
        <button class="logout-btn" onclick="handleLogout()" title="Выход">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9" stroke="currentColor" stroke-width="2"/>
            </svg>
        </button>
    </div>

    <a href="changelog.html" class="top-bar-changelog-link">📜 История</a>
</div>
```

Перед закрывающим `</body>` добавьте:
```html
<!-- Limit Banner -->
<div id="limitBanner" class="limit-banner" style="display: none;">
    <span id="limitText"></span>
    <button onclick="showUpgradeModal()">Upgrade to Premium</button>
</div>

<!-- Auth Modal -->
<div id="authModal" class="auth-modal" style="display: none;">
    <div class="auth-modal-overlay" onclick="closeAuthModal()"></div>
    <div class="auth-modal-content">
        <button class="auth-modal-close" onclick="closeAuthModal()">&times;</button>

        <h2 class="auth-modal-title">Вход в аккаунт</h2>

        <div class="auth-tabs">
            <button class="auth-tab active" onclick="switchAuthTab('login')">Вход</button>
            <button class="auth-tab" onclick="switchAuthTab('register')">Регистрация</button>
        </div>

        <!-- Login Form -->
        <form id="loginForm" class="auth-form" onsubmit="handleLogin(event)">
            <div class="form-group">
                <input type="email" id="loginEmail" class="form-input" placeholder="Email" required>
            </div>
            <div class="form-group">
                <input type="password" id="loginPassword" class="form-input" placeholder="Пароль" required>
            </div>
            <button type="submit" class="auth-submit-btn">Войти</button>
            <div class="auth-error" id="loginError"></div>
        </form>

        <!-- Register Form -->
        <form id="registerForm" class="auth-form" style="display: none;" onsubmit="handleRegister(event)">
            <div class="form-group">
                <input type="text" id="registerName" class="form-input" placeholder="Имя" required>
            </div>
            <div class="form-group">
                <input type="email" id="registerEmail" class="form-input" placeholder="Email" required>
            </div>
            <div class="form-group">
                <input type="password" id="registerPassword" class="form-input" placeholder="Пароль (мин. 6 символов)" required>
            </div>
            <button type="submit" class="auth-submit-btn">Зарегистрироваться</button>
            <div class="auth-error" id="registerError"></div>
        </form>

        <div class="auth-divider">или войти через</div>

        <div class="social-auth">
            <button class="social-btn google-btn" onclick="googleLogin()">
                <svg width="18" height="18" viewBox="0 0 18 18">
                    <path fill="#4285F4" d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844c-.209 1.125-.843 2.078-1.796 2.717v2.258h2.908c1.702-1.567 2.684-3.874 2.684-6.615z"/>
                    <path fill="#34A853" d="M9.003 18c2.43 0 4.467-.806 5.956-2.184l-2.908-2.258c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.96v2.332C2.438 15.983 5.482 18 9.003 18z"/>
                    <path fill="#FBBC05" d="M3.964 10.71c-.18-.54-.282-1.117-.282-1.71s.102-1.17.282-1.71V4.958H.957C.347 6.173 0 7.548 0 9s.348 2.827.957 4.042l3.007-2.332z"/>
                    <path fill="#EA4335" d="M9.003 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.464.891 11.428 0 9.003 0 5.482 0 2.438 2.017.96 4.958L3.967 7.29c.708-2.127 2.692-3.71 5.036-3.71z"/>
                </svg>
                Google
            </button>
        </div>
    </div>
</div>

<script src="auth.js"></script>
```

### 4. Добавить CSS стили в `frontend/style.css`

В конец файла добавьте:

```css
/* ============================================================
   AUTH STYLES
   ============================================================ */

/* Auth Button */
.auth-btn {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 8px 16px;
    background: linear-gradient(135deg, #ec4899 0%, #a855f7 100%);
    color: white;
    border: none;
    border-radius: 12px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
}

.auth-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(236, 72, 153, 0.4);
}

/* User Profile */
.user-profile {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 8px 12px;
    background: rgba(255, 255, 255, 0.5);
    backdrop-filter: blur(10px);
    border-radius: 50px;
}

.user-avatar {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    object-fit: cover;
}

.user-info {
    display: flex;
    flex-direction: column;
    gap: 2px;
}

.user-name {
    font-size: 0.875rem;
    font-weight: 600;
    color: var(--slate-800);
}

.user-status-badge {
    font-size: 0.75rem;
    padding: 2px 8px;
    border-radius: 6px;
    font-weight: 600;
}

.user-status-badge.free {
    background: rgba(100, 116, 139, 0.1);
    color: var(--slate-600);
}

.user-status-badge.premium {
    background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
    color: white;
}

.logout-btn {
    background: none;
    border: none;
    color: var(--slate-600);
    cursor: pointer;
    padding: 4px;
    display: flex;
    align-items: center;
}

.logout-btn:hover {
    color: var(--slate-800);
}

/* Limit Banner */
.limit-banner {
    position: fixed;
    bottom: 20px;
    left: 50%;
    transform: translateX(-50%);
    background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
    color: white;
    padding: 12px 24px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    gap: 16px;
    box-shadow: 0 8px 32px rgba(251, 191, 36, 0.4);
    z-index: 1000;
}

.limit-banner button {
    background: white;
    color: #f59e0b;
    border: none;
    padding: 6px 12px;
    border-radius: 6px;
    font-weight: 600;
    cursor: pointer;
}

/* Auth Modal */
.auth-modal {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: 10000;
    display: flex;
    align-items: center;
    justify-content: center;
}

.auth-modal-overlay {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(8px);
}

.auth-modal-content {
    position: relative;
    background: white;
    border-radius: 24px;
    padding: 40px;
    max-width: 440px;
    width: 90%;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
    z-index: 1;
}

.auth-modal-close {
    position: absolute;
    top: 16px;
    right: 16px;
    background: none;
    border: none;
    font-size: 28px;
    color: var(--slate-400);
    cursor: pointer;
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.auth-modal-title {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--slate-800);
    margin-bottom: 24px;
    text-align: center;
}

.auth-tabs {
    display: flex;
    gap: 8px;
    margin-bottom: 24px;
    background: rgba(0, 0, 0, 0.05);
    padding: 4px;
    border-radius: 12px;
}

.auth-tab {
    flex: 1;
    padding: 8px 16px;
    border: none;
    background: none;
    border-radius: 8px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
}

.auth-tab.active {
    background: white;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.auth-form {
    display: flex;
    flex-direction: column;
    gap: 16px;
}

.form-group {
    display: flex;
    flex-direction: column;
}

.form-input {
    padding: 12px 16px;
    border: 1px solid rgba(0, 0, 0, 0.1);
    border-radius: 12px;
    font-size: 1rem;
    transition: all 0.2s ease;
}

.form-input:focus {
    outline: none;
    border-color: #ec4899;
    box-shadow: 0 0 0 3px rgba(236, 72, 153, 0.1);
}

.auth-submit-btn {
    padding: 14px;
    background: linear-gradient(135deg, #ec4899 0%, #a855f7 100%);
    color: white;
    border: none;
    border-radius: 12px;
    font-weight: 600;
    font-size: 1rem;
    cursor: pointer;
    transition: all 0.3s ease;
}

.auth-submit-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(236, 72, 153, 0.3);
}

.auth-error {
    color: #dc2626;
    font-size: 0.875rem;
    min-height: 20px;
}

.auth-divider {
    text-align: center;
    color: var(--slate-400);
    font-size: 0.875rem;
    margin: 20px 0;
    position: relative;
}

.auth-divider::before,
.auth-divider::after {
    content: '';
    position: absolute;
    top: 50%;
    width: 40%;
    height: 1px;
    background: rgba(0, 0, 0, 0.1);
}

.auth-divider::before {
    left: 0;
}

.auth-divider::after {
    right: 0;
}

.social-auth {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.social-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
    padding: 12px;
    border: 1px solid rgba(0, 0, 0, 0.1);
    border-radius: 12px;
    background: white;
    cursor: pointer;
    font-weight: 600;
    transition: all 0.2s ease;
}

.social-btn:hover {
    background: rgba(0, 0, 0, 0.02);
    border-color: rgba(0, 0, 0, 0.2);
}

@media (max-width: 768px) {
    .auth-modal-content {
        padding: 24px;
    }

    .user-profile {
        padding: 6px 10px;
        gap: 8px;
    }

    .user-avatar {
        width: 28px;
        height: 28px;
    }

    .user-name {
        font-size: 0.8125rem;
    }
}
```

### 5. Обновить `handleTryOn()` в `app.js`

В начало функции добавьте:
```javascript
async function handleTryOn() {
    // Проверить авторизацию
    if (!auth.user) {
        showAuthModal();
        return;
    }

    // Проверить лимит
    const limit = await auth.checkLimit();
    if (!limit.can_generate) {
        showUpgradeModal('Вы исчерпали дневной лимит генераций (3/день). Перейдите на Premium для безлимитного доступа!');
        return;
    }

    // Обновить индикатор лимита
    auth.updateLimitIndicator();

    // Продолжить с существующим кодом...
```

### 6. Добавить переменную окружения в Railway

В настройках Railway добавьте:
```
JWT_SECRET_KEY=your_super_secret_key_change_this_in_production_use_random_64_chars
```

---

## 🎯 Порядок действий:

1. Применить SQL миграцию ✅
2. Обновить backend/app.py с auth endpoints ✅
3. Добавить HTML в index.html ✅
4. Добавить CSS в style.css ✅
5. Обновить app.js (handleTryOn) ✅
6. Установить зависимости: `pip install -r requirements.txt` ✅
7. Добавить JWT_SECRET_KEY в Railway ✅
8. Деплой и тестирование ✅

ВЕСЬ ПОЛНЫЙ КОД для шагов 2-5 находится в этом файле и в AUTH_IMPLEMENTATION_PLAN.md!
