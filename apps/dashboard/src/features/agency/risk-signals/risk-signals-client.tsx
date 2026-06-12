"use client";

import { DataTable } from '@/src/shared/ui/data-table';
import { Badge } from '@/src/shared/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/src/shared/ui/card';
import { RiskSignalMap } from '@/src/features/agency/risk-signals/risk-map';
import { Skeleton } from '@/src/shared/ui/skeleton';
import { getRiskSignals } from '@/src/shared/api/client';
import { useAgencySession } from '@/src/features/auth/session-context';
import type { RiskSignalItem } from '@/src/shared/types/api';
import { useQuery } from '@tanstack/react-query';
import type { ColumnDef } from '@tanstack/react-table';

const columns: ColumnDef<RiskSignalItem>[] = [
  { accessorKey: 'jurisdiction_id', header: 'District' },
  { accessorKey: 'disease_class', header: 'Class' },
  { accessorKey: 'signal_count', header: 'Signals' },
  { accessorKey: 'risk_level', header: 'Risk level', cell: ({ row }) => <Badge variant="warning">{row.original.risk_level}</Badge> },
  { accessorKey: 'priority', header: 'Priority' },
  { accessorKey: 'source_result_ids', header: 'Sources', cell: ({ row }) => row.original.source_result_ids.length }
];

export function RiskSignalsClient() {
  const { token, agencyUserId } = useAgencySession();
  const query = useQuery({ queryKey: ['risk-signals'], queryFn: () => getRiskSignals(token, agencyUserId), enabled: Boolean(token && agencyUserId) });

  if (query.isLoading) {
    return <Card><CardContent className="space-y-3 pt-6"><Skeleton className="h-10 w-full" /><Skeleton className="h-10 w-full" /></CardContent></Card>;
  }

  if (query.isError) {
    return <Card><CardHeader><CardTitle>Could not load risk signals</CardTitle></CardHeader><CardContent className="text-sm text-destructive">{query.error.message}</CardContent></Card>;
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader><CardTitle>Jurisdiction signal map</CardTitle></CardHeader>
        <CardContent><RiskSignalMap signals={query.data?.signals ?? []} /></CardContent>
      </Card>
      <DataTable columns={columns} data={query.data?.signals ?? []} emptyLabel="No district-level risk signals are active for this agency scope." />
    </div>
  );
}
