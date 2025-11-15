/**
 * Admin Panel JavaScript
 * Manages admin dashboard, user management, feedback, and audit logs
 */

class AdminPanel {
    constructor() {
        this.API_URL = window.location.hostname === 'localhost' ? 'http://localhost:5000' : '';
        this.currentPage = 1;
        this.pageSize = 20;
        this.searchTimeout = null;
        this.unauthorizedShown = false;
    }

    async init() {
        // Check if user is admin
        if (!auth || !auth.user) {
            await auth.checkAuth();
        }

        if (!auth.user || auth.user.role !== 'admin') {
            alert('❌ Доступ запрещён. Только для администраторов.');
            window.location.href = '/';
            return;
        }

        // Show admin info
        document.getElementById('adminUserInfo').textContent = `Admin: ${auth.user.email}`;

        // Setup tab navigation
        this.setupTabs();

        // Setup search
        this.setupSearch();

        // Load initial data
        this.loadDashboard();
    }

    setupTabs() {
        const tabs = document.querySelectorAll('.admin-tab');
        const sections = document.querySelectorAll('.admin-section');

        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                const targetTab = tab.dataset.tab;

                // Update active states
                tabs.forEach(t => t.classList.remove('active'));
                sections.forEach(s => s.classList.remove('active'));

                tab.classList.add('active');
                document.getElementById(`${targetTab}-section`).classList.add('active');

                // Load data for tab
                if (targetTab === 'dashboard') this.loadDashboard();
                if (targetTab === 'users') this.loadUsers();
                if (targetTab === 'feedback') this.loadFeedback();
                if (targetTab === 'audit') this.loadAudit();
            });
        });
    }

    setupSearch() {
        const searchInput = document.getElementById('userSearch');
        if (!searchInput) return;

        searchInput.addEventListener('input', (e) => {
            clearTimeout(this.searchTimeout);
            this.searchTimeout = setTimeout(() => {
                this.currentPage = 1;
                this.loadUsers(e.target.value);
            }, 500); // Debounce 500ms
        });
    }

    async apiCall(endpoint, options = {}) {
        const fetchOptions = {
            credentials: 'include',
            ...options,
        };

        fetchOptions.headers = {
            'Content-Type': 'application/json',
            ...(options.headers || {}),
        };

        const response = await fetch(`${this.API_URL}${endpoint}`, fetchOptions);

        if (response.status === 401 || response.status === 403) {
            throw new Error('ADMIN_UNAUTHORIZED');
        }

        if (!response.ok) {
            let errorMessage = `HTTP ${response.status}`;
            try {
                const error = await response.json();
                errorMessage = error.error || errorMessage;
            } catch (parseError) {
                console.warn('[ADMIN] Failed to parse error response:', parseError);
            }
            throw new Error(errorMessage);
        }

        return response.json();
    }

    // ============================================================
    // Dashboard
    // ============================================================

    async loadDashboard() {
        try {
            const data = await this.apiCall('/api/admin/summary');

            document.getElementById('usersTotal').textContent = data.users_total || 0;
            document.getElementById('premiumTotal').textContent = data.premium_total || 0;
            document.getElementById('generationsToday').textContent = data.generations_today || 0;
            document.getElementById('feedbackPending').textContent = data.feedback_pending || 0;

            console.log('[ADMIN] Dashboard loaded');
        } catch (error) {
            if (error.message === 'ADMIN_UNAUTHORIZED') {
                this.handleUnauthorized();
                return;
            }
            console.error('[ADMIN] Failed to load dashboard:', error);
            alert('Ошибка загрузки дашборда: ' + error.message);
        }
    }

    // ============================================================
    // Users Management
    // ============================================================

    async loadUsers(search = '') {
        try {
            const params = new URLSearchParams({
                page: this.currentPage,
                page_size: this.pageSize,
            });

            if (search) params.append('search', search);

            const data = await this.apiCall(`/api/admin/users?${params}`);

            this.renderUsersTable(data.users);
            this.renderPagination(data);

            console.log('[ADMIN] Users loaded:', data.total);
        } catch (error) {
            if (error.message === 'ADMIN_UNAUTHORIZED') {
                this.handleUnauthorized();
                return;
            }
            console.error('[ADMIN] Failed to load users:', error);
            document.getElementById('usersTableBody').innerHTML =
                `<tr><td colspan="8" class="loading">Ошибка загрузки: ${error.message}</td></tr>`;
        }
    }

    renderUsersTable(users) {
        const tbody = document.getElementById('usersTableBody');

        if (!users || users.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="loading">Пользователи не найдены</td></tr>';
            return;
        }

        tbody.innerHTML = users.map(user => `
            <tr>
                <td>${user.id}</td>
                <td>${this.escapeHtml(user.email)}</td>
                <td>${this.escapeHtml(user.full_name)}</td>
                <td><span class="badge badge-${user.provider}">${user.provider}</span></td>
                <td><span class="badge badge-${user.role}">${user.role}</span></td>
                <td>${user.is_premium ? '<span class="badge badge-premium">Yes</span>' : 'No'}</td>
                <td>${user.generations_count || 0}</td>
                <td>
                    ${user.role === 'user'
                        ? `<button class="action-btn action-btn-primary" onclick="adminPanel.changeRole(${user.id}, 'admin')">👑 Сделать админом</button>`
                        : `<button class="action-btn action-btn-warning" onclick="adminPanel.changeRole(${user.id}, 'user')">👤 Снять админа</button>`
                    }
                    ${!user.is_premium
                        ? `<button class="action-btn action-btn-success" onclick="adminPanel.togglePremium(${user.id}, true)">⭐ Дать Premium</button>`
                        : `<button class="action-btn action-btn-danger" onclick="adminPanel.togglePremium(${user.id}, false)">❌ Убрать Premium</button>`
                    }
                    <button class="action-btn action-btn-primary" onclick="adminPanel.resetLimit(${user.id})">🔄 Сбросить лимит</button>
                </td>
            </tr>
        `).join('');
    }

    renderPagination(data) {
        const pagination = document.getElementById('usersPagination');
        const { page, total_pages } = data;

        pagination.innerHTML = `
            <button onclick="adminPanel.goToPage(${page - 1})" ${page <= 1 ? 'disabled' : ''}>← Назад</button>
            <span>Страница ${page} из ${total_pages}</span>
            <button onclick="adminPanel.goToPage(${page + 1})" ${page >= total_pages ? 'disabled' : ''}>Вперёд →</button>
        `;
    }

    goToPage(page) {
        this.currentPage = page;
        const search = document.getElementById('userSearch').value;
        this.loadUsers(search);
    }

    async changeRole(userId, newRole) {
        const action = newRole === 'admin' ? 'сделать администратором' : 'снять права администратора';
        if (!confirm(`Вы уверены, что хотите ${action} этого пользователя?`)) {
            return;
        }

        try {
            await this.apiCall(`/api/admin/users/${userId}/role`, {
                method: 'PATCH',
                body: JSON.stringify({ role: newRole }),
            });

            alert(`✅ Роль успешно изменена на "${newRole}"`);
            this.loadUsers(document.getElementById('userSearch').value);
        } catch (error) {
            if (error.message === 'ADMIN_UNAUTHORIZED') {
                this.handleUnauthorized();
                return;
            }
            console.error('[ADMIN] Failed to change role:', error);
            alert('❌ Ошибка изменения роли: ' + error.message);
        }
    }

    async togglePremium(userId, enable) {
        const action = enable ? 'выдать Premium' : 'отобрать Premium';
        if (!confirm(`Вы уверены, что хотите ${action}?`)) {
            return;
        }

        const days = enable ? prompt('На сколько дней выдать Premium?', '30') : null;
        if (enable && (!days || isNaN(days) || days < 1)) {
            alert('Некорректное количество дней');
            return;
        }

        try {
            await this.apiCall(`/api/admin/users/${userId}/premium`, {
                method: 'PATCH',
                body: JSON.stringify({ enable, days: parseInt(days) || 30 }),
            });

            alert(`✅ Premium ${enable ? 'выдан' : 'отобран'}`);
            this.loadUsers(document.getElementById('userSearch').value);
        } catch (error) {
            if (error.message === 'ADMIN_UNAUTHORIZED') {
                this.handleUnauthorized();
                return;
            }
            console.error('[ADMIN] Failed to toggle premium:', error);
            alert('❌ Ошибка: ' + error.message);
        }
    }

    async resetLimit(userId) {
        if (!confirm('Сбросить дневной лимит для этого пользователя?')) {
            return;
        }

        try {
            await this.apiCall(`/api/admin/users/${userId}/reset-limit`, {
                method: 'POST',
            });

            alert('✅ Лимит сброшен');
        } catch (error) {
            if (error.message === 'ADMIN_UNAUTHORIZED') {
                this.handleUnauthorized();
                return;
            }
            console.error('[ADMIN] Failed to reset limit:', error);
            alert('❌ Ошибка: ' + error.message);
        }
    }

    // ============================================================
    // Feedback
    // ============================================================

    async loadFeedback() {
        try {
            const data = await this.apiCall('/api/admin/feedback');

            const container = document.getElementById('feedbackList');

            if (!data || data.length === 0) {
                container.innerHTML = '<div class="loading">Обращений пока нет</div>';
                return;
            }

            container.innerHTML = data.map(item => `
                <div class="feedback-card">
                    <div class="feedback-header">
                        <span class="feedback-email">${this.escapeHtml(item.email)}</span>
                        <span class="feedback-date">${new Date(item.created_at).toLocaleString('ru-RU')}</span>
                    </div>
                    <div class="feedback-message">${this.escapeHtml(item.message)}</div>
                    ${item.category ? `<div style="margin-top: 10px;"><span class="badge badge-primary">${this.escapeHtml(item.category)}</span></div>` : ''}
                </div>
            `).join('');

            console.log('[ADMIN] Feedback loaded:', data.length);
        } catch (error) {
            if (error.message === 'ADMIN_UNAUTHORIZED') {
                this.handleUnauthorized();
                return;
            }
            console.error('[ADMIN] Failed to load feedback:', error);
            document.getElementById('feedbackList').innerHTML =
                `<div class="loading">Ошибка загрузки: ${error.message}</div>`;
        }
    }

    // ============================================================
    // Audit Logs
    // ============================================================

    async loadAudit() {
        try {
            const data = await this.apiCall('/api/admin/audit?limit=50');

            const tbody = document.getElementById('auditTableBody');

            if (!data || data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" class="loading">Записей пока нет</td></tr>';
                return;
            }

            tbody.innerHTML = data.map(log => `
                <tr>
                    <td>${new Date(log.created_at).toLocaleString('ru-RU')}</td>
                    <td>${this.escapeHtml(log.admin_email)}</td>
                    <td><span class="badge badge-primary">${log.action}</span></td>
                    <td>${log.target_type} #${log.target_id || 'N/A'}</td>
                    <td>${log.ip_address || 'N/A'}</td>
                    <td><code>${JSON.stringify(log.payload).substring(0, 100)}</code></td>
                </tr>
            `).join('');

            console.log('[ADMIN] Audit logs loaded:', data.length);
        } catch (error) {
            if (error.message === 'ADMIN_UNAUTHORIZED') {
                this.handleUnauthorized();
                return;
            }
            console.error('[ADMIN] Failed to load audit logs:', error);
            document.getElementById('auditTableBody').innerHTML =
                `<tr><td colspan="6" class="loading">Ошибка загрузки: ${error.message}</td></tr>`;
        }
    }

    // ============================================================
    // Utilities
    // ============================================================

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    handleUnauthorized() {
        if (this.unauthorizedShown) {
            return;
        }

        this.unauthorizedShown = true;
        alert('❌ Сессия администратора истекла. Пожалуйста, войдите заново.');

        if (auth && typeof auth.clearLocalSession === 'function') {
            auth.clearLocalSession(false);
        }

        window.location.href = '/';
    }
}

// Initialize admin panel
const adminPanel = new AdminPanel();

// Wait for auth to be ready, then init admin panel
document.addEventListener('DOMContentLoaded', () => {
    // Wait a bit for auth.js to initialize
    setTimeout(() => {
        adminPanel.init();
    }, 100);
});
