'use client';

export default function ServiceUpdates() {
  return (
    <article className="card">
      <div className="section-header">
        <div className="section-title">Обновления сервиса</div>
      </div>

      <p className="card-subtitle">
        Мы постоянно улучшаем Tap to look, чтобы примерка была точнее, а образы — интереснее.
      </p>

      <ul className="m-0 pl-[18px] mt-2 text-[13px] text-[var(--text-muted)] space-y-0">
        <li>Добавили новые образы для новогодних вечеринок.</li>
        <li>Улучшили качество примерок для тёмной одежды.</li>
        <li>Скоро: полноценный конструктор образов из Zara и H&M.</li>
      </ul>
    </article>
  );
}
