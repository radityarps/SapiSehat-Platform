import { FollowUpsClient } from "./follow-ups-client";

export default function FollowUpsPage() {
	return (
		<div className="space-y-6">
			<section className="space-y-2">
				<h1 className="text-3xl font-semibold tracking-tight">Work queue</h1>
				<p className="max-w-2xl text-sm text-muted-foreground">
					Record open, in-progress, or resolved follow-up status from review
					items.
				</p>
			</section>

			<FollowUpsClient />
		</div>
	);
}
