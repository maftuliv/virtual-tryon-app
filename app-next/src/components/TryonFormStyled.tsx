'use client';

import { useState, useEffect, useRef } from 'react';
import { useImageUpload } from '@/hooks/useImageUpload';
import { tryonApi, type TryonResult } from '@/lib/api';
import { getDeviceFingerprint } from '@/lib/fingerprint';
import { useAuth } from '@/hooks/useAuth';
import LoadingOverlay from './LoadingOverlay';
import ResultDisplay from './ResultDisplay';

export default function TryonFormStyled() {
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

  const personInputRef = useRef<HTMLInputElement>(null);
  const garmentInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!isAuthenticated) {
      getDeviceFingerprint().then(setFingerprint);
    }
  }, [isAuthenticated]);

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
      setLoadingMessage('📤 Загрузка изображений...');
      setLoadingTip('Подготавливаем ваши фотографии для обработки');

      const uploadResponse = await tryonApi.upload({
        personImages: [personImage.file],
        garmentImage: garmentImage.file,
      });

      if (!uploadResponse.success) {
        throw new Error('Ошибка загрузки файлов');
      }

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

      <div className="tryon-form-container">
        {/* Левая сторона: Шаги */}
        <div className="tryon-steps-panel">
          {/* Шаг 1 */}
          <div
            className={`tryon-step-card ${currentStep === 1 ? 'active' : ''}`}
            onClick={() => !isGenerating && personInputRef.current?.click()}
          >
            <div className="step-header">
              <div className="step-icon">📷</div>
              <div className="step-info">
                <div className="step-title">Шаг 1</div>
                <div className="step-subtitle">Загрузите своё фото</div>
              </div>
              {currentStep === 1 && <div className="step-arrow">→</div>}
            </div>

            <div className="step-upload-zone">
              {personImage.preview ? (
                <div className="upload-preview">
                  <img src={personImage.preview} alt="Ваше фото" />
                </div>
              ) : (
                <div className="upload-placeholder">
                  <div className="upload-icon">⬆️</div>
                  <div className="upload-text">Перетащите фото или выберите</div>
                  <div className="upload-hint">JPG/PNG, минимум 512px</div>
                  <button className="upload-button">Выбрать файл</button>
                </div>
              )}
            </div>

            <input
              ref={personInputRef}
              type="file"
              accept="image/jpeg,image/png,image/webp"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) personImage.handleUpload(file);
              }}
              disabled={isGenerating}
              style={{ display: 'none' }}
            />
          </div>

          {/* Шаг 2 */}
          <div
            className={`tryon-step-card ${currentStep === 2 ? 'active' : ''} ${currentStep === 1 ? 'disabled' : ''}`}
            onClick={() => currentStep === 2 && !isGenerating && garmentInputRef.current?.click()}
          >
            <div className="step-header">
              <div className="step-icon">👗</div>
              <div className="step-info">
                <div className="step-title">Шаг 2</div>
                <div className="step-subtitle">Добавьте одежду</div>
              </div>
              {currentStep === 2 && !garmentImage.file && <div className="step-checkmark">✓</div>}
            </div>

            <div className="step-upload-zone">
              {garmentImage.preview ? (
                <div className="upload-preview">
                  <img src={garmentImage.preview} alt="Одежда" />
                </div>
              ) : (
                <div className="upload-placeholder">
                  <div className="upload-icon">⬆️</div>
                  <div className="upload-text">Перетащите фото или выберите</div>
                  <div className="upload-hint">JPG/PNG, минимум 512px</div>
                  <button className="upload-button" disabled={currentStep === 1}>
                    Выбрать файл
                  </button>
                </div>
              )}
            </div>

            {currentStep === 1 && (
              <div className="step-overlay">
                <p>Сначала загрузите ваше фото</p>
              </div>
            )}

            <input
              ref={garmentInputRef}
              type="file"
              accept="image/jpeg,image/png,image/webp"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) garmentImage.handleUpload(file);
              }}
              disabled={isGenerating || currentStep === 1}
              style={{ display: 'none' }}
            />
          </div>
        </div>

        {/* Правая сторона: Информация */}
        <div className="tryon-info-panel">
          <div className="info-card">
            <h3 className="info-title">Готовы примерить?</h3>
            <p className="info-description">
              Загрузите своё фото и желаемую одежду. Нажмите кнопку - всё остальное сделаем мы 😉
            </p>

            <button
              className="btn-tryon-generate"
              onClick={handleGenerate}
              disabled={!canGenerate}
            >
              ✨ сделать примерку
            </button>

            {error && (
              <div className="error-message">
                {error}
              </div>
            )}

            <div className="info-stats">
              <div className="stat-item">
                <div className="stat-icon">👑</div>
                <div className="stat-text">∞ примерок</div>
              </div>
            </div>

            <div className="info-footer">
              <p>Бесплатно. Без регистрации. Качественно</p>
              <p className="info-note">
                Спасибо, что используете наш сервис! Мы ценим каждого пользователя и постоянно работаем над улучшением качества примерки. Ваша поддержка вдохновляет нас делать сервис ещё лучше! 💜
              </p>
            </div>
          </div>

          <div className="requirements-card">
            <h4>Требования</h4>
            <ul>
              <li>Полный рост, вертикальное фото</li>
              <li>Хорошее освещение, чёткое изображение</li>
              <li>Однотонный фон желателен</li>
              <li className="requirement-warning">Не подойдут: селфи и обрезанные фото</li>
            </ul>
            <button className="btn-examples">🖼️ Посмотреть примеры</button>
          </div>
        </div>
      </div>
    </>
  );
}
