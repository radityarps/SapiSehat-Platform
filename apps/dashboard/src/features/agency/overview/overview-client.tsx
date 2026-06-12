"use client";

import { Badge } from '@/src/shared/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/src/shared/ui/card';
import { Skeleton } from '@/src/shared/ui/skeleton';
import { getAgencyRegistry, getAuditLogs, getDetectionMonitoring, getRiskSignals } from '@/src/shared/api/client';
import { useAgencySession } from '@/src/features/auth/session-context';
import { useQuery } from '@tanstack/react-query';

function CountCard({ label, value, note, loading }: { label: string; value: string; note: string; loading?: boolean }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{label}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-1">
        {loading ? <Skeleton className="h-8 w-24" /> : <div className="text-2xl font-semibold tracking-tight">{value}</div>}
        <p className="text-xs text-muted-foreground">{note}</p>
      </CardContent>
    </Card>
  );
}

export function OverviewClient() {
  const { token, agencyUserId } = useAgencySession();
  const enabled = Boolean(token && agencyUserId);
  const registry = useQuery({ queryKey: ['overview-registry'], queryFn: () => getAgencyRegistry(token, agencyUserId), enabled });
  const detections = useQuery({ queryKey: ['overview-detections'], queryFn: () => getDetectionMonitoring(token, agencyUserId), enabled });
  const riskSignals = useQuery({ queryKey: ['overview-risk-signals'], queryFn: () => getRiskSignals(token, agencyUserId), enabled });
  const auditLogs = useQuery({ queryKey: ['overview-audit-logs'], queryFn: () => getAuditLogs(token, agencyUserId), enabled });

  const anyLoading = registry.isLoading || detections.isLoading || riskSignals.isLoading || auditLogs.isLoading;
  const errors = [registry.error, detections.error, riskSignals.error, auditLogs.error].filter(Boolean);

  return (
    <div className="space-y-4">
      {errors.length ? (
        <Card className="border-amber-200 bg-amber-50 text-amber-950">
          <CardContent className="pt-6 text-sm">
            Some live dashboard data could not load. Check backend and agency scope headers.
          </CardContent>
        </Card>
      ) : null}

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <CountCard label="Review items" value={`${detections.data?.detections.length ?? 0}`} note="Agency-scoped detection review rows" loading={anyLoading} />
        <CountCard label="Risk signals" value={`${riskSignals.data?.signals.length ?? 0}`} note="Possible increased risk only" loading={anyLoading} />
        <CountCard label="Registry" value={`${registry.data?.farmers.length ?? 0} / ${registry.data?.cattle.length ?? 0}`} note="Farmers / cattle in scope" loading={anyLoading} />
        <CountCard label="Audit logs" value={`${auditLogs.data?.logs.length ?? 0}`} note="Recent admin-visible backend actions" loading={anyLoading} />
      </section>

      <section className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
        <Card>
          <CardHeader>
            <CardTitle>Operational posture</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm text-muted-foreground">
            <div className="flex items-center gap-2"><Badge variant="secondary">Safe language</Badge><span>Dashboard says risk signal and follow-up priority, never diagnosis.</span></div>
            <div className="flex items-center gap-2"><Badge variant="secondary">Agency scope</Badge><span>Registry and monitoring calls use district-scoped agency headers.</span></div>
            <div className="flex items-center gap-2"><Badge variant="secondary">Evidence state</Badge><span>Image/NLP breakdown and conflict state remain review aids.</span></div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Next action</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            Start from review items when detections exist. Use risk signals only for district-level prioritization.
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
