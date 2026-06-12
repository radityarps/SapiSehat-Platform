"use client";

import { Button } from '@/src/shared/ui/button';
import { useAgencySession } from '@/src/features/auth/session-context';
import { useRouter } from 'next/navigation';

export function LogoutButton() {
  const router = useRouter();
  const { signOut } = useAgencySession();

  return (
    <Button
      variant="outline"
      onClick={() => {
        signOut();
        router.push('/login');
      }}
    >
      Sign out
    </Button>
  );
}
