'use client';

export default function PremiumBanner() {
  const remainingTryons = 50;
  const totalTryons = 100;
  const progressPercent = (remainingTryons / totalTryons) * 100;

  return (
    <article className="card">
      <div className="card-title">Премиум аккаунт</div>
      <p className="text-sm mb-2.5">{remainingTryons} примерок осталось в этом месяце</p>

      {/* Progress bar */}
      <div className="w-full h-2.5 rounded-full bg-[rgba(233,219,255,0.9)] mb-2 overflow-hidden relative">
        <div
          className="absolute inset-0 rounded-full"
          style={{
            width: `${progressPercent}%`,
            background: 'linear-gradient(90deg, #ffcc68, #ff78d3, #9b5cff)',
          }}
        />
      </div>

      <p className="text-xs text-[var(--text-muted)] mb-1.5">
        Используйте лимит, чтобы протестировать максимум образов. В следующем месяце счётчик обновится.
      </p>

      <button className="btn-premium w-full">
        Подробнее о премиуме
      </button>
    </article>
  );
}
