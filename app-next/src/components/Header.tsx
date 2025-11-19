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
    if (user?.full_name) return user.full_name.charAt(0).toUpperCase();
    if (user?.email) return user.email.charAt(0).toUpperCase();
    return 'U';
  };

  return (
    <>
      {/* EXACT Header from HTML file - NOT fixed */}
      <header
        className="flex items-center justify-between px-5 py-3.5 mb-5 rounded-full border flex-wrap gap-2.5"
        style={{
          background: 'rgba(255, 255, 255, 0.86)',
          borderColor: 'var(--card-border)',
          boxShadow: '0 16px 45px rgba(164, 116, 255, 0.35)',
          backdropFilter: 'blur(18px)',
        }}
      >
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2.5 font-semibold text-lg">
          <div className="logo-pill">Tap</div>
          <div style={{ color: '#433d74' }}>to look</div>
        </Link>

        {/* Centered tagline - hidden on mobile */}
        <div className="hidden lg:block text-[13px] text-[var(--text-muted)] whitespace-nowrap">
          ✨✨ Здесь рождается твой новый стиль — просто нажми, чтобы посмотреть! ✨✨
        </div>

        {/* Right section */}
        <div className="flex items-center gap-3.5 text-sm">
          {/* Navigation Links - hidden on small screens */}
          <nav className="hidden md:flex items-center gap-2.5 text-[13px] text-[var(--text-muted)]">
            <Link
              href="/dashboard"
              className={`px-2.5 py-1 rounded-full cursor-pointer transition-all duration-150 ${
                isDashboardPage
                  ? 'bg-[rgba(248,235,255,0.95)] text-[var(--accent)] font-semibold'
                  : 'hover:bg-[rgba(239,228,255,0.9)] hover:text-[var(--text-main)]'
              }`}
            >
              Дашборд
            </Link>
            {isHomePage ? (
              <a
                href="#tryon"
                className="px-2.5 py-1 rounded-full cursor-pointer transition-all duration-150 hover:bg-[rgba(239,228,255,0.9)] hover:text-[var(--text-main)]"
              >
                Примерка
              </a>
            ) : (
              <Link
                href="/#tryon"
                className="px-2.5 py-1 rounded-full cursor-pointer transition-all duration-150 hover:bg-[rgba(239,228,255,0.9)] hover:text-[var(--text-main)]"
              >
                Примерка
              </Link>
            )}
            <Link
              href="/dashboard"
              className="px-2.5 py-1 rounded-full cursor-pointer transition-all duration-150 hover:bg-[rgba(239,228,255,0.9)] hover:text-[var(--text-main)]"
            >
              Образы
            </Link>
            <Link
              href="/dashboard"
              className="px-2.5 py-1 rounded-full cursor-pointer transition-all duration-150 hover:bg-[rgba(239,228,255,0.9)] hover:text-[var(--text-main)]"
            >
              Моя одежда
            </Link>
            <Link
              href="/dashboard"
              className="px-2.5 py-1 rounded-full cursor-pointer transition-all duration-150 hover:bg-[rgba(239,228,255,0.9)] hover:text-[var(--text-main)]"
            >
              История
            </Link>
          </nav>

          {/* User section */}
          {isAuthenticated ? (
            <div className="user-pill">
              <div className="user-avatar">{getUserInitial()}</div>
              <span className="font-medium text-[var(--text-main)]">
                {user?.full_name || user?.email?.split('@')[0] || 'User'}
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
      </header>

      {/* Auth Modal */}
      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
        initialTab={authModalTab}
      />
    </>
  );
}
