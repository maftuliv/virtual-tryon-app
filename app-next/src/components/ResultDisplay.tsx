'use client';

import { useState } from 'react';
import Image from 'next/image';
import Button from './Button';
import type { TryonResult } from '@/lib/api';

interface ResultDisplayProps {
  results: TryonResult[];
  onReset: () => void;
}

export default function ResultDisplay({ results, onReset }: ResultDisplayProps) {
  const [selectedIndex, setSelectedIndex] = useState(0);
  const currentResult = results[selectedIndex];

  const handleDownload = async () => {
    try {
      const response = await fetch(currentResult.result_url);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = currentResult.result_filename || 'tryon-result.jpg';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
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
      // Fallback: copy to clipboard
      try {
        await navigator.clipboard.writeText(currentResult.result_url);
        alert('Ссылка скопирована в буфер обмена!');
      } catch (error) {
        console.error('Copy failed:', error);
      }
    }
  };

  return (
    <div className="w-full max-w-6xl mx-auto p-6 animate-fade-in">
      <div className="glass rounded-4xl p-8">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold">Результат примерки</h2>
          <Button variant="ghost" size="sm" onClick={onReset}>
            Новая примерка
          </Button>
        </div>

        {/* Main Result */}
        <div className="mb-6">
          <div className="relative aspect-[3/4] rounded-2xl overflow-hidden bg-gray-100 max-w-md mx-auto">
            <Image
              src={currentResult.result_url}
              alt="Результат виртуальной примерки"
              fill
              className="object-contain"
              priority
              sizes="(max-width: 768px) 100vw, 50vw"
            />
          </div>
        </div>

        {/* Thumbnails if multiple results */}
        {results.length > 1 && (
          <div className="flex gap-3 justify-center mb-6 overflow-x-auto pb-2">
            {results.map((result, index) => (
              <button
                key={index}
                onClick={() => setSelectedIndex(index)}
                className={`
                  relative w-20 h-24 rounded-lg overflow-hidden flex-shrink-0
                  border-2 transition-all
                  ${index === selectedIndex ? 'border-primary scale-105' : 'border-white/40 hover:border-primary/50'}
                `}
              >
                <Image
                  src={result.result_url}
                  alt={`Результат ${index + 1}`}
                  fill
                  className="object-cover"
                  sizes="80px"
                />
              </button>
            ))}
          </div>
        )}

        {/* Actions */}
        <div className="flex flex-col sm:flex-row gap-3">
          <Button
            variant="primary"
            size="lg"
            fullWidth
            onClick={handleDownload}
          >
            📥 Скачать
          </Button>
          <Button
            variant="secondary"
            size="lg"
            fullWidth
            onClick={handleShare}
          >
            📤 Поделиться
          </Button>
        </div>

        {/* Info */}
        <p className="text-xs text-center text-gray-500 mt-6">
          Результаты сохранены в вашем кабинете и доступны в любое время
        </p>
      </div>
    </div>
  );
}
