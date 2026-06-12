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

	if (status === "authenticated" && agency?.account_type === "agency")
		return <>{children}</>;

	if (status === "checking") {
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
					<CardTitle>
						{status === "anonymous" ? "Sign in required" : "Session expired"}
					</CardTitle>
				</CardHeader>
				<CardContent className="space-y-4 text-sm text-muted-foreground">
					<p>
						{status === "anonymous"
							? "Agency dashboard requires an active agency session."
							: "Your agency session is no longer valid. Sign in again."}
					</p>
					<Button
						onClick={() =>
							router.push(`/login?next=${encodeURIComponent(pathname)}`)
						}
					>
						Go to login
					</Button>
				</CardContent>
			</Card>
		</main>
	);
}
