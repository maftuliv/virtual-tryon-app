'use client';

import { useState } from 'react';
import { useAuth } from '@/hooks/useAuth';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import Button from './Button';
import AuthModal from './modals/AuthModal';

export default function Header() {
  const { isAuthenticated, user } = useAuth();
  const pathname = usePathname();
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [authModalTab, setAuthModalTab] = useState<'login' | 'register'>('login');

  const isHomePage = pathname === '/';
  const isDashboardPage = pathname === '/dashboard';

  const handleOpenLogin = () => {
    setAuthModalTab('login');
    setIsAuthModalOpen(true);
  };

  const handleOpenRegister = () => {
    setAuthModalTab('register');
    setIsAuthModalOpen(true);
  };

  // Получаем первую букву имени или email для аватара
  const getUserInitial = () => {
    if (user?.name) return user.name.charAt(0).toUpperCase();
    if (user?.email) return user.email.charAt(0).toUpperCase();
    return 'U';
  };

  return (
    <>
      <header className="fixed top-0 left-0 right-0 z-50 px-4 pt-6">
        <div className="max-w-[1200px] mx-auto">
          <div className="glass-strong rounded-full px-5 py-3.5 flex items-center justify-between gap-4 flex-wrap">
            {/* Logo */}
            <Link href="/" className="flex items-center gap-2.5">
              <div className="logo-pill">Tap</div>
              <div className="text-lg font-semibold text-[#433d74]">to look</div>
            </Link>

            {/* Centered tagline - hidden on mobile */}
            <div className="hidden lg:block text-[13px] text-[var(--text-muted)] whitespace-nowrap">
              ✨✨ Здесь рождается твой новый стиль — просто нажми, чтобы посмотреть! ✨✨
            </div>

            {/* Right section */}
            <div className="flex items-center gap-3.5">
              {/* Navigation Links - hidden on small screens */}
              <nav className="hidden md:flex items-center gap-2.5 text-[13px]">
                <Link
                  href="/dashboard"
                  className={`px-2.5 py-1 rounded-full transition-all duration-150 cursor-pointer ${
                    isDashboardPage
                      ? 'bg-[rgba(248,235,255,0.95)] text-[var(--accent)] font-semibold'
                      : 'text-[var(--text-muted)] hover:bg-[rgba(239,228,255,0.9)] hover:text-[var(--text-main)]'
                  }`}
                >
                  Дашборд
                </Link>
                {isHomePage ? (
                  <a
                    href="#tryon"
                    className="px-2.5 py-1 rounded-full text-[var(--text-muted)] hover:bg-[rgba(239,228,255,0.9)] hover:text-[var(--text-main)] transition-all duration-150 cursor-pointer"
                  >
                    Примерка
                  </a>
                ) : (
                  <Link
                    href="/#tryon"
                    className="px-2.5 py-1 rounded-full text-[var(--text-muted)] hover:bg-[rgba(239,228,255,0.9)] hover:text-[var(--text-main)] transition-all duration-150 cursor-pointer"
                  >
                    Примерка
                  </Link>
                )}
                <Link
                  href="/dashboard"
                  className="px-2.5 py-1 rounded-full text-[var(--text-muted)] hover:bg-[rgba(239,228,255,0.9)] hover:text-[var(--text-main)] transition-all duration-150 cursor-pointer"
                >
                  Образы
                </Link>
                <Link
                  href="/dashboard"
                  className="px-2.5 py-1 rounded-full text-[var(--text-muted)] hover:bg-[rgba(239,228,255,0.9)] hover:text-[var(--text-main)] transition-all duration-150 cursor-pointer"
                >
                  Моя одежда
                </Link>
                <Link
                  href="/dashboard"
                  className="px-2.5 py-1 rounded-full text-[var(--text-muted)] hover:bg-[rgba(239,228,255,0.9)] hover:text-[var(--text-main)] transition-all duration-150 cursor-pointer"
                >
                  История
                </Link>
              </nav>

              {/* User section */}
              {isAuthenticated ? (
                <div className="user-pill">
                  <div className="user-avatar">{getUserInitial()}</div>
                  <span className="text-sm font-medium text-[var(--text-main)] hidden sm:inline">
                    {user?.name || 'User'}
                  </span>
                  <span className="badge-premium">Premium</span>
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <Button variant="ghost" size="sm" onClick={handleOpenLogin}>
                    Вход
                  </Button>
                  <Button variant="primary" size="sm" onClick={handleOpenRegister}>
                    Регистрация
                  </Button>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Spacer to prevent content from being hidden behind fixed header */}
      <div className="h-[88px]" />

      {/* Auth Modal */}
      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
        initialTab={authModalTab}
      />
    </>
  );
}
