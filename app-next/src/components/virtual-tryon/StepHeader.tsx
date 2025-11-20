'use client';

interface StepHeaderProps {
  currentStep: 1 | 2;
}

export default function StepHeader({ currentStep }: StepHeaderProps) {
  return (
    <div className="flex items-center justify-center gap-4 mb-8">
      {/* Шаг 1 */}
      <div
        className={`flex items-center gap-3 px-6 py-3 rounded-2xl transition-all ${
          currentStep === 1
            ? 'bg-purple-100 border-2 border-purple-300'
            : 'bg-white border-2 border-gray-200'
        }`}
      >
        <div
          className={`w-10 h-10 rounded-full flex items-center justify-center ${
            currentStep === 1 ? 'bg-purple-200' : 'bg-gray-100'
          }`}
        >
          <svg
            className={`w-6 h-6 ${currentStep === 1 ? 'text-purple-600' : 'text-gray-400'}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"
            />
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"
            />
          </svg>
        </div>
        <div>
          <div className={`text-sm font-semibold ${currentStep === 1 ? 'text-purple-700' : 'text-gray-500'}`}>
            Шаг 1
          </div>
          <div className={`text-xs ${currentStep === 1 ? 'text-purple-600' : 'text-gray-400'}`}>
            Загрузите своё фото
          </div>
        </div>
        {currentStep >= 1 && (
          <svg className="w-5 h-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
              clipRule="evenodd"
            />
          </svg>
        )}
      </div>

      {/* Стрелка */}
      <svg className="w-6 h-6 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
      </svg>

      {/* Шаг 2 */}
      <div
        className={`flex items-center gap-3 px-6 py-3 rounded-2xl transition-all ${
          currentStep === 2
            ? 'bg-purple-100 border-2 border-purple-300'
            : 'bg-white border-2 border-gray-200'
        }`}
      >
        <div
          className={`w-10 h-10 rounded-full flex items-center justify-center ${
            currentStep === 2 ? 'bg-purple-200' : 'bg-gray-100'
          }`}
        >
          <svg
            className={`w-6 h-6 ${currentStep === 2 ? 'text-purple-600' : 'text-gray-400'}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01"
            />
          </svg>
        </div>
        <div>
          <div className={`text-sm font-semibold ${currentStep === 2 ? 'text-purple-700' : 'text-gray-500'}`}>
            Шаг 2
          </div>
          <div className={`text-xs ${currentStep === 2 ? 'text-purple-600' : 'text-gray-400'}`}>
            Добавьте одежду
          </div>
        </div>
        {currentStep === 2 && (
          <svg className="w-5 h-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
              clipRule="evenodd"
            />
          </svg>
        )}
      </div>
    </div>
  );
}
