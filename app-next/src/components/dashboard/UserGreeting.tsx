'use client';

import { useAuth } from '@/hooks/useAuth';
import DashboardSection from './DashboardSection';

export default function UserGreeting() {
  const { user } = useAuth();

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Доброе утро';
    if (hour < 18) return 'Добрый день';
    return 'Добрый вечер';
  };

  return (
    <DashboardSection title={`${getGreeting()}, ${user?.name || 'Пользователь'}!`}>
      <p className="text-sm text-gray-600">
        Добро пожаловать в вашу личную студию виртуальной примерки
      </p>
    </DashboardSection>
  );
}
