"use client";

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { clearAgencyToken, getAgencyToken, sessionEventName } from '@/lib/auth';
import { getMe } from '@/lib/api';
import { usePathname, useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

type State = 'checking' | 'valid' | 'missing' | 'invalid';

export function SessionGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [state, setState] = useState<State>('checking');

  useEffect(() => {
    let active = true;

    async function validate() {
      const token = getAgencyToken();
      if (!token) {
        setState('missing');
        return;
      }
      setState('checking');
      try {
        const me = await getMe(token);
        if (!active) return;
        if (me.account_type !== 'agency') {
          clearAgencyToken();
          setState('invalid');
          return;
        }
        setState('valid');
      } catch {
        if (!active) return;
        clearAgencyToken();
        setState('invalid');
      }
    }

    validate();
    window.addEventListener(sessionEventName, validate);
    return () => {
      active = false;
      window.removeEventListener(sessionEventName, validate);
    };
  }, [pathname]);

  if (state === 'valid') return <>{children}</>;

  if (state === 'checking') {
    return (
      <main className="flex min-h-screen items-center justify-center bg-background px-4 py-10">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle>Checking session</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-3/4" />
          </CardContent>
        </Card>
      </main>
    );
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-background px-4 py-10">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>{state === 'missing' ? 'Sign in required' : 'Session expired'}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-sm text-muted-foreground">
          <p>{state === 'missing' ? 'Agency dashboard requires an active agency session.' : 'Your agency session is no longer valid. Sign in again.'}</p>
          <Button onClick={() => router.push(`/login?next=${encodeURIComponent(pathname)}`)}>Go to login</Button>
        </CardContent>
      </Card>
    </main>
  );
}
