"use client";

import React from "react";
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
import {
	getAgencyRegistry,
	getDetectionMonitoring,
} from "@/src/shared/api/client";
import { useAgencySession } from "@/src/features/auth/session-context";
import type {
	AgencyRegistryCattle,
	DetectionMonitoringItem,
} from "@/src/shared/types/api";
import { useQuery } from "@tanstack/react-query";
import {
	ArrowLeft,
	ChevronDown,
	ChevronUp,
	History,
	Search,
} from "lucide-react";
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

export function FarmerDetailClient({ farmerId }: { farmerId: string }) {
	const { token, agencyUserId } = useAgencySession();
	const router = useRouter();
	const enabled = Boolean(token && agencyUserId);

	const registryQuery = useQuery({
		queryKey: ["registry"],
		queryFn: () => getAgencyRegistry(token, agencyUserId),
		enabled,
	});

	const detectionsQuery = useQuery({
		queryKey: ["detections"],
		queryFn: () => getDetectionMonitoring(token, agencyUserId),
		enabled,
	});

	const farmer = useMemo(() => {
		return registryQuery.data?.farmers.find((f) => f.id === farmerId) ?? null;
	}, [registryQuery.data?.farmers, farmerId]);

	const cattle = useMemo(() => {
		return (registryQuery.data?.cattle ?? []).filter(
			(c) => c.farmer_id === farmerId,
		);
	}, [registryQuery.data?.cattle, farmerId]);

	const farmerDetections = useMemo(() => {
		return (detectionsQuery.data?.detections ?? []).filter(
			(d) => d.farmer_id === farmerId,
		);
	}, [detectionsQuery.data?.detections, farmerId]);

	if (registryQuery.isLoading) {
		return (
			<div className="space-y-4">
				<Skeleton className="h-8 w-48" />
				<Skeleton className="h-32 w-full" />
				<Skeleton className="h-64 w-full" />
			</div>
		);
	}

	if (!farmer) {
		return (
			<div className="space-y-4">
				<Button
					variant="ghost"
					size="sm"
					onClick={() => router.push("/agency/registry")}
					className="gap-1"
				>
					<ArrowLeft className="h-4 w-4" /> Back to registry
				</Button>
				<div className="rounded-md border border-destructive/50 bg-destructive/5 p-4 text-sm text-destructive">
					Farmer not found or not in your jurisdiction scope.
				</div>
			</div>
		);
	}

	return (
		<div className="space-y-6">
			{/* Back button + header */}
			<div className="space-y-3">
				<Button
					variant="ghost"
					size="sm"
					onClick={() => router.push("/agency/registry")}
					className="gap-1"
				>
					<ArrowLeft className="h-4 w-4" /> Back to registry
				</Button>
				<div className="flex items-center gap-3">
					<div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center">
						<span className="text-sm font-semibold text-primary">
							{farmer.name.charAt(0)}
						</span>
					</div>
					<div>
						<h1 className="text-2xl font-semibold tracking-tight">
							{farmer.name}
						</h1>
						<p className="text-sm text-muted-foreground">
							{farmer.jurisdiction_id} · {farmer.id}
						</p>
					</div>
					<Badge
						variant={farmer.consent_tier === "private" ? "outline" : "default"}
						className="ml-auto"
					>
						{farmer.consent_tier.replace(/_/g, " ")}
					</Badge>
				</div>
			</div>

			{/* Farmer info summary */}
			<div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
				<InfoBlock label="Cattle" value={String(cattle.length)} />
				<InfoBlock label="Detections" value={String(farmerDetections.length)} />
				<InfoBlock label="Jurisdiction" value={farmer.jurisdiction_id} />
				<InfoBlock
					label="Consent"
					value={farmer.consent_tier.replace(/_/g, " ")}
				/>
			</div>

			{/* Cattle table */}
			<section className="space-y-3">
				<h2 className="text-lg font-semibold">Cattle</h2>
				<CattleTable cattle={cattle} detections={farmerDetections} />
			</section>
		</div>
	);
}

function InfoBlock({ label, value }: { label: string; value: string }) {
	return (
		<div className="rounded-md border px-4 py-3">
			<p className="text-xs text-muted-foreground">{label}</p>
			<p className="text-lg font-semibold">{value}</p>
		</div>
	);
}

