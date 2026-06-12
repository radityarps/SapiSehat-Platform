"use client";

import { Badge } from '@/src/shared/ui/badge';
import { Button } from '@/src/shared/ui/button';
import { cn } from '@/src/shared/lib/utils';
import { Activity, Bell, ClipboardList, LayoutDashboard, ShieldAlert, FileClock, Menu, Users } from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEffect, useState } from 'react';
import { useAgencySession } from '@/src/features/auth/session-context';
import { getMe } from '@/src/shared/api/client';
import type { AgencyMe } from '@/src/shared/types/api';
import { LogoutButton } from './logout-button';

const navItems = [
  { href: '/agency/overview', label: 'Overview', icon: LayoutDashboard },
  { href: '/agency/registry', label: 'Registry', icon: Users },
  { href: '/agency/detections', label: 'Detections', icon: ClipboardList },
  { href: '/agency/risk-signals', label: 'Risk Signals', icon: ShieldAlert },
  { href: '/agency/follow-ups', label: 'Follow Ups', icon: Bell },
  { href: '/agency/audit-logs', label: 'Audit Logs', icon: FileClock }
];

export function AppShell({ children, agencyName }: { children: React.ReactNode; agencyName: string }) {
  const pathname = usePathname();
  const { token } = useAgencySession();
  const [me, setMe] = useState<AgencyMe | null>(null);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    if (!token) return;
    getMe(token).then(setMe).catch(() => setMe(null));
  }, [token]);

  useEffect(() => {
    setMobileOpen(false);
  }, [pathname]);

  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/80">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-3 lg:px-6">
          <div className="flex items-center gap-3">
            <Button variant="outline" size="icon" className="lg:hidden" aria-label="Open navigation" onClick={() => setMobileOpen((value) => !value)}>
              <Menu className="h-4 w-4" />
            </Button>
            <div>
              <div className="text-sm font-semibold">SapiSehat Agency</div>
              <div className="text-xs text-muted-foreground">{me?.name ?? agencyName}</div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="secondary" className="hidden gap-1 lg:inline-flex">
              <Activity className="h-3.5 w-3.5" />
              Calm triage
            </Badge>
            <LogoutButton />
          </div>
        </div>
      </div>

      {mobileOpen ? (
        <div className="border-b bg-background lg:hidden">
          <nav className="mx-auto grid max-w-7xl gap-1 px-4 py-3">
            {navItems.map((item) => {
              const active = pathname === item.href;
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                    active ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:bg-secondary hover:text-foreground'
                  )}
                >
                  <Icon className="h-4 w-4" />
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>
      ) : null}

      <div className="mx-auto grid max-w-7xl gap-6 px-4 py-6 lg:grid-cols-[240px_minmax(0,1fr)] lg:px-6">
        <aside className="hidden lg:block">
          <nav className="sticky top-6 space-y-1 rounded-lg border bg-card p-3 shadow-sm">
            {navItems.map((item) => {
              const active = pathname === item.href;
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                    active ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:bg-secondary hover:text-foreground'
                  )}
                >
                  <Icon className="h-4 w-4" />
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </aside>

        <main className="min-w-0">
          <div className="mb-6 rounded-lg border bg-card p-4 text-sm text-muted-foreground shadow-sm">
            Agency UI uses safe wording, risk signals, review items, and follow-up priority. No diagnosis, no outbreak claim.
          </div>
          {children}
        </main>
      </div>
    </div>
  );
}
