'use client';

import { useTryons } from '@/hooks/useTryons';
import DashboardSection from './DashboardSection';
import Image from 'next/image';
import { formatDistanceToNow } from 'date-fns';
import { ru } from 'date-fns/locale';

export default function RecentTryons() {
  const { tryons, isLoading } = useTryons();

  const recentTryons = tryons?.slice(0, 6) || [];

  return (
    <DashboardSection title="Недавние примерки">
      {isLoading ? (
        <div className="text-sm text-gray-500">Загрузка...</div>
      ) : recentTryons.length > 0 ? (
        <div className="grid grid-cols-3 gap-3">
          {recentTryons.map((tryon) => (
            <div
              key={tryon.id}
              className="group cursor-pointer"
            >
              <div className="relative aspect-[3/4] rounded-xl overflow-hidden mb-2">
                <Image
                  src={tryon.r2_url}
                  alt={tryon.title || 'Примерка'}
                  fill
                  className="object-cover group-hover:scale-105 transition-transform duration-200"
                  sizes="(max-width: 768px) 33vw, 200px"
                />
              </div>
              <p className="text-xs text-gray-600 truncate">
                {tryon.title || 'Без названия'}
              </p>
              <p className="text-xs text-gray-400">
                {formatDistanceToNow(new Date(tryon.created_at), {
                  addSuffix: true,
                  locale: ru,
                })}
              </p>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-sm text-gray-500">
          Создайте свою первую виртуальную примерку!
        </p>
      )}
    </DashboardSection>
  );
}
