import { Badge } from '@/src/shared/ui/badge';
import { AuditLogsClient } from './audit-logs-client';

export default function AuditLogsPage() {
  return (
    <div className="space-y-6">
      <section className="space-y-2">
        <Badge variant="secondary">Audit logs</Badge>
        <h1 className="text-3xl font-semibold tracking-tight">Ops trail</h1>
        <p className="max-w-2xl text-sm text-muted-foreground">Recent backend actions for admin review and release validation.</p>
      </section>

      <AuditLogsClient />
    </div>
  );
}
