"use client";

import { Button } from "@/src/shared/ui/button";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/src/shared/ui/sheet";
import { Skeleton } from "@/src/shared/ui/skeleton";
import { getNotifications, markAllNotificationsRead, markNotificationRead } from "@/src/shared/api/client";
import { useAgencySession } from "@/src/features/auth/session-context";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bell, Check, ExternalLink } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

export function NotificationBell() {
	const { token } = useAgencySession();
	const [open, setOpen] = useState(false);
	const enabled = Boolean(token);

	const query = useQuery({
		queryKey: ["notifications"],
		queryFn: () => getNotifications(token),
		enabled,
		refetchInterval: 30000,
	});

	const unreadCount = query.data?.unread_count ?? 0;

	return (
		<>
			<Button
				variant="ghost"
				size="icon"
				className="relative h-8 w-8"
				aria-label="Notifications"
				onClick={() => setOpen(true)}
			>
				<Bell className="h-4 w-4" />
				{unreadCount > 0 && (
					<span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-destructive px-1 text-[10px] font-medium text-destructive-foreground">
						{unreadCount > 99 ? "99+" : unreadCount}
					</span>
				)}
			</Button>
			<NotificationSheet open={open} onOpenChange={setOpen} />
		</>
	);
}

function NotificationSheet({ open, onOpenChange }: { open: boolean; onOpenChange: (v: boolean) => void }) {
	const { token } = useAgencySession();
	const queryClient = useQueryClient();
	const router = useRouter();
	const enabled = Boolean(token);

	const query = useQuery({
		queryKey: ["notifications"],
		queryFn: () => getNotifications(token),
		enabled,
	});

	const markRead = useMutation({
		mutationFn: (id: string) => markNotificationRead(token, id),
		onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notifications"] }),
	});

	const markAll = useMutation({
		mutationFn: () => markAllNotificationsRead(token),
		onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notifications"] }),
	});

	const notifications = query.data?.notifications ?? [];

	function handleClick(link: string | null | undefined, id: string) {
		if (!markRead.isPending) markRead.mutate(id);
		if (link) {
			onOpenChange(false);
			router.push(link);
		}
	}

	return (
		<Sheet open={open} onOpenChange={onOpenChange}>
			<SheetContent className="w-full sm:max-w-md">
				<SheetHeader className="space-y-1">
					<SheetTitle className="text-base">Notifications</SheetTitle>
					<SheetDescription className="sr-only">
						Recent notifications for your account.
					</SheetDescription>
				</SheetHeader>

				<div className="mt-4 flex items-center justify-between">
					<p className="text-xs text-muted-foreground">
						{query.isLoading ? "Loading..." : `${notifications.length} notification${notifications.length === 1 ? "" : "s"}`}
					</p>
					{notifications.some((n) => !n.is_read) && (
						<Button
							variant="ghost"
							size="sm"
							className="h-7 text-xs"
							onClick={() => markAll.mutate()}
							disabled={markAll.isPending}
						>
							<Check className="mr-1 h-3 w-3" /> Mark all read
						</Button>
					)}
				</div>

				<div className="mt-2 h-[calc(100vh-180px)] overflow-y-auto pr-1">
					{query.isLoading ? (
						<div className="space-y-2">
							<Skeleton className="h-16 w-full" />
							<Skeleton className="h-16 w-full" />
							<Skeleton className="h-16 w-full" />
						</div>
					) : notifications.length === 0 ? (
						<div className="flex flex-col items-center justify-center py-12 text-center text-sm text-muted-foreground">
							<Bell className="mb-2 h-8 w-8 opacity-20" />
							<p>No notifications yet.</p>
						</div>
					) : (
						<div className="space-y-1">
							{notifications.map((n) => (
								<button
									key={n.id}
									type="button"
									onClick={() => handleClick(n.link, n.id)}
									className={`group flex w-full gap-3 rounded-md border p-3 text-left transition-colors hover:bg-muted/50 ${n.is_read ? "bg-background opacity-70" : "bg-muted/20"}`}
								>
									<div className="flex-1 min-w-0">
										<p className="text-sm font-medium">{n.title}</p>
										<p className="line-clamp-2 text-xs text-muted-foreground">{n.body}</p>
										<p className="mt-1 text-[10px] text-muted-foreground">
											{n.created_at ? new Date(n.created_at).toLocaleString() : ""}
										</p>
									</div>
									<div className="flex flex-col items-end gap-1">
										{!n.is_read && <span className="h-2 w-2 rounded-full bg-primary" />}
										{n.link && <ExternalLink className="h-3 w-3 text-muted-foreground opacity-0 group-hover:opacity-100" />}
									</div>
								</button>
							))}
						</div>
					)}
				</div>
			</SheetContent>
		</Sheet>
	);
}
	