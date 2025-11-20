'use client';

import { useAuth } from '@/hooks/useAuth';
import { useTryons } from '@/hooks/useTryons';
import { useLimit } from '@/hooks/useLimit';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useState, useRef, useEffect } from 'react';
import TryonFormStepped from './TryonFormStepped';

export default function TryonPage() {
  const { user, isAuthenticated, logout } = useAuth();
  const { tryons } = useTryons();
  const { limitData } = useLimit();
  const router = useRouter();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  const userName = user?.full_name || user?.email?.split('@')[0] || 'Пользователь';
  const userInitial = userName.charAt(0).toUpperCase();
  const favoritesCount = tryons?.filter((t) => t.is_favorite).length || 0;

  const isPremium = user?.is_premium || false;
  const isAdmin = user?.role === 'admin';
  const used = limitData?.used ?? 0;
  const limit = limitData?.limit ?? 3;
  const remaining = limit === -1 ? Infinity : Math.max(0, limit - used);
  const progressPercent = limit === -1 ? 100 : Math.min(100, (used / limit) * 100);

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
            <Link href="/" className="nav-link">Дашборд</Link>
            <div className="nav-link nav-link_active">Примерка</div>
            <div className="nav-link">Образы</div>
            <div className="nav-link">Моя одежда</div>
            <div className="nav-link">История</div>
          </nav>
          {isAuthenticated ? (
            <div className="user-menu-container" ref={menuRef}>
              <div
                className="user-pill"
                onClick={() => setIsMenuOpen(!isMenuOpen)}
              >
                <div className="user-avatar">{userInitial}</div>
                <div className="user-name">{userName}</div>
              </div>
              {isMenuOpen && (
                <div className="user-dropdown">
                  <Link href="/dashboard" className="dropdown-item">
                    📊 Мой дашборд
                  </Link>
                  <div className="dropdown-item" onClick={handleSettings}>
                    ⚙️ Настройки
                  </div>
                  {user?.role === 'admin' && (
                    <Link href="/admin" className="dropdown-item">
                      👑 Админ-панель
                    </Link>
                  )}
                  <div className="dropdown-divider"></div>
                  <div className="dropdown-item" onClick={handleLogout}>
                    🚪 Выход
                  </div>
                </div>
              )}
            </div>
          ) : (
            <button className="btn btn-primary" onClick={handleLoginClick}>
              Войти
            </button>
          )}
        </div>
      </header>

      {/* ФОРМА ПРИМЕРКИ - заменяет приветствие и 3 кнопки */}
      <section style={{ marginBottom: '22px' }}>
        <TryonFormStepped />
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
                {Array.from({ length: Math.max(0, 3 - tryons.length) }).map((_, idx) => (
                  <div key={`placeholder-${idx}`} className="tryon-card-new">
                    <div className="tryon-card-name">Создать новый образ</div>
                    <div className="tryon-card-date">Пусто</div>
                    <button className="btn-tryon-open">✨ Создать образ</button>
                  </div>
                ))}
              </>
            ) : (
              <>
                {Array.from({ length: 3 }).map((_, idx) => (
                  <div key={`empty-${idx}`} className="tryon-card-new">
                    <div className="tryon-card-name">Создать новый образ</div>
                    <div className="tryon-card-date">Пусто</div>
                    <button className="btn-tryon-open">✨ Создать образ</button>
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
              <div className="look-name">Офисный лук</div>
              <div className="look-tag">Повседневный строгий</div>
              <button className="btn-chip">✨ Открыть образ</button>
            </div>
            <div className="look-card">
              <div className="look-name">Casual party</div>
              <div className="look-tag">Яркий и стильный</div>
              <button className="btn-chip">✨ Открыть образ</button>
            </div>
          </div>
        </article>

        {/* МОИ ФОТО */}
        <article className="card">
          <div className="section-header">
            <div className="section-title">МОИ ФОТО</div>
            <div className="section-link">Посмотреть все</div>
          </div>
          <p className="card-subtitle">
            Галерея загруженных изображений. Можете использовать их повторно в новых примерках.
          </p>
          <div className="photo-preview-row">
            <div className="photo-thumb">Фото 1</div>
            <div className="photo-thumb">Фото 2</div>
            <div className="photo-thumb">Фото 3</div>
          </div>
        </article>
      </section>

      {/* ИЗБРАННОЕ + РЕКОМЕНДАЦИИ */}
      <section className="favorites-reco-grid">
        {/* Избранное */}
        <article className="card">
          <div className="section-header">
            <div className="section-title">Избранное ({favoritesCount})</div>
            <div className="section-link">Посмотреть все</div>
          </div>
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
