import { Badge } from '@/components/ui/badge';
import { RiskSignalsClient } from './risk-signals-client';

export default function RiskSignalsPage() {
  return (
    <div className="space-y-6">
      <section className="space-y-2">
        <Badge variant="secondary">Risk signals</Badge>
        <h1 className="text-3xl font-semibold tracking-tight">District signals</h1>
        <p className="max-w-2xl text-sm text-muted-foreground">Possible increased risk only, with signal count and follow-up priority.</p>
      </section>

      <RiskSignalsClient />
    </div>
  );
}
