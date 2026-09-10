import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function proxy(request: NextRequest) {
	const pathname = request.nextUrl.pathname;
	const isLogin = pathname === "/login";
	const isDashboard = pathname === "/agency" || pathname.startsWith("/agency/");
	const token = request.cookies.get("sapisehat_agency_token")?.value;

	if (isLogin && token) {
		const url = request.nextUrl.clone();
		url.pathname = "/agency/overview";
		url.search = "";
		return NextResponse.redirect(url);
	}

	if (isDashboard && !token) {
		const url = request.nextUrl.clone();
		url.pathname = "/login";
		url.search = "";
		url.searchParams.set("next", pathname);
		return NextResponse.redirect(url);
	}

	return NextResponse.next();
}

export const config = {
	matcher: ["/login", "/agency", "/agency/:path*"],
};
