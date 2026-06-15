import "./globals.css";
import { ReactQueryProvider } from "./providers";
import { Toaster } from "@/src/shared/ui/sonner";

export const metadata = {
	title: "SapiSehat Agency Dashboard",
	description:
		"Agency triage dashboard for disease-risk monitoring and follow-up.",
};

export default function RootLayout({
	children,
}: {
	children: React.ReactNode;
}) {
	return (
		<html lang="en">
			<body>
				<ReactQueryProvider>{children}</ReactQueryProvider>
				<Toaster richColors closeButton position="top-right" />
			</body>
		</html>
	);
}
