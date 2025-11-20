'use client';

import { useAuth } from '@/hooks/useAuth';
import { useRouter } from 'next/navigation';
import { useState, useEffect } from 'react';

interface User {
  id: number;
  email: string;
  full_name: string | null;
  role: string;
  provider: string;
  is_premium: boolean;
  created_at: string;
  last_login?: string;
  last_action?: string;
  generations_count?: number;
}

interface DashboardStats {
  users_total: number;
  premium_total: number;
  generations_today: number;
  feedback_pending: number;
}

interface Feedback {
  id: number;
  user_email: string;
  type: string;
  message: string;
  created_at: string;
  status: string;
}

interface AuditLog {
  id: number;
  admin_email: string;
  action: string;
  target_user_email?: string;
  details?: string;
  created_at: string;
}

export default function AdminPanel() {
  const { user, isAuthenticated } = useAuth();
  const router = useRouter();
  const [activeTab, setActiveTab] = useState('dashboard');
  const [loading, setLoading] = useState(false);

  // Dashboard state
  const [stats, setStats] = useState<DashboardStats | null>(null);

  // Users state
  const [users, setUsers] = useState<User[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  // Feedback state
  const [feedback, setFeedback] = useState<Feedback[]>([]);

  // Audit state
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

  // Check admin access
  useEffect(() => {
    if (!isAuthenticated || user?.role !== 'admin') {
      router.push('/');
    }
  }, [isAuthenticated, user, router]);

  // Load data based on active tab
  useEffect(() => {
    if (activeTab === 'dashboard') {
      loadDashboardStats();
    } else if (activeTab === 'users') {
      loadUsers();
    } else if (activeTab === 'feedback') {
      loadFeedback();
    } else if (activeTab === 'audit') {
      loadAuditLogs();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab, currentPage, searchQuery]);

  const loadDashboardStats = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${apiUrl}/api/admin/summary`, {
        credentials: 'include',
      });
      if (response.ok) {
        const data = await response.json();
        setStats(data.data);
      }
    } catch (error) {
      console.error('Error loading stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadUsers = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: currentPage.toString(),
        page_size: '20',
        ...(searchQuery && { search: searchQuery }),
      });
      const response = await fetch(`${apiUrl}/api/admin/users?${params}`, {
        credentials: 'include',
      });
      if (response.ok) {
        const data = await response.json();
        setUsers(data.data.users);
        setTotalPages(data.data.total_pages);
      }
    } catch (error) {
      console.error('Error loading users:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadFeedback = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${apiUrl}/api/admin/feedback`, {
        credentials: 'include',
      });
      if (response.ok) {
        const data = await response.json();
        setFeedback(data.data);
      }
    } catch (error) {
      console.error('Error loading feedback:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadAuditLogs = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${apiUrl}/api/admin/audit`, {
        credentials: 'include',
      });
      if (response.ok) {
        const data = await response.json();
        setAuditLogs(data.data);
      }
    } catch (error) {
      console.error('Error loading audit logs:', error);
    } finally {
      setLoading(false);
    }
  };

  const changeUserRole = async (userId: number, newRole: string) => {
    try {
      const response = await fetch(`${apiUrl}/api/admin/users/${userId}/role`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ role: newRole }),
      });
      if (response.ok) {
        loadUsers();
      } else {
        const data = await response.json();
        alert(`Ошибка при изменении роли: ${data.error || 'Неизвестная ошибка'}`);
      }
    } catch (error) {
      console.error('Error changing role:', error);
      alert('Ошибка при изменении роли');
    }
  };

  const changeTariff = async (userId: number, newTariff: string) => {
    try {
      // Определяем параметры в зависимости от тарифа
      const enable = newTariff === 'premium';
      const days = 30;

      const response = await fetch(`${apiUrl}/api/admin/users/${userId}/premium`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ enable, days }),
      });
      if (response.ok) {
        loadUsers();
      } else {
        const data = await response.json();
        alert(`Ошибка при изменении тарифа: ${data.error || 'Неизвестная ошибка'}`);
      }
    } catch (error) {
      console.error('Error changing tariff:', error);
      alert('Ошибка при изменении тарифа');
    }
  };

  const deleteUser = async (userId: number, userEmail: string) => {
    if (!confirm(`Вы уверены, что хотите удалить пользователя ${userEmail}?`)) {
      return;
    }
    try {
      const response = await fetch(`${apiUrl}/api/admin/users/${userId}`, {
        method: 'DELETE',
        credentials: 'include',
      });
      if (response.ok) {
        loadUsers();
        alert('Пользователь успешно удалён');
      } else {
        alert('Ошибка при удалении пользователя');
      }
    } catch (error) {
      console.error('Error deleting user:', error);
      alert('Ошибка при удалении пользователя');
    }
  };

  const resetUserLimit = async (userId: number) => {
    try {
      const response = await fetch(`${apiUrl}/api/admin/users/${userId}/reset-limit`, {
        method: 'POST',
        credentials: 'include',
      });
      if (response.ok) {
        alert('Лимит сброшен успешно');
        loadUsers();
      } else {
        alert('Ошибка при сбросе лимита');
      }
    } catch (error) {
      console.error('Error resetting limit:', error);
      alert('Ошибка при сбросе лимита');
    }
  };

  if (!isAuthenticated || user?.role !== 'admin') {
    return null;
  }

  return (
    <div className="admin-page">
      <header className="admin-header">
        <div className="admin-header-content">
          <div className="logo">
            <div className="logo-pill">Tap</div>
            <div className="logo-text">to look - Админ панель</div>
          </div>
          <button className="btn btn-back" onClick={() => router.push('/')}>
            ← Вернуться на главную
          </button>
        </div>
      </header>

      <div className="admin-container">
        <nav className="admin-tabs">
          <button
            className={`admin-tab ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveTab('dashboard')}
          >
            📊 Дашборд
          </button>
          <button
            className={`admin-tab ${activeTab === 'users' ? 'active' : ''}`}
            onClick={() => setActiveTab('users')}
          >
            👥 Пользователи
          </button>
          <button
            className={`admin-tab ${activeTab === 'feedback' ? 'active' : ''}`}
            onClick={() => setActiveTab('feedback')}
          >
            💬 Обратная связь
          </button>
          <button
            className={`admin-tab ${activeTab === 'audit' ? 'active' : ''}`}
            onClick={() => setActiveTab('audit')}
          >
            📋 Аудит
          </button>
        </nav>

        {loading && <div className="admin-loading">Загрузка...</div>}

        {/* DASHBOARD TAB */}
        {activeTab === 'dashboard' && stats && (
          <div className="admin-content">
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-icon">👥</div>
                <div className="stat-value">{stats.users_total}</div>
                <div className="stat-label">Всего пользователей</div>
              </div>
              <div className="stat-card">
                <div className="stat-icon">⭐</div>
                <div className="stat-value">{stats.premium_total}</div>
                <div className="stat-label">Премиум аккаунтов</div>
              </div>
              <div className="stat-card">
                <div className="stat-icon">🎨</div>
                <div className="stat-value">{stats.generations_today}</div>
                <div className="stat-label">Примерок сегодня</div>
              </div>
              <div className="stat-card">
                <div className="stat-icon">💬</div>
                <div className="stat-value">{stats.feedback_pending}</div>
                <div className="stat-label">Ожидает ответа</div>
              </div>
            </div>
          </div>
        )}

        {/* USERS TAB */}
        {activeTab === 'users' && (
          <div className="admin-content">
            <div className="users-controls">
              <input
                type="text"
                className="search-input"
                placeholder="Поиск по email или имени..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>

            <div className="users-table-container">
              <table className="users-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Email</th>
                    <th>Имя</th>
                    <th>Провайдер</th>
                    <th>Роль</th>
                    <th>Тариф</th>
                    <th>Примерок</th>
                    <th>Последний визит</th>
                    <th>Последнее действие</th>
                    <th>Действия</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((u) => (
                    <tr key={u.id}>
                      <td>{u.id}</td>
                      <td>{u.email}</td>
                      <td>{u.full_name || '—'}</td>
                      <td>
                        <span className="provider-badge">
                          {u.provider === 'google' && '🔵 Google'}
                          {u.provider === 'email' && '📧 Email'}
                          {u.provider === 'vk' && '🔷 VK'}
                          {u.provider === 'telegram' && '✈️ Telegram'}
                          {!['google', 'email', 'vk', 'telegram'].includes(u.provider) && u.provider}
                        </span>
                      </td>
                      <td>
                        <select
                          value={u.role}
                          onChange={(e) => changeUserRole(u.id, e.target.value)}
                          className="role-select"
                        >
                          <option value="user">User</option>
                          <option value="admin">Admin</option>
                        </select>
                      </td>
                      <td>
                        <select
                          value={u.role === 'admin' ? 'admin' : (u.is_premium ? 'premium' : 'free')}
                          onChange={(e) => changeTariff(u.id, e.target.value)}
                          className="tariff-select"
                          disabled={u.role === 'admin'}
                        >
                          <option value="free">Free (3/неделя)</option>
                          <option value="premium">Premium (50/месяц)</option>
                          {u.role === 'admin' && <option value="admin">Admin (безлимит)</option>}
                        </select>
                      </td>
                      <td>{u.generations_count || 0}</td>
                      <td>{u.last_login ? new Date(u.last_login).toLocaleString('ru-RU') : '—'}</td>
                      <td>{u.last_action || '—'}</td>
                      <td>
                        <div className="action-buttons">
                          <button
                            className="btn-action btn-reset"
                            onClick={() => resetUserLimit(u.id)}
                            title="Сбросить лимит"
                          >
                            🔄
                          </button>
                          <button
                            className="btn-action btn-delete"
                            onClick={() => deleteUser(u.id, u.email)}
                            title="Удалить пользователя"
                          >
                            🗑️
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {totalPages > 1 && (
              <div className="pagination">
                <button
                  onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                  disabled={currentPage === 1}
                  className="btn-page"
                >
                  ← Назад
                </button>
                <span className="page-info">
                  Страница {currentPage} из {totalPages}
                </span>
                <button
                  onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                  disabled={currentPage === totalPages}
                  className="btn-page"
                >
                  Вперёд →
                </button>
              </div>
            )}
          </div>
        )}

        {/* FEEDBACK TAB */}
        {activeTab === 'feedback' && (
          <div className="admin-content">
            <div className="feedback-list">
              {feedback.map((f) => (
                <div key={f.id} className="feedback-card">
                  <div className="feedback-header">
                    <span className="feedback-type">{f.type}</span>
                    <span className="feedback-date">{new Date(f.created_at).toLocaleString('ru-RU')}</span>
                  </div>
                  <div className="feedback-user">{f.user_email}</div>
                  <div className="feedback-message">{f.message}</div>
                  <div className="feedback-status">Статус: {f.status}</div>
                </div>
              ))}
              {feedback.length === 0 && <div className="empty-state">Нет обратной связи</div>}
            </div>
          </div>
        )}

        {/* AUDIT TAB */}
        {activeTab === 'audit' && (
          <div className="admin-content">
            <div className="audit-list">
              {auditLogs.map((log) => (
                <div key={log.id} className="audit-card">
                  <div className="audit-header">
                    <span className="audit-admin">{log.admin_email}</span>
                    <span className="audit-date">{new Date(log.created_at).toLocaleString('ru-RU')}</span>
                  </div>
                  <div className="audit-action">{log.action}</div>
                  {log.target_user_email && <div className="audit-target">Пользователь: {log.target_user_email}</div>}
                  {log.details && <div className="audit-details">{log.details}</div>}
                </div>
              ))}
              {auditLogs.length === 0 && <div className="empty-state">Нет записей аудита</div>}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
