import { Badge } from '@/src/shared/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/src/shared/ui/card';
import { RegistryClient } from './registry-client';

export default function RegistryPage() {
  return (
    <div className="space-y-6">
      <section className="space-y-2">
        <Badge variant="secondary">Registry</Badge>
        <h1 className="text-3xl font-semibold tracking-tight">Agency scope</h1>
        <p className="max-w-2xl text-sm text-muted-foreground">Farmer and cattle registry rows will land here once registry tracer is wired into the dashboard.</p>
      </section>

      <Card>
        <CardHeader>
          <CardTitle>Live registry</CardTitle>
        </CardHeader>
        <CardContent>
          <RegistryClient />
        </CardContent>
      </Card>
    </div>
  );
}
