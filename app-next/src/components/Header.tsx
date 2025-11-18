'use client';

import { useState } from 'react';
import { useAuth } from '@/hooks/useAuth';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import Button from './Button';
import AuthModal from './modals/AuthModal';

export default function Header() {
  const { isAuthenticated, user, logout } = useAuth();
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

  return (
    <header className="fixed top-0 left-0 right-0 z-50 glass border-b border-white/20">
      <div className="max-w-7xl mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2">
            <h1 className="text-2xl font-bold bg-gradient-to-r from-primary to-purple-600 bg-clip-text text-transparent">
              Tap to look
            </h1>
          </Link>

          {/* Navigation */}
          <nav className="hidden md:flex items-center gap-6">
            {isHomePage ? (
              <a href="#tryon" className="text-sm font-medium hover:text-primary transition-colors">
                Примерка
              </a>
            ) : (
              <Link href="/#tryon" className="text-sm font-medium hover:text-primary transition-colors">
                Примерка
              </Link>
            )}

            {isAuthenticated && (
              <Link
                href="/dashboard"
                className={`text-sm font-medium hover:text-primary transition-colors ${isDashboardPage ? 'text-primary' : ''}`}
              >
                Кабинет
              </Link>
            )}

            {isHomePage ? (
              <a href="#about" className="text-sm font-medium hover:text-primary transition-colors">
                О нас
              </a>
            ) : (
              <Link href="/#about" className="text-sm font-medium hover:text-primary transition-colors">
                О нас
              </Link>
            )}
          </nav>

          {/* Auth buttons */}
          <div className="flex items-center gap-3">
            {isAuthenticated ? (
              <>
                <Link href="/dashboard" className="text-sm text-gray-600 hidden sm:inline hover:text-primary transition-colors">
                  {user?.name || user?.email}
                </Link>
                <Button variant="secondary" size="sm" onClick={logout}>
                  Выход
                </Button>
              </>
            ) : (
              <>
                <Button variant="ghost" size="sm" onClick={handleOpenLogin}>
                  Вход
                </Button>
                <Button variant="primary" size="sm" onClick={handleOpenRegister}>
                  Регистрация
                </Button>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Auth Modal */}
      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
        initialTab={authModalTab}
      />
    </header>
  );
}
