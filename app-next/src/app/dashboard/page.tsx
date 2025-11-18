import type { Metadata } from 'next';
import DashboardClient from '@/components/dashboard/DashboardClient';

export const metadata: Metadata = {
  title: 'Мой кабинет - Tap to look',
  description: 'Управляйте вашими виртуальными примерками, создавайте образы и следите за своим стилем',
};

// Server Component
export default function DashboardPage() {
  return <DashboardClient />;
}
