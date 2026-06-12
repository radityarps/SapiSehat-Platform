import { Badge } from '@/src/shared/ui/badge';
import { DetectionsClient } from './detections-client';

export default function DetectionsPage() {
  return (
    <div className="space-y-6">
      <section className="space-y-2">
        <Badge variant="secondary">Detections</Badge>
        <h1 className="text-3xl font-semibold tracking-tight">Review items</h1>
        <p className="max-w-2xl text-sm text-muted-foreground">Disease risk signals queue for early detection items, Risk signal review, Image/NLP breakdown, evidence state, and handling advice.</p>
      </section>

      <DetectionsClient />
    </div>
  );
}
