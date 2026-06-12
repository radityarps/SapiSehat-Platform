"use client";

import { DataTable } from '@/src/shared/ui/data-table';
import { Badge } from '@/src/shared/ui/badge';
import { Button } from '@/src/shared/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/src/shared/ui/card';
import { Input } from '@/src/shared/ui/input';
import { Label } from '@/src/shared/ui/label';
import { Skeleton } from '@/src/shared/ui/skeleton';
import { Textarea } from '@/src/shared/ui/textarea';
import { createAgencyFollowUp, getAgencyFollowUps } from '@/src/shared/api/client';
import { useAgencySession } from '@/src/features/auth/session-context';
import type { AgencyFollowUpItem } from '@/src/shared/types/api';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type { ColumnDef } from '@tanstack/react-table';
import { useState } from 'react';

const columns: ColumnDef<AgencyFollowUpItem>[] = [
  { accessorKey: 'status', header: 'Status', cell: ({ row }) => <Badge variant="secondary">{row.original.status}</Badge> },
  { accessorKey: 'farmer_id', header: 'Farmer ID', cell: ({ row }) => <span className="font-mono text-xs">{row.original.farmer_id}</span> },
  { accessorKey: 'cattle_id', header: 'Cattle ID', cell: ({ row }) => <span className="font-mono text-xs">{row.original.cattle_id ?? 'not linked'}</span> },
  { accessorKey: 'public_message', header: 'Farmer message' },
  { accessorKey: 'internal_notes', header: 'Internal notes' }
];

export function FollowUpsClient() {
  const { token, agencyUserId } = useAgencySession();
  const queryClient = useQueryClient();
  const [farmerId, setFarmerId] = useState('');
  const [cattleId, setCattleId] = useState('');
  const [status, setStatus] = useState('needs_follow_up');
  const [publicMessage, setPublicMessage] = useState('Petugas akan meninjau sinyal risiko ini. Ini bukan diagnosis.');
  const [internalNotes, setInternalNotes] = useState('');
  const query = useQuery({ queryKey: ['follow-ups', agencyUserId], queryFn: () => getAgencyFollowUps(token, agencyUserId), enabled: Boolean(token && agencyUserId) });
  const mutation = useMutation({
    mutationFn: () => createAgencyFollowUp(token, agencyUserId, {
      farmer_id: farmerId,
      cattle_id: cattleId || undefined,
      status,
      public_message: publicMessage,
      internal_notes: internalNotes
    }),
    onSuccess: async () => {
      setFarmerId('');
      setCattleId('');
      setInternalNotes('');
      await queryClient.invalidateQueries({ queryKey: ['follow-ups'] });
    }
  });

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader><CardTitle>Record follow-up</CardTitle></CardHeader>
        <CardContent>
          <form className="grid gap-4 lg:grid-cols-2" onSubmit={(event) => { event.preventDefault(); mutation.mutate(); }}>
            <div className="space-y-2"><Label htmlFor="farmer-id">Farmer ID</Label><Input id="farmer-id" value={farmerId} onChange={(e) => setFarmerId(e.target.value)} required /></div>
            <div className="space-y-2"><Label htmlFor="cattle-id">Cattle ID optional</Label><Input id="cattle-id" value={cattleId} onChange={(e) => setCattleId(e.target.value)} /></div>
            <div className="space-y-2"><Label htmlFor="status">Status</Label><Input id="status" value={status} onChange={(e) => setStatus(e.target.value)} required /></div>
            <div className="space-y-2"><Label htmlFor="public-message">Farmer-safe message</Label><Input id="public-message" value={publicMessage} onChange={(e) => setPublicMessage(e.target.value)} required /></div>
            <div className="space-y-2 lg:col-span-2"><Label htmlFor="internal-notes">Internal notes</Label><Textarea id="internal-notes" value={internalNotes} onChange={(e) => setInternalNotes(e.target.value)} placeholder="Agency-only note; avoid diagnosis or outbreak confirmation." /></div>
            {mutation.isError ? <p className="text-sm text-destructive lg:col-span-2">{mutation.error.message}</p> : null}
            {mutation.isSuccess ? <p className="text-sm text-emerald-700 lg:col-span-2">Follow-up saved.</p> : null}
            <div className="lg:col-span-2"><Button type="submit" disabled={mutation.isPending}>{mutation.isPending ? 'Saving...' : 'Save follow-up'}</Button></div>
          </form>
        </CardContent>
      </Card>

      {query.isLoading ? <Card><CardContent className="space-y-3 pt-6"><Skeleton className="h-10 w-full" /><Skeleton className="h-10 w-full" /></CardContent></Card> : null}
      {query.isError ? <Card><CardHeader><CardTitle>Could not load follow-ups</CardTitle></CardHeader><CardContent className="text-sm text-destructive">{query.error.message}</CardContent></Card> : null}
      {query.isSuccess ? <DataTable columns={columns} data={query.data.followUps} emptyLabel="No agency follow-ups have been created yet." /> : null}
    </div>
  );
}
