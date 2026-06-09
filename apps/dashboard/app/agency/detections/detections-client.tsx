"use client";

import { DataTable } from '@/components/data-table';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { getDetectionMonitoring } from '@/lib/api';
import { getAgencyToken } from '@/lib/auth';
import type { DetectionMonitoringItem } from '@/lib/types';
import { useQuery } from '@tanstack/react-query';
import type { ColumnDef } from '@tanstack/react-table';

const columns: ColumnDef<DetectionMonitoringItem>[] = [
  { accessorKey: 'disease_class', header: 'Class' },
  { accessorKey: 'confidence', header: 'Confidence', cell: ({ row }) => `${Math.round(row.original.confidence * 100)}%` },
  { accessorKey: 'confidence_level', header: 'Level', cell: ({ row }) => row.original.confidence_level ?? 'unknown' },
  { accessorKey: 'reliability', header: 'Reliability', cell: ({ row }) => row.original.reliability ?? 'needs review' },
  { accessorKey: 'conflict_status', header: 'Evidence state', cell: ({ row }) => row.original.conflict_status ?? 'image only' },
  { accessorKey: 'cattle_id', header: 'Cattle ID', cell: ({ row }) => <span className="font-mono text-xs">{row.original.cattle_id ?? 'not linked'}</span> }
];

export function DetectionsClient() {
  const token = getAgencyToken();
  const query = useQuery({ queryKey: ['detections'], queryFn: () => getDetectionMonitoring(token), enabled: Boolean(token) });

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
        Sorted table for risk review, not diagnosis.
      </div>
      <DataTable columns={columns} data={query.data?.detections ?? []} emptyLabel="No review items are available for this agency scope yet." />
    </div>
  );
}
