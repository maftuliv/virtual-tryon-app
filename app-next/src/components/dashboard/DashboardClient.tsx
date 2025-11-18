'use client';

import { useAuth } from '@/hooks/useAuth';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import Header from '@/components/Header';
import UserGreeting from './UserGreeting';
import PremiumBanner from './PremiumBanner';
import LikedItems from './LikedItems';
import RecentTryons from './RecentTryons';
import MyPhotos from './MyPhotos';
import Recommendations from './Recommendations';
import LooksSection from './LooksSection';
import BrandConstructor from './BrandConstructor';
import StylePlan from './StylePlan';
import ServiceUpdates from './ServiceUpdates';

export default function DashboardClient() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    // Редирект на главную если не авторизован
    if (!isLoading && !isAuthenticated) {
      router.push('/');
    }
  }, [isAuthenticated, isLoading, router]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4" />
          <p className="text-gray-600">Загрузка...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="min-h-screen">
      {/* EXACT page structure from HTML file */}
      <div className="w-full max-w-[1200px] mx-auto px-4 py-6 pb-10">
        <Header />
        {/* HERO GRID: Greeting + Premium + Liked - EXACT from HTML */}
        <section className="grid grid-cols-1 lg:grid-cols-[2.2fr_1.4fr] gap-[18px] mb-[22px]">
          {/* LEFT: Greeting card */}
          <UserGreeting />

          {/* RIGHT: Premium + Liked */}
          <div className="grid grid-rows-2 gap-3.5">
            <PremiumBanner />
            <LikedItems />
          </div>
        </section>

        {/* MAIN GRID: Try-ons+Looks | Photos+Brands+Recommendations - EXACT from HTML */}
        <section className="grid grid-cols-1 lg:grid-cols-[2.05fr_1.6fr] gap-5 mb-6">
          {/* LEFT COLUMN: Try-ons + Looks */}
          <div className="flex flex-col gap-4">
            <RecentTryons />
            <LooksSection />
          </div>

          {/* RIGHT COLUMN: Photos + Brands + Recommendations */}
          <div className="flex flex-col gap-4">
            <MyPhotos />
            <BrandConstructor />
            <Recommendations />
          </div>
        </section>

        {/* LOWER GRID: Style Plan + Service Updates - EXACT from HTML */}
        <section className="grid grid-cols-1 lg:grid-cols-[1.8fr_1.6fr] gap-[18px] mb-4">
          <StylePlan />
          <ServiceUpdates />
        </section>

        {/* FEEDBACK CARD */}
        <section className="card mb-3.5">
          <div className="section-header">
            <div className="section-title">Поделитесь мнением</div>
            <div className="section-link">Подробнее</div>
          </div>
          <p className="card-subtitle">
            Расскажите, что улучшить. Ваши идеи и замечания напрямую влияют на развитие сервиса.
          </p>
          <div className="flex flex-wrap gap-2 mb-3">
            <button className="btn-chip">🐞 Сообщить об ошибке</button>
            <button className="btn-chip">💡 Предложить идею</button>
            <button className="btn-chip">⭐ Оценить качество примерки</button>
          </div>
        </section>

        {/* FOOTER BAR */}
        <div className="flex flex-wrap gap-2.5 justify-end mb-2.5">
          <button className="btn-ghost text-sm">📜 История примерок</button>
          <button className="btn-ghost text-sm">🛟 Поддержка</button>
          <button className="btn-gradient text-sm">💌 Отправить отзыв</button>
        </div>
        <div className="text-[11px] text-[var(--text-muted)] text-center opacity-90">
          Используя сервис, вы соглашаетесь с условиями и политикой конфиденциальности. Все права защищены.
        </div>
      </div>
    </div>
  );
}
