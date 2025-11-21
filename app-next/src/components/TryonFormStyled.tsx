'use client';

import { useState, useEffect, useRef } from 'react';
import { useImageUpload } from '@/hooks/useImageUpload';
import { tryonApi, type TryonResult } from '@/lib/api';
import { getDeviceFingerprint } from '@/lib/fingerprint';
import { useAuth } from '@/hooks/useAuth';
import LoadingOverlay from './LoadingOverlay';

type GarmentCategory = 'auto' | 'upper' | 'lower' | 'overall';

const GARMENT_CATEGORIES = [
  { value: 'auto' as GarmentCategory, label: 'Авто', icon: '✨' },
  { value: 'upper' as GarmentCategory, label: 'Верх', icon: '👕' },
  { value: 'lower' as GarmentCategory, label: 'Низ', icon: '👖' },
  { value: 'overall' as GarmentCategory, label: 'Комплект', icon: '👗' },
];

export default function TryonFormStyled() {
  const { isAuthenticated } = useAuth();
  const [currentStep, setCurrentStep] = useState<1 | 2>(1);
  const [isGenerating, setIsGenerating] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState('Загрузка...');
  const [loadingTip, setLoadingTip] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<TryonResult[] | null>(null);
  const [fingerprint, setFingerprint] = useState<string>('');
  const [garmentCategory, setGarmentCategory] = useState<GarmentCategory>('auto');
  const [showRating, setShowRating] = useState(false);
  const [userRating, setUserRating] = useState<'like' | 'dislike' | null>(null);

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
    setShowRating(false);
    setUserRating(null);

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
        garment_category: garmentCategory,
        device_fingerprint: isAuthenticated ? undefined : fingerprint,
      });

      if (!tryonResponse.success || !tryonResponse.results || tryonResponse.results.length === 0) {
        throw new Error('Не удалось получить результаты. Попробуйте еще раз.');
      }

      setResults(tryonResponse.results);
      setShowRating(true);

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
    setGarmentCategory('auto');
    setShowRating(false);
    setUserRating(null);
  };

  const handleRating = async (rating: 'like' | 'dislike') => {
    setUserRating(rating);
    // TODO: Отправить рейтинг на сервер
    if (rating === 'like') {
      // Обновить список примерок на главной странице
      setTimeout(() => {
        window.location.href = '/';
      }, 1500);
    }
  };

  const canGenerate = personImage.file && garmentImage.file && !isGenerating;
  const resultRef = useRef<HTMLDivElement>(null);

  // Плавная анимация скролла к результату
  useEffect(() => {
    if (results && resultRef.current) {
      setTimeout(() => {
        resultRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 300);
    }
  }, [results]);

  return (
    <>
      <LoadingOverlay
        isVisible={isGenerating}
        message={loadingMessage}
        tip={loadingTip}
      />

      <div className="tryon-form-wrapper">
        {/* ШАГ 1: Загрузка фото */}
        <div className="tryon-step-block">
          <div className="step-block-header">
            <div className="step-icon-large">📷</div>
            <div className="step-block-info">
              <h3 className="step-block-title">ШАГ 1</h3>
              <p className="step-block-subtitle">Загрузите своё фото</p>
            </div>
          </div>

          <div className="step-content-grid">
            {/* Зона загрузки */}
            <div
              className="upload-zone-compact"
              onClick={() => !isGenerating && personInputRef.current?.click()}
            >
              {personImage.preview ? (
                <div className="upload-preview-compact">
                  <img src={personImage.preview} alt="Ваше фото" />
                  <button
                    className="btn-remove-image"
                    onClick={(e) => {
                      e.stopPropagation();
                      personImage.reset();
                      setCurrentStep(1);
                    }}
                  >
                    ✕
                  </button>
                </div>
              ) : (
                <div className="upload-placeholder-compact">
                  <div className="upload-icon-compact">
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                      <polyline points="17 8 12 3 7 8"/>
                      <line x1="12" y1="3" x2="12" y2="15"/>
                    </svg>
                  </div>
                  <div className="upload-text-compact">Перетащите фото или выберите</div>
                  <div className="upload-hint-compact">JPG/PNG, минимум 512px</div>
                  <button className="upload-button-compact">Выбрать файл</button>
                </div>
              )}
            </div>

            {/* Требования */}
            <div className="requirements-inline">
              <h4 className="requirements-inline-title">Требования к фото</h4>
              <ul className="requirements-inline-list">
                <li>✓ Полный рост, вертикальное фото</li>
                <li>✓ Хорошее освещение, чёткое изображение</li>
                <li>✓ Однотонный фон желателен</li>
                <li className="requirement-warning">✗ Не подойдут: селфи и обрезанные фото</li>
              </ul>
            </div>
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

        {/* ШАГ 2: Загрузка одежды */}
        <div className={`tryon-step-block ${currentStep === 1 ? 'disabled' : ''}`}>
          <div className="step-block-header">
            <div className="step-icon-large">👗</div>
            <div className="step-block-info">
              <h3 className="step-block-title">ШАГ 2</h3>
              <p className="step-block-subtitle">Добавьте одежду</p>
            </div>
          </div>

          <div className="step-content-grid">
            {/* Зона загрузки */}
            <div
              className="upload-zone-compact"
              onClick={() => currentStep === 2 && !isGenerating && garmentInputRef.current?.click()}
            >
              {garmentImage.preview ? (
                <div className="upload-preview-compact">
                  <img src={garmentImage.preview} alt="Одежда" />
                  <button
                    className="btn-remove-image"
                    onClick={(e) => {
                      e.stopPropagation();
                      garmentImage.reset();
                    }}
                  >
                    ✕
                  </button>
                </div>
              ) : (
                <div className="upload-placeholder-compact">
                  <div className="upload-icon-compact">
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                      <polyline points="17 8 12 3 7 8"/>
                      <line x1="12" y1="3" x2="12" y2="15"/>
                    </svg>
                  </div>
                  <div className="upload-text-compact">Перетащите фото или выберите</div>
                  <div className="upload-hint-compact">JPG/PNG, минимум 512px</div>
                  <button className="upload-button-compact" disabled={currentStep === 1}>
                    Выбрать файл
                  </button>
                </div>
              )}

              {currentStep === 1 && (
                <div className="step-overlay-compact">
                  <p>Сначала загрузите ваше фото</p>
                </div>
              )}
            </div>

            {/* Подсказки и тип одежды */}
            <div className="hints-inline">
              <h4 className="hints-inline-title">Тип одежды</h4>
              <div className="garment-type-selector">
                {GARMENT_CATEGORIES.map((cat) => (
                  <button
                    key={cat.value}
                    className={`garment-type-btn ${garmentCategory === cat.value ? 'active' : ''}`}
                    onClick={() => setGarmentCategory(cat.value)}
                    disabled={currentStep === 1}
                  >
                    <span className="garment-type-icon">{cat.icon}</span>
                    <span className="garment-type-label">{cat.label}</span>
                  </button>
                ))}
              </div>

              <div className="hints-text">
                <p>💡 <strong>Авто</strong> - система определит тип автоматически</p>
                <p>💡 <strong>Верх</strong> - футболки, блузки, пиджаки</p>
                <p>💡 <strong>Низ</strong> - брюки, юбки, шорты</p>
                <p>💡 <strong>Комплект</strong> - платья, комбинезоны</p>
              </div>
            </div>
          </div>

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

        {/* Кнопка генерации */}
        <div className="generate-section">
          <button
            className="btn-generate-main"
            onClick={handleGenerate}
            disabled={!canGenerate}
          >
            <span className="btn-icon">✨</span>
            <span className="btn-text">Сделать примерку</span>
          </button>

          {error && (
            <div className="error-message-inline">
              {error}
            </div>
          )}
        </div>
      </div>

      {/* РЕЗУЛЬТАТ - показывается ниже формы */}
      {results && (
        <div ref={resultRef} className="result-section-wrapper">
          {/* Результат генерации */}
          <div className="result-display-compact">
            <div className="result-header">
              <h2 className="result-title">Результат примерки</h2>
              <button className="btn-new-tryon" onClick={handleReset}>
                Новая примерка
              </button>
            </div>
            <div className="result-image-container">
              {results[0]?.result_url && (
                <img
                  src={results[0].result_url}
                  alt="Результат примерки"
                  className="result-image-main"
                />
              )}
            </div>
            <div className="result-actions">
              <button className="btn-result-action btn-download">
                📥 Скачать
              </button>
              <button className="btn-result-action btn-share">
                🔗 Поделиться
              </button>
            </div>
          </div>

          {/* До/После и Оценка горизонтально */}
          <div className="result-bottom-grid">
            {/* Блок До/После */}
            <div className="before-after-card">
              <h3 className="card-title-small">Сравнение: До и После</h3>
              <div className="comparison-mini-grid">
                <div className="comparison-mini-item">
                  <div className="comparison-mini-label">Ваше фото</div>
                  <div className="comparison-mini-image">
                    {personImage.preview && (
                      <img src={personImage.preview} alt="До" />
                    )}
                  </div>
                </div>
                <div className="comparison-arrow-mini">→</div>
                <div className="comparison-mini-item">
                  <div className="comparison-mini-label">Одежда</div>
                  <div className="comparison-mini-image">
                    {garmentImage.preview && (
                      <img src={garmentImage.preview} alt="Одежда" />
                    )}
                  </div>
                </div>
                <div className="comparison-arrow-mini">→</div>
                <div className="comparison-mini-item highlighted">
                  <div className="comparison-mini-label">Результат</div>
                  <div className="comparison-mini-image">
                    {results[0]?.result_url && (
                      <img src={results[0].result_url} alt="После" />
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Блок оценки */}
            {showRating && (
              <div className="rating-card-compact">
                <h3 className="card-title-small">Понравился результат?</h3>
                <p className="rating-description-compact">
                  Ваша оценка помогает нам улучшать качество
                </p>
                <div className="rating-buttons-compact">
                  <button
                    className={`rating-btn-compact rating-like ${userRating === 'like' ? 'active' : ''}`}
                    onClick={() => handleRating('like')}
                    disabled={userRating !== null}
                  >
                    <span className="rating-icon-compact">👍</span>
                    <span className="rating-text-compact">Да!</span>
                  </button>
                  <button
                    className={`rating-btn-compact rating-dislike ${userRating === 'dislike' ? 'active' : ''}`}
                    onClick={() => handleRating('dislike')}
                    disabled={userRating !== null}
                  >
                    <span className="rating-icon-compact">👎</span>
                    <span className="rating-text-compact">Не очень</span>
                  </button>
                </div>
                {userRating === 'like' && (
                  <div className="rating-feedback-compact success">
                    ✨ Отлично! Примерка сохранена
                  </div>
                )}
                {userRating === 'dislike' && (
                  <div className="rating-feedback-compact">
                    Спасибо за отзыв!
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
}
