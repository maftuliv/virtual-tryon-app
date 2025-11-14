/**
 * Authentication Manager
 * Handles user authentication, token management, and premium features
 */

class AuthManager {
    constructor() {
        this.token = localStorage.getItem('auth_token');
        this.user = null;
        this.API_URL = window.location.hostname === 'localhost'
            ? 'http://localhost:5000'
            : '';
    }

    // ============================================================
    // Authentication Methods
    // ============================================================

    async register(email, password, fullName) {
        try {
            const response = await fetch(`${this.API_URL}/api/auth/register`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    email: email,
                    password: password,
                    full_name: fullName
                })
            });

            const data = await response.json();

            if (data.success) {
                this.token = data.token;
                this.user = data.user;
                localStorage.setItem('auth_token', this.token);
                this.updateUI();
                closeAuthModal();
                this.showSuccess('Регистрация успешна!');
            } else {
                this.showError(data.error || 'Ошибка регистрации');
            }

            return data;
        } catch (error) {
            console.error('Register error:', error);
            this.showError('Ошибка соединения с сервером');
            return {success: false, error: error.message};
        }
    }

    async login(email, password) {
        try {
            const response = await fetch(`${this.API_URL}/api/auth/login`, {
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
                closeAuthModal();
                this.showSuccess(`Добро пожаловать, ${this.user.full_name}!`);
            } else {
                this.showError(data.error || 'Неверный email или пароль');
            }

            return data;
        } catch (error) {
            console.error('Login error:', error);
            this.showError('Ошибка соединения с сервером');
            return {success: false, error: error.message};
        }
    }

    async checkAuth() {
        if (!this.token) {
            this.updateUI();
            return false;
        }

        try {
            const response = await fetch(`${this.API_URL}/api/auth/me`, {
                headers: {'Authorization': `Bearer ${this.token}`}
            });

            if (response.ok) {
                const data = await response.json();
                this.user = data.user;
                this.updateUI();
                return true;
            } else {
                this.logout();
                return false;
            }
        } catch (error) {
            console.error('Check auth error:', error);
            this.logout();
            return false;
        }
    }

    logout() {
        this.token = null;
        this.user = null;
        localStorage.removeItem('auth_token');
        this.updateUI();
        this.showSuccess('Вы вышли из системы');
    }

    // ============================================================
    // Limit Checking
    // ============================================================

    async checkLimit() {
        if (!this.token) {
            return {can_generate: false, remaining: 0, limit: 3, requiresAuth: true};
        }

        try {
            const response = await fetch(`${this.API_URL}/api/auth/check-limit`, {
                headers: {'Authorization': `Bearer ${this.token}`}
            });

            if (response.ok) {
                return await response.json();
            }

            return {can_generate: false, remaining: 0, limit: 3};
        } catch (error) {
            console.error('Check limit error:', error);
            return {can_generate: false, remaining: 0, limit: 3};
        }
    }

    // ============================================================
    // UI Updates
    // ============================================================

    updateUI() {
        const authButton = document.getElementById('authButton');
        const userProfile = document.getElementById('userProfile');
        const userName = document.getElementById('userName');
        const userStatus = document.getElementById('userStatus');
        const userAvatar = document.getElementById('userAvatar');

        if (this.user) {
            // Show user profile
            if (authButton) authButton.style.display = 'none';
            if (userProfile) userProfile.style.display = 'flex';
            if (userName) userName.textContent = this.user.full_name;

            if (userStatus) {
                if (this.user.is_premium) {
                    userStatus.textContent = '✨ Premium';
                    userStatus.className = 'user-status-badge premium';
                } else {
                    userStatus.textContent = 'Free';
                    userStatus.className = 'user-status-badge free';
                }
            }

            if (userAvatar && this.user.avatar_url) {
                userAvatar.src = this.user.avatar_url;
            }

            // Update limit indicator
            this.updateLimitIndicator();

            // Show admin link if user is admin
            const adminLink = document.getElementById('adminLink');
            if (adminLink) {
                adminLink.style.display = this.user.role === 'admin' ? 'inline-flex' : 'none';
            }

            // Hide auth required banner when logged in
            const authBanner = document.getElementById('authRequiredBanner');
            if (authBanner) {
                authBanner.style.display = 'none';
            }
        } else {
            // Show auth button
            if (authButton) authButton.style.display = 'inline-flex';
            if (userProfile) userProfile.style.display = 'none';

            // Hide admin link
            const adminLink = document.getElementById('adminLink');
            if (adminLink) adminLink.style.display = 'none';
        }
    }

    async updateLimitIndicator() {
        const userLimitBadge = document.getElementById('userLimit');

        if (!this.user || this.user.is_premium) {
            // Hide limit indicator for premium users
            const limitBanner = document.getElementById('limitBanner');
            if (limitBanner) limitBanner.style.display = 'none';
            if (userLimitBadge) userLimitBadge.style.display = 'none';
            return;
        }

        const limit = await this.checkLimit();
        const limitBanner = document.getElementById('limitBanner');
        const limitText = document.getElementById('limitText');

        // Update user profile limit badge
        if (userLimitBadge && limit.remaining !== undefined) {
            userLimitBadge.textContent = `${limit.remaining}/${limit.limit}`;
            userLimitBadge.style.display = 'inline-block';

            // Change color based on remaining count
            if (limit.remaining === 0) {
                // No generations left (0/3) - red
                userLimitBadge.style.background = 'rgba(220, 38, 38, 0.1)';
                userLimitBadge.style.color = '#dc2626';
            } else if (limit.remaining <= 1) {
                // Low on generations (1/3) - yellow
                userLimitBadge.style.background = 'rgba(251, 191, 36, 0.1)';
                userLimitBadge.style.color = '#f59e0b';
            } else {
                // Plenty left (2/3, 3/3) - pink
                userLimitBadge.style.background = 'rgba(236, 72, 153, 0.1)';
                userLimitBadge.style.color = '#ec4899';
            }
        }

        // Show warning banner when limit is low
        if (limitBanner && limitText) {
            if (limit.remaining !== undefined && limit.remaining >= 0 && limit.remaining <= 1) {
                limitBanner.style.display = 'flex';
                limitText.textContent = `⚠️ Осталось генераций сегодня: ${limit.remaining}/${limit.limit}`;
            } else {
                limitBanner.style.display = 'none';
            }
        }
    }

    showSuccess(message) {
        // TODO: Replace with your notification system
        alert(message);
    }

    showError(message) {
        // TODO: Replace with your notification system
        alert('Ошибка: ' + message);
    }

    // ============================================================
    // Google OAuth
    // ============================================================

    googleLogin() {
        window.location.href = `${this.API_URL}/api/auth/google`;
    }
}

