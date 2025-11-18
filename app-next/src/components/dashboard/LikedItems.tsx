'use client';

import { useTryons } from '@/hooks/useTryons';
import DashboardSection from './DashboardSection';
import Image from 'next/image';

export default function LikedItems() {
  const { tryons, isLoading } = useTryons();

  const likedTryons = tryons?.filter((tryon) => tryon.is_favorite).slice(0, 3) || [];

  return (
    <DashboardSection title="Избранное">
      {isLoading ? (
        <div className="text-sm text-gray-500">Загрузка...</div>
      ) : likedTryons.length > 0 ? (
        <div className="grid grid-cols-3 gap-2">
          {likedTryons.map((tryon) => (
            <div
              key={tryon.id}
              className="relative aspect-[3/4] rounded-xl overflow-hidden group cursor-pointer"
            >
              <Image
                src={tryon.r2_url}
                alt={tryon.title || 'Избранная примерка'}
                fill
                className="object-cover group-hover:scale-105 transition-transform duration-200"
                sizes="(max-width: 768px) 33vw, 150px"
              />
            </div>
          ))}
        </div>
      ) : (
        <p className="text-sm text-gray-500">
          У вас пока нет избранных примерок
        </p>
      )}
    </DashboardSection>
  );
}
