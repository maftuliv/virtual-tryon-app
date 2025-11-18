'use client';

import DashboardSection from './DashboardSection';
import Button from '../Button';

const BRANDS = [
  { id: 'zara', name: 'Zara', color: 'from-black to-gray-800' },
  { id: 'hm', name: 'H&M', color: 'from-red-500 to-red-700' },
  { id: 'mango', name: 'Mango', color: 'from-orange-400 to-yellow-500' },
];

export default function BrandConstructor() {
  return (
    <DashboardSection title="Brand Constructor">
      <p className="text-sm text-gray-600 mb-4">
        Создавайте образы в стиле любимых брендов
      </p>
      <div className="space-y-2">
        {BRANDS.map((brand) => (
          <Button
            key={brand.id}
            variant="secondary"
            size="sm"
            fullWidth
            className={`bg-gradient-to-r ${brand.color} text-white hover:opacity-90`}
          >
            {brand.name}
          </Button>
        ))}
      </div>
    </DashboardSection>
  );
}
