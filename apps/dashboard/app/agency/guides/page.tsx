import { GuideCmsClient } from "@/src/features/agency/guides/guide-cms-client";

export default function GuideCmsPage() {
	return (
		<div className="space-y-6">
			<section className="space-y-2">
				<h1 className="text-3xl font-semibold tracking-tight">
					Guide CMS
				</h1>
				<p className="max-w-2xl text-sm text-muted-foreground">
					Manage instructional guide articles and publish educational content for farmers.
				</p>
			</section>

			<GuideCmsClient />
		</div>
	);
}
