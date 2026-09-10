"use client";

import { getMe } from "@/src/shared/api/client";
import {
	clearAgencyToken,
	getAgencyToken,
	sessionEventName,
	setAgencyToken,
} from "@/src/shared/auth/session";
import type { AgencyMe } from "@/src/shared/types/api";
import { isAgencyRole } from "@/src/shared/auth/route-permissions";
import {
	createContext,
	useCallback,
	useContext,
	useEffect,
	useMemo,
	useState,
} from "react";

type AuthState = "checking" | "authenticated" | "anonymous" | "invalid";

type AgencySession = {
	status: AuthState;
	token: string;
	agency: AgencyMe | null;
	agencyUserId: string;
	signIn: (token: string) => Promise<AgencyMe>;
	signOut: () => void;
	refresh: () => Promise<void>;
};

const AgencySessionContext = createContext<AgencySession | null>(null);

function agencyUserIdFrom(me: AgencyMe | null) {
	return me?.id ?? "";
}

function hasDashboardPermission(me: AgencyMe | null) {
	return me?.account_type === "agency" && isAgencyRole(me.role);
}

export function AgencySessionProvider({
	children,
}: {
	children: React.ReactNode;
}) {
	const [status, setStatus] = useState<AuthState>("checking");
	const [token, setToken] = useState("");
	const [agency, setAgency] = useState<AgencyMe | null>(null);

	const refresh = useCallback(async () => {
		const storedToken = getAgencyToken();
		if (!storedToken) {
			setToken("");
			setAgency(null);
			setStatus("anonymous");
			return;
		}
		setStatus("checking");
		try {
			const me = await getMe(storedToken);
			if (!hasDashboardPermission(me)) {
				clearAgencyToken();
				setToken("");
				setAgency(null);
				setStatus("invalid");
				return;
			}
			setToken(storedToken);
			setAgency(me);
			setStatus("authenticated");
		} catch {
			clearAgencyToken();
			setToken("");
			setAgency(null);
			setStatus("invalid");
		}
	}, []);

	const signIn = useCallback(async (nextToken: string) => {
		try {
			const me = await getMe(nextToken);
			if (!hasDashboardPermission(me))
				throw new Error("Account has no dashboard permission");
			setAgencyToken(nextToken);
			setToken(nextToken);
			setAgency(me);
			setStatus("authenticated");
			return me;
		} catch (error) {
			clearAgencyToken();
			setToken("");
			setAgency(null);
			setStatus("invalid");
			throw error;
		}
	}, []);

	const signOut = useCallback(() => {
		clearAgencyToken();
		setToken("");
		setAgency(null);
		setStatus("anonymous");
	}, []);

	useEffect(() => {
		refresh();
		window.addEventListener(sessionEventName, refresh);
		return () => window.removeEventListener(sessionEventName, refresh);
	}, [refresh]);

	const value = useMemo<AgencySession>(
		() => ({
			status,
			token,
			agency,
			agencyUserId: agencyUserIdFrom(agency),
			signIn,
			signOut,
			refresh,
		}),
		[agency, refresh, signIn, signOut, status, token],
	);

	return (
		<AgencySessionContext.Provider value={value}>
			{children}
		</AgencySessionContext.Provider>
	);
}

export function useAgencySession() {
	const session = useContext(AgencySessionContext);
	if (!session)
		throw new Error("useAgencySession must be used inside AgencySessionProvider");
	return session;
}
