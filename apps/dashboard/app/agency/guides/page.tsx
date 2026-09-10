import { GuideCmsClient } from "@/src/features/agency/guides/guide-cms-client";

export default function GuideCmsPage() {
	return (
		<div className="space-y-6">
			<section>
				<h1 className="text-3xl font-semibold tracking-tight">Guide Article CMS</h1>
				<p className="text-sm text-muted-foreground">
					Kelola Panduan yang tersedia untuk peternak secara online dan offline.
				</p>
			</section>
			<GuideCmsClient />
		</div>
	);
}
