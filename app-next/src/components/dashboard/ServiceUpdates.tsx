'use client';

import DashboardSection from './DashboardSection';

const UPDATES = [
  {
    id: 1,
    title: 'Новые AI фильтры',
    description: 'Добавлены фильтры для вечерних образов',
    date: '2024-01-15',
    type: 'feature' as const,
  },
  {
    id: 2,
    title: 'Улучшена скорость',
    description: 'Генерация стала быстрее на 40%',
    date: '2024-01-10',
    type: 'improvement' as const,
  },
  {
    id: 3,
    title: 'Исправлены ошибки',
    description: 'Улучшена стабильность работы',
    date: '2024-01-05',
    type: 'bugfix' as const,
  },
];

const typeIcons = {
  feature: '✨',
  improvement: '⚡',
  bugfix: '🔧',
};

export default function ServiceUpdates() {
  return (
    <DashboardSection title="Обновления сервиса">
      <div className="space-y-3">
        {UPDATES.map((update) => (
          <div key={update.id} className="glass rounded-xl p-3">
            <div className="flex items-start gap-2">
              <span className="text-lg">{typeIcons[update.type]}</span>
              <div className="flex-1">
                <p className="text-sm font-medium">{update.title}</p>
                <p className="text-xs text-gray-600 mt-1">{update.description}</p>
                <p className="text-xs text-gray-400 mt-1">{update.date}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </DashboardSection>
  );
}
