import { AppShell } from '@/components/app-shell';
import { SessionGuard } from '@/components/session-guard';

export default function AgencyLayout({ children }: { children: React.ReactNode }) {
  return (
    <SessionGuard>
      <AppShell agencyName="Semarang Officer">{children}</AppShell>
    </SessionGuard>
  );
}
