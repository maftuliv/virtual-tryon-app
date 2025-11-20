'use client';

import { useState, useEffect } from 'react';
import { useImageUpload } from '@/hooks/useImageUpload';
import { tryonApi, type TryonResult } from '@/lib/api';
import { getDeviceFingerprint } from '@/lib/fingerprint';
import { useAuth } from '@/hooks/useAuth';
import ImageUpload from './ImageUpload';
import Button from './Button';
import LoadingOverlay from './LoadingOverlay';
import ResultDisplay from './ResultDisplay';

export default function TryonFormStepped() {
  const { isAuthenticated } = useAuth();
  const [currentStep, setCurrentStep] = useState<1 | 2>(1);
  const [isGenerating, setIsGenerating] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState('Загрузка...');
  const [loadingTip, setLoadingTip] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<TryonResult[] | null>(null);
  const [fingerprint, setFingerprint] = useState<string>('');

  const personImage = useImageUpload({
    maxSize: 10 * 1024 * 1024,
    onError: (err) => setError(err),
  });

  const garmentImage = useImageUpload({
    maxSize: 10 * 1024 * 1024,
    onError: (err) => setError(err),
  });

  // Генерируем fingerprint при монтировании (для анонимов)
  useEffect(() => {
    if (!isAuthenticated) {
      getDeviceFingerprint().then(setFingerprint);
    }
  }, [isAuthenticated]);

  // Автоматически переходим на шаг 2 после загрузки первого фото
  useEffect(() => {
    if (personImage.file && currentStep === 1) {
      setCurrentStep(2);
    }
  }, [personImage.file, currentStep]);

  const handleGenerate = async () => {
    if (!personImage.file || !garmentImage.file) {
      setError('Загрузите оба изображения');
      return;
    }

    setIsGenerating(true);
    setError(null);
    setResults(null);

    try {
      // Шаг 1: Загрузка файлов
      setLoadingMessage('📤 Загрузка изображений...');
      setLoadingTip('Подготавливаем ваши фотографии для обработки');

      const uploadResponse = await tryonApi.upload({
        personImages: [personImage.file],
        garmentImage: garmentImage.file,
      });

      if (!uploadResponse.success) {
        throw new Error('Ошибка загрузки файлов');
      }

      // Шаг 2: Генерация примерки
      setLoadingMessage('<span class="text-2xl">✨</span> Создается магия твоего стиля <span class="text-2xl">✨</span>');
      setLoadingTip('💡 Это может занять 10-30 секунд. Пока подумайте, где примените этот образ!');

      const tryonResponse = await tryonApi.generate({
        person_images: uploadResponse.person_images,
        garment_image: uploadResponse.garment_image,
        garment_category: 'auto',
        device_fingerprint: isAuthenticated ? undefined : fingerprint,
      });

      if (!tryonResponse.success || !tryonResponse.results || tryonResponse.results.length === 0) {
        throw new Error('Не удалось получить результаты. Попробуйте еще раз.');
      }

      // Успех! Показываем результаты
      setResults(tryonResponse.results);

    } catch (err) {
      const error = err as Error;
      console.error('Tryon error:', error);
      setError(error.message || 'Ошибка генерации. Попробуйте еще раз.');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleReset = () => {
    setResults(null);
    personImage.reset();
    garmentImage.reset();
    setError(null);
    setCurrentStep(1);
  };

  const canGenerate = personImage.file && garmentImage.file && !isGenerating;

  // Если есть результаты - показываем их
  if (results) {
    return <ResultDisplay results={results} onReset={handleReset} />;
  }

  return (
    <>
      <LoadingOverlay
        isVisible={isGenerating}
        message={loadingMessage}
        tip={loadingTip}
      />

      <div className="w-full max-w-6xl mx-auto p-6">
        <div className="glass rounded-4xl p-8 mb-6">
          <h2 className="text-2xl font-bold mb-6 text-center">
            Виртуальная примерка
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            {/* Шаг 1: Ваше фото */}
            <div className="relative">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-medium">Ваше фото</h3>
                {currentStep === 1 && (
                  <span className="text-xs px-2 py-1 rounded-full bg-blue-100 text-blue-700 font-medium">
                    Шаг 1
                  </span>
                )}
              </div>
              <ImageUpload
                label=""
                preview={personImage.preview}
                onUpload={personImage.handleUpload}
                disabled={isGenerating}
              />
            </div>

            {/* Шаг 2: Одежда */}
            <div className="relative">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-medium">Одежда</h3>
                {currentStep === 2 && !garmentImage.file && (
                  <span className="text-xs px-2 py-1 rounded-full bg-blue-100 text-blue-700 font-medium">
                    Шаг 2
                  </span>
                )}
              </div>
              <ImageUpload
                label=""
                preview={garmentImage.preview}
                onUpload={garmentImage.handleUpload}
                disabled={isGenerating || currentStep === 1}
              />
              {currentStep === 1 && (
                <div className="absolute inset-0 bg-gray-100 bg-opacity-80 rounded-2xl flex items-center justify-center">
                  <p className="text-sm text-gray-500">Сначала загрузите ваше фото</p>
                </div>
              )}
            </div>
          </div>

          {error && (
            <div className="mb-4 p-4 rounded-xl bg-red-100 border border-red-200 text-red-700 text-sm">
              {error}
            </div>
          )}

          <div className="flex gap-4">
            <Button
              variant="primary"
              size="lg"
              fullWidth
              onClick={handleGenerate}
              disabled={!canGenerate}
              isLoading={isGenerating}
            >
              {isGenerating ? 'Генерация...' : 'Примерить'}
            </Button>

            <Button
              variant="secondary"
              size="lg"
              onClick={handleReset}
              disabled={isGenerating}
            >
              Сбросить
            </Button>
          </div>

          {!isAuthenticated && !isGenerating && (
            <p className="text-xs text-center text-gray-500 mt-4">
              ⚡ Бесплатно: 3 примерки в день без регистрации
            </p>
          )}
        </div>
      </div>
    </>
  );
}
