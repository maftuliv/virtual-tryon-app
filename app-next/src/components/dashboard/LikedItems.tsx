'use client';

import { useTryons } from '@/hooks/useTryons';
import Image from 'next/image';

export default function LikedItems() {
  const { tryons, isLoading } = useTryons();

  const likedTryons = tryons?.filter((tryon) => tryon.is_favorite) || [];
  const likedCount = likedTryons.length;

  return (
    <article className="card">
      <div className="section-header">
        <div className="section-title">Мне понравилось ❤️</div>
        <div className="section-link">Открыть галерею</div>
      </div>

      <div className="text-[28px] font-bold my-1 text-[var(--primary)]">
        {likedCount}
      </div>

      <p className="card-subtitle">
        Ваши любимые результаты. Можно вернуться к ним и доработать детали.
      </p>

      {!isLoading && likedTryons.length > 0 ? (
        <div className="flex gap-2">
          {likedTryons.slice(0, 3).map((tryon, idx) => (
            <div
              key={tryon.id}
              className="w-[46px] h-[58px] rounded-[14px] overflow-hidden relative"
              style={{
                background: 'linear-gradient(135deg, #f8edff, #ffe5f2)',
                boxShadow: '0 8px 20px rgba(57, 20, 95, 0.18)',
              }}
            >
              <Image
                src={tryon.r2_url}
                alt={`Look ${idx + 1}`}
                fill
                className="object-cover"
                sizes="46px"
              />
            </div>
          ))}
        </div>
      ) : (
        <div className="flex gap-2">
          {[1, 2, 3].map((idx) => (
            <div
              key={idx}
              className="w-[46px] h-[58px] rounded-[14px] flex items-center justify-center text-[10px] text-[var(--text-muted)]"
              style={{
                background: 'linear-gradient(135deg, #f8edff, #ffe5f2)',
                boxShadow: '0 8px 20px rgba(57, 20, 95, 0.18)',
              }}
            >
              Look {idx}
            </div>
          ))}
        </div>
      )}
    </article>
  );
}
