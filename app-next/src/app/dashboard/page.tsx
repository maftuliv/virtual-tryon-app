import { redirect } from 'next/navigation';

// Redirect to gallery page
export default function DashboardPage() {
  redirect('/gallery');
}
