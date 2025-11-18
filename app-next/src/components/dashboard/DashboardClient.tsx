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
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50">
      <Header />

      <main className="w-full max-w-7xl mx-auto p-6 pt-24">
        <h1 className="text-3xl font-bold mb-6">Мой кабинет</h1>

        {/* Основная сетка Dashboard */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Левая колонка */}
          <div className="lg:col-span-3 space-y-6">
            <UserGreeting />
            <PremiumBanner />
            <Recommendations />
            <LikedItems />
          </div>

          {/* Правая колонка */}
          <div className="lg:col-span-9">
            {/* My Photos - галерея всех примерок */}
            <div className="mb-6">
              <MyPhotos />
            </div>

            {/* Недавние примерки - на всю ширину */}
            <div className="mb-6">
              <RecentTryons />
            </div>

            {/* Нижняя сетка - 3 колонки */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-6">
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

        {/* Нижняя секция - Feedback */}
        <div className="mt-8 glass rounded-4xl p-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div>
              <h3 className="text-lg font-semibold mb-1">Поделитесь мнением</h3>
              <p className="text-sm text-gray-600">Это поможет нам улучшить Tap to look</p>
            </div>
            <button className="btn-primary">
              💌 Отправить отзыв
            </button>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="py-12 px-6 border-t border-white/20 mt-12">
        <div className="max-w-7xl mx-auto text-center text-sm text-gray-600">
          <p>&copy; 2024 Tap to look. Все права защищены.</p>
        </div>
      </footer>
    </div>
  );
}
