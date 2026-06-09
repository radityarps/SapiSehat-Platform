"use client";

import { DataTable } from '@/components/data-table';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { getRiskSignals } from '@/lib/api';
import { getAgencyToken } from '@/lib/auth';
import type { RiskSignalItem } from '@/lib/types';
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
  const token = getAgencyToken();
  const query = useQuery({ queryKey: ['risk-signals'], queryFn: () => getRiskSignals(token), enabled: Boolean(token) });

  if (query.isLoading) {
    return <Card><CardContent className="space-y-3 pt-6"><Skeleton className="h-10 w-full" /><Skeleton className="h-10 w-full" /></CardContent></Card>;
  }

  if (query.isError) {
    return <Card><CardHeader><CardTitle>Could not load risk signals</CardTitle></CardHeader><CardContent className="text-sm text-destructive">{query.error.message}</CardContent></Card>;
  }

  return <DataTable columns={columns} data={query.data?.signals ?? []} emptyLabel="No district-level risk signals are active for this agency scope." />;
}
