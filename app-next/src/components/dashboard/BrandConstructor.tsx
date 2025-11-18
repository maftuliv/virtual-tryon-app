'use client';

const BRANDS = [
  { id: 'zara', name: 'Zara · Осень', tagline: 'Плащи, джинсы, базовые свитшоты' },
  { id: 'hm', name: 'H&M · Casual', tagline: 'На каждый день в городе' },
  { id: 'mango', name: 'Mango · Вечер', tagline: 'Платья и вечерние комплекты' },
];

export default function BrandConstructor() {
  return (
    <article className="card">
      <div className="section-header">
        <div className="section-title">Конструктор образов из брендов</div>
        <div className="section-link">Открыть конструктор</div>
      </div>

      <p className="card-subtitle">
        Собирайте образы из готовых подборок Zara, H&M, Mango и других брендов. Выберите вещи — мы примерим их на вас.
      </p>

      <div className="flex flex-wrap gap-2.5 mt-1.5">
        {BRANDS.map((brand) => (
          <div
            key={brand.id}
            className="flex-1 min-w-[120px] rounded-2xl p-2 text-xs"
            style={{
              background: 'linear-gradient(135deg, #f4f0ff, #ffe7f0)',
              border: '1px solid rgba(234, 219, 255, 0.95)',
              boxShadow: '0 8px 20px rgba(40, 16, 80, 0.16)',
            }}
          >
            <div className="font-semibold mb-0.5">{brand.name}</div>
            <div className="text-[11px] text-[var(--text-muted)]">
              {brand.tagline}
            </div>
          </div>
        ))}
      </div>

      <div className="mt-3">
        <button className="btn btn-gradient">Собрать образ из брендов</button>
      </div>
    </article>
  );
}
