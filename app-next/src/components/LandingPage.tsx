'use client';

import { useAuth } from '@/hooks/useAuth';
import { useTryons } from '@/hooks/useTryons';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

export default function LandingPage() {
  const { user, isAuthenticated } = useAuth();
  const { tryons } = useTryons();
  const router = useRouter();

  const userName = user?.full_name || user?.email?.split('@')[0] || 'Пользователь';
  const userInitial = userName.charAt(0).toUpperCase();
  const favoritesCount = tryons?.filter((t) => t.is_favorite).length || 0;

  const handleLoginClick = () => {
    router.push('/api/auth/google/login');
  };

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
            <div className="user-pill">
              <div className="user-avatar">{userInitial}</div>
              <span className="user-name">{userName}</span>
              <span className="badge-premium">Premium</span>
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
        </article>

        {/* RIGHT: Премиум аккаунт */}
        <article className="card">
          <div className="card-title">Премиум аккаунт</div>
          <p className="premium-count">50 примерок осталось в этом месяце</p>
          <div className="premium-progress">
            <div className="premium-progress-fill"></div>
          </div>
          <p className="premium-note">
            Используйте лимит, чтобы протестировать максимум образов. В следующем месяце счётчик обновится.
          </p>
          <button className="btn btn-premium">Подробнее о премиуме</button>
        </article>
      </section>

      {/* ПОДПИСЬ */}
      <section className="hero-grid" style={{ marginTop: '-10px' }}>
        <article className="card">
          <div className="hero-meta-row">
            <div className="meta-pill">
              <span className="meta-dot"></span>
              Последняя примерка: <strong>вчера</strong>
            </div>
            <div className="meta-pill">
              🎨 Образов создано: <strong>12</strong>
            </div>
            <div className="meta-pill">
              ⭐ Лайкнутые образы: <strong>{favoritesCount}</strong>
            </div>
          </div>
        </article>
        <div></div>
      </section>

      {/* ТРИ КНОПКИ */}
      <section style={{ marginBottom: '22px' }}>
        <div className="hero-modes" style={{ maxWidth: '100%' }}>
          <Link href="#tryon">
            <button className="btn btn-gradient mode-btn">
              <span className="mode-icon">👔</span> Сделать примерку
            </button>
          </Link>
          <button className="btn btn-ghost mode-btn">
            <span className="mode-icon">✨</span> Создать свой образ
          </button>
          <button className="btn btn-ghost mode-btn">
            <span className="mode-icon">🧩</span> Собрать образ из брендов
          </button>
        </div>
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
          <div className="card-row">
            {tryons && tryons.length > 0 ? (
              tryons.slice(0, 4).map((tryon, idx) => (
                <div key={tryon.id || idx} className="tryon-card">
                  <div className="tryon-thumb">Превью образа</div>
                  <div className="tryon-body">
                    <div className="tryon-name">{tryon.title || `Образ ${idx + 1}`}</div>
                    <div className="tryon-date">{new Date(tryon.created_at).toLocaleDateString('ru-RU')}</div>
                    <div className="tryon-actions">
                      <button className="btn-small btn-small-solid">Открыть</button>
                      <button className="btn-small btn-small-outline">Похожий</button>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="tryon-card">
                <div className="tryon-thumb">Новый образ</div>
                <div className="tryon-body">
                  <div className="tryon-name">Создать с нуля</div>
                  <div className="tryon-date">Черновик</div>
                  <div className="tryon-actions">
                    <Link href="#tryon">
                      <button className="btn-small btn-small-solid">Создать</button>
                    </Link>
                    <button className="btn-small btn-small-outline">Шаблон</button>
                  </div>
                </div>
              </div>
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

      {/* ПОДЕЛИТЕСЬ МНЕНИЕМ */}
      <section className="card" style={{ marginBottom: '14px' }}>
        <div className="section-header">
          <div className="section-title">Поделитесь мнением</div>
          <div className="section-link">Подробнее</div>
        </div>
        <p className="card-subtitle">
          Расскажите, что улучшить. Ваши идеи и замечания напрямую влияют на развитие сервиса.
        </p>
        <div className="chip-row">
          <button className="btn-chip">🐛 Сообщить об ошибке</button>
          <button className="btn-chip">💡 Предложить идею</button>
          <button className="btn-chip">⭐ Оценить качество примерки</button>
        </div>
      </section>

      {/* ПОДДЕРЖКА (FOOTER) */}
      <div className="footer-bar">
        <button className="btn-ghost">📜 История примерок</button>
        <button className="btn-ghost">💬 Поддержка</button>
        <button className="btn-accent">💌 Отправить отзыв</button>
      </div>
      <div className="footer-legal">
        Используя сервис, вы соглашаетесь с условиями и политикой конфиденциальности. Все права защищены.
      </div>
    </div>
  );
}
