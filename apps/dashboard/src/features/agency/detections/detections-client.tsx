"use client";

import { Badge } from '@/src/shared/ui/badge';
import { Button } from '@/src/shared/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/src/shared/ui/dialog';
import { Input } from '@/src/shared/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/src/shared/ui/select';
import { Skeleton } from '@/src/shared/ui/skeleton';
import { getDetectionMonitoring } from '@/src/shared/api/client';
import { useAgencySession } from '@/src/features/auth/session-context';
import { EvidenceDetail, EvidenceLabel } from '@/src/features/agency/detections/evidence-label';
import type { DetectionMonitoringItem } from '@/src/shared/types/api';
import { useQuery } from '@tanstack/react-query';
import { Eye, Search } from 'lucide-react';
import { useMemo, useState } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  flexRender,
  type ColumnDef,
  type SortingState,
} from '@tanstack/react-table';

function evidenceState(item: DetectionMonitoringItem): string {
  const image = item.evidence_breakdown?.image && typeof item.evidence_breakdown.image === 'object';
  const nlp = item.evidence_breakdown?.nlp && typeof item.evidence_breakdown.nlp === 'object';
  if (image && nlp) return 'image_nlp';
  if (image) return 'image_only';
  if (nlp) return 'nlp_only';
  return 'missing';
}

