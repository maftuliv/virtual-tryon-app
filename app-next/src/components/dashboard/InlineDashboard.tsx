'use client';

import UserGreeting from './UserGreeting';
import PremiumBanner from './PremiumBanner';
import LikedItems from './LikedItems';
import RecentTryons from './RecentTryons';
import LooksSection from './LooksSection';
import BrandConstructor from './BrandConstructor';
import StylePlan from './StylePlan';
import ServiceUpdates from './ServiceUpdates';

export default function InlineDashboard() {
  return (
    <div className="w-full max-w-7xl mx-auto p-6 mt-8">
      {/* Заголовок Dashboard */}
      <h2 className="text-3xl font-bold mb-6 text-center">Ваш кабинет</h2>

      {/* Основная сетка Dashboard */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Левая колонка */}
        <div className="lg:col-span-3 space-y-6">
          <UserGreeting />
          <PremiumBanner />
          <LikedItems />
        </div>

        {/* Правая колонка */}
        <div className="lg:col-span-9">
          {/* Недавние примерки - на всю ширину */}
          <div className="mb-6">
            <RecentTryons />
          </div>

          {/* Нижняя сетка - 3 колонки */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <LooksSection />
            <div className="space-y-6">
              <BrandConstructor />
            </div>
            <div className="space-y-6">
              <StylePlan />
              <ServiceUpdates />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
