"use client";

import type { AgencyRole } from "@/src/shared/types/api";
import { useAgencySession } from "@/src/features/auth/session-context";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

const routePermissions: Record<string, AgencyRole[]> = {
	"/agency/overview": [
		"admin",
		"province_officer",
		"district_officer",
		"village_officer",
		"viewer",
	],
	"/agency/registry": ["admin", "province_officer", "district_officer"],
	"/agency/detections": ["admin", "province_officer", "district_officer"],
	"/agency/risk-signals": ["admin", "province_officer", "district_officer"],
	"/agency/follow-ups": ["admin", "province_officer", "district_officer"],
	"/agency/audit-logs": ["admin"],
	"/agency/users": ["admin"],
	"/agency/settings": [
		"admin",
		"province_officer",
		"district_officer",
		"village_officer",
		"viewer",
	],
};

export function useRouteGuard(pathname: string) {
	const { agency, status } = useAgencySession();
	const router = useRouter();

	useEffect(() => {
		if (status !== "authenticated") return;
		const role = agency?.role;
		if (!role) return;

		const allowedRoles = routePermissions[pathname];
		if (allowedRoles && !allowedRoles.includes(role)) {
			router.replace("/agency/overview");
		}
	}, [agency?.role, pathname, router, status]);
}