function CattleTable({
	cattle,
	detections,
}: {
	cattle: AgencyRegistryCattle[];
	detections: DetectionMonitoringItem[];
}) {
	const [sorting, setSorting] = useState<SortingState>([]);
	const [globalFilter, setGlobalFilter] = useState("");
	const [statusFilter, setStatusFilter] = useState("all");
	const [expandedCattleId, setExpandedCattleId] = useState<string | null>(null);

	const filtered = useMemo(() => {
		let list = cattle;
		if (statusFilter !== "all")
			list = list.filter((c) => c.status === statusFilter);
		return list;
	}, [cattle, statusFilter]);

	const statuses = useMemo(
		() => [...new Set(cattle.map((c) => c.status))].sort(),
		[cattle],
	);

	const columns: ColumnDef<AgencyRegistryCattle>[] = useMemo(
		() => [
			{
				accessorKey: "tag",
				header: "Tag",
				cell: ({ row }) => (
					<span className="font-mono text-xs">{row.original.tag}</span>
				),
			},
			{ accessorKey: "breed", header: "Breed" },
			{
				accessorKey: "sex",
				header: "Sex",
				cell: ({ row }) => (
					<span className="capitalize">{row.original.sex}</span>
				),
			},
			{
				accessorKey: "status",
				header: "Status",
				cell: ({ row }) => (
					<Badge
						variant={row.original.status === "active" ? "default" : "secondary"}
					>
						{row.original.status}
					</Badge>
				),
			},
			{
				id: "actions",
				header: "Actions",
				meta: { align: "right" },
				cell: ({ row }) => {
					const isExpanded = expandedCattleId === row.original.id;
					return (
						<div className="flex items-center justify-end">
							<Button
								variant="ghost"
								size="sm"
								className="h-7 gap-1 text-xs"
								onClick={() =>
									setExpandedCattleId(isExpanded ? null : row.original.id)
								}
							>
								<History className="h-3.5 w-3.5" />
								History
								{isExpanded ? (
									<ChevronUp className="h-3 w-3" />
								) : (
									<ChevronDown className="h-3 w-3" />
								)}
							</Button>
						</div>
					);
				},
				enableSorting: false,
			},
		],
		[expandedCattleId],
	);

	const table = useReactTable({
		data: filtered,
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

	return (
		<div className="space-y-3">
			{/* Filter bar */}
			<div className="flex flex-col gap-3 sm:flex-row sm:items-center">
				<div className="relative flex-1 sm:max-w-xs">
					<Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
					<Input
						placeholder="Search cattle..."
						value={globalFilter}
						onChange={(e) => setGlobalFilter(e.target.value)}
						className="pl-9"
					/>
				</div>
				<Select value={statusFilter} onValueChange={setStatusFilter}>
					<SelectTrigger className="w-[150px]">
						<SelectValue placeholder="All statuses" />
					</SelectTrigger>
					<SelectContent>
						<SelectItem value="all">All statuses</SelectItem>
						{statuses.map((s) => (
							<SelectItem key={s} value={s}>
								{s}
							</SelectItem>
						))}
					</SelectContent>
				</Select>
				<span className="text-sm text-muted-foreground ml-auto">
					{table.getFilteredRowModel().rows.length} cattle
				</span>
			</div>

			{/* Table */}
			<div className="rounded-md border">
				<table className="w-full text-sm">
					<thead>
						{table.getHeaderGroups().map((headerGroup) => (
							<tr key={headerGroup.id} className="border-b bg-muted/40">
								{headerGroup.headers.map((header) => {
									const align = (
										header.column.columnDef.meta as
											| { align?: string }
											| undefined
									)?.align;
									return (
										<th
											key={header.id}
											className={`px-4 py-2.5 text-xs font-medium text-muted-foreground cursor-pointer select-none ${align === "center" ? "text-center" : align === "right" ? "text-right" : "text-left"}`}
											onClick={header.column.getToggleSortingHandler()}
										>
											<div
												className={`flex items-center gap-1 ${align === "center" ? "justify-center" : align === "right" ? "justify-end" : ""}`}
											>
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
									);
								})}
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
									No cattle registered.
								</td>
							</tr>
						) : (
							table.getRowModel().rows.map((row, i) => (
								<React.Fragment key={row.id}>
									<tr
										className={`border-b transition-colors hover:bg-muted/20 ${i % 2 === 1 ? "bg-muted/5" : ""}`}
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
									{expandedCattleId === row.original.id && (
										<tr key={`${row.id}-history`} className="border-b">
											<td colSpan={columns.length} className="p-4 bg-muted/10">
												<DetectionHistoryTable
													detections={detections.filter(
														(d) => d.cattle_id === row.original.id,
													)}
												/>
											</td>
										</tr>
									)}
								</React.Fragment>
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

function DetectionHistoryTable({
	detections,
}: {
	detections: DetectionMonitoringItem[];
}) {
	if (detections.length === 0) {
		return (
			<div className="text-sm text-muted-foreground text-center py-4">
				No detection history for this cattle.
			</div>
		);
	}

	return (
		<div className="space-y-2">
			<p className="text-xs font-medium text-muted-foreground">
				Detection History ({detections.length})
			</p>
			<div className="rounded-md border bg-background">
				<table className="w-full text-sm">
					<thead>
						<tr className="border-b bg-muted/30">
							<th className="px-3 py-2 text-left text-xs font-medium text-muted-foreground">
								Date
							</th>
							<th className="px-3 py-2 text-left text-xs font-medium text-muted-foreground">
								Disease Class
							</th>
							<th className="px-3 py-2 text-left text-xs font-medium text-muted-foreground">
								Confidence
							</th>
							<th className="px-3 py-2 text-left text-xs font-medium text-muted-foreground">
								Reliability
							</th>
						</tr>
					</thead>
					<tbody>
						{detections.map((d) => (
							<tr
								key={d.id}
								className="border-b last:border-0 hover:bg-muted/10"
							>
								<td className="px-3 py-2 text-xs">
									{d.created_at
										? new Date(d.created_at).toLocaleDateString()
										: "—"}
								</td>
								<td className="px-3 py-2 capitalize">
									{d.disease_class.replace(/_/g, " ")}
								</td>
								<td className="px-3 py-2 font-mono text-xs">
									{(d.confidence * 100).toFixed(1)}%
								</td>
								<td className="px-3 py-2">
									<Badge
										variant={d.reliability === "high" ? "default" : "secondary"}
									>
										{d.reliability ?? "—"}
									</Badge>
								</td>
							</tr>
						))}
					</tbody>
				</table>
			</div>
		</div>
	);
}
