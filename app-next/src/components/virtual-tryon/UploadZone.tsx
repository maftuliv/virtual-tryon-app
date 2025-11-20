'use client';

import { useCallback, useState } from 'react';
import Image from 'next/image';

interface UploadZoneProps {
  title: string;
  preview: string | null;
  onUpload: (file: File) => void;
  disabled?: boolean;
}

export default function UploadZone({ title, preview, onUpload, disabled }: UploadZoneProps) {
  const [isDragging, setIsDragging] = useState(false);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);

      if (disabled) return;

      const files = Array.from(e.dataTransfer.files);
      if (files.length > 0 && files[0].type.startsWith('image/')) {
        onUpload(files[0]);
      }
    },
    [disabled, onUpload]
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files;
      if (files && files.length > 0) {
        onUpload(files[0]);
      }
    },
    [onUpload]
  );

  return (
    <div className="flex flex-col">
      <h3 className="text-sm font-medium text-gray-700 mb-3">{title}</h3>
      <div
        className={`relative border-2 border-dashed rounded-3xl p-8 transition-all ${
          isDragging
            ? 'border-purple-400 bg-purple-50'
            : disabled
            ? 'border-gray-200 bg-gray-50'
            : 'border-gray-300 bg-white hover:border-purple-300'
        } ${preview ? 'min-h-[400px]' : 'min-h-[500px]'} flex flex-col items-center justify-center`}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
      >
        {preview ? (
          <div className="relative w-full h-full min-h-[400px]">
            <Image
              src={preview}
              alt="Preview"
              fill
              className="object-contain rounded-2xl"
            />
          </div>
        ) : (
          <>
            <div className="w-20 h-20 rounded-full bg-gray-100 flex items-center justify-center mb-4">
              <svg className="w-10 h-10 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                />
              </svg>
            </div>
            <p className="text-center text-gray-600 mb-2 font-medium">
              Перетащите фото или выберите
            </p>
            <p className="text-xs text-gray-400 mb-4">JPG/PNG, минимум 512px</p>
            <label className="cursor-pointer">
              <input
                type="file"
                className="hidden"
                accept="image/png,image/jpeg,image/jpg,image/webp"
                onChange={handleFileSelect}
                disabled={disabled}
              />
              <span className="inline-block px-6 py-3 bg-gray-900 text-white rounded-xl font-medium hover:bg-gray-800 transition-colors">
                Выбрать файл
              </span>
            </label>
          </>
        )}

        {disabled && !preview && (
          <div className="absolute inset-0 bg-gray-100 bg-opacity-80 rounded-3xl flex items-center justify-center">
            <p className="text-sm text-gray-500">Сначала загрузите своё фото</p>
          </div>
        )}
      </div>
    </div>
  );
}
