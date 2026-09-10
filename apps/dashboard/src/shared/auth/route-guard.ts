"use client";

import { useAgencySession } from "@/src/features/auth/session-context";
import { hasRoutePermission } from "@/src/shared/auth/route-permissions";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export function useRouteGuard(pathname: string) {
	const { agency, status } = useAgencySession();
	const router = useRouter();
	const hasPermission =
		status === "authenticated" && hasRoutePermission(pathname, agency?.role);

	useEffect(() => {
		if (status === "authenticated" && !hasPermission) {
			router.replace("/agency/overview");
		}
	}, [hasPermission, router, status]);

	return hasPermission;
}
