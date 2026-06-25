import { RegistryClient } from "@/src/features/agency/registry/registry-client";

export default function RegistryPage() {
	return (
		<div className="space-y-6">
			<section className="space-y-2">
				<h1 className="text-3xl font-semibold tracking-tight">Registry</h1>
				<p className="max-w-2xl text-sm text-muted-foreground">
					Farmer records scoped to your jurisdiction. Use search and filters to
					find specific entries.
				</p>
			</section>

			<RegistryClient />
		</div>
	);
}