export function DetectionsClient() {
  const { token, agencyUserId } = useAgencySession();
  const [sorting, setSorting] = useState<SortingState>([]);
  const [globalFilter, setGlobalFilter] = useState('');
  const [classFilter, setClassFilter] = useState('all');
  const [selected, setSelected] = useState<DetectionMonitoringItem | null>(null);

  const query = useQuery({
    queryKey: ['detections'],
    queryFn: () => getDetectionMonitoring(token, agencyUserId),
    enabled: Boolean(token && agencyUserId),
  });

  const detections = useMemo(() => {
    const list = query.data?.detections ?? [];
    if (classFilter === 'all') return list;
    return list.filter((d) => d.disease_class === classFilter);
  }, [query.data?.detections, classFilter]);

  const diseaseClasses = useMemo(() => {
    const all = query.data?.detections ?? [];
    return [...new Set(all.map((d) => d.disease_class))].sort();
  }, [query.data?.detections]);

  const columns: ColumnDef<DetectionMonitoringItem>[] = useMemo(() => [
    {
      accessorKey: 'disease_class',
      header: 'Class',
      cell: ({ row }) => <span className="font-medium capitalize">{row.original.disease_class.replace(/_/g, ' ')}</span>,
    },
    {
      accessorKey: 'confidence',
      header: 'Confidence',
      meta: { align: 'center' },
      cell: ({ row }) => <div className="text-center font-mono text-xs">{Math.round(row.original.confidence * 100)}%</div>,
    },
    {
      accessorKey: 'reliability',
      header: 'Reliability',
      meta: { align: 'center' },
      cell: ({ row }) => (
        <div className="text-center">
          <Badge variant={row.original.reliability === 'high' ? 'default' : 'secondary'}>
            {row.original.reliability ?? 'needs review'}
          </Badge>
        </div>
      ),
    },
    {
      id: 'evidence',
      header: 'Evidence',
      cell: ({ row }) => <EvidenceLabel item={row.original} />,
    },
    {
      accessorKey: 'cattle_id',
      header: 'Cattle',
      cell: ({ row }) => <span className="font-mono text-xs">{row.original.cattle_id ?? 'not linked'}</span>,
    },
    {
      id: 'actions',
      header: 'Actions',
      meta: { align: 'right' },
      cell: ({ row }) => (
        <div className="flex items-center justify-end">
          <Button variant="ghost" size="icon" className="h-7 w-7" aria-label="View detail" onClick={() => setSelected(row.original)}>
            <Eye className="h-3.5 w-3.5" />
          </Button>
        </div>
      ),
      enableSorting: false,
    },
  ], []);

  const table = useReactTable({
    data: detections,
    columns,
    state: { sorting, globalFilter },
    onSortingChange: setSorting,
    onGlobalFilterChange: setGlobalFilter,
    getCoreRowModel: getCoreRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getSortedRowModel: getSortedRowModel(),
    initialState: { pagination: { pageSize: 10 } },
  });

  if (query.isLoading) {
    return (
      <div className="space-y-3">
        <Skeleton className="h-9 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (query.isError) {
    return (
      <div className="rounded-md border border-destructive/50 bg-destructive/5 p-4 text-sm text-destructive">
        Could not load review items: {query.error.message}
      </div>
    );
  }

  return (
    <>
      <div className="space-y-4">
        {/* Safe-language banner */}
        <div className="rounded-md border bg-muted/30 px-4 py-2 text-sm text-muted-foreground">
          {query.data?.safeLanguage?.description ?? 'Risk signals for monitoring and follow-up. Not confirmed diagnosis or outbreak declaration.'}
        </div>

        {/* Filter bar */}
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
          <div className="relative flex-1 sm:max-w-xs">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search review items..."
              value={globalFilter}
              onChange={(e) => setGlobalFilter(e.target.value)}
              className="pl-9"
            />
          </div>
          <Select value={classFilter} onValueChange={setClassFilter}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="All disease classes" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All disease classes</SelectItem>
              {diseaseClasses.map((c) => (
                <SelectItem key={c} value={c} className="capitalize">{c.replace(/_/g, ' ')}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <span className="text-sm text-muted-foreground ml-auto">
            {table.getFilteredRowModel().rows.length} items
          </span>
        </div>

        {/* Table */}
        <div className="rounded-md border">
          <table className="w-full text-sm">
            <thead>
              {table.getHeaderGroups().map((headerGroup) => (
                <tr key={headerGroup.id} className="border-b bg-muted/40">
                  {headerGroup.headers.map((header) => {
                    const align = (header.column.columnDef.meta as { align?: string } | undefined)?.align;
                    return (
                      <th
                        key={header.id}
                        className={`px-4 py-2.5 text-xs font-medium text-muted-foreground cursor-pointer select-none ${align === 'center' ? 'text-center' : align === 'right' ? 'text-right' : 'text-left'}`}
                        onClick={header.column.getToggleSortingHandler()}
                      >
                        <div className={`flex items-center gap-1 ${align === 'center' ? 'justify-center' : align === 'right' ? 'justify-end' : ''}`}>
                          {header.isPlaceholder ? null : flexRender(header.column.columnDef.header, header.getContext())}
                          {header.column.getIsSorted() === 'asc' && ' ↑'}
                          {header.column.getIsSorted() === 'desc' && ' ↓'}
                        </div>
                      </th>
                    );
                  })}
                </tr>
              ))}
            </thead>
            <tbody>
              {table.getRowModel().rows.length === 0 ? (
                <tr>
                  <td colSpan={columns.length} className="px-4 py-8 text-center text-muted-foreground">
                    No review items are available for this agency scope yet.
                  </td>
                </tr>
              ) : (
                table.getRowModel().rows.map((row, i) => (
                  <tr key={row.id} className={`border-b last:border-0 transition-colors hover:bg-muted/20 ${i % 2 === 1 ? 'bg-muted/5' : ''}`}>
                    {row.getVisibleCells().map((cell) => (
                      <td key={cell.id} className="px-4 py-2.5">
                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                      </td>
                    ))}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {table.getPageCount() > 1 && (
          <div className="flex items-center justify-between">
            <p className="text-xs text-muted-foreground">
              Page {table.getState().pagination.pageIndex + 1} of {table.getPageCount()}
            </p>
            <div className="flex items-center gap-1">
              <Button variant="outline" size="sm" onClick={() => table.previousPage()} disabled={!table.getCanPreviousPage()}>
                Previous
              </Button>
              <Button variant="outline" size="sm" onClick={() => table.nextPage()} disabled={!table.getCanNextPage()}>
                Next
              </Button>
            </div>
          </div>
        )}
      </div>

      {/* Detail modal */}
      <DetectionDetailDialog item={selected} open={!!selected} onClose={() => setSelected(null)} />
    </>
  );
}

function DetectionDetailDialog({
  item,
  open,
  onClose,
}: {
  item: DetectionMonitoringItem | null;
  open: boolean;
  onClose: () => void;
}) {
  if (!item) return null;

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) onClose(); }}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="capitalize">{item.disease_class.replace(/_/g, ' ')} detection</DialogTitle>
        </DialogHeader>

        <div className="space-y-3 mt-2">
          <DetailRow label="Detection ID" value={item.id} mono />
          <DetailRow label="Farmer ID" value={item.farmer_id} mono />
          <DetailRow label="Cattle ID" value={item.cattle_id ?? 'not linked'} mono />
          <DetailRow label="Disease Class">
            <span className="capitalize">{item.disease_class.replace(/_/g, ' ')}</span>
          </DetailRow>
          <DetailRow label="Confidence" value={`${Math.round(item.confidence * 100)}%`} />
          <DetailRow label="Confidence Level" value={item.confidence_level ?? 'unknown'} />
          <DetailRow label="Reliability">
            <Badge variant={item.reliability === 'high' ? 'default' : 'secondary'}>{item.reliability ?? 'needs review'}</Badge>
          </DetailRow>
          <DetailRow label="Review State" value={item.conflict_status ?? 'image only'} />
          <DetailRow label="Evidence">
            <div className="flex flex-col items-end gap-1">
              <EvidenceLabel item={item} />
              <EvidenceDetail item={item} />
            </div>
          </DetailRow>
          {item.created_at && <DetailRow label="Submitted" value={new Date(item.created_at).toLocaleString()} />}
        </div>
      </DialogContent>
    </Dialog>
  );
}

function DetailRow({ label, value, mono, children }: { label: string; value?: string; mono?: boolean; children?: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between py-1.5 border-b last:border-0">
      <span className="text-sm text-muted-foreground">{label}</span>
      {children ?? <span className={`text-sm font-medium ${mono ? 'font-mono text-xs' : ''}`}>{value}</span>}
    </div>
  );
}
