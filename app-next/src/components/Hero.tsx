'use client';

import Button from './Button';

export default function Hero() {
  const scrollToTryon = () => {
    document.getElementById('tryon')?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <section className="min-h-screen flex items-center justify-center px-6 pt-20">
      <div className="max-w-4xl mx-auto text-center">
        {/* Hero content */}
        <div className="glass glass-hover rounded-4xl p-12 mb-8 animate-fade-in">
          <h1 className="text-5xl md:text-6xl font-bold mb-6 bg-gradient-to-r from-primary via-purple-600 to-pink-600 bg-clip-text text-transparent">
            Виртуальная примерка
            <br />
            с помощью AI
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
            Загрузите свое фото и посмотрите, как на вас будет сидеть любая вещь.
            Технология искусственного интеллекта создаст реалистичную примерку за секунды.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button variant="primary" size="lg" onClick={scrollToTryon}>
              Попробовать бесплатно
            </Button>
            <Button variant="secondary" size="lg">
              Смотреть примеры
            </Button>
          </div>
        </div>

        {/* Features */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 animate-slide-up">
          <div className="glass glass-hover rounded-4xl p-6">
            <div className="text-4xl mb-3">⚡</div>
            <h3 className="font-semibold mb-2">Быстро</h3>
            <p className="text-sm text-gray-600">
              Результат готов менее чем за 30 секунд
            </p>
          </div>
          <div className="glass glass-hover rounded-4xl p-6">
            <div className="text-4xl mb-3">🎯</div>
            <h3 className="font-semibold mb-2">Точно</h3>
            <p className="text-sm text-gray-600">
              Реалистичная посадка одежды с сохранением деталей
            </p>
          </div>
          <div className="glass glass-hover rounded-4xl p-6">
            <div className="text-4xl mb-3">🔒</div>
            <h3 className="font-semibold mb-2">Безопасно</h3>
            <p className="text-sm text-gray-600">
              Ваши фото хранятся конфиденциально и защищены
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
