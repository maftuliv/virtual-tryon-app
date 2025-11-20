'use client';

interface TryOnCTAProps {
  canGenerate: boolean;
  isGenerating: boolean;
  onGenerate: () => void;
  onReset: () => void;
}

export default function TryOnCTA({ canGenerate, isGenerating, onGenerate, onReset }: TryOnCTAProps) {
  return (
    <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-3xl p-6 shadow-sm border border-purple-100">
      <h4 className="font-semibold text-gray-800 mb-3">Готовы примерить?</h4>
      <p className="text-sm text-gray-600 mb-6">
        Загрузите своё фото и желаемую одежду. Нажмите кнопку - всё остальное сделаем мы 😊
      </p>

      <button
        onClick={onGenerate}
        disabled={!canGenerate || isGenerating}
        className={`w-full py-4 px-6 rounded-2xl font-semibold text-white transition-all mb-4 ${
          canGenerate && !isGenerating
            ? 'bg-gradient-to-r from-purple-500 via-pink-500 to-purple-600 hover:shadow-lg hover:scale-105'
            : 'bg-gray-300 cursor-not-allowed'
        }`}
      >
        {isGenerating ? (
          <span className="flex items-center justify-center gap-2">
            <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
            Генерация...
          </span>
        ) : (
          <span className="flex items-center justify-center gap-2">
            ✨ сделать примерку
          </span>
        )}
      </button>

      <div className="flex items-center justify-center gap-2 mb-4">
        <div className="flex items-center gap-1">
          <span className="text-2xl">🎉</span>
          <span className="text-sm font-medium text-purple-700">∞ примерок</span>
        </div>
        <div className="flex-1 h-2 bg-purple-200 rounded-full overflow-hidden">
          <div className="h-full w-full bg-gradient-to-r from-purple-400 to-pink-400 rounded-full animate-pulse" />
        </div>
        <span className="text-2xl">🍰</span>
      </div>

      <div className="text-center space-y-1">
        <p className="text-sm font-semibold text-pink-600">
          Бесплатно. Без регистрации. Качественно
        </p>
        <p className="text-xs text-gray-500">
          Спасибо, что используете наш сервис! Мы ценим каждого пользователя и постоянно работаем над улучшением качества примерки. Ваша поддержка вдохновляет нас делать сервис ещё лучше! 💜
        </p>
      </div>

      <button
        onClick={onReset}
        disabled={isGenerating}
        className="mt-4 w-full py-2 px-4 border border-gray-200 rounded-xl hover:bg-gray-50 transition-colors text-sm font-medium text-gray-700"
      >
        Сбросить
      </button>
    </div>
  );
}
