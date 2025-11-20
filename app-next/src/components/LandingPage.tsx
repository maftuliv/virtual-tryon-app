'use client';

import { useAuth } from '@/hooks/useAuth';
import { useTryons } from '@/hooks/useTryons';
import { useLimit } from '@/hooks/useLimit';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useState, useRef, useEffect } from 'react';

export default function LandingPage() {
  const { user, isAuthenticated, logout } = useAuth();
  const { tryons } = useTryons();
  const { limitData } = useLimit();
  const router = useRouter();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  const userName = user?.full_name || user?.email?.split('@')[0] || 'Пользователь';
  const userInitial = userName.charAt(0).toUpperCase();
  const favoritesCount = tryons?.filter((t) => t.is_favorite).length || 0;

  // Calculate tariff display info
  const isPremium = user?.is_premium || false;
  const isAdmin = user?.role === 'admin';
  const used = limitData?.used ?? 0;
  const limit = limitData?.limit ?? 3;
  const remaining = limit === -1 ? Infinity : Math.max(0, limit - used);
  const progressPercent = limit === -1 ? 100 : Math.min(100, (used / limit) * 100);

  const handleLoginClick = async () => {
    try {
      // Получаем authorization URL от backend
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';
      const response = await fetch(`${apiUrl}/api/auth/google/login`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (data.success && data.authorization_url) {
        // Редиректим на Google OAuth
        window.location.href = data.authorization_url;
      } else {
        alert('Не удалось получить URL для входа через Google. Попробуйте еще раз.');
      }
    } catch (error) {
      console.error('Ошибка при инициализации Google OAuth:', error);
      alert('Ошибка при входе через Google. Попробуйте еще раз.');
    }
  };

  const handleLogout = () => {
    logout();
    setIsMenuOpen(false);
  };

  const handleSettings = () => {
    router.push('/settings');
    setIsMenuOpen(false);
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

  return (
    <div className="page">
      {/* ВЕРХНЕЕ МЕНЮ */}
      <header className="header">
        <div className="logo">
          <div className="logo-pill">Tap</div>
          <div className="logo-text">to look</div>
        </div>
        <div className="header-right">
          <nav className="nav-links">
            <div className="nav-link nav-link_active">Дашборд</div>
            <Link href="#tryon" className="nav-link">Примерка</Link>
            <div className="nav-link">Образы</div>
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
                <span className="badge-premium">Premium</span>
              </div>

              {isMenuOpen && (
                <div className="user-dropdown">
                  {user?.role === 'admin' && (
                    <button className="dropdown-item" onClick={() => { router.push('/admin'); setIsMenuOpen(false); }}>
                      🔧 Админка
                    </button>
                  )}
                  <button className="dropdown-item" onClick={handleSettings}>
                    ⚙️ Настройки
                  </button>
                  <button className="dropdown-item dropdown-item-logout" onClick={handleLogout}>
                    🚪 Выйти
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

      {/* ПРИВЕТСТВИЕ ПОЛЬЗОВАТЕЛЯ + ПРЕМИУМ АККАУНТ */}
      <section className="hero-grid">
        {/* LEFT: Приветствие */}
        <article className="card">
          <h1 className="hero-main-title">Привет, {userName} 👋</h1>
          <p className="hero-subtitle">
            Здесь твоя зона стиля. Что сделаем сейчас: примерку, новый образ или соберём look из брендов?
          </p>
          <div className="hero-meta-row" style={{ marginTop: '16px' }}>
            <div className="meta-pill">
              <span className="meta-dot"></span>
              Последняя примерка: <strong>вчера</strong>
            </div>
            <div className="meta-pill">
              🎨 Образов создано: <strong>12</strong>
            </div>
          </div>
        </article>

        {/* RIGHT: Тарифный план */}
        <article className="card">
          {isAdmin ? (
            <>
              <div className="card-title">👑 Администратор</div>
              <p className="premium-count">Безлимитные примерки</p>
              <div className="premium-progress">
                <div className="premium-progress-fill" style={{ width: '100%' }}></div>
              </div>
              <p className="premium-note">
                У вас есть полный доступ ко всем функциям платформы без ограничений.
              </p>
            </>
          ) : isPremium ? (
            <>
              <div className="card-title">⭐ Премиум аккаунт</div>
              <p className="premium-count">
                {remaining === Infinity ? 'Безлимитно' : `${remaining} из ${limit} примерок осталось в этом месяце`}
              </p>
              <div className="premium-progress">
                <div className="premium-progress-fill" style={{ width: `${progressPercent}%` }}></div>
              </div>
              <p className="premium-note">
                {remaining > 0
                  ? 'Используйте лимит, чтобы протестировать максимум образов. В следующем месяце счётчик обновится.'
                  : 'Вы использовали весь месячный лимит. Ожидайте обновления в следующем месяце.'}
              </p>
            </>
          ) : (
            <>
              <div className="card-title">Бесплатный план</div>
              <p className="premium-count">
                {remaining} из {limit} примерок осталось на этой неделе
              </p>
              <div className="premium-progress">
                <div className="premium-progress-fill" style={{ width: `${progressPercent}%` }}></div>
              </div>
              <p className="premium-note">
                {remaining > 0
                  ? 'У вас есть 3 бесплатные примерки каждую неделю. Обновление каждый понедельник.'
                  : 'Вы использовали все бесплатные примерки на этой неделе. Обновление в понедельник.'}
              </p>
              <button className="btn btn-premium">Перейти на Premium ($4.99/месяц)</button>
            </>
          )}
        </article>
      </section>


      {/* ТРИ ГЛАВНЫЕ КНОПКИ - новый дизайн */}
      <section className="hero-modes">
        <Link href="#tryon" className="mode-btn mode-btn-tryon">
          <div className="mode-btn-content">
            <div className="mode-btn-label">Инструмент</div>
            <div className="mode-btn-title">Сделать примерку</div>
            <div className="mode-btn-desc">Фото + одежда → новый look</div>
          </div>
          <div className="mode-icon">👗</div>
        </Link>

        <button className="mode-btn mode-btn-create">
          <div className="mode-btn-content">
            <div className="mode-btn-label">Инструмент</div>
            <div className="mode-btn-title">Создать свой образ</div>
            <div className="mode-btn-desc">Фильтры, стиль, настроение</div>
          </div>
          <div className="mode-icon">🎨</div>
        </button>

        <button className="mode-btn mode-btn-brands">
          <div className="mode-btn-content">
            <div className="mode-btn-label">Инструмент</div>
            <div className="mode-btn-title">Собрать образ из брендов</div>
            <div className="mode-btn-desc">Выбор вещей по любимым маркам</div>
          </div>
          <div className="mode-icon">🛍️</div>
        </button>
      </section>

      {/* НЕДАВНИЕ РЕЗУЛЬТАТЫ */}
      <section style={{ marginBottom: '22px' }}>
        <h2 className="section-title" style={{ fontSize: '18px', fontWeight: '600', marginBottom: '12px' }}>
          НЕДАВНИЕ РЕЗУЛЬТАТЫ
        </h2>
      </section>

      {/* МОИ ПРИМЕРКИ + МОИ ОБРАЗЫ + МОИ ФОТО */}
      <section className="main-grid">
        {/* МОИ ПРИМЕРКИ */}
        <article className="card">
          <div className="section-header">
            <div className="section-title">МОИ ПРИМЕРКИ</div>
            <Link href="/dashboard" className="section-link">Посмотреть все</Link>
          </div>
          <p className="card-subtitle">
            Последние результаты примерки. Откройте, чтобы сохранить, поделиться или создать похожий образ.
          </p>
          <div className="tryons-grid">
            {tryons && tryons.length > 0 ? (
              <>
                {tryons.slice(0, 3).map((tryon, idx) => (
                  <div key={tryon.id || idx} className="tryon-card-new">
                    <div className="tryon-card-name">{tryon.title || `Образ ${idx + 1}`}</div>
                    <div className="tryon-card-date">{new Date(tryon.created_at).toLocaleDateString('ru-RU')}</div>
                    <button className="btn-tryon-open">✨ Открыть образ</button>
                  </div>
                ))}
                {/* Fill up to 3 cards minimum */}
                {Array.from({ length: Math.max(0, 3 - tryons.length) }).map((_, idx) => (
                  <div key={`placeholder-${idx}`} className="tryon-card-new">
                    <div className="tryon-card-name">Создать новый образ</div>
                    <div className="tryon-card-date">Пусто</div>
                    <Link href="#tryon">
                      <button className="btn-tryon-open">✨ Создать образ</button>
                    </Link>
                  </div>
                ))}
              </>
            ) : (
              <>
                {Array.from({ length: 3 }).map((_, idx) => (
                  <div key={`empty-${idx}`} className="tryon-card-new">
                    <div className="tryon-card-name">Создать новый образ</div>
                    <div className="tryon-card-date">Пусто</div>
                    <Link href="#tryon">
                      <button className="btn-tryon-open">✨ Создать образ</button>
                    </Link>
                  </div>
                ))}
              </>
            )}
          </div>
        </article>

        {/* МОИ ОБРАЗЫ */}
        <article className="card">
          <div className="section-header">
            <div className="section-title">МОИ ОБРАЗЫ</div>
            <div className="section-link">Открыть все</div>
          </div>
          <p className="card-subtitle">
            Образы, созданные с помощью фильтров: свидание, офис, вечеринка, путешествие и другие.
          </p>
          <div className="looks-grid">
            <div className="look-card">
              <div className="look-name">Образ для свидания</div>
              <div className="look-tag">Элегантный вечерний стиль</div>
              <button className="btn-chip">✨ Открыть образ</button>
            </div>
            <div className="look-card">
              <div className="look-name">Образ для офиса</div>
              <div className="look-tag">Минимализм и нейтральные оттенки</div>
              <button className="btn-chip">✨ Открыть образ</button>
            </div>
            <div className="look-card">
              <div className="look-name">Образ для вечеринки</div>
              <div className="look-tag">Яркий и стильный look</div>
              <button className="btn-chip">✨ Открыть образ</button>
            </div>
          </div>
        </article>

        {/* МОИ ФОТО */}
        <article className="card">
          <div className="section-header">
            <div className="section-title">МОИ ФОТО</div>
            <div className="section-link">Управлять</div>
          </div>
          <p className="card-subtitle">
            Базовые фотографии, с которыми мы работаем. Рекомендуем периодически обновлять их.
          </p>
          <div className="photo-grid">
            <div className="photo-card">
              <div>Фото в полный рост</div>
              <div className="photo-label">Основное для примерок</div>
              <div className="photo-status">Рекомендовано ✓</div>
            </div>
            <div className="photo-card">
              <div>Портрет</div>
              <div className="photo-label">Подходит для аватаров и лиц</div>
            </div>
            <div className="photo-card">
              <div>Фото в деловом стиле</div>
              <div className="photo-label">Для офисных образов</div>
            </div>
          </div>
        </article>
      </section>

      {/* ЛАЙКНУТЫЕ ОБРАЗЫ + РЕКОМЕНДАЦИИ */}
      <section className="lower-grid">
        {/* Лайкнутые образы */}
        <article className="card">
          <div className="section-header">
            <div className="section-title">Лайкнутые образы</div>
            <Link href="/dashboard" className="section-link">Открыть галерею</Link>
          </div>
          <div className="liked-count">{favoritesCount}</div>
          <p className="card-subtitle">
            Ваши любимые результаты. Можно вернуться к ним и доработать детали.
          </p>
          <div className="liked-preview-row">
            <div className="liked-thumb">Look 1</div>
            <div className="liked-thumb">Look 2</div>
            <div className="liked-thumb">Look 3</div>
          </div>
        </article>

        {/* Рекомендации */}
        <article className="card">
          <div className="section-header">
            <div className="section-title">Рекомендации</div>
          </div>
          <p className="card-subtitle">
            Сегодняшняя рекомендация: попробуйте образ для свидания с тёмным низом и светлым верхом.
          </p>
          <div className="chip-row">
            <button className="btn-chip">💼 На работу</button>
            <button className="btn-chip">❤️ На свидание</button>
            <button className="btn-chip">🧳 В путешествие</button>
            <button className="btn-chip">🎉 На вечеринку</button>
          </div>
          <ul className="reco-list">
            <li>Вы уже протестировали 8 образов. Ещё 2 — и мы соберём для вас подборку «Топ-3 образа месяца».</li>
            <li>Попробуйте создать капсулу из 5–7 вещей для ближайших недель.</li>
          </ul>
        </article>
      </section>

      {/* ОБРАТНАЯ СВЯЗЬ */}
      <section className="card" style={{ marginBottom: '14px' }}>
        <div className="section-header">
          <div className="section-title">Обратная связь</div>
          <div className="section-link">Подробнее</div>
        </div>
        <p className="card-subtitle">
          Расскажите, что улучшить. Ваши идеи и замечания напрямую влияют на развитие сервиса.
        </p>
        <div className="chip-row">
          <button className="btn-chip btn-chip-lg">🐞 Сообщить об ошибке</button>
          <button className="btn-chip btn-chip-lg">💡 Предложить идею</button>
          <button className="btn-chip btn-chip-lg">⭐ Оценить качество примерки</button>
          <button className="btn-chip btn-chip-lg">💬 Отдел заботы</button>
          <button className="btn-chip btn-chip-lg">💌 Отправить отзыв</button>
        </div>
      </section>

      {/* FOOTER */}
      <div className="footer-legal">
        Используя сервис, вы соглашаетесь с условиями и политикой конфиденциальности. Все права защищены.
      </div>
    </div>
  );
}
