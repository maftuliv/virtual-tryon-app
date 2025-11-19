'use client';

import { ReactNode } from 'react';
import { SWRConfig } from 'swr';
import { swrConfig } from '@/lib/swr-config';
import GoogleOAuthHandler from './GoogleOAuthHandler';

export default function ClientProviders({ children }: { children: ReactNode }) {
  return (
    <SWRConfig value={swrConfig}>
      <GoogleOAuthHandler />
      {children}
    </SWRConfig>
  );
}
