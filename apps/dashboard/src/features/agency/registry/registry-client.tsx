"use client";

import { DataTable } from '@/src/shared/ui/data-table';
import { Badge } from '@/src/shared/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/src/shared/ui/card';
import { Input } from '@/src/shared/ui/input';
import { Skeleton } from '@/src/shared/ui/skeleton';
import { getAgencyRegistry } from '@/src/shared/api/client';
import { useAgencySession } from '@/src/features/auth/session-context';
import type { AgencyRegistryCattle, AgencyRegistryFarmer } from '@/src/shared/types/api';
import { useQuery } from '@tanstack/react-query';
import type { ColumnDef } from '@tanstack/react-table';
import { useMemo, useState } from 'react';

const farmerColumns: ColumnDef<AgencyRegistryFarmer>[] = [
  { accessorKey: 'name', header: 'Farmer' },
  { accessorKey: 'jurisdiction_id', header: 'District' },
  { accessorKey: 'consent_tier', header: 'Consent' }
];

const cattleColumns: ColumnDef<AgencyRegistryCattle>[] = [
  { accessorKey: 'tag', header: 'Tag' },
  { accessorKey: 'farmer_id', header: 'Farmer ID' },
  { accessorKey: 'jurisdiction_id', header: 'District' },
  { accessorKey: 'breed', header: 'Breed' },
  { accessorKey: 'status', header: 'Status' }
];

export function RegistryClient() {
  const { token, agencyUserId } = useAgencySession();
  const [search, setSearch] = useState('');
  const query = useQuery({ queryKey: ['registry'], queryFn: () => getAgencyRegistry(token, agencyUserId), enabled: Boolean(token && agencyUserId) });

  const farmers = useMemo(() => {
    const list = query.data?.farmers ?? [];
    if (!search) return list;
    return list.filter((item) => [item.name, item.jurisdiction_id, item.consent_tier].some((value) => value.toLowerCase().includes(search.toLowerCase())));
  }, [query.data?.farmers, search]);

  const cattle = useMemo(() => {
    const list = query.data?.cattle ?? [];
    if (!search) return list;
    return list.filter((item) => [item.tag, item.farmer_id, item.jurisdiction_id, item.breed, item.status].some((value) => value.toLowerCase().includes(search.toLowerCase())));
  }, [query.data?.cattle, search]);

  if (query.isLoading) {
    return <Card><CardContent className="space-y-3 pt-6"><Skeleton className="h-10 w-full" /><Skeleton className="h-10 w-full" /></CardContent></Card>;
  }

  if (query.isError) {
    return <Card><CardHeader><CardTitle>Could not load registry</CardTitle></CardHeader><CardContent className="text-sm text-destructive">{query.error.message}</CardContent></Card>;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <Badge variant="secondary">{query.data?.farmers.length ?? 0} farmers · {query.data?.cattle.length ?? 0} cattle</Badge>
        <Input className="sm:max-w-xs" placeholder="Search name, tag, district, consent" value={search} onChange={(e) => setSearch(e.target.value)} />
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Farmers</CardTitle>
          </CardHeader>
          <CardContent>
            <DataTable columns={farmerColumns} data={farmers} emptyLabel="No farmers in current agency scope." />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Cattle</CardTitle>
          </CardHeader>
          <CardContent>
            <DataTable columns={cattleColumns} data={cattle} emptyLabel="No cattle in current agency scope." />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
