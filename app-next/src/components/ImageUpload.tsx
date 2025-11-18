'use client';

import { useRef } from 'react';
import Image from 'next/image';

interface ImageUploadProps {
  label: string;
  preview: string | null;
  onUpload: (file: File) => void;
  disabled?: boolean;
  accept?: string;
}

export default function ImageUpload({
  label,
  preview,
  onUpload,
  disabled = false,
  accept = 'image/jpeg,image/png,image/webp',
}: ImageUploadProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      onUpload(file);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (file && !disabled) {
      onUpload(file);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  return (
    <div className="w-full">
      <label className="block text-sm font-medium mb-2">{label}</label>
      <div
        onClick={handleClick}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        className={`
          relative w-full aspect-[3/4] rounded-2xl overflow-hidden
          glass glass-hover cursor-pointer
          border-2 border-dashed border-white/40
          flex items-center justify-center
          transition-all duration-200
          ${disabled ? 'opacity-50 cursor-not-allowed' : 'hover:border-primary/60'}
        `}
      >
        {preview ? (
          <Image
            src={preview}
            alt={label}
            fill
            className="object-cover"
            sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
          />
        ) : (
          <div className="text-center p-6">
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
              stroke="currentColor"
              fill="none"
              viewBox="0 0 48 48"
              aria-hidden="true"
            >
              <path
                d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                strokeWidth={2}
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            <p className="mt-2 text-sm text-gray-600">
              Нажмите или перетащите изображение
            </p>
            <p className="text-xs text-gray-500 mt-1">
              PNG, JPG, WEBP до 10MB
            </p>
          </div>
        )}
      </div>
      <input
        ref={fileInputRef}
        type="file"
        accept={accept}
        onChange={handleFileChange}
        disabled={disabled}
        className="hidden"
      />
    </div>
  );
}
