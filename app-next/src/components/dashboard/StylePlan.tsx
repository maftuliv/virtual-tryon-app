'use client';

import DashboardSection from './DashboardSection';
import Button from '../Button';

export default function StylePlan() {
  return (
    <DashboardSection title="Style Plan">
      <p className="text-sm text-gray-600 mb-4">
        Персональные рекомендации по стилю от AI
      </p>
      <div className="space-y-2 mb-4">
        <div className="glass rounded-xl p-3">
          <p className="text-sm font-medium">Весна 2024</p>
          <p className="text-xs text-gray-600">Пастельные оттенки, легкие ткани</p>
        </div>
        <div className="glass rounded-xl p-3">
          <p className="text-sm font-medium">Деловой стиль</p>
          <p className="text-xs text-gray-600">Классика + современность</p>
        </div>
      </div>
      <Button variant="primary" size="sm" fullWidth>
        Создать новый план
      </Button>
    </DashboardSection>
  );
}