// Initialize auth manager
const auth = new AuthManager();

// Check authentication on page load
document.addEventListener('DOMContentLoaded', () => {
    auth.checkAuth();

    // Check for token in URL (from OAuth callback)
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('token');
    if (token) {
        auth.token = token;
        localStorage.setItem('auth_token', token);
        auth.checkAuth();
        // Remove token from URL
        window.history.replaceState({}, document.title, window.location.pathname);
    }
});

// ============================================================
// Modal Functions
// ============================================================

function showAuthModal() {
    const modal = document.getElementById('authModal');
    if (modal) {
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }
}

function closeAuthModal() {
    const modal = document.getElementById('authModal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = '';
    }

    // Clear form errors
    const errors = document.querySelectorAll('.auth-error');
    errors.forEach(error => error.textContent = '');

    // Re-enable generate button if it was disabled
    const generateSwitch = document.querySelector('.cta-button');
    if (generateSwitch) {
        generateSwitch.disabled = false;
    }
}

function switchAuthTab(tab) {
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    const tabs = document.querySelectorAll('.auth-tab');

    tabs.forEach(t => t.classList.remove('active'));

    if (tab === 'login') {
        loginForm.style.display = 'block';
        registerForm.style.display = 'none';
        tabs[0].classList.add('active');
    } else {
        loginForm.style.display = 'none';
        registerForm.style.display = 'block';
        tabs[1].classList.add('active');
    }
}

// ============================================================
// Form Handlers
// ============================================================

async function handleLogin(event) {
    event.preventDefault();

    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;
    const errorEl = document.getElementById('loginError');

    errorEl.textContent = '';

    const result = await auth.login(email, password);

    if (!result.success && result.error) {
        errorEl.textContent = result.error;
    }
}

async function handleRegister(event) {
    event.preventDefault();

    const name = document.getElementById('registerName').value;
    const email = document.getElementById('registerEmail').value;
    const password = document.getElementById('registerPassword').value;
    const errorEl = document.getElementById('registerError');

    errorEl.textContent = '';

    if (password.length < 6) {
        errorEl.textContent = 'Пароль должен быть минимум 6 символов';
        return;
    }

    const result = await auth.register(email, password, name);

    if (!result.success && result.error) {
        errorEl.textContent = result.error;
    }
}

function googleLogin() {
    auth.googleLogin();
}

function handleLogout() {
    console.log('[LOGOUT] Logout button clicked');
    try {
        if (confirm('Вы уверены, что хотите выйти?')) {
            console.log('[LOGOUT] User confirmed logout');
            auth.logout();
        } else {
            console.log('[LOGOUT] User cancelled logout');
        }
    } catch (error) {
        console.error('[LOGOUT] Error during logout:', error);
        // Fallback - logout without confirmation
        auth.logout();
    }
}

// ============================================================
// Premium/Upgrade Functions
// ============================================================

function showUpgradeModal(message) {
    alert(message || 'Перейдите на Premium для безлимитного доступа!');
    // TODO: Create proper upgrade modal with pricing
}
