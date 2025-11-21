'use client';

import { useAuth } from '@/hooks/useAuth';
import { useTryons } from '@/hooks/useTryons';
import Link from 'next/link';

export default function UserGreeting() {
  const { user } = useAuth();
  const { tryons } = useTryons();

  const userName = user?.full_name || user?.email?.split('@')[0] || 'Пользователь';
  const tryonCount = tryons?.length || 0;
  const favoritesCount = tryons?.filter((t) => t.is_favorite).length || 0;

  return (
    <article className="card">
      <h1 className="text-[26px] font-bold mb-1.5">
        Привет, {userName} 👋
      </h1>
      <p className="text-[15px] text-[var(--text-muted)] mb-4 max-w-[460px]">
        Здесь твоя зона стиля. Что сделаем сейчас: примерку, новый образ или соберём look из брендов?
      </p>

      {/* Mode buttons */}
      <div className="flex flex-wrap gap-2.5 mb-3.5">
        <Link
          href="/#tryon"
          className="btn-gradient flex-1 min-w-[150px] justify-start"
        >
          <span className="text-lg">👗</span>
          <span>Сделать примерку</span>
        </Link>
        <button className="btn-ghost flex-1 min-w-[150px] justify-start">
          <span className="text-lg">✨</span>
          <span>Создать образ по фильтрам</span>
        </button>
        <button className="btn-ghost flex-1 min-w-[150px] justify-start">
          <span className="text-lg">🧩</span>
          <span>Собрать образ из брендов</span>
        </button>
      </div>

      {/* Meta info */}
      <div className="flex flex-wrap gap-2.5">
        <div className="meta-pill">
          <span className="meta-dot"></span>
          <span>Последняя примерка: <strong>недавно</strong></span>
        </div>
        <div className="meta-pill">
          <span>👕 Образов создано: <strong>{tryonCount}</strong></span>
        </div>
        <div className="meta-pill">
          <span>⭐ Мне понравилось: <strong>{favoritesCount}</strong></span>
        </div>
      </div>
    </article>
  );
}
