import { AppShell } from "@/src/features/agency/layout/app-shell";
import { SessionGuard } from "@/src/features/auth/session-guard";
import { TooltipProvider } from "@/src/shared/ui/tooltip";

export default function AgencyLayout({
	children,
}: {
	children: React.ReactNode;
}) {
	return (
		<SessionGuard>
			<TooltipProvider>
				<AppShell>{children}</AppShell>
			</TooltipProvider>
		</SessionGuard>
	);
}
