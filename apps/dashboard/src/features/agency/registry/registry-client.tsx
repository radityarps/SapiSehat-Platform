"use client";

import { Badge } from "@/src/shared/ui/badge";
import { Button } from "@/src/shared/ui/button";
import { Input } from "@/src/shared/ui/input";
import {
	Select,
	SelectContent,
	SelectItem,
	SelectTrigger,
	SelectValue,
} from "@/src/shared/ui/select";
import { Skeleton } from "@/src/shared/ui/skeleton";
import { getAgencyRegistry, getDetectionMonitoring } from "@/src/shared/api/client";
import { useAgencySession } from "@/src/features/auth/session-context";
import type { AgencyRegistryFarmer } from "@/src/shared/types/api";
import { useQuery } from "@tanstack/react-query";
import { Eye, Search } from "lucide-react";
import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import {
	useReactTable,
	getCoreRowModel,
	getFilteredRowModel,
	getPaginationRowModel,
	getSortedRowModel,
	flexRender,
	type ColumnDef,
	type SortingState,
} from "@tanstack/react-table";

export function RegistryClient() {
	const { token, agencyUserId } = useAgencySession();
	const router = useRouter();
	const [sorting, setSorting] = useState<SortingState>([]);
	const [globalFilter, setGlobalFilter] = useState("");
	const [jurisdictionFilter, setJurisdictionFilter] = useState("all");

	const query = useQuery({
		queryKey: ["registry"],
		queryFn: () => getAgencyRegistry(token, agencyUserId),
		enabled: Boolean(token && agencyUserId),
	});

	const detectionsQuery = useQuery({
		queryKey: ["detections"],
		queryFn: () => getDetectionMonitoring(token, agencyUserId),
		enabled: Boolean(token && agencyUserId),
	});

	const cattleCountByFarmer = useMemo(() => {
		const map: Record<string, number> = {};
		(query.data?.cattle ?? []).forEach((c) => {
			map[c.farmer_id] = (map[c.farmer_id] ?? 0) + 1;
		});
		return map;
	}, [query.data?.cattle]);

	const detectionCountByFarmer = useMemo(() => {
		const map: Record<string, number> = {};
		(detectionsQuery.data?.detections ?? []).forEach((d) => {
			map[d.farmer_id] = (map[d.farmer_id] ?? 0) + 1;
		});
		return map;
	}, [detectionsQuery.data?.detections]);

	const farmers = useMemo(() => {
		const list = query.data?.farmers ?? [];
		if (jurisdictionFilter === "all") return list;
		return list.filter((f) => f.jurisdiction_id === jurisdictionFilter);
	}, [query.data?.farmers, jurisdictionFilter]);

	const jurisdictions = useMemo(() => {
		const all = query.data?.farmers ?? [];
		return [...new Set(all.map((f) => f.jurisdiction_id))].sort();
	}, [query.data?.farmers]);

	const columns: ColumnDef<AgencyRegistryFarmer>[] = useMemo(
		() => [
			{
				accessorKey: "id",
				header: "ID",
				cell: ({ row }) => (
					<span className="font-mono text-xs">{row.original.id}</span>
				),
			},
			{
				accessorKey: "name",
				header: "Name",
				cell: ({ row }) => (
					<span className="font-medium">{row.original.name}</span>
				),
			},
			{ accessorKey: "jurisdiction_id", header: "Jurisdiction" },
			{
				id: "cattle",
				header: "Cattle",
				accessorFn: (row) => cattleCountByFarmer[row.id] ?? 0,
				cell: ({ row }) => (
					<span className="tabular-nums">{cattleCountByFarmer[row.original.id] ?? 0}</span>
				),
			},
			{
				id: "detections",
				header: "Detections",
				accessorFn: (row) => detectionCountByFarmer[row.id] ?? 0,
				cell: ({ row }) => (
					<span className="tabular-nums">{detectionCountByFarmer[row.original.id] ?? 0}</span>
				),
			},
			{
				accessorKey: "consent_tier",
				header: "Consent",
				cell: ({ row }) => {
					const tier = row.original.consent_tier;
					const variant =
						tier === "agency_monitoring"
							? "default"
							: tier === "research_and_monitoring"
								? "secondary"
								: "outline";
					return <Badge variant={variant}>{tier.replace(/_/g, " ")}</Badge>;
				},
			},
			{
				id: "actions",
				header: () => <span className="sr-only">Actions</span>,
				cell: ({ row }) => (
					<div className="flex items-center justify-end">
						<Button
							variant="ghost"
							size="icon"
							className="h-7 w-7"
							aria-label={`View ${row.original.name}`}
							onClick={() => router.push(`/agency/farmers/${row.original.id}`)}
						>
							<Eye className="h-3.5 w-3.5" />
						</Button>
					</div>
				),
				enableSorting: false,
			},
		],
		[router, cattleCountByFarmer, detectionCountByFarmer],
	);

	const table = useReactTable({
		data: farmers,
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
				Could not load registry: {query.error.message}
			</div>
		);
	}

	return (
		<div className="space-y-4">
			{/* Filter bar */}
			<div className="flex flex-col gap-3 sm:flex-row sm:items-center">
				<div className="relative flex-1 sm:max-w-xs">
					<Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
					<Input
						placeholder="Search farmers..."
						value={globalFilter}
						onChange={(e) => setGlobalFilter(e.target.value)}
						className="pl-9"
					/>
				</div>
				<Select
					value={jurisdictionFilter}
					onValueChange={setJurisdictionFilter}
				>
					<SelectTrigger className="w-[180px]">
						<SelectValue placeholder="All jurisdictions" />
					</SelectTrigger>
					<SelectContent>
						<SelectItem value="all">All jurisdictions</SelectItem>
						{jurisdictions.map((j) => (
							<SelectItem key={j} value={j}>
								{j}
							</SelectItem>
						))}
					</SelectContent>
				</Select>
				<span className="text-sm text-muted-foreground ml-auto">
					{table.getFilteredRowModel().rows.length} farmers
				</span>
			</div>

			{/* Table */}
			<div className="rounded-md border">
				<table className="w-full text-sm">
					<thead>
						{table.getHeaderGroups().map((headerGroup) => (
							<tr key={headerGroup.id} className="border-b bg-muted/40">
								{headerGroup.headers.map((header) => (
									<th
										key={header.id}
										className="px-4 py-2.5 text-left text-xs font-medium text-muted-foreground cursor-pointer select-none"
										onClick={header.column.getToggleSortingHandler()}
									>
										<div className="flex items-center gap-1">
											{header.isPlaceholder
												? null
												: flexRender(
														header.column.columnDef.header,
														header.getContext(),
													)}
											{header.column.getIsSorted() === "asc" && " ↑"}
											{header.column.getIsSorted() === "desc" && " ↓"}
										</div>
									</th>
								))}
							</tr>
						))}
					</thead>
					<tbody>
						{table.getRowModel().rows.length === 0 ? (
							<tr>
								<td
									colSpan={columns.length}
									className="px-4 py-8 text-center text-muted-foreground"
								>
									No farmers in current agency scope.
								</td>
							</tr>
						) : (
							table.getRowModel().rows.map((row, i) => (
								<tr
									key={row.id}
									className={`border-b last:border-0 transition-colors hover:bg-muted/20 ${i % 2 === 1 ? "bg-muted/5" : ""}`}
								>
									{row.getVisibleCells().map((cell) => (
										<td key={cell.id} className="px-4 py-2.5">
											{flexRender(
												cell.column.columnDef.cell,
												cell.getContext(),
											)}
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
						Page {table.getState().pagination.pageIndex + 1} of{" "}
						{table.getPageCount()}
					</p>
					<div className="flex items-center gap-1">
						<Button
							variant="outline"
							size="sm"
							onClick={() => table.previousPage()}
							disabled={!table.getCanPreviousPage()}
						>
							Previous
						</Button>
						<Button
							variant="outline"
							size="sm"
							onClick={() => table.nextPage()}
							disabled={!table.getCanNextPage()}
						>
							Next
						</Button>
					</div>
				</div>
			)}
		</div>
	);
}
