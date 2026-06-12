import { Badge } from '@/src/shared/ui/badge';
import { OverviewClient } from './overview-client';

export default function OverviewPage() {
  return (
    <div className="space-y-6">
      <section className="space-y-2">
        <Badge variant="secondary">Overview</Badge>
        <h1 className="text-3xl font-semibold tracking-tight">Agency triage</h1>
        <p className="max-w-2xl text-sm text-muted-foreground">Review items, district risk signals, and follow-up work stay in one flow with safe wording and clear priorities.</p>
      </section>

      <OverviewClient />
    </div>
  );
}
