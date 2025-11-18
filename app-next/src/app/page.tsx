import HomeClient from '@/components/HomeClient';

// Server Component - статический контент рендерится на сервере
export default function Home() {
  return (
    <>
      <HomeClient />

      {/* About Section - Server Component */}
      <section id="about" className="py-20 px-6 bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50">
        <div className="max-w-4xl mx-auto">
          <div className="glass glass-hover rounded-4xl p-12 text-center">
            <h2 className="text-3xl font-bold mb-6">
              О технологии
            </h2>
            <p className="text-gray-600 mb-4">
              Tap to look использует передовые алгоритмы искусственного интеллекта
              для создания реалистичной виртуальной примерки одежды.
            </p>
            <p className="text-gray-600">
              Наша технология анализирует форму тела, освещение и текстуру одежды,
              чтобы создать максимально точное изображение того, как вещь будет на вас сидеть.
            </p>
          </div>
        </div>
      </section>

      {/* Footer - Server Component */}
      <footer className="py-12 px-6 border-t border-white/20 bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50">
        <div className="max-w-7xl mx-auto text-center text-sm text-gray-600">
          <p>&copy; 2024 Tap to look. Все права защищены.</p>
        </div>
      </footer>
    </>
  );
}
