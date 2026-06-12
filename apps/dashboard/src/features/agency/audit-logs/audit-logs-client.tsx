"use client";

import { DataTable } from '@/src/shared/ui/data-table';
import { Card, CardContent, CardHeader, CardTitle } from '@/src/shared/ui/card';
import { Skeleton } from '@/src/shared/ui/skeleton';
import { getAuditLogs } from '@/src/shared/api/client';
import { useAgencySession } from '@/src/features/auth/session-context';
import type { AuditLogItem } from '@/src/shared/types/api';
import { useQuery } from '@tanstack/react-query';
import type { ColumnDef } from '@tanstack/react-table';

const columns: ColumnDef<AuditLogItem>[] = [
  { accessorKey: 'created_at', header: 'Time' },
  { accessorKey: 'action', header: 'Action' },
  { accessorKey: 'actor_id', header: 'Actor' },
  { accessorKey: 'resource_type', header: 'Resource type' },
  { accessorKey: 'resource_id', header: 'Resource ID', cell: ({ row }) => <span className="font-mono text-xs">{row.original.resource_id}</span> }
];

export function AuditLogsClient() {
  const { token, agencyUserId } = useAgencySession();
  const query = useQuery({ queryKey: ['audit-logs'], queryFn: () => getAuditLogs(token, agencyUserId), enabled: Boolean(token && agencyUserId) });

  if (query.isLoading) {
    return <Card><CardContent className="space-y-3 pt-6"><Skeleton className="h-10 w-full" /><Skeleton className="h-10 w-4/5" /></CardContent></Card>;
  }

  if (query.isError) {
    return <Card><CardHeader><CardTitle>Could not load audit logs</CardTitle></CardHeader><CardContent className="text-sm text-destructive">{query.error.message}</CardContent></Card>;
  }

  return <DataTable columns={columns} data={query.data?.logs ?? []} emptyLabel="No audit logs are available yet." />;
}
