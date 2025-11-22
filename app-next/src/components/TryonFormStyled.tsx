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

// Лимиты примерок
const MONTHLY_LIMIT = 50;

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
  const [remainingTries, setRemainingTries] = useState<number>(MONTHLY_LIMIT);

  // Флаг состояния: есть результат или нет
  const hasResult = results !== null && results.length > 0;

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
  const resultRef = useRef<HTMLDivElement>(null);

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

  // Плавная анимация скролла к результату
  useEffect(() => {
    if (hasResult && resultRef.current) {
      setTimeout(() => {
        resultRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 300);
    }
  }, [hasResult]);

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

      // Обновляем оставшиеся примерки
      if (tryonResponse.daily_limit) {
        setRemainingTries(tryonResponse.daily_limit.remaining);
      }

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

  const handleNewTryon = () => {
    // Сбрасываем только результат, но не загруженные изображения
    setResults(null);
    setShowRating(false);
    setUserRating(null);
  };

  const handleRating = async (rating: 'like' | 'dislike') => {
    setUserRating(rating);

    if (isAuthenticated && results && results[0]?.generation_id) {
      try {
        const isFavorite = rating === 'like';
        await tryonApi.toggleFavorite(results[0].generation_id, isFavorite);
      } catch (error) {
        console.error('Failed to save rating:', error);
        setError('Не удалось сохранить оценку');
      }
    }
  };

  const handleDownload = async () => {
    if (!results || !results[0]) return;

    try {
      let imageUrl = '';
      if (results[0].result_image) {
        imageUrl = results[0].result_image.startsWith('data:')
          ? results[0].result_image
          : `data:image/png;base64,${results[0].result_image}`;
      } else if (results[0].r2_url) {
        imageUrl = results[0].r2_url;
      } else if (results[0].result_url) {
        imageUrl = results[0].result_url;
      }

      if (imageUrl.startsWith('data:')) {
        const link = document.createElement('a');
        link.href = imageUrl;
        link.download = 'tryon-result.png';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      } else {
        const response = await fetch(imageUrl);
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'tryon-result.png';
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }
    } catch (error) {
      console.error('Download failed:', error);
      alert('Не удалось скачать изображение');
    }
  };

  const handleShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: 'Моя виртуальная примерка',
          text: 'Посмотрите на мою виртуальную примерку в Tap to look!',
          url: window.location.href,
        });
      } catch (error) {
        console.log('Share cancelled or failed:', error);
      }
    } else {
      try {
        await navigator.clipboard.writeText(window.location.href);
        alert('Ссылка скопирована в буфер обмена!');
      } catch (error) {
        console.error('Copy failed:', error);
      }
    }
  };

  const canGenerate = personImage.file && garmentImage.file && !isGenerating;
  const progressPercent = Math.round((remainingTries / MONTHLY_LIMIT) * 100);

  // Получаем URL результата
  const getResultImageUrl = () => {
    if (!results || !results[0]) return null;
    if (results[0].result_image) {
      return results[0].result_image.startsWith('data:')
        ? results[0].result_image
        : `data:image/png;base64,${results[0].result_image}`;
    }
    if (results[0].r2_url) return results[0].r2_url;
    if (results[0].result_url) return results[0].result_url;
    return null;
  };

  return (
    <>
      <LoadingOverlay
        isVisible={isGenerating}
        message={loadingMessage}
        tip={loadingTip}
      />

      {/* ================= РЕЖИМ SETUP (до генерации) ================= */}
      {!hasResult && (
        <div className="tryon-main-layout">
          {/* Steps row */}
          <div className="tryon-steps-row">
            {/* ШАГ 1: Загрузка фото */}
            <div className="tryon-step-block-compact">
              <div className="step-block-header-compact">
                <div className="step-icon-medium">📷</div>
                <div className="step-block-info-compact">
                  <h3>ШАГ 1</h3>
                  <p>Загрузите своё фото</p>
                </div>
              </div>

              <div className="step-content-row">
                <div
                  className="upload-zone-card"
                  onClick={() => !isGenerating && personInputRef.current?.click()}
                >
                  {personImage.preview ? (
                    <div className="upload-preview-card">
                      <img src={personImage.preview} alt="Ваше фото" />
                      <button
                        className="btn-remove-image-card"
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
                    <div className="upload-placeholder-card">
                      <div className="upload-icon-card">
                        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                          <polyline points="17 8 12 3 7 8"/>
                          <line x1="12" y1="3" x2="12" y2="15"/>
                        </svg>
                      </div>
                      <div className="upload-text-card">Перетащите фото или выберите</div>
                      <div className="upload-hint-card">JPG/PNG, минимум 512px</div>
                      <button className="upload-button-card">Выбрать файл</button>
                    </div>
                  )}
                </div>

                <div className="requirements-compact">
                  <h4>Требования к фото</h4>
                  <ul>
                    <li>✓ Полный рост, вертикальное фото</li>
                    <li>✓ Хорошее освещение, чёткое изображение</li>
                    <li>✓ Однотонный фон желателен</li>
                    <li className="warning">✗ Не подойдут: селфи и обрезанные фото</li>
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
            <div className={`tryon-step-block-compact ${currentStep === 1 ? 'disabled' : ''}`}>
              <div className="step-block-header-compact">
                <div className="step-icon-medium">👗</div>
                <div className="step-block-info-compact">
                  <h3>ШАГ 2</h3>
                  <p>Добавьте одежду</p>
                </div>
              </div>

              <div className="step-content-row">
                <div
                  className="upload-zone-card"
                  onClick={() => currentStep === 2 && !isGenerating && garmentInputRef.current?.click()}
                >
                  {garmentImage.preview ? (
                    <div className="upload-preview-card">
                      <img src={garmentImage.preview} alt="Одежда" />
                      <button
                        className="btn-remove-image-card"
                        onClick={(e) => {
                          e.stopPropagation();
                          garmentImage.reset();
                        }}
                      >
                        ✕
                      </button>
                    </div>
                  ) : (
                    <div className="upload-placeholder-card">
                      <div className="upload-icon-card">
                        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                          <polyline points="17 8 12 3 7 8"/>
                          <line x1="12" y1="3" x2="12" y2="15"/>
                        </svg>
                      </div>
                      <div className="upload-text-card">Перетащите фото или выберите</div>
                      <div className="upload-hint-card">JPG/PNG, минимум 512px</div>
                      <button className="upload-button-card" disabled={currentStep === 1}>
                        Выбрать файл
                      </button>
                    </div>
                  )}

                  {currentStep === 1 && (
                    <div className="step-overlay-card">
                      <p>Сначала загрузите ваше фото</p>
                    </div>
                  )}
                </div>

                <div className="hints-compact">
                  <h4>Тип одежды</h4>
                  <div className="garment-type-grid">
                    {GARMENT_CATEGORIES.map((cat) => (
                      <button
                        key={cat.value}
                        className={`garment-type-btn-compact ${garmentCategory === cat.value ? 'active' : ''}`}
                        onClick={() => setGarmentCategory(cat.value)}
                        disabled={currentStep === 1}
                      >
                        <span className="garment-icon">{cat.icon}</span>
                        <span className="garment-label">{cat.label}</span>
                      </button>
                    ))}
                  </div>

                  <div className="hints-list">
                    <p>💡 <strong>Авто</strong> - система определит тип</p>
                    <p>💡 <strong>Верх</strong> - футболки, блузки</p>
                    <p>💡 <strong>Низ</strong> - брюки, юбки</p>
                    <p>💡 <strong>Комплект</strong> - платья</p>
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
          </div>

          {/* Блок «Готовы примерить?» - ТОЛЬКО до генерации */}
          <div className="generate-block">
            <h3 className="generate-block-title">Готовы примерить?</h3>
            <p className="generate-block-subtitle">
              Осталось <strong>{remainingTries}</strong> примерок в этом месяце
            </p>

            <div className="progress-bar-container">
              <div
                className="progress-bar-fill"
                style={{ width: `${progressPercent}%` }}
              />
            </div>

            <button
              className="btn-generate-styled"
              onClick={handleGenerate}
              disabled={!canGenerate}
            >
              <span className="btn-sparkle">✨</span>
              Сделать примерку
            </button>

            {error && (
              <div className="error-message-block">
                {error}
              </div>
            )}
          </div>
        </div>
      )}

      {/* ================= РЕЖИМ RESULT (после генерации) ================= */}
      {hasResult && (
        <div ref={resultRef} className="result-section-wrapper">
          {/* ЗАМЕТКА 1: Блок результата генерации - компактная карточка */}
          <section className="mt-8 flex justify-center">
            <div className="
              flex flex-col items-center gap-4
              rounded-3xl border border-white/40 bg-white/55
              px-6 py-6 shadow-[0_24px_70px_rgba(126,96,191,0.28)]
              backdrop-blur-2xl
              max-w-[560px] w-full
            ">
              {/* Заголовок + подзаголовок */}
              <div className="text-center">
                <h2 className="text-2xl font-bold text-gray-800 mb-2">
                  Ваш новый образ готов ✨
                </h2>
                <p className="text-gray-600 text-sm">
                  Посмотрите, как одежда смотрится на вас. Если нравится — сохраните или поделитесь!
                </p>
              </div>

              {/* Изображение результата */}
              <div className="w-full max-w-[460px]">
                {getResultImageUrl() && (
                  <img
                    src={getResultImageUrl()!}
                    alt="Результат примерки"
                    className="w-full h-auto rounded-2xl object-contain"
                  />
                )}
              </div>

              {/* ЗАМЕТКА 4: Кнопки Скачать / Поделиться - glassmorphism стиль */}
              <div className="flex gap-3 flex-wrap justify-center">
                <button
                  onClick={handleDownload}
                  className="
                    rounded-full px-5 py-2 text-sm font-medium
                    bg-white/70 hover:bg-white
                    border border-white/60
                    shadow-[0_12px_35px_rgba(0,0,0,0.10)]
                    backdrop-blur-xl
                    flex items-center gap-2
                    transition-all duration-200
                  "
                >
                  <span>⬇️</span> Скачать
                </button>
                <button
                  onClick={handleShare}
                  className="
                    rounded-full px-5 py-2 text-sm font-medium
                    bg-white/70 hover:bg-white
                    border border-white/60
                    shadow-[0_12px_35px_rgba(0,0,0,0.10)]
                    backdrop-blur-xl
                    flex items-center gap-2
                    transition-all duration-200
                  "
                >
                  <span>🔗</span> Поделиться
                </button>
              </div>

              {/* ЗАМЕТКА 4: Блок «Понравился результат?» - внутри карточки */}
              {showRating && (
                <div className="w-full pt-4 border-t border-white/30">
                  <div className="text-center">
                    <p className="text-gray-700 font-medium mb-3">Понравился результат?</p>
                    <div className="flex gap-3 justify-center">
                      <button
                        onClick={() => handleRating('like')}
                        disabled={userRating !== null}
                        className={`
                          rounded-full px-4 py-2 text-sm font-medium
                          flex items-center gap-2 transition-all duration-200
                          ${userRating === 'like'
                            ? 'bg-green-100 border-green-300 text-green-700'
                            : 'bg-white/70 hover:bg-green-50 border border-white/60'}
                          ${userRating !== null && userRating !== 'like' ? 'opacity-50' : ''}
                        `}
                      >
                        <span>👍</span> Да!
                      </button>
                      <button
                        onClick={() => handleRating('dislike')}
                        disabled={userRating !== null}
                        className={`
                          rounded-full px-4 py-2 text-sm font-medium
                          flex items-center gap-2 transition-all duration-200
                          ${userRating === 'dislike'
                            ? 'bg-orange-100 border-orange-300 text-orange-700'
                            : 'bg-white/70 hover:bg-orange-50 border border-white/60'}
                          ${userRating !== null && userRating !== 'dislike' ? 'opacity-50' : ''}
                        `}
                      >
                        <span>🤔</span> Не очень
                      </button>
                    </div>
                    {userRating === 'like' && (
                      <p className="mt-3 text-green-600 text-sm">✨ Отлично! Примерка сохранена</p>
                    )}
                    {userRating === 'dislike' && (
                      <p className="mt-3 text-gray-500 text-sm">Спасибо за отзыв!</p>
                    )}
                  </div>
                </div>
              )}
            </div>
          </section>

          {/* ЗАМЕТКА 3: Блок «Сравнение: До и После» - увеличенные превью */}
          <section className="mt-8">
            <div className="
              rounded-3xl border border-white/40 bg-white/55
              px-6 py-6 shadow-[0_24px_70px_rgba(126,96,191,0.25)]
              backdrop-blur-2xl
            ">
              <h3 className="text-lg font-semibold text-gray-800 mb-4 text-center">
                Сравнение: До и После
              </h3>
              <div className="flex flex-wrap justify-center items-end gap-4">
                {/* Ваше фото */}
                <div className="flex flex-col items-center group">
                  <span className="text-sm text-gray-600 mb-2">Ваше фото</span>
                  <div className="
                    w-[160px] h-[220px] rounded-2xl overflow-hidden
                    border-2 border-white/50
                    shadow-[0_8px_25px_rgba(0,0,0,0.12)]
                    transition-all duration-300
                    group-hover:scale-105 group-hover:shadow-[0_12px_35px_rgba(126,96,191,0.3)]
                  ">
                    {personImage.preview && (
                      <img
                        src={personImage.preview}
                        alt="До"
                        className="w-full h-full object-cover"
                      />
                    )}
                  </div>
                </div>

                {/* Стрелка */}
                <div className="text-2xl text-gray-400 pb-[110px] hidden sm:block">→</div>

                {/* Одежда */}
                <div className="flex flex-col items-center group">
                  <span className="text-sm text-gray-600 mb-2">Одежда</span>
                  <div className="
                    w-[160px] h-[220px] rounded-2xl overflow-hidden
                    border-2 border-white/50
                    shadow-[0_8px_25px_rgba(0,0,0,0.12)]
                    transition-all duration-300
                    group-hover:scale-105 group-hover:shadow-[0_12px_35px_rgba(126,96,191,0.3)]
                  ">
                    {garmentImage.preview && (
                      <img
                        src={garmentImage.preview}
                        alt="Одежда"
                        className="w-full h-full object-cover"
                      />
                    )}
                  </div>
                </div>

                {/* Стрелка */}
                <div className="text-2xl text-gray-400 pb-[110px] hidden sm:block">→</div>

                {/* Результат */}
                <div className="flex flex-col items-center group">
                  <span className="text-sm text-gray-600 mb-2">Результат</span>
                  <div className="
                    w-[160px] h-[220px] rounded-2xl overflow-hidden
                    border-2 border-purple-300
                    shadow-[0_8px_25px_rgba(126,96,191,0.25)]
                    transition-all duration-300
                    group-hover:scale-105 group-hover:shadow-[0_12px_35px_rgba(126,96,191,0.4)]
                    ring-2 ring-purple-200/50
                  ">
                    {getResultImageUrl() && (
                      <img
                        src={getResultImageUrl()!}
                        alt="После"
                        className="w-full h-full object-cover"
                      />
                    )}
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* ЗАМЕТКА 5: Блок «Готовы повторить?» - ПОСЛЕ генерации */}
          <section className="mt-8">
            <div className="
              rounded-3xl border border-white/40 bg-white/55
              px-6 py-5 shadow-[0_24px_70px_rgba(126,96,191,0.25)]
              backdrop-blur-2xl
            ">
              <h3 className="text-xl font-semibold text-gray-800 mb-2 text-center">
                Готовы повторить?
              </h3>
              <p className="text-gray-600 text-sm text-center mb-4">
                Вы можете попробовать другую одежду или фото — примерки ещё доступны.
              </p>

              {/* Прогресс-бар */}
              <div className="max-w-md mx-auto mb-2">
                <div className="text-center text-sm text-gray-600 mb-1">
                  Осталось <strong>{remainingTries}</strong> примерок в этом месяце
                </div>
                <div className="progress-bar-container">
                  <div
                    className="progress-bar-fill"
                    style={{ width: `${progressPercent}%` }}
                  />
                </div>
              </div>

              {/* Кнопка */}
              <div className="flex justify-center mt-4">
                <button
                  className="btn-generate-styled"
                  onClick={handleNewTryon}
                >
                  <span className="btn-sparkle">✨</span>
                  Сделать примерку
                </button>
              </div>
            </div>
          </section>
        </div>
      )}
    </>
  );
}
