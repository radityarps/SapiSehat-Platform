"use client";

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
} from "@/src/shared/ui/sidebar";
import {
  Activity,
  Bell,
  ChevronsUpDown,
  ClipboardList,
  FileClock,
  BookOpen,
  LayoutDashboard,
  LogOut,
  Search,
  Settings,
  ShieldAlert,
  Users,
} from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAgencySession } from "@/src/features/auth/session-context";
import { NotificationBell } from "@/src/features/agency/notifications/notification-sheet";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/src/shared/ui/dropdown-menu";
import { useEffect, useRef, useState } from "react";

import type { AgencyRole } from "@/src/shared/types/api";

const navItems = [
  {
    href: "/agency/overview",
    label: "Overview",
    icon: LayoutDashboard,
    keywords: ["home", "dashboard", "triage", "summary"],
    roles: [
      "admin",
      "province_officer",
      "district_officer",
      "village_officer",
      "viewer",
    ] as AgencyRole[],
  },
  {
    href: "/agency/registry",
    label: "Registry",
    icon: Users,
    keywords: ["farmers", "cattle", "list", "search"],
    roles: ["admin", "province_officer", "district_officer"] as AgencyRole[],
  },
  {
    href: "/agency/detections",
    label: "Detections",
    icon: ClipboardList,
    keywords: ["disease", "scan", "evidence", "monitoring"],
    roles: ["admin", "province_officer", "district_officer"] as AgencyRole[],
  },
  {
    href: "/agency/risk-signals",
    label: "Risk Signals",
    icon: ShieldAlert,
    keywords: ["risk", "signal", "jurisdiction", "priority"],
    roles: ["admin", "province_officer", "district_officer"] as AgencyRole[],
  },
  {
    href: "/agency/follow-ups",
    label: "Follow-ups",
    icon: Bell,
    keywords: ["follow", "action", "status", "record"],
    roles: ["admin", "province_officer", "district_officer"] as AgencyRole[],
  },
  {
    href: "/agency/guides",
    label: "Guide CMS",
    icon: BookOpen,
    keywords: ["guide", "article", "category", "cms"],
    roles: ["admin"] as AgencyRole[],
  },
  {
    href: "/agency/audit-logs",
    label: "Audit Logs",
    icon: FileClock,
    keywords: ["audit", "log", "history", "activity"],
    roles: ["admin"] as AgencyRole[],
  },
  {
    href: "/agency/users",
    label: "User Management",
    icon: Users,
    keywords: ["users", "roles", "permissions", "manage"],
    roles: ["admin"] as AgencyRole[],
  },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <SidebarProvider>
      <AppSidebar />
      <main className="flex-1 overflow-auto">
        <TopBar />
        <div className="p-6">{children}</div>
      </main>
    </SidebarProvider>
  );
}

function TopBar() {
  return (
    <header className="sticky top-0 z-10 flex h-14 items-center gap-3 border-b bg-background px-4">
      <SidebarTrigger />
      <div className="flex-1 flex justify-center">
        <CommandSearch />
      </div>
      <div className="flex items-center gap-1">
        <NotificationBell />
      </div>
    </header>
  );
}

