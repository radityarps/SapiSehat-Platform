"use client";

import { cn } from '@/src/shared/lib/utils';
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarProvider,
  SidebarTrigger,
  useSidebar,
} from '@/src/shared/ui/sidebar';
import { Activity, Bell, ClipboardList, FileClock, LayoutDashboard, ShieldAlert, Users } from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAgencySession } from '@/src/features/auth/session-context';
import { LogoutButton } from './logout-button';

const navItems = [
  { href: '/agency/overview', label: 'Overview', icon: LayoutDashboard },
  { href: '/agency/registry', label: 'Registry', icon: Users },
  { href: '/agency/detections', label: 'Detections', icon: ClipboardList },
  { href: '/agency/risk-signals', label: 'Risk Signals', icon: ShieldAlert },
  { href: '/agency/follow-ups', label: 'Follow-ups', icon: Bell },
  { href: '/agency/audit-logs', label: 'Audit Logs', icon: FileClock },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <SidebarProvider>
      <AppSidebar />
      <main className="flex-1 overflow-auto">
        <header className="sticky top-0 z-10 flex h-14 items-center gap-2 border-b bg-background px-4">
          <SidebarTrigger />
          <div className="flex-1" />
          <LogoutButton />
        </header>
        <div className="p-6">{children}</div>
      </main>
    </SidebarProvider>
  );
}

function AppSidebar() {
  const pathname = usePathname();
  const { agency } = useAgencySession();

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader className="border-b px-4 py-3">
        <div className="flex items-center gap-2 overflow-hidden">
          <Activity className="h-5 w-5 shrink-0 text-primary" />
          <span className="truncate text-sm font-semibold">SapiSehat Agency</span>
        </div>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              {navItems.map((item) => {
                const active = pathname === item.href;
                return (
                  <SidebarMenuItem key={item.href}>
                    <SidebarMenuButton asChild isActive={active} tooltip={item.label}>
                      <Link href={item.href}>
                        <item.icon className="h-4 w-4" />
                        <span>{item.label}</span>
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                );
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="border-t px-4 py-3">
        <div className="flex items-center gap-2 overflow-hidden">
          <div className="h-6 w-6 shrink-0 rounded-full bg-primary/10 flex items-center justify-center">
            <span className="text-xs font-medium text-primary">
              {agency?.name?.charAt(0) ?? 'A'}
            </span>
          </div>
          <span className="truncate text-xs text-muted-foreground">
            {agency?.name ?? 'Agency Officer'}
          </span>
        </div>
      </SidebarFooter>
    </Sidebar>
  );
}
