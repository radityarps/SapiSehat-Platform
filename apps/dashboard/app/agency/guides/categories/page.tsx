import { GuideCategoriesClient } from "@/src/features/agency/guides/guide-categories-client";

export default function GuideCategoriesPage() {
	return (
		<div className="space-y-6">
			<section className="space-y-2">
				<h1 className="text-3xl font-semibold tracking-tight">
					Guide Categories
				</h1>
				<p className="max-w-2xl text-sm text-muted-foreground">
					Manage category taxonomies and multilingual labels for farmer guide articles.
				</p>
			</section>

			<GuideCategoriesClient />
		</div>
	);
}
