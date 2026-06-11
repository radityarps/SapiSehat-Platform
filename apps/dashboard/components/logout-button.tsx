"use client";

import { Button } from '@/components/ui/button';
import { clearAgencyToken } from '@/lib/auth';
import { useRouter } from 'next/navigation';

export function LogoutButton() {
  const router = useRouter();

  return (
    <Button
      variant="outline"
      onClick={() => {
        clearAgencyToken();
        router.push('/login');
      }}
    >
      Sign out
    </Button>
  );
}
