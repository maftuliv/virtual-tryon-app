import { useState, useCallback } from 'react';

interface UseImageUploadOptions {
  maxSize?: number; // в байтах
  acceptedFormats?: string[];
  onError?: (error: string) => void;
}

export function useImageUpload(options: UseImageUploadOptions = {}) {
  const {
    maxSize = 10 * 1024 * 1024, // 10MB по умолчанию
    acceptedFormats = ['image/jpeg', 'image/png', 'image/webp'],
    onError,
  } = options;

  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleUpload = useCallback(
    (uploadedFile: File) => {
      setError(null);

      // Проверка формата
      if (!acceptedFormats.includes(uploadedFile.type)) {
        const errorMsg = `Неподдерживаемый формат. Используйте: ${acceptedFormats.join(', ')}`;
        setError(errorMsg);
        onError?.(errorMsg);
        return;
      }

      // Проверка размера
      if (uploadedFile.size > maxSize) {
        const errorMsg = `Файл слишком большой. Максимальный размер: ${maxSize / 1024 / 1024}MB`;
        setError(errorMsg);
        onError?.(errorMsg);
        return;
      }

      setIsLoading(true);

      // Создание превью
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreview(reader.result as string);
        setFile(uploadedFile);
        setIsLoading(false);
      };
      reader.onerror = () => {
        const errorMsg = 'Ошибка при чтении файла';
        setError(errorMsg);
        onError?.(errorMsg);
        setIsLoading(false);
      };
      reader.readAsDataURL(uploadedFile);
    },
    [maxSize, acceptedFormats, onError]
  );

  const reset = useCallback(() => {
    setFile(null);
    setPreview(null);
    setError(null);
    setIsLoading(false);
  }, []);

  return {
    file,
    preview,
    error,
    isLoading,
    handleUpload,
    reset,
  };
}
