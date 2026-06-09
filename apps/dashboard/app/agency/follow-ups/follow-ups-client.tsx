"use client";

import { DataTable } from '@/components/data-table';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { getAgencyFollowUps } from '@/lib/api';
import { getAgencyToken } from '@/lib/auth';
import type { AgencyFollowUpItem } from '@/lib/types';
import { useQuery } from '@tanstack/react-query';
import type { ColumnDef } from '@tanstack/react-table';

const columns: ColumnDef<AgencyFollowUpItem>[] = [
  { accessorKey: 'status', header: 'Status', cell: ({ row }) => <Badge variant="secondary">{row.original.status}</Badge> },
  { accessorKey: 'farmer_id', header: 'Farmer ID', cell: ({ row }) => <span className="font-mono text-xs">{row.original.farmer_id}</span> },
  { accessorKey: 'cattle_id', header: 'Cattle ID', cell: ({ row }) => <span className="font-mono text-xs">{row.original.cattle_id ?? 'not linked'}</span> },
  { accessorKey: 'public_message', header: 'Farmer message' },
  { accessorKey: 'internal_notes', header: 'Internal notes' }
];

export function FollowUpsClient() {
  const token = getAgencyToken();
  const query = useQuery({ queryKey: ['follow-ups'], queryFn: () => getAgencyFollowUps(token), enabled: Boolean(token) });

  if (query.isLoading) {
    return <Card><CardContent className="space-y-3 pt-6"><Skeleton className="h-10 w-full" /><Skeleton className="h-10 w-full" /></CardContent></Card>;
  }

  if (query.isError) {
    return <Card><CardHeader><CardTitle>Could not load follow-ups</CardTitle></CardHeader><CardContent className="text-sm text-destructive">{query.error.message}</CardContent></Card>;
  }

  return <DataTable columns={columns} data={query.data?.followUps ?? []} emptyLabel="No agency follow-ups have been created yet." />;
}
