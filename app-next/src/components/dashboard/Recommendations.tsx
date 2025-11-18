'use client';

export default function Recommendations() {
  return (
    <article className="card">
      <div className="section-header">
        <div className="section-title">Рекомендации</div>
      </div>

      <p className="card-subtitle">
        Сегодняшняя рекомендация: попробуйте образ для свидания с тёмным низом и светлым верхом.
      </p>

      <div className="flex flex-wrap gap-2 my-2 mb-3">
        <button className="btn-chip">💼 На работу</button>
        <button className="btn-chip">❤️ На свидание</button>
        <button className="btn-chip">🧳 В путешествие</button>
        <button className="btn-chip">🎉 На вечеринку</button>
      </div>

      <ul className="m-0 pl-[18px] text-[13px] text-[var(--text-muted)] space-y-0 mb-3">
        <li>
          Вы уже протестировали 8 образов. Ещё 2 — и мы соберём для вас подборку "Топ-3 образа месяца".
        </li>
        <li>
          Попробуйте создать капсулу из 5–7 вещей для ближайших недель.
        </li>
      </ul>

      <div className="mt-3">
        <button className="btn btn-ghost">Создать образ по сегодняшней рекомендации</button>
      </div>
    </article>
  );
}
