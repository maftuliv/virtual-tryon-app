'use client';

import { useState, useEffect } from 'react';
import Button from '../Button';

interface OnboardingModalProps {
  isOpen: boolean;
  onClose: () => void;
  userName?: string;
}

export default function OnboardingModal({ isOpen, onClose, userName }: OnboardingModalProps) {
  const [currentStep, setCurrentStep] = useState(0);

  // Reset step when modal opens
  useEffect(() => {
    if (isOpen) {
      setCurrentStep(0);
    }
  }, [isOpen]);

  const steps = [
    {
      title: 'Добро пожаловать в Tap to look!',
      description: userName
        ? `Привет, ${userName}! Рады видеть тебя в нашем сервисе виртуальной примерки одежды.`
        : 'Привет! Рады видеть тебя в нашем сервисе виртуальной примерки одежды.',
      icon: (
        <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center text-white text-4xl">
          👋
        </div>
      ),
      content: (
        <div className="space-y-4 text-left">
          <p className="text-gray-600">
            С помощью AI-технологий ты сможешь примерить любую одежду на свое фото без похода в магазин!
          </p>
          <div className="glass rounded-2xl p-4 space-y-2">
            <div className="flex items-start gap-3">
              <span className="text-2xl">🎨</span>
              <div>
                <p className="font-semibold">Реалистичный результат</p>
                <p className="text-sm text-gray-600">Наша AI создает фотореалистичные примерки</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <span className="text-2xl">⚡</span>
              <div>
                <p className="font-semibold">Быстрая генерация</p>
                <p className="text-sm text-gray-600">Результат за 10-30 секунд</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <span className="text-2xl">💾</span>
              <div>
                <p className="font-semibold">Сохранение в облаке</p>
                <p className="text-sm text-gray-600">Все твои примерки доступны навсегда</p>
              </div>
            </div>
          </div>
        </div>
      ),
    },
    {
      title: 'Как это работает?',
      description: 'Всего 3 простых шага до идеального образа',
      icon: (
        <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-gradient-to-br from-blue-500 to-cyan-600 flex items-center justify-center text-white text-4xl">
          ✨
        </div>
      ),
      content: (
        <div className="space-y-6 text-left">
          <div className="flex gap-4">
            <div className="flex-shrink-0 w-10 h-10 rounded-full bg-primary text-white flex items-center justify-center font-bold">
              1
            </div>
            <div>
              <p className="font-semibold mb-1">Загрузи свое фото</p>
              <p className="text-sm text-gray-600">
                Лучше всего подойдет фото в полный рост на светлом фоне
              </p>
            </div>
          </div>

          <div className="flex gap-4">
            <div className="flex-shrink-0 w-10 h-10 rounded-full bg-primary text-white flex items-center justify-center font-bold">
              2
            </div>
            <div>
              <p className="font-semibold mb-1">Загрузи фото одежды</p>
              <p className="text-sm text-gray-600">
                Можно с магазина, сайта или своего гардероба
              </p>
            </div>
          </div>

          <div className="flex gap-4">
            <div className="flex-shrink-0 w-10 h-10 rounded-full bg-primary text-white flex items-center justify-center font-bold">
              3
            </div>
            <div>
              <p className="font-semibold mb-1">Получи результат!</p>
              <p className="text-sm text-gray-600">
                Скачай, поделись или сохрани в своем кабинете
              </p>
            </div>
          </div>

          <div className="glass rounded-2xl p-4 bg-blue-50 border-blue-200">
            <p className="text-sm text-gray-700">
              <span className="font-semibold">💡 Совет:</span> Для лучшего результата используй четкие фото с хорошим освещением
            </p>
          </div>
        </div>
      ),
    },
    {
      title: 'Твой тарифный план',
      description: 'Выбери подходящий для тебя вариант',
      icon: (
        <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-gradient-to-br from-purple-500 to-pink-600 flex items-center justify-center text-white text-4xl">
          🎁
        </div>
      ),
      content: (
        <div className="space-y-4">
          <div className="glass rounded-2xl p-6 border-2 border-primary">
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-lg font-bold">Бесплатный</h4>
              <span className="px-3 py-1 bg-primary text-white text-sm font-semibold rounded-full">
                Активен
              </span>
            </div>
            <div className="space-y-2 text-sm text-gray-600 mb-4">
              <div className="flex items-center gap-2">
                <span className="text-green-600">✓</span>
                <span>10 примерок в день</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-green-600">✓</span>
                <span>Облачное хранение результатов</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-green-600">✓</span>
                <span>Скачивание в высоком качестве</span>
              </div>
            </div>
            <p className="text-xs text-gray-500">
              Этого достаточно для ежедневного использования!
            </p>
          </div>

          <div className="glass rounded-2xl p-6 border border-gray-200 opacity-75">
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-lg font-bold">Premium</h4>
              <span className="px-3 py-1 bg-gradient-to-r from-purple-600 to-pink-600 text-white text-sm font-semibold rounded-full">
                Скоро
              </span>
            </div>
            <div className="space-y-2 text-sm text-gray-600 mb-4">
              <div className="flex items-center gap-2">
                <span className="text-green-600">✓</span>
                <span>Безлимитные примерки</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-green-600">✓</span>
                <span>Приоритетная генерация</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-green-600">✓</span>
                <span>AI-рекомендации стилиста</span>
              </div>
            </div>
          </div>
        </div>
      ),
    },
  ];

  const currentStepData = steps[currentStep];
  const isLastStep = currentStep === steps.length - 1;

  const handleNext = () => {
    if (isLastStep) {
      // Сохраняем флаг, что onboarding пройден
      if (typeof window !== 'undefined') {
        localStorage.setItem('onboarding-completed', 'true');
      }
      onClose();
    } else {
      setCurrentStep((prev) => prev + 1);
    }
  };

  const handlePrev = () => {
    if (currentStep > 0) {
      setCurrentStep((prev) => prev - 1);
    }
  };

  const handleSkip = () => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('onboarding-completed', 'true');
    }
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 backdrop-blur-sm animate-fade-in">
      <div className="glass rounded-4xl p-8 max-w-2xl w-full mx-4 relative">
        {/* Skip button */}
        <button
          onClick={handleSkip}
          className="absolute top-4 right-4 text-sm text-gray-500 hover:text-gray-700 transition-colors"
        >
          Пропустить
        </button>

        {/* Step indicator */}
        <div className="flex items-center justify-center gap-2 mb-8">
          {steps.map((_, index) => (
            <div
              key={index}
              className={`h-2 rounded-full transition-all ${
                index === currentStep
                  ? 'w-8 bg-primary'
                  : index < currentStep
                  ? 'w-2 bg-primary/50'
                  : 'w-2 bg-gray-300'
              }`}
            />
          ))}
        </div>

        {/* Content */}
        <div className="text-center mb-8">
          {currentStepData.icon}
          <h2 className="text-2xl font-bold mb-3">{currentStepData.title}</h2>
          <p className="text-gray-600 mb-6">{currentStepData.description}</p>
          {currentStepData.content}
        </div>

        {/* Navigation */}
        <div className="flex gap-3">
          {currentStep > 0 && (
            <Button variant="secondary" size="lg" onClick={handlePrev}>
              Назад
            </Button>
          )}
          <Button variant="primary" size="lg" fullWidth onClick={handleNext}>
            {isLastStep ? 'Начать использовать' : 'Далее'}
          </Button>
        </div>
      </div>
    </div>
  );
}
