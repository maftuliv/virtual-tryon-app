'use client';

import useSWR from 'swr';
import { tryonApi, type UserTryon } from '@/lib/api';
import { useAuth } from './useAuth';

export function useTryons() {
  const { isAuthenticated } = useAuth();

  const { data, error, isLoading, mutate } = useSWR<UserTryon[]>(
    isAuthenticated ? '/api/user/tryons' : null,
    () => tryonApi.getUserTryons(),
    {
      revalidateOnFocus: false,
      revalidateOnReconnect: false,
    }
  );

  const toggleFavorite = async (tryonId: number, isFavorite: boolean) => {
    try {
      await tryonApi.toggleFavorite(tryonId, isFavorite);
      // Оптимистичное обновление
      mutate();
    } catch (error) {
      console.error('Failed to toggle favorite:', error);
      throw error;
    }
  };

  const updateTitle = async (tryonId: string, title: string) => {
    try {
      await tryonApi.updateTitle(tryonId, title);
      // Оптимистичное обновление
      mutate();
    } catch (error) {
      console.error('Failed to update title:', error);
      throw error;
    }
  };

  return {
    tryons: data,
    isLoading,
    isError: error,
    toggleFavorite,
    updateTitle,
    refresh: mutate,
  };
}
