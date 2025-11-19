'use client';

import { useEffect } from 'react';
import { useAuthStore } from '@/store/auth.store';
import { authApi } from '@/lib/api';

interface User {
  id: string;
  email: string;
  name?: string;
  createdAt: string;
}

/**
 * Component to handle Google OAuth callback with JWT token in URL hash
 *
 * After Google OAuth, backend redirects to:
 * /#google_auth_success=1&token=<jwt_token>
 * or
 * /#google_auth_error=1&message=<error_message>
 *
 * This component reads the hash, extracts the token, fetches user data,
 * and stores both in the auth store.
 */
export default function GoogleOAuthHandler() {
  const { login, setLoading } = useAuthStore();

  useEffect(() => {
    // Only run in browser
    if (typeof window === 'undefined') return;

    const handleOAuthCallback = async () => {
      // Check for hash params (Google OAuth callback uses hash, not query params)
      const hash = window.location.hash;
      if (!hash || !hash.includes('google_auth')) return;

      // Parse hash params
      const hashParams = new URLSearchParams(hash.substring(1));

      // Check for error
      if (hashParams.has('google_auth_error')) {
        const message = hashParams.get('message') || 'Ошибка входа через Google';
        console.error('[GoogleOAuthHandler] OAuth error:', message);
        alert(message);

        // Clean up URL
        window.history.replaceState(null, '', window.location.pathname);
        return;
      }

      // Check for success with token
      if (hashParams.has('google_auth_success') && hashParams.has('token')) {
        const token = hashParams.get('token');

        if (!token) {
          console.error('[GoogleOAuthHandler] No token in success callback');
          return;
        }

        setLoading(true);

        try {
          // Fetch user data using the token
          const user = await authApi.me(token) as User;

          // Store user and token in auth store (persists to localStorage)
          login(user, token);

          console.log('[GoogleOAuthHandler] User logged in:', user.email);

          // Clean up URL (remove hash)
          window.history.replaceState(null, '', window.location.pathname);

        } catch (error) {
          console.error('[GoogleOAuthHandler] Failed to fetch user data:', error);
          alert('Не удалось получить данные пользователя. Попробуйте еще раз.');
          setLoading(false);
        }
      }
    };

    // Run handler on mount and when hash changes
    handleOAuthCallback();

    // Listen for hash changes (in case user navigates with back/forward)
    window.addEventListener('hashchange', handleOAuthCallback);

    return () => {
      window.removeEventListener('hashchange', handleOAuthCallback);
    };
  }, [login, setLoading]);

  // This component doesn't render anything
  return null;
}
