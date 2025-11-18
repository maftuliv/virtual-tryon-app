'use client';

export default function StylePlan() {
  return (
    <article className="card">
      <div className="section-header">
        <div className="section-title">План стиля на месяц</div>
        <div className="section-link">Подробнее</div>
      </div>

      <p className="card-subtitle">
        Следите за прогрессом, чтобы шаг за шагом прокачивать свой стиль.
      </p>

      <ul className="m-0 pl-[18px] mt-2.5 text-[13px] text-[var(--text-muted)] space-y-0">
        <li className="text-[#34a853]">Загрузить базовое фото в полный рост</li>
        <li className="text-[#34a853]">Сделать 3 примерки с разной одеждой</li>
        <li>Создать 1 образ для работы</li>
        <li>Создать 1 образ для свидания</li>
        <li>Собрать капсулу из брендов на неделю</li>
      </ul>

      <div className="mt-3">
        <button className="btn btn-gradient">Продолжить план</button>
      </div>
    </article>
  );
}
