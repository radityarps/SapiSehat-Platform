"use client";

import { Button } from "@/src/shared/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/src/shared/ui/card";
import { Skeleton } from "@/src/shared/ui/skeleton";
import { useAgencySession } from "@/src/features/auth/session-context";
import { useRouteGuard } from "@/src/shared/auth/route-guard";
import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";

export function SessionGuard({ children }: { children: React.ReactNode }) {
	const router = useRouter();
	const pathname = usePathname();
	const { status, agency, signOut } = useAgencySession();

	useRouteGuard(pathname);

	useEffect(() => {
		if (status === "invalid") signOut();
	}, [signOut, status]);

	useEffect(() => {
		if (status === "anonymous" || status === "invalid") {
			router.replace(`/login?next=${encodeURIComponent(pathname)}`);
		}
	}, [status, pathname, router]);

	if (status === "authenticated" && agency?.account_type === "agency")
		return <>{children}</>;

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
