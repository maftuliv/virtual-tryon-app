import { SWRConfiguration } from 'swr';
import api from './api';

// Глобальная конфигурация SWR
export const swrConfig: SWRConfiguration = {
  // Fetcher по умолчанию
  fetcher: (url: string) => api.get(url).json(),

  // Настройки кеширования
  revalidateOnFocus: false, // Не ревалидировать при фокусе окна
  revalidateOnReconnect: true, // Ревалидировать при восстановлении соединения
  dedupingInterval: 2000, // Дедупликация запросов (2 секунды)

  // Оптимизация производительности
  errorRetryCount: 2, // Количество повторных попыток при ошибке
  errorRetryInterval: 5000, // Интервал между повторами (5 секунд)
  focusThrottleInterval: 5000, // Throttle для revalidateOnFocus

  // Загрузка в фоне
  loadingTimeout: 3000, // Таймаут для индикатора загрузки

  // Обработка ошибок
  onError: (error, key) => {
    if (error.status !== 403 && error.status !== 404) {
      console.error('SWR Error:', error, 'Key:', key);
    }
  },

  // Стратегия обновления
  compare: (a, b) => {
    // Сравнение данных для определения необходимости обновления
    return JSON.stringify(a) === JSON.stringify(b);
  },
};

// Хук для работы с оптимистичными обновлениями
export function getOptimisticData<T>(
  currentData: T | undefined,
  newData: Partial<T>
): T | undefined {
  if (!currentData) return undefined;
  return { ...currentData, ...newData };
}
