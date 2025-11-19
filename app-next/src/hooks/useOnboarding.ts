'use client';

import { useState, useEffect } from 'react';
import { useAuth } from './useAuth';

export function useOnboarding() {
  const { isAuthenticated, user } = useAuth();
  const [shouldShowOnboarding, setShouldShowOnboarding] = useState(false);
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    // Проверяем только если пользователь авторизован
    if (!isAuthenticated) {
      setIsChecking(false);
      setShouldShowOnboarding(false);
      return;
    }

    // Проверяем, был ли уже показан onboarding
    const onboardingCompleted = localStorage.getItem('onboarding-completed');

    if (!onboardingCompleted) {
      // Показываем с небольшой задержкой для плавности
      setTimeout(() => {
        setShouldShowOnboarding(true);
        setIsChecking(false);
      }, 500);
    } else {
      setIsChecking(false);
    }
  }, [isAuthenticated]);

  const completeOnboarding = () => {
    localStorage.setItem('onboarding-completed', 'true');
    setShouldShowOnboarding(false);
  };

  return {
    shouldShowOnboarding,
    isChecking,
    completeOnboarding,
    userName: user?.full_name,
  };
}
