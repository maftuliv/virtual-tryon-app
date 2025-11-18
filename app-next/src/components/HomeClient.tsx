'use client';

import { useAuth } from '@/hooks/useAuth';
import { useOnboarding } from '@/hooks/useOnboarding';
import Header from '@/components/Header';
import Hero from '@/components/Hero';
import TryonForm from '@/components/TryonForm';
import InlineDashboard from '@/components/dashboard/InlineDashboard';
import OnboardingModal from '@/components/modals/OnboardingModal';

export default function HomeClient() {
  const { isAuthenticated } = useAuth();
  const { shouldShowOnboarding, completeOnboarding, userName } = useOnboarding();

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50">
      <Header />

      <main>
        {/* Hero Section */}
        <Hero />

        {/* Try-on Section */}
        <section id="tryon" className="py-20">
          <TryonForm />
        </section>

        {/* Inline Dashboard - показываем только для авторизованных */}
        {isAuthenticated && (
          <section id="dashboard" className="py-20">
            <InlineDashboard />
          </section>
        )}
      </main>

      {/* Onboarding Modal для новых пользователей */}
      <OnboardingModal
        isOpen={shouldShowOnboarding}
        onClose={completeOnboarding}
        userName={userName}
      />
    </div>
  );
}
