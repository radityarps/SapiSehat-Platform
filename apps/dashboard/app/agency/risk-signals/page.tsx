import { RiskSignalsClient } from "./risk-signals-client";

export default function RiskSignalsPage() {
	return (
		<div className="space-y-6">
			<section className="space-y-2">
				<h1 className="text-3xl font-semibold tracking-tight">Risk signals</h1>
				<p className="max-w-2xl text-sm text-muted-foreground">
					Possible increased risk only, with signal count and follow-up priority. Not confirmed outbreak and not veterinary diagnosis.
				</p>
			</section>

			<RiskSignalsClient />
		</div>
	);
}
