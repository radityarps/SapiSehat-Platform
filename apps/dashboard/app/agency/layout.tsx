import { AppShell } from '@/src/features/agency/layout/app-shell';
import { SessionGuard } from '@/src/features/auth/session-guard';

export default function AgencyLayout({ children }: { children: React.ReactNode }) {
  return (
    <SessionGuard>
      <AppShell agencyName="Semarang Officer">{children}</AppShell>
    </SessionGuard>
  );
}
