"use client";

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AgencySessionProvider } from '@/src/features/auth/session-context';
import { useState } from 'react';

export function ReactQueryProvider({ children }: { children: React.ReactNode }) {
  const [client] = useState(() => new QueryClient());
  return <QueryClientProvider client={client}><AgencySessionProvider>{children}</AgencySessionProvider></QueryClientProvider>;
}
