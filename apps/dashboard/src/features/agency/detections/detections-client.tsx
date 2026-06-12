"use client";

import { DataTable } from '@/src/shared/ui/data-table';
import { Badge } from '@/src/shared/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/src/shared/ui/card';
import { Skeleton } from '@/src/shared/ui/skeleton';
import { getDetectionMonitoring } from '@/src/shared/api/client';
import { useAgencySession } from '@/src/features/auth/session-context';
import { EvidenceDetail, EvidenceLabel } from '@/src/features/agency/detections/evidence-label';
import type { DetectionMonitoringItem } from '@/src/shared/types/api';
import { useQuery } from '@tanstack/react-query';
import type { ColumnDef } from '@tanstack/react-table';

const columns: ColumnDef<DetectionMonitoringItem>[] = [
  { accessorKey: 'disease_class', header: 'Class' },
  { accessorKey: 'confidence', header: 'Confidence', cell: ({ row }) => `${Math.round(row.original.confidence * 100)}%` },
  { accessorKey: 'confidence_level', header: 'Level', cell: ({ row }) => row.original.confidence_level ?? 'unknown' },
  { accessorKey: 'reliability', header: 'Reliability', cell: ({ row }) => row.original.reliability ?? 'needs review' },
  { id: 'evidence_label', header: 'Evidence', cell: ({ row }) => <div className="space-y-1"><EvidenceLabel item={row.original} /><EvidenceDetail item={row.original} /></div> },
  { accessorKey: 'conflict_status', header: 'Review state', cell: ({ row }) => row.original.conflict_status ?? 'image only' },
  { accessorKey: 'cattle_id', header: 'Cattle ID', cell: ({ row }) => <span className="font-mono text-xs">{row.original.cattle_id ?? 'not linked'}</span> }
];

export function DetectionsClient() {
  const { token, agencyUserId } = useAgencySession();
  const query = useQuery({ queryKey: ['detections'], queryFn: () => getDetectionMonitoring(token, agencyUserId), enabled: Boolean(token && agencyUserId) });

  if (query.isLoading) {
    return <Card><CardContent className="space-y-3 pt-6"><Skeleton className="h-10 w-full" /><Skeleton className="h-10 w-full" /><Skeleton className="h-10 w-3/4" /></CardContent></Card>;
  }

  if (query.isError) {
    return <Card><CardHeader><CardTitle>Could not load review items</CardTitle></CardHeader><CardContent className="text-sm text-destructive">{query.error.message}</CardContent></Card>;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Badge variant="secondary">{query.data?.detections.length ?? 0} items</Badge>
        {query.data?.safeLanguage?.description ?? 'Sorted table for risk review, not diagnosis.'}
      </div>
      {query.data?.safeLanguage?.forbidden_terms ? <p className="text-xs text-muted-foreground">Forbidden wording: {query.data.safeLanguage.forbidden_terms}</p> : null}
      <DataTable columns={columns} data={query.data?.detections ?? []} emptyLabel="No review items are available for this agency scope yet." />
    </div>
  );
}
