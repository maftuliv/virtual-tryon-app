'use client';

import { useTryons } from '@/hooks/useTryons';
import Image from 'next/image';
import { formatDistanceToNow } from 'date-fns';
import { ru } from 'date-fns/locale';

export default function RecentTryons() {
  const { tryons, isLoading } = useTryons();

  const recentTryons = tryons?.slice(0, 4) || [];

  return (
    <article className="card">
      <div className="section-header">
        <div className="section-title">Мои примерки</div>
        <div className="section-link">Посмотреть все</div>
      </div>

      <p className="card-subtitle">
        Последние результаты примерки. Откройте, чтобы сохранить, поделиться или создать похожий образ.
      </p>

      {isLoading ? (
        <div className="text-sm text-[var(--text-muted)]">Загрузка...</div>
      ) : (
        <div className="flex gap-3.5 overflow-x-auto pb-1">
          {recentTryons.map((tryon) => (
            <div
              key={tryon.id}
              className="flex-shrink-0 w-[170px] rounded-[18px] overflow-hidden"
              style={{
                background: 'rgba(255, 255, 255, 0.97)',
                border: '1px solid rgba(241, 229, 255, 0.9)',
                boxShadow: '0 12px 30px rgba(38, 9, 88, 0.18)',
              }}
            >
              {/* Thumbnail */}
              <div className="h-[120px] relative bg-gradient-to-br from-[#d9d4f2] to-[#f6e6ff]">
                <Image
                  src={tryon.r2_url}
                  alt={tryon.title || 'Примерка'}
                  fill
                  className="object-cover"
                  sizes="170px"
                />
              </div>

              {/* Body */}
              <div className="p-3 text-[13px]">
                <div className="font-semibold mb-1 truncate">
                  {tryon.title || 'Без названия'}
                </div>
                <div className="text-xs text-[var(--text-muted)] mb-2">
                  {formatDistanceToNow(new Date(tryon.created_at), {
                    addSuffix: true,
                    locale: ru,
                  })}
                </div>

                {/* Actions */}
                <div className="flex gap-1.5">
                  <button className="btn-small btn-small-solid flex-1">
                    Открыть
                  </button>
                  <button className="btn-small btn-small-outline flex-1">
                    Похожий
                  </button>
                </div>
              </div>
            </div>
          ))}

          {/* Add new card */}
          <div
            className="flex-shrink-0 w-[170px] rounded-[18px] overflow-hidden cursor-pointer hover:scale-[1.02] transition-transform"
            style={{
              background: 'rgba(255, 255, 255, 0.97)',
              border: '1px solid rgba(241, 229, 255, 0.9)',
              boxShadow: '0 12px 30px rgba(38, 9, 88, 0.18)',
            }}
          >
            <div className="h-[120px] bg-gradient-to-br from-[#d9d4f2] to-[#f6e6ff] flex items-center justify-center text-xs text-[var(--text-muted)]">
              Новый образ
            </div>
            <div className="p-3 text-[13px]">
              <div className="font-semibold mb-1">Создать с нуля</div>
              <div className="text-xs text-[var(--text-muted)] mb-2">Черновик</div>
              <div className="flex gap-1.5">
                <button className="btn-small btn-small-solid flex-1">
                  Создать
                </button>
                <button className="btn-small btn-small-outline flex-1">
                  Шаблон
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </article>
  );
}
