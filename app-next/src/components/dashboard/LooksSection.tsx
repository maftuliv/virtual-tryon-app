'use client';

const LOOKS = [
  { id: 1, name: 'Образ для свидания', tag: 'Элегантный вечерний стиль' },
  { id: 2, name: 'Образ для офиса', tag: 'Минимализм и нейтральные оттенки' },
  { id: 3, name: 'Образ для путешествия', tag: 'Удобно и стильно на каждый день' },
];

export default function LooksSection() {
  return (
    <article className="card">
      <div className="section-header">
        <div className="section-title">Мои образы</div>
        <div className="section-link">Открыть все</div>
      </div>

      <p className="card-subtitle">
        Образы, созданные с помощью фильтров: свидание, офис, вечеринка, путешествие и другие.
      </p>

      <div className="flex flex-wrap gap-3 mb-3.5">
        {LOOKS.map((look) => (
          <div
            key={look.id}
            className="flex-1 min-w-[150px] rounded-[18px] p-2.5 text-[13px]"
            style={{
              background: 'linear-gradient(135deg, #fbefff, #ffe5f2)',
              border: '1px solid rgba(244, 221, 255, 0.9)',
              boxShadow: '0 10px 24px rgba(58, 12, 94, 0.18)',
            }}
          >
            <div className="font-semibold mb-1">{look.name}</div>
            <div className="text-xs text-[var(--text-muted)] mb-2">{look.tag}</div>
            <button className="btn-chip">✨ Открыть образ</button>
          </div>
        ))}
      </div>

      <button className="btn-gradient w-full">
        Создать новый образ по фильтрам
      </button>
    </article>
  );
}
