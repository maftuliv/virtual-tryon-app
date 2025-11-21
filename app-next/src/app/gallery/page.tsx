'use client';

import { useAuth } from '@/hooks/useAuth';
import { useTryons } from '@/hooks/useTryons';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { useState, useRef, useEffect, Suspense } from 'react';
import '@/styles/gallery.css';

function GalleryContent() {
  const { user, isAuthenticated, logout } = useAuth();
  const { tryons, toggleFavorite, refresh } = useTryons();
  const router = useRouter();
  const searchParams = useSearchParams();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [selectedTryon, setSelectedTryon] = useState<number | null>(null);
  const [filter, setFilter] = useState<'all' | 'favorites'>('all');
  const menuRef = useRef<HTMLDivElement>(null);

  const userName = user?.full_name || user?.email?.split('@')[0] || 'Пользователь';
  const userInitial = userName.charAt(0).toUpperCase();

  // Set filter from URL params
  useEffect(() => {
    const filterParam = searchParams.get('filter');
    if (filterParam === 'favorites') {
      setFilter('favorites');
    }
  }, [searchParams]);

  const handleLoginClick = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';
      const response = await fetch(`${apiUrl}/api/auth/google/login`);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      if (data.success && data.authorization_url) {
        window.location.href = data.authorization_url;
      } else {
        alert('Не удалось получить URL для входа через Google.');
      }
    } catch (error) {
      console.error('Ошибка при инициализации Google OAuth:', error);
      alert('Ошибка при входе через Google.');
    }
  };

  const handleLogout = () => {
    logout();
    setIsMenuOpen(false);
  };

  const handleToggleFavorite = async (tryonId: number, currentFavorite: boolean) => {
    try {
      await toggleFavorite(tryonId, !currentFavorite);
      refresh();
    } catch (error) {
      console.error('Failed to toggle favorite:', error);
    }
  };

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsMenuOpen(false);
      }
    };

    if (isMenuOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isMenuOpen]);

  const filteredTryons = filter === 'favorites'
    ? tryons?.filter(t => t.is_favorite)
    : tryons;

  const selectedTryonData = tryons?.find(t => t.id === selectedTryon);

  return (
    <div className="gallery-page">
      {/* Header */}
      <header className="header">
        <div className="logo">
          <div className="logo-pill">Tap</div>
          <div className="logo-text">to look</div>
        </div>
        <div className="header-right">
          <nav className="nav-links">
            <Link href="/" className="nav-link">Главная</Link>
            <Link href="/tryon" className="nav-link">Примерка</Link>
            <div className="nav-link nav-link_active">Галерея</div>
            <div className="nav-link">Моя одежда</div>
            <div className="nav-link">История</div>
          </nav>
          {isAuthenticated ? (
            <div className="user-menu-container" ref={menuRef}>
              <div
                className="user-pill"
                onClick={() => setIsMenuOpen(!isMenuOpen)}
                style={{ cursor: 'pointer' }}
              >
                <div className="user-avatar">{userInitial}</div>
                <span className="user-name">{userName}</span>
              </div>

              {isMenuOpen && (
                <div className="user-dropdown">
                  {user?.role === 'admin' && (
                    <button className="dropdown-item" onClick={() => { router.push('/admin'); setIsMenuOpen(false); }}>
                      Админка
                    </button>
                  )}
                  <button className="dropdown-item" onClick={() => { router.push('/settings'); setIsMenuOpen(false); }}>
                    Настройки
                  </button>
                  <button className="dropdown-item dropdown-item-logout" onClick={handleLogout}>
                    Выйти
                  </button>
                </div>
              )}
            </div>
          ) : (
            <button className="btn btn-gradient" onClick={handleLoginClick}>
              Войти
            </button>
          )}
        </div>
      </header>

      {/* Gallery Title */}
      <div className="gallery-header">
        <h1 className="gallery-title">Мои примерки</h1>
        <p className="gallery-subtitle">
          Все ваши результаты примерок в одном месте
        </p>
      </div>

      {/* Filter Tabs */}
      <div className="gallery-filters">
        <button
          className={`filter-tab ${filter === 'all' ? 'active' : ''}`}
          onClick={() => setFilter('all')}
        >
          Все ({tryons?.length || 0})
        </button>
        <button
          className={`filter-tab ${filter === 'favorites' ? 'active' : ''}`}
          onClick={() => setFilter('favorites')}
        >
          Избранное ({tryons?.filter(t => t.is_favorite).length || 0})
        </button>
      </div>

      {/* Gallery Grid */}
      <div className="gallery-grid">
        {filteredTryons && filteredTryons.length > 0 ? (
          filteredTryons.map((tryon) => (
            <div
              key={tryon.id}
              className={`gallery-card ${selectedTryon === tryon.id ? 'selected' : ''}`}
              onClick={() => setSelectedTryon(tryon.id)}
            >
              <div className="gallery-card-image">
                {tryon.r2_url ? (
                  <img src={tryon.r2_url} alt={tryon.title || 'Примерка'} />
                ) : (
                  <div className="gallery-card-placeholder">Нет изображения</div>
                )}
              </div>
              <div className="gallery-card-overlay">
                <button
                  className={`favorite-btn ${tryon.is_favorite ? 'active' : ''}`}
                  onClick={(e) => {
                    e.stopPropagation();
                    handleToggleFavorite(tryon.id, tryon.is_favorite);
                  }}
                >
                  {tryon.is_favorite ? '❤️' : '🤍'}
                </button>
              </div>
              <div className="gallery-card-info">
                <div className="gallery-card-title">{tryon.title || 'Без названия'}</div>
                <div className="gallery-card-date">
                  {new Date(tryon.created_at).toLocaleDateString('ru-RU', {
                    day: 'numeric',
                    month: 'long',
                    year: 'numeric'
                  })}
                </div>
              </div>
            </div>
          ))
        ) : (
          <div className="gallery-empty">
            <div className="gallery-empty-icon">👗</div>
            <h3>Пока нет примерок</h3>
            <p>Создайте свою первую примерку!</p>
            <Link href="/tryon" className="btn btn-gradient">
              Создать примерку
            </Link>
          </div>
        )}
      </div>

      {/* Selected Image Modal */}
      {selectedTryonData && (
        <div className="gallery-modal" onClick={() => setSelectedTryon(null)}>
          <div className="gallery-modal-content" onClick={(e) => e.stopPropagation()}>
            <button className="gallery-modal-close" onClick={() => setSelectedTryon(null)}>
              ×
            </button>
            <div className="gallery-modal-image">
              <img src={selectedTryonData.r2_url} alt={selectedTryonData.title || 'Примерка'} />
            </div>
            <div className="gallery-modal-info">
              <h2>{selectedTryonData.title || 'Без названия'}</h2>
              <p className="gallery-modal-date">
                {new Date(selectedTryonData.created_at).toLocaleDateString('ru-RU', {
                  day: 'numeric',
                  month: 'long',
                  year: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit'
                })}
              </p>
              <div className="gallery-modal-actions">
                <button
                  className={`btn ${selectedTryonData.is_favorite ? 'btn-favorite-active' : 'btn-favorite'}`}
                  onClick={() => handleToggleFavorite(selectedTryonData.id, selectedTryonData.is_favorite)}
                >
                  {selectedTryonData.is_favorite ? '❤️ В избранном' : '🤍 В избранное'}
                </button>
                <a
                  href={selectedTryonData.r2_url}
                  download
                  className="btn btn-download"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Скачать
                </a>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="footer-legal">
        Используя сервис, вы соглашаетесь с условиями и политикой конфиденциальности.
      </div>
    </div>
  );
}

export default function GalleryPage() {
  return (
    <Suspense fallback={<div className="gallery-page"><div className="gallery-loading">Загрузка...</div></div>}>
      <GalleryContent />
    </Suspense>
  );
}
