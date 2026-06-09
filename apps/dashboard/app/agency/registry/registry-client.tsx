"use client";

import { DataTable } from '@/components/data-table';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui/skeleton';
import { getAgencyRegistry } from '@/lib/api';
import { getAgencyToken } from '@/lib/auth';
import type { AgencyRegistryCattle, AgencyRegistryFarmer } from '@/lib/types';
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
  const token = getAgencyToken();
  const [search, setSearch] = useState('');
  const query = useQuery({ queryKey: ['registry'], queryFn: () => getAgencyRegistry(token), enabled: Boolean(token) });

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
