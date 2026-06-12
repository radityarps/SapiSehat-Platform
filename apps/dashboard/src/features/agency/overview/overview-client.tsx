"use client";

import { Card, CardContent, CardHeader, CardTitle } from '@/src/shared/ui/card';
import { Skeleton } from '@/src/shared/ui/skeleton';
import { Button } from '@/src/shared/ui/button';
import { getAgencyFollowUps, getAgencyRegistry, getAuditLogs, getDetectionMonitoring, getRiskSignals } from '@/src/shared/api/client';
import { useAgencySession } from '@/src/features/auth/session-context';
import { useQuery } from '@tanstack/react-query';
import { Activity, AlertTriangle, ArrowRight, ClipboardList, ShieldAlert, TrendingUp, Users } from 'lucide-react';
import Link from 'next/link';

export function OverviewClient() {
  const { token, agencyUserId, agency } = useAgencySession();
  const enabled = Boolean(token && agencyUserId);

  const registry = useQuery({ queryKey: ['overview-registry'], queryFn: () => getAgencyRegistry(token, agencyUserId), enabled });
  const detections = useQuery({ queryKey: ['overview-detections'], queryFn: () => getDetectionMonitoring(token, agencyUserId), enabled });
  const riskSignals = useQuery({ queryKey: ['overview-risk-signals'], queryFn: () => getRiskSignals(token, agencyUserId), enabled });
  const auditLogs = useQuery({ queryKey: ['overview-audit-logs'], queryFn: () => getAuditLogs(token, agencyUserId), enabled });
  const followUps = useQuery({ queryKey: ['overview-follow-ups'], queryFn: () => getAgencyFollowUps(token, agencyUserId), enabled });

  const anyLoading = registry.isLoading || detections.isLoading || riskSignals.isLoading || auditLogs.isLoading || followUps.isLoading;

  const totalDetections = detections.data?.detections.length ?? 0;
  const totalSignals = riskSignals.data?.signals.length ?? 0;
  const totalFarmers = registry.data?.farmers.length ?? 0;
  const totalCattle = registry.data?.cattle.length ?? 0;
  const totalFollowUps = followUps.data?.followUps.length ?? 0;
  const pendingFollowUps = followUps.data?.followUps.filter(f => f.status === 'pending') ?? [];
  const highRiskSignals = riskSignals.data?.signals.filter(s => s.risk_level === 'high') ?? [];
  const recentLogs = auditLogs.data?.logs.slice(0, 5) ?? [];

  // Disease class breakdown
  const diseaseBreakdown: Record<string, number> = {};
  detections.data?.detections.forEach(d => {
    diseaseBreakdown[d.disease_class] = (diseaseBreakdown[d.disease_class] ?? 0) + 1;
  });

  // Jurisdiction signal breakdown
  const jurisdictionBreakdown: Record<string, number> = {};
  riskSignals.data?.signals.forEach(s => {
    jurisdictionBreakdown[s.jurisdiction_id] = (jurisdictionBreakdown[s.jurisdiction_id] ?? 0) + s.signal_count;
  });

  if (anyLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 8 }).map((_, i) => (
          <Skeleton key={i} className="h-32 w-full rounded-lg" />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Jurisdiction scope banner */}
      <div className="flex items-center gap-2 rounded-lg border bg-muted/30 px-4 py-2 text-sm text-muted-foreground">
        <ShieldAlert className="h-4 w-4" />
        <span>Viewing data scoped to <strong className="text-foreground">{agency?.jurisdiction_id ?? 'all'}</strong> jurisdiction</span>
        <span className="ml-auto text-xs">{agency?.role ?? 'officer'}</span>
      </div>

      {/* Bento grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">

        {/* Metric: Detections — spans 1 */}
        <Card className="relative overflow-hidden">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Review Items</CardTitle>
            <ClipboardList className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{totalDetections}</div>
            <p className="text-xs text-muted-foreground mt-1">Detection submissions in scope</p>
            <Link href="/agency/detections" className="absolute inset-0" aria-label="Go to detections" />
          </CardContent>
        </Card>

        {/* Metric: Risk Signals */}
        <Card className="relative overflow-hidden">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Risk Signals</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{totalSignals}</div>
            <div className="flex items-center gap-1 mt-1">
              {highRiskSignals.length > 0 && (
                <span className="inline-flex items-center rounded-full bg-destructive/10 px-2 py-0.5 text-xs font-medium text-destructive">
                  {highRiskSignals.length} high
                </span>
              )}
              <span className="text-xs text-muted-foreground">prioritization signals</span>
            </div>
            <Link href="/agency/risk-signals" className="absolute inset-0" aria-label="Go to risk signals" />
          </CardContent>
        </Card>

        {/* Metric: Follow-ups */}
        <Card className="relative overflow-hidden">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Follow-ups</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{totalFollowUps}</div>
            <div className="flex items-center gap-1 mt-1">
              {pendingFollowUps.length > 0 && (
                <span className="inline-flex items-center rounded-full bg-amber-500/10 px-2 py-0.5 text-xs font-medium text-amber-700">
                  {pendingFollowUps.length} pending
                </span>
              )}
              <span className="text-xs text-muted-foreground">work items</span>
            </div>
            <Link href="/agency/follow-ups" className="absolute inset-0" aria-label="Go to follow-ups" />
          </CardContent>
        </Card>

        {/* Metric: Registry */}
        <Card className="relative overflow-hidden">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Registry</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{totalFarmers}</div>
            <p className="text-xs text-muted-foreground mt-1">{totalCattle} cattle registered</p>
            <Link href="/agency/registry" className="absolute inset-0" aria-label="Go to registry" />
          </CardContent>
        </Card>

        {/* Disease breakdown — spans 2 cols */}
        <Card className="md:col-span-2">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Detection by Disease Class</CardTitle>
          </CardHeader>
          <CardContent>
            {Object.keys(diseaseBreakdown).length === 0 ? (
              <p className="text-sm text-muted-foreground">No detections yet.</p>
            ) : (
              <div className="space-y-2">
                {Object.entries(diseaseBreakdown)
                  .sort(([, a], [, b]) => b - a)
                  .map(([disease, count]) => {
                    const pct = totalDetections > 0 ? (count / totalDetections) * 100 : 0;
                    return (
                      <div key={disease} className="space-y-1">
                        <div className="flex items-center justify-between text-sm">
                          <span className="capitalize">{disease.replace(/_/g, ' ')}</span>
                          <span className="text-muted-foreground">{count}</span>
                        </div>
                        <div className="h-2 w-full rounded-full bg-muted">
                          <div
                            className="h-2 rounded-full bg-primary transition-all"
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Jurisdiction signal density — spans 2 cols */}
        <Card className="md:col-span-2">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Signal Density by Jurisdiction</CardTitle>
          </CardHeader>
          <CardContent>
            {Object.keys(jurisdictionBreakdown).length === 0 ? (
              <p className="text-sm text-muted-foreground">No signals yet.</p>
            ) : (
              <div className="space-y-2">
                {Object.entries(jurisdictionBreakdown)
                  .sort(([, a], [, b]) => b - a)
                  .map(([jurisdiction, count]) => {
                    const maxCount = Math.max(...Object.values(jurisdictionBreakdown));
                    const pct = maxCount > 0 ? (count / maxCount) * 100 : 0;
                    return (
                      <div key={jurisdiction} className="space-y-1">
                        <div className="flex items-center justify-between text-sm">
                          <span>{jurisdiction}</span>
                          <span className="text-muted-foreground">{count} signals</span>
                        </div>
                        <div className="h-2 w-full rounded-full bg-muted">
                          <div
                            className="h-2 rounded-full bg-amber-500 transition-all"
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Pending work queue — spans 2 cols */}
        <Card className="md:col-span-2 lg:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <CardTitle className="text-sm font-medium">Pending Work</CardTitle>
            <Button variant="ghost" size="sm" asChild>
              <Link href="/agency/follow-ups" className="gap-1">
                View all <ArrowRight className="h-3 w-3" />
              </Link>
            </Button>
          </CardHeader>
          <CardContent>
            {pendingFollowUps.length === 0 ? (
              <p className="text-sm text-muted-foreground">No pending follow-ups. All clear.</p>
            ) : (
              <div className="space-y-2">
                {pendingFollowUps.slice(0, 5).map((item) => (
                  <div key={item.id} className="flex items-center justify-between rounded-md border px-3 py-2">
                    <div className="space-y-0.5">
                      <p className="text-sm font-medium">Farmer: {item.farmer_id}</p>
                      <p className="text-xs text-muted-foreground line-clamp-1">{item.public_message}</p>
                    </div>
                    <span className="inline-flex items-center rounded-full bg-amber-500/10 px-2 py-0.5 text-xs font-medium text-amber-700">
                      {item.status}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recent activity — spans 2 cols */}
        <Card className="md:col-span-2 lg:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <CardTitle className="text-sm font-medium">Recent Activity</CardTitle>
            <Button variant="ghost" size="sm" asChild>
              <Link href="/agency/audit-logs" className="gap-1">
                View all <ArrowRight className="h-3 w-3" />
              </Link>
            </Button>
          </CardHeader>
          <CardContent>
            {recentLogs.length === 0 ? (
              <p className="text-sm text-muted-foreground">No recent activity.</p>
            ) : (
              <div className="space-y-2">
                {recentLogs.map((log) => (
                  <div key={log.id} className="flex items-center gap-3 rounded-md border px-3 py-2">
                    <Activity className="h-4 w-4 shrink-0 text-muted-foreground" />
                    <div className="flex-1 space-y-0.5 overflow-hidden">
                      <p className="truncate text-sm">
                        <span className="font-medium">{log.actor_id}</span>
                        {' '}{log.action}{' '}
                        <span className="text-muted-foreground">{log.resource_type}/{log.resource_id}</span>
                      </p>
                      <p className="text-xs text-muted-foreground">{new Date(log.created_at).toLocaleString()}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

      </div>
    </div>
  );
}
