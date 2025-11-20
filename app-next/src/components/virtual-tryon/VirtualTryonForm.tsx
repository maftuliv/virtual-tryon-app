'use client';

import { useState, useEffect } from 'react';
import { useImageUpload } from '@/hooks/useImageUpload';
import { tryonApi, type TryonResult } from '@/lib/api';
import { getDeviceFingerprint } from '@/lib/fingerprint';
import { useAuth } from '@/hooks/useAuth';
import StepHeader from './StepHeader';
import UploadZone from './UploadZone';
import RequirementsCard from './RequirementsCard';
import TryOnCTA from './TryOnCTA';
import LoadingOverlay from '../LoadingOverlay';
import ResultDisplay from '../ResultDisplay';

export default function VirtualTryonForm() {
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

  const canGenerate = Boolean(personImage.file && garmentImage.file && !isGenerating);

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

      <div className="w-full max-w-7xl mx-auto px-4 py-8">
        {/* Заголовок */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">Виртуальная примерка</h1>
          <p className="text-gray-600">Загрузите своё фото и одежду — и получите результат за секунды.</p>
        </div>

        {/* Шаги */}
        <StepHeader currentStep={currentStep} />

        {/* Основной контент */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Левая часть - загрузка фото */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-3xl p-6 shadow-sm border border-gray-100">
              {currentStep === 1 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <UploadZone
                    title="Ваше фото"
                    preview={personImage.preview}
                    onUpload={personImage.handleUpload}
                    disabled={isGenerating}
                  />
                  <div className="hidden md:block">
                    <RequirementsCard />
                  </div>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <UploadZone
                    title="Ваше фото"
                    preview={personImage.preview}
                    onUpload={personImage.handleUpload}
                    disabled={isGenerating}
                  />
                  <UploadZone
                    title="Одежда"
                    preview={garmentImage.preview}
                    onUpload={garmentImage.handleUpload}
                    disabled={isGenerating}
                  />
                </div>
              )}

              {error && (
                <div className="mt-6 p-4 rounded-xl bg-red-100 border border-red-200 text-red-700 text-sm">
                  {error}
                </div>
              )}
            </div>

            {/* Requirements для мобильных на шаге 1 */}
            {currentStep === 1 && (
              <div className="md:hidden mt-6">
                <RequirementsCard />
              </div>
            )}
          </div>

          {/* Правая часть - CTA */}
          <div className="lg:col-span-1">
            <TryOnCTA
              canGenerate={canGenerate}
              isGenerating={isGenerating}
              onGenerate={handleGenerate}
              onReset={handleReset}
            />
          </div>
        </div>
      </div>
    </>
  );
}
