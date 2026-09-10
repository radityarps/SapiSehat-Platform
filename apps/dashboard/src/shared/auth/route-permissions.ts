import type { AgencyRole } from "@/src/shared/types/api";

const allAgencyRoles: AgencyRole[] = [
	"admin",
	"province_officer",
	"district_officer",
	"village_officer",
	"viewer",
];

export function isAgencyRole(value: unknown): value is AgencyRole {
	return (
		typeof value === "string" && allAgencyRoles.includes(value as AgencyRole)
	);
}

export const routePermissions: Record<string, AgencyRole[]> = {
	"/agency/overview": allAgencyRoles,
	"/agency/registry": ["admin", "province_officer", "district_officer"],
	"/agency/farmers": ["admin", "province_officer", "district_officer"],
	"/agency/detections": ["admin", "province_officer", "district_officer"],
	"/agency/risk-signals": ["admin", "province_officer", "district_officer"],
	"/agency/follow-ups": ["admin", "province_officer", "district_officer"],
	"/agency/guides": ["admin"],
	"/agency/audit-logs": ["admin"],
	"/agency/users": ["admin"],
	"/agency/jurisdictions": ["admin"],
	"/agency/settings": allAgencyRoles,
};

export function hasRoutePermission(
	pathname: string,
	role: AgencyRole | undefined,
) {
	if (!role || !isAgencyRole(role)) return false;

	const route = Object.keys(routePermissions).find(
		(candidate) => pathname === candidate || pathname.startsWith(`${candidate}/`),
	);
	return route ? routePermissions[route].includes(role) : false;
}
