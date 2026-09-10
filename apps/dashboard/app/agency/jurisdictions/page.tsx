import { JurisdictionsClient } from "./jurisdictions-client";

export default function JurisdictionsPage() {
  return (
    <div className="space-y-6">
      <section className="space-y-2">
        <h1 className="text-3xl font-semibold tracking-tight">
          Jurisdiction Management
        </h1>
        <p className="max-w-2xl text-sm text-muted-foreground">
          Manage the administrative areas used for agency access and data scope.
        </p>
      </section>
      <JurisdictionsClient />
    </div>
  );
}
