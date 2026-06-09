import { Badge } from '@/components/ui/badge';
import { DetectionsClient } from './detections-client';

export default function DetectionsPage() {
  return (
    <div className="space-y-6">
      <section className="space-y-2">
        <Badge variant="secondary">Detections</Badge>
        <h1 className="text-3xl font-semibold tracking-tight">Review items</h1>
        <p className="max-w-2xl text-sm text-muted-foreground">Table-first queue for early detection items, evidence state, and handling advice.</p>
      </section>

      <DetectionsClient />
    </div>
  );
}
