'use client';

export default function MyPhotos() {
  return (
    <article className="card">
      <div className="section-header">
        <div className="section-title">Мои фото</div>
        <div className="section-link">Управлять</div>
      </div>

      <p className="card-subtitle">
        Базовые фотографии, с которыми мы работаем. Рекомендуем периодически обновлять их.
      </p>

      <div className="flex flex-wrap gap-3">
        {/* Photo card 1 */}
        <div
          className="flex-1 min-w-[120px] h-[140px] rounded-[18px] flex flex-col items-center justify-center text-center p-2 text-xs text-[var(--text-muted)]"
          style={{
            background: 'linear-gradient(135deg, #f7efff, #ffe9f4)',
            border: '1px solid rgba(237, 222, 255, 0.9)',
            boxShadow: '0 10px 20px rgba(43, 18, 83, 0.15)',
          }}
        >
          <div className="mb-1.5">Фото в полный рост</div>
          <div className="text-[11px] text-[var(--text-muted)]">
            Основное для примерок
          </div>
          <div className="text-[11px] mt-1 text-[#34a853]">Рекомендовано ✔</div>
        </div>

        {/* Photo card 2 */}
        <div
          className="flex-1 min-w-[120px] h-[140px] rounded-[18px] flex flex-col items-center justify-center text-center p-2 text-xs text-[var(--text-muted)]"
          style={{
            background: 'linear-gradient(135deg, #f7efff, #ffe9f4)',
            border: '1px solid rgba(237, 222, 255, 0.9)',
            boxShadow: '0 10px 20px rgba(43, 18, 83, 0.15)',
          }}
        >
          <div className="mb-1.5">Портрет</div>
          <div className="text-[11px]">Подходит для аватаров и тестов</div>
        </div>

        {/* Photo card 3 */}
        <div
          className="flex-1 min-w-[120px] h-[140px] rounded-[18px] flex flex-col items-center justify-center text-center p-2 text-xs text-[var(--text-muted)]"
          style={{
            background: 'linear-gradient(135deg, #f7efff, #ffe9f4)',
            border: '1px solid rgba(237, 222, 255, 0.9)',
            boxShadow: '0 10px 20px rgba(43, 18, 83, 0.15)',
          }}
        >
          <div className="mb-1.5">Фото сбоку</div>
          <div className="text-[11px]">Для более точной посадки</div>
        </div>

        {/* Add photo card */}
        <div
          className="flex-1 min-w-[120px] h-[140px] rounded-[18px] flex flex-col items-center justify-center text-center p-2 text-xs cursor-pointer hover:scale-105 transition-transform"
          style={{
            background: 'rgba(255, 255, 255, 0.75)',
            border: '2px dashed rgba(182, 152, 255, 0.95)',
            boxShadow: '0 10px 20px rgba(43, 18, 83, 0.15)',
          }}
        >
          <div className="text-2xl mb-1">+</div>
          <div className="text-[11px] text-[var(--text-muted)]">
            Добавить новое фото
          </div>
        </div>
      </div>

      <div className="mt-2.5">
        <button className="btn btn-ghost">Обновить базовое фото</button>
      </div>
    </article>
  );
}
