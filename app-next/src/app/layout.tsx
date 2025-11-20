import type { Metadata } from 'next';
import ClientProviders from '@/components/ClientProviders';
import '@/styles/globals.css';
import '@/styles/dashboard.css';
import '@/styles/landing.css';
import '@/styles/admin.css';

export const metadata: Metadata = {
  title: 'Tap to look - Виртуальная примерка одежды',
  description: 'Попробуйте одежду виртуально с помощью искусственного интеллекта. Загрузите свое фото и посмотрите, как на вас будет сидеть любая вещь.',
  keywords: ['виртуальная примерка', 'AI', 'мода', 'одежда', 'онлайн шопинг'],
  authors: [{ name: 'Tap to look' }],
  viewport: {
    width: 'device-width',
    initialScale: 1,
    maximumScale: 5,
  },
  themeColor: '#4A90E2',
  openGraph: {
    type: 'website',
    locale: 'ru_RU',
    url: 'https://taptolook.com',
    title: 'Tap to look - Виртуальная примерка одежды',
    description: 'Попробуйте одежду виртуально с помощью искусственного интеллекта',
    siteName: 'Tap to look',
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ru">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body className="antialiased">
        <ClientProviders>
          {children}
        </ClientProviders>
      </body>
    </html>
  );
}
