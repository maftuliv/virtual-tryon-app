'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useAuth } from '@/hooks/useAuth';
import Button from '../Button';

// Схемы валидации
const loginSchema = z.object({
  email: z.string().email('Неверный формат email'),
  password: z.string().min(6, 'Минимум 6 символов'),
});

const registerSchema = z.object({
  email: z.string().email('Неверный формат email'),
  password: z.string().min(6, 'Минимум 6 символов'),
  name: z.string().min(2, 'Минимум 2 символа').optional(),
  confirmPassword: z.string(),
}).refine((data) => data.password === data.confirmPassword, {
  message: 'Пароли не совпадают',
  path: ['confirmPassword'],
});

type LoginFormData = z.infer<typeof loginSchema>;
type RegisterFormData = z.infer<typeof registerSchema>;

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialTab?: 'login' | 'register';
}

export default function AuthModal({ isOpen, onClose, initialTab = 'login' }: AuthModalProps) {
  const [activeTab, setActiveTab] = useState<'login' | 'register'>(initialTab);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { login, register: registerUser } = useAuth();

  const loginForm = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: '',
      password: '',
    },
  });

  const registerForm = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      email: '',
      password: '',
      name: '',
      confirmPassword: '',
    },
  });

  const handleLogin = async (data: LoginFormData) => {
    setIsLoading(true);
    setError(null);

    try {
      await login(data.email, data.password);
      onClose();
      loginForm.reset();
    } catch (err) {
      const error = err as Error;
      setError(error.message || 'Ошибка входа. Проверьте данные.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegister = async (data: RegisterFormData) => {
    setIsLoading(true);
    setError(null);

    try {
      await registerUser(data.email, data.password, data.name);
      onClose();
      registerForm.reset();
    } catch (err) {
      const error = err as Error;
      setError(error.message || 'Ошибка регистрации. Попробуйте еще раз.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleClose = () => {
    if (!isLoading) {
      onClose();
      setError(null);
      loginForm.reset();
      registerForm.reset();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 backdrop-blur-sm animate-fade-in">
      <div className="glass rounded-4xl p-8 max-w-md w-full mx-4 relative">
        {/* Close button */}
        <button
          onClick={handleClose}
          disabled={isLoading}
          className="absolute top-4 right-4 text-gray-500 hover:text-gray-700 transition-colors disabled:opacity-50"
          aria-label="Закрыть"
        >
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        {/* Tabs */}
        <div className="flex gap-4 mb-6 border-b border-gray-200">
          <button
            onClick={() => setActiveTab('login')}
            disabled={isLoading}
            className={`pb-3 px-4 font-semibold transition-colors border-b-2 -mb-px ${
              activeTab === 'login'
                ? 'border-primary text-primary'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            Вход
          </button>
          <button
            onClick={() => setActiveTab('register')}
            disabled={isLoading}
            className={`pb-3 px-4 font-semibold transition-colors border-b-2 -mb-px ${
              activeTab === 'register'
                ? 'border-primary text-primary'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            Регистрация
          </button>
        </div>

        {/* Error message */}
        {error && (
          <div className="mb-4 p-4 rounded-xl bg-red-100 border border-red-200 text-red-700 text-sm">
            {error}
          </div>
        )}

        {/* Login Form */}
        {activeTab === 'login' && (
          <form onSubmit={loginForm.handleSubmit(handleLogin)} className="space-y-4">
            <div>
              <label htmlFor="login-email" className="block text-sm font-medium text-gray-700 mb-1">
                Email
              </label>
              <input
                id="login-email"
                type="email"
                {...loginForm.register('email')}
                disabled={isLoading}
                className="w-full px-4 py-2 rounded-xl border border-gray-300 focus:ring-2 focus:ring-primary focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed"
                placeholder="your@email.com"
              />
              {loginForm.formState.errors.email && (
                <p className="mt-1 text-sm text-red-600">{loginForm.formState.errors.email.message}</p>
              )}
            </div>

            <div>
              <label htmlFor="login-password" className="block text-sm font-medium text-gray-700 mb-1">
                Пароль
              </label>
              <input
                id="login-password"
                type="password"
                {...loginForm.register('password')}
                disabled={isLoading}
                className="w-full px-4 py-2 rounded-xl border border-gray-300 focus:ring-2 focus:ring-primary focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed"
                placeholder="••••••"
              />
              {loginForm.formState.errors.password && (
                <p className="mt-1 text-sm text-red-600">{loginForm.formState.errors.password.message}</p>
              )}
            </div>

            <Button
              type="submit"
              variant="primary"
              size="lg"
              fullWidth
              disabled={isLoading}
              isLoading={isLoading}
            >
              {isLoading ? 'Вход...' : 'Войти'}
            </Button>

            <div className="relative my-6">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-300"></div>
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-4 bg-white text-gray-500">или</span>
              </div>
            </div>

            <button
              type="button"
              onClick={() => {
                window.location.href = '/api/auth/google/login';
              }}
              disabled={isLoading}
              className="w-full flex items-center justify-center gap-3 px-4 py-3 border border-gray-300 rounded-xl hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M19.8 10.2273C19.8 9.51819 19.7364 8.83637 19.6182 8.18182H10.2V12.05H15.5818C15.3273 13.3 14.5636 14.3591 13.4091 15.0682V17.5773H16.7364C18.7091 15.8364 19.8 13.2727 19.8 10.2273Z" fill="#4285F4"/>
                <path d="M10.2 20C12.9 20 15.1727 19.1045 16.7364 17.5773L13.4091 15.0682C12.4636 15.6682 11.2727 16.0227 10.2 16.0227C7.59091 16.0227 5.37273 14.2636 4.54091 11.9H1.09091V14.4909C2.64545 17.5909 6.16364 20 10.2 20Z" fill="#34A853"/>
                <path d="M4.54091 11.9C4.32273 11.3 4.2 10.6591 4.2 10C4.2 9.34091 4.32273 8.7 4.54091 8.1V5.50909H1.09091C0.395455 6.89091 0 8.44545 0 10C0 11.5545 0.395455 13.1091 1.09091 14.4909L4.54091 11.9Z" fill="#FBBC05"/>
                <path d="M10.2 3.97727C11.3818 3.97727 12.4409 4.37727 13.2864 5.18182L16.2091 2.25909C15.1682 1.29545 12.9045 0 10.2 0C6.16364 0 2.64545 2.40909 1.09091 5.50909L4.54091 8.1C5.37273 5.73636 7.59091 3.97727 10.2 3.97727Z" fill="#EA4335"/>
              </svg>
              <span className="font-medium text-gray-700">Войти через Google</span>
            </button>

            <p className="text-xs text-center text-gray-500 mt-4">
              Нет аккаунта?{' '}
              <button
                type="button"
                onClick={() => setActiveTab('register')}
                disabled={isLoading}
                className="text-primary hover:underline disabled:opacity-50"
              >
                Зарегистрируйтесь
              </button>
            </p>
          </form>
        )}

        {/* Register Form */}
        {activeTab === 'register' && (
          <form onSubmit={registerForm.handleSubmit(handleRegister)} className="space-y-4">
            <div>
              <label htmlFor="register-name" className="block text-sm font-medium text-gray-700 mb-1">
                Имя (необязательно)
              </label>
              <input
                id="register-name"
                type="text"
                {...registerForm.register('name')}
                disabled={isLoading}
                className="w-full px-4 py-2 rounded-xl border border-gray-300 focus:ring-2 focus:ring-primary focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed"
                placeholder="Ваше имя"
              />
              {registerForm.formState.errors.name && (
                <p className="mt-1 text-sm text-red-600">{registerForm.formState.errors.name.message}</p>
              )}
            </div>

            <div>
              <label htmlFor="register-email" className="block text-sm font-medium text-gray-700 mb-1">
                Email
              </label>
              <input
                id="register-email"
                type="email"
                {...registerForm.register('email')}
                disabled={isLoading}
                className="w-full px-4 py-2 rounded-xl border border-gray-300 focus:ring-2 focus:ring-primary focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed"
                placeholder="your@email.com"
              />
              {registerForm.formState.errors.email && (
                <p className="mt-1 text-sm text-red-600">{registerForm.formState.errors.email.message}</p>
              )}
            </div>

            <div>
              <label htmlFor="register-password" className="block text-sm font-medium text-gray-700 mb-1">
                Пароль
              </label>
              <input
                id="register-password"
                type="password"
                {...registerForm.register('password')}
                disabled={isLoading}
                className="w-full px-4 py-2 rounded-xl border border-gray-300 focus:ring-2 focus:ring-primary focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed"
                placeholder="••••••"
              />
              {registerForm.formState.errors.password && (
                <p className="mt-1 text-sm text-red-600">{registerForm.formState.errors.password.message}</p>
              )}
            </div>

            <div>
              <label htmlFor="register-confirm-password" className="block text-sm font-medium text-gray-700 mb-1">
                Подтверждение пароля
              </label>
              <input
                id="register-confirm-password"
                type="password"
                {...registerForm.register('confirmPassword')}
                disabled={isLoading}
                className="w-full px-4 py-2 rounded-xl border border-gray-300 focus:ring-2 focus:ring-primary focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed"
                placeholder="••••••"
              />
              {registerForm.formState.errors.confirmPassword && (
                <p className="mt-1 text-sm text-red-600">{registerForm.formState.errors.confirmPassword.message}</p>
              )}
            </div>

            <Button
              type="submit"
              variant="primary"
              size="lg"
              fullWidth
              disabled={isLoading}
              isLoading={isLoading}
            >
              {isLoading ? 'Регистрация...' : 'Зарегистрироваться'}
            </Button>

            <div className="relative my-6">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-300"></div>
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-4 bg-white text-gray-500">или</span>
              </div>
            </div>

            <button
              type="button"
              onClick={() => {
                window.location.href = '/api/auth/google/login';
              }}
              disabled={isLoading}
              className="w-full flex items-center justify-center gap-3 px-4 py-3 border border-gray-300 rounded-xl hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M19.8 10.2273C19.8 9.51819 19.7364 8.83637 19.6182 8.18182H10.2V12.05H15.5818C15.3273 13.3 14.5636 14.3591 13.4091 15.0682V17.5773H16.7364C18.7091 15.8364 19.8 13.2727 19.8 10.2273Z" fill="#4285F4"/>
                <path d="M10.2 20C12.9 20 15.1727 19.1045 16.7364 17.5773L13.4091 15.0682C12.4636 15.6682 11.2727 16.0227 10.2 16.0227C7.59091 16.0227 5.37273 14.2636 4.54091 11.9H1.09091V14.4909C2.64545 17.5909 6.16364 20 10.2 20Z" fill="#34A853"/>
                <path d="M4.54091 11.9C4.32273 11.3 4.2 10.6591 4.2 10C4.2 9.34091 4.32273 8.7 4.54091 8.1V5.50909H1.09091C0.395455 6.89091 0 8.44545 0 10C0 11.5545 0.395455 13.1091 1.09091 14.4909L4.54091 11.9Z" fill="#FBBC05"/>
                <path d="M10.2 3.97727C11.3818 3.97727 12.4409 4.37727 13.2864 5.18182L16.2091 2.25909C15.1682 1.29545 12.9045 0 10.2 0C6.16364 0 2.64545 2.40909 1.09091 5.50909L4.54091 8.1C5.37273 5.73636 7.59091 3.97727 10.2 3.97727Z" fill="#EA4335"/>
              </svg>
              <span className="font-medium text-gray-700">Войти через Google</span>
            </button>

            <p className="text-xs text-center text-gray-500 mt-4">
              Уже есть аккаунт?{' '}
              <button
                type="button"
                onClick={() => setActiveTab('login')}
                disabled={isLoading}
                className="text-primary hover:underline disabled:opacity-50"
              >
                Войдите
              </button>
            </p>
          </form>
        )}
      </div>
    </div>
  );
}