function CommandSearch() {
  const router = useRouter();
  const { agency } = useAgencySession();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const visibleItems = navItems.filter(
    (item) => !agency?.role || item.roles.includes(agency.role),
  );

  const filtered = visibleItems.filter((item) => {
    if (!query) return true;
    const q = query.toLowerCase();
    return (
      item.label.toLowerCase().includes(q) ||
      item.keywords.some((k) => k.includes(q))
    );
  });

  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setOpen(true);
        setTimeout(() => inputRef.current?.focus(), 0);
      }
      if (e.key === "Escape") {
        setOpen(false);
        setQuery("");
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (
        containerRef.current &&
        !containerRef.current.contains(e.target as Node)
      ) {
        setOpen(false);
        setQuery("");
      }
    }
    if (open) document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, [open]);

  function navigate(href: string) {
    router.push(href);
    setOpen(false);
    setQuery("");
  }

  return (
    <div ref={containerRef} className="relative w-full max-w-sm">
      <button
        type="button"
        onClick={() => {
          setOpen(true);
          setTimeout(() => inputRef.current?.focus(), 0);
        }}
        className="flex h-8 w-full items-center gap-2 rounded-md border bg-muted/40 px-3 text-sm text-muted-foreground transition-colors hover:bg-muted/60"
      >
        <Search className="h-3.5 w-3.5" />
        <span className="flex-1 text-left">Search menu...</span>
        <kbd className="pointer-events-none hidden rounded border bg-background px-1.5 py-0.5 text-[10px] font-medium text-muted-foreground sm:inline-block">
          ⌘K
        </kbd>
      </button>

      {open && (
        <div className="absolute top-full left-0 z-50 mt-1 w-full rounded-md border bg-popover p-1 shadow-md">
          <div className="flex items-center gap-2 border-b px-2 pb-1.5">
            <Search className="h-3.5 w-3.5 text-muted-foreground" />
            <input
              ref={inputRef}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && filtered.length > 0) {
                  navigate(filtered[0].href);
                }
              }}
              placeholder="Search pages..."
              className="flex-1 bg-transparent py-1.5 text-sm outline-none placeholder:text-muted-foreground"
            />
          </div>
          <div className="mt-1 max-h-48 overflow-auto">
            {filtered.length === 0 && (
              <p className="px-2 py-3 text-center text-xs text-muted-foreground">
                No results found.
              </p>
            )}
            {filtered.map((item) => (
              <button
                key={item.href}
                type="button"
                onClick={() => navigate(item.href)}
                className="flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-sm hover:bg-accent hover:text-accent-foreground"
              >
                <item.icon className="h-4 w-4 text-muted-foreground" />
                <span>{item.label}</span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function AppSidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { agency, signOut } = useAgencySession();

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader className="border-b px-4 py-3">
        <div className="flex items-center gap-2 overflow-hidden">
          <Activity className="h-5 w-5 shrink-0 text-primary" />
          <span className="truncate text-sm font-semibold">
            SapiSehat Dashboard
          </span>
        </div>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              {navItems
                .filter(
                  (item) => !agency?.role || item.roles.includes(agency.role),
                )
                .map((item) => {
                  const active = pathname === item.href;
                  return (
                    <SidebarMenuItem key={item.href}>
                      <SidebarMenuButton
                        asChild
                        isActive={active}
                        tooltip={item.label}
                      >
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

      <SidebarFooter className="border-t">
        <SidebarMenu>
          <SidebarMenuItem>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <SidebarMenuButton className="w-full">
                  <div className="h-6 w-6 shrink-0 rounded-full bg-primary/10 flex items-center justify-center">
                    <span className="text-xs font-medium text-primary">
                      {agency?.name?.charAt(0) ?? "A"}
                    </span>
                  </div>
                  <span className="truncate text-xs">
                    {agency?.name ?? "Agency Officer"}
                  </span>
                  <ChevronsUpDown className="ml-auto h-4 w-4 text-muted-foreground" />
                </SidebarMenuButton>
              </DropdownMenuTrigger>
              <DropdownMenuContent side="right" align="end" className="w-56">
                <div className="px-2 py-1.5">
                  <p className="text-sm font-medium">
                    {agency?.name ?? "Agency Officer"}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {agency?.role ?? "officer"} ·{" "}
                    {agency?.jurisdiction_id ?? "unknown"}
                  </p>
                </div>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  onClick={() => router.push("/agency/settings")}
                >
                  <Settings className="mr-2 h-4 w-4" />
                  Settings
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => signOut()}>
                  <LogOut className="mr-2 h-4 w-4" />
                  Log out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
    </Sidebar>
  );
}
