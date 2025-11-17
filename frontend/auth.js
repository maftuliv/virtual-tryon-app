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

    getRequestUrl(path = '') {
        if (!path) {
            return this.API_URL;
        }
        if (path.startsWith('http://') || path.startsWith('https://')) {
            return path;
        }
        return `${this.API_URL}${path}`;
    }

    buildAuthHeaders(extraHeaders = {}, body = null) {
        const headers = {...extraHeaders};

        if (body && !(body instanceof FormData) && !headers['Content-Type']) {
            headers['Content-Type'] = 'application/json';
        }

        if (this.token && !headers['Authorization']) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }

        return headers;
    }

    async fetchWithAuth(path, options = {}) {
        const url = this.getRequestUrl(path);
        const config = {
            credentials: 'include',
            ...options,
        };

        const headers = this.buildAuthHeaders(config.headers || {}, config.body);

        if (Object.keys(headers).length > 0) {
            config.headers = headers;
        } else {
            delete config.headers;
        }

        return fetch(url, config);
    }

    async getAdminSessionUser() {
        try {
            const response = await this.fetchWithAuth('/api/auth/admin/session');
            if (!response.ok) {
                return null;
            }

            const data = await response.json();
            return data.user || null;
        } catch (error) {
            console.error('[ADMIN] Failed to fetch admin session info:', error);
            return null;
        }
    }

    // ============================================================
    // Authentication Methods
    // ============================================================

    async register(email, password, fullName) {
        try {
            const response = await this.fetchWithAuth('/api/auth/register', {
                method: 'POST',
                body: JSON.stringify({
                    email: email,
                    password: password,
                    full_name: fullName
                })
            });

            const data = await response.json();

            if (data.success) {
                // Server sets HTTP-only cookie automatically.
                // Backend returns JWT in top-level "token" field, not inside user object.
                const token = data.token;
                if (token) {
                    this.token = token;
                    localStorage.setItem('auth_token', this.token);
                } else {
                    console.warn('[AUTH] Register: token missing in response');
                }

                this.user = data.user;
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
            const response = await this.fetchWithAuth('/api/auth/login', {
                method: 'POST',
                body: JSON.stringify({email, password})
            });

            const data = await response.json();

            if (data.success) {
                // Server sets HTTP-only cookie automatically.
                // Backend returns JWT in top-level "token" field, not inside user object.
                const token = data.token;
                if (token) {
                    this.token = token;
                    localStorage.setItem('auth_token', this.token);
                } else {
                    console.warn('[AUTH] Login: token missing in response');
                }

                this.user = data.user;
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
        try {
            const response = await this.fetchWithAuth('/api/auth/me');

            if (response.ok) {
                const data = await response.json();
                this.user = data.user;
                this.updateUI();
                return true;
            }

            if (response.status === 401 || response.status === 403) {
                this.clearLocalSession(false);
            }
            return false;
        } catch (error) {
            console.error('Check auth error:', error);
            return false;
        }
    }

    async logout(showNotification = true) {
        try {
            // Call server logout endpoint to clear HTTP-only cookie
            await this.fetchWithAuth('/api/auth/logout', {
                method: 'POST',
            });
        } catch (error) {
            console.error('Logout API error:', error);
            // Continue with local logout even if server call fails
        }

        this.clearLocalSession(showNotification);
    }

    clearLocalSession(showNotification = true) {
        this.token = null;
        this.user = null;
        localStorage.removeItem('auth_token');
        this.updateUI();
        if (showNotification) {
            this.showSuccess('Вы вышли из системы');
        }
    }

    // ============================================================
    // Limit Checking
    // ============================================================

    async checkLimit() {
        if (!this.token) {
            return {can_generate: false, remaining: 0, limit: 3, requiresAuth: true};
        }

        try {
            const response = await this.fetchWithAuth('/api/auth/check-limit');

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

            // Hide free generations counter for logged users
            const freeCounter = document.getElementById('freeGenerationsCounter');
            if (freeCounter) {
                freeCounter.classList.add('hide');
            }

            // Show user generations counter
            const userGenCounter = document.getElementById('userGenerationsCounter');
            if (userGenCounter) {
                userGenCounter.style.display = 'block';
            }
        } else {
            // Show auth button
            if (authButton) authButton.style.display = 'inline-flex';
            if (userProfile) userProfile.style.display = 'none';

            // Hide admin link
            const adminLink = document.getElementById('adminLink');
            if (adminLink) adminLink.style.display = 'none';

            // Show free generations counter for guests
            const freeCounter = document.getElementById('freeGenerationsCounter');
            if (freeCounter) {
                freeCounter.classList.remove('hide');
                // Update counter data
                if (typeof updateFreeGenerationsIndicator === 'function') {
                    updateFreeGenerationsIndicator();
                }
            }

            // Hide user generations counter
            const userGenCounter = document.getElementById('userGenerationsCounter');
            if (userGenCounter) {
                userGenCounter.style.display = 'none';
            }
        }
    }

    async updateLimitIndicator() {
        const userLimitBadge = document.getElementById('userLimit');
        const userGenCounter = document.getElementById('userGenerationsCounter');
        const userGenRemaining = document.getElementById('userGenRemaining');
        const userGenTitle = document.getElementById('userGenTitle');
        const userGenIcon = document.getElementById('userGenIcon');
        const userGenProgressBar = document.getElementById('userGenProgressBar');

        if (!this.user) {
            // Hide limit indicators when not logged in
            const limitBanner = document.getElementById('limitBanner');
            if (limitBanner) limitBanner.style.display = 'none';
            if (userLimitBadge) userLimitBadge.style.display = 'none';
            if (userGenCounter) userGenCounter.style.display = 'none';
            return;
        }

        const limit = await this.checkLimit();

        // Determine user type by limit value from server (more reliable than local flags)
        // limit = -1 → Admin (unlimited)
        // limit = 50 → Premium (monthly)
        // limit = 3 → Free (weekly)

        // Update counters based on server-returned limit
        if (userGenCounter) {
            userGenCounter.style.display = 'inline-flex';
        }

        if (limit.limit === -1) {
            // Admin: unlimited generations
            if (userLimitBadge) {
                userLimitBadge.textContent = '∞';
                userLimitBadge.style.display = 'inline-block';
                userLimitBadge.style.background = 'rgba(139, 92, 246, 0.1)';
                userLimitBadge.style.color = '#8b5cf6';
            }
            if (userGenIcon) userGenIcon.textContent = '👑';
            if (userGenTitle) userGenTitle.textContent = '∞ примерок';
            if (userGenRemaining) userGenRemaining.textContent = '';
            if (userGenProgressBar) userGenProgressBar.style.width = '100%';
            return;
        } else if (limit.limit === 50) {
            // Premium user: 50 generations per month
            const word = this.getPluralForm(limit.remaining, 'примерка', 'примерки', 'примерок');
            if (userGenIcon) userGenIcon.textContent = '📦';
            if (userGenTitle) userGenTitle.textContent = `${limit.remaining} ${word}`;
            if (userGenRemaining) userGenRemaining.textContent = 'осталось в этом месяце';
            // Calculate progress percentage
            const progressPercent = (limit.remaining / limit.limit) * 100;
            if (userGenProgressBar) userGenProgressBar.style.width = `${progressPercent}%`;
        } else {
            // Free user: 3 generations per week (or any other limit)
            const word = this.getPluralForm(limit.remaining, 'примерка', 'примерки', 'примерок');
            if (userGenIcon) userGenIcon.textContent = '🎁';
            if (userGenTitle) userGenTitle.textContent = `${limit.remaining} ${word}`;
            if (userGenRemaining) userGenRemaining.textContent = 'осталось на этой неделе';
            // Calculate progress percentage
            const progressPercent = (limit.remaining / limit.limit) * 100;
            if (userGenProgressBar) userGenProgressBar.style.width = `${progressPercent}%`;
        }

        const limitBanner = document.getElementById('limitBanner');
        const limitText = document.getElementById('limitText');

        // Update user profile limit badge
        if (userLimitBadge && limit.remaining !== undefined) {
            userLimitBadge.textContent = `${limit.remaining}/${limit.limit}`;
            userLimitBadge.style.display = 'inline-block';

            // Change color based on remaining count
            if (limit.remaining === 0) {
                // No generations left - red
                userLimitBadge.style.background = 'rgba(220, 38, 38, 0.1)';
                userLimitBadge.style.color = '#dc2626';
            } else if (limit.remaining <= Math.ceil(limit.limit * 0.2)) {
                // Low on generations (less than 20%) - yellow
                userLimitBadge.style.background = 'rgba(251, 191, 36, 0.1)';
                userLimitBadge.style.color = '#f59e0b';
            } else {
                // Plenty left - pink
                userLimitBadge.style.background = 'rgba(236, 72, 153, 0.1)';
                userLimitBadge.style.color = '#ec4899';
            }
        }

        // Show warning banner when limit is low
        if (limitBanner && limitText) {
            if (limit.remaining !== undefined && limit.remaining >= 0 && limit.remaining <= Math.ceil(limit.limit * 0.1)) {
                limitBanner.style.display = 'flex';
                // Use limit value to determine period text (more reliable)
                const periodText = limit.limit === 50 ? 'в этом месяце' : 'на этой неделе';
                limitText.textContent = `⚠️ Осталось генераций ${periodText}: ${limit.remaining}/${limit.limit}`;
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
    // Helper Methods
    // ============================================================

    /**
     * Get correct Russian plural form for a number
     * @param {number} n - The number
     * @param {string} one - Form for 1 (примерка)
     * @param {string} few - Form for 2-4 (примерки)
     * @param {string} many - Form for 5+ (примерок)
     * @returns {string} The correct plural form
     */
    getPluralForm(n, one, few, many) {
        const abs = Math.abs(n);
        if (abs % 10 === 1 && abs % 100 !== 11) {
            return one;
        }
        if (abs % 10 >= 2 && abs % 10 <= 4 && (abs % 100 < 10 || abs % 100 >= 20)) {
            return few;
        }
        return many;
    }

    // ============================================================
    // Google OAuth
    // ============================================================

    /**
     * Check if Google OAuth is enabled on the server
     * Returns true if enabled, false otherwise
     */
    async checkGoogleOAuthStatus() {
        try {
            const response = await this.fetchWithAuth('/api/auth/google/status');

            if (!response.ok) {
                console.warn('[GOOGLE-AUTH] Status check failed, assuming OAuth disabled');
                return false;
            }

            const data = await response.json();
            console.log('[GOOGLE-AUTH] Status:', data);

            return data.enabled === true;

        } catch (error) {
            console.warn('[GOOGLE-AUTH] Status check error, assuming OAuth disabled:', error);
            return false;
        }
    }

    /**
     * Update Google Sign-In button visibility based on OAuth status
     */
    async updateGoogleButtonVisibility() {
        const googleButton = document.querySelector('.google-btn');
        const socialAuth = document.querySelector('.social-auth');

        if (!googleButton) {
            console.log('[GOOGLE-AUTH] Google button not found in DOM');
            return;
        }

        const isEnabled = await this.checkGoogleOAuthStatus();

        if (isEnabled) {
            console.log('[GOOGLE-AUTH] OAuth enabled, showing button');
            googleButton.style.display = 'flex';
            if (socialAuth) socialAuth.style.display = 'block';
        } else {
            console.log('[GOOGLE-AUTH] OAuth disabled, hiding button');
            googleButton.style.display = 'none';
            // Hide entire social auth section if no other buttons
            const otherButtons = socialAuth?.querySelectorAll('.social-btn:not(.google-btn)');
            if (socialAuth && (!otherButtons || otherButtons.length === 0)) {
                socialAuth.style.display = 'none';
            }
        }
    }

    async googleLogin() {
        try {
            console.log('[GOOGLE-AUTH] Initiating Google OAuth flow...');

            // Request authorization URL from backend
            const response = await this.fetchWithAuth('/api/auth/google/login', {
                method: 'GET',
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();

            if (!data.success || !data.authorization_url) {
                throw new Error(data.error || 'Не удалось получить ссылку для авторизации');
            }

            console.log('[GOOGLE-AUTH] Redirecting to Google...');
            // Redirect to Google authorization page
            window.location.href = data.authorization_url;

        } catch (error) {
            console.error('[GOOGLE-AUTH] Login initiation failed:', error);
            alert(`Ошибка входа через Google: ${error.message}`);
        }
    }

    /**
     * Handle Google OAuth callback (after redirect back from Google)
     */
    handleGoogleCallback() {
        const hash = window.location.hash.substring(1); // Remove '#'
        const params = new URLSearchParams(hash);

        // Check for success
        if (params.has('google_auth_success')) {
            const token = params.get('token');

            if (token) {
                console.log('[GOOGLE-AUTH] Callback successful, token received');

                // Save token to localStorage (same as login/register)
                this.token = token;
                localStorage.setItem('auth_token', this.token);

                // Clean URL
                window.location.hash = '';

                // Fetch user info and update UI
                this.checkAuth();

                // Show success message
                this.showNotification('Вход через Google выполнен успешно!', 'success');
            } else {
                console.error('[GOOGLE-AUTH] Callback successful but no token');
                this.showNotification('Ошибка: токен не получен', 'error');
            }
        }

        // Check for error
        else if (params.has('google_auth_error')) {
            const errorMessage = params.get('message') || 'Неизвестная ошибка';
            console.error('[GOOGLE-AUTH] Callback error:', errorMessage);

            // Clean URL
            window.location.hash = '';

            // Show error message
            this.showNotification(`Ошибка входа через Google: ${decodeURIComponent(errorMessage)}`, 'error');
        }
    }

    /**
     * Show notification to user
     */
    showNotification(message, type = 'info') {
        // TODO: Replace with your notification system
        if (type === 'error') {
            alert('❌ ' + message);
        } else if (type === 'success') {
            alert('✅ ' + message);
        } else {
            alert('ℹ️ ' + message);
        }
    }
}

// Initialize auth manager
const auth = new AuthManager();

// Check authentication on page load
document.addEventListener('DOMContentLoaded', () => {
    // Check for Google OAuth callback first
    auth.handleGoogleCallback();

    // Then check normal authentication
    auth.checkAuth();

    // Check Google OAuth availability and update button visibility
    auth.updateGoogleButtonVisibility();

    // Check for token in URL (from OAuth callback - legacy)
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
