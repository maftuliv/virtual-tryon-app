'use client';

import DashboardSection from './DashboardSection';
import Button from '../Button';

const LOOKS = [
  { id: 1, name: 'Casual', emoji: '👕' },
  { id: 2, name: 'Business', emoji: '👔' },
  { id: 3, name: 'Party', emoji: '🎉' },
  { id: 4, name: 'Sport', emoji: '⚽' },
  { id: 5, name: 'Beach', emoji: '🏖️' },
];

export default function LooksSection() {
  return (
    <DashboardSection title="Looks - AI фильтры стиля">
      <p className="text-sm text-gray-600 mb-4">
        Примерьте образы под разные случаи жизни
      </p>
      <div className="grid grid-cols-2 gap-2">
        {LOOKS.map((look) => (
          <Button
            key={look.id}
            variant="secondary"
            size="sm"
            className="flex items-center justify-center gap-2"
          >
            <span className="text-xl">{look.emoji}</span>
            <span>{look.name}</span>
          </Button>
        ))}
      </div>
    </DashboardSection>
  );
}
