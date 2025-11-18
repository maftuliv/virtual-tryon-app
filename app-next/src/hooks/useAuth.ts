import { useAuthStore } from '@/store/auth.store';
import { authApi } from '@/lib/api';
import { useCallback } from 'react';

export function useAuth() {
  const { user, token, isAuthenticated, isLoading, login, logout, setLoading } = useAuthStore();

  const handleLogin = useCallback(
    async (email: string, password: string) => {
      setLoading(true);
      try {
        const response = await authApi.login(email, password);
        login(response.user, response.token);
        return { success: true };
      } catch (err) {
        const error = err as Error;
        setLoading(false);
        return {
          success: false,
          error: error.message || 'Ошибка входа',
        };
      }
    },
    [login, setLoading]
  );

  const handleRegister = useCallback(
    async (email: string, password: string, name?: string) => {
      setLoading(true);
      try {
        const response = await authApi.register(email, password, name);
        login(response.user, response.token);
        return { success: true };
      } catch (err) {
        const error = err as Error;
        setLoading(false);
        return {
          success: false,
          error: error.message || 'Ошибка регистрации',
        };
      }
    },
    [login, setLoading]
  );

  const handleLogout = useCallback(async () => {
    try {
      await authApi.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      logout();
    }
  }, [logout]);

  return {
    user,
    token,
    isAuthenticated,
    isLoading,
    login: handleLogin,
    register: handleRegister,
    logout: handleLogout,
  };
}
