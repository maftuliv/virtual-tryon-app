'use client';

import Button from '../Button';
import DashboardSection from './DashboardSection';

export default function PremiumBanner() {
  return (
    <DashboardSection
      title="Premium доступ"
      variant="strong"
      className="bg-gradient-to-br from-primary/20 to-purple-500/20"
    >
      <p className="text-sm text-gray-700 mb-4">
        Получите неограниченный доступ ко всем функциям и премиум фильтрам
      </p>
      <Button variant="primary" size="sm" fullWidth>
        Подключить Premium
      </Button>
    </DashboardSection>
  );
}
