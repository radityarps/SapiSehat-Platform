"use client";

import { Badge } from "@/src/shared/ui/badge";
import { Button } from "@/src/shared/ui/button";
import {
	Dialog,
	DialogContent,
	DialogHeader,
	DialogTitle,
} from "@/src/shared/ui/dialog";
import { Input } from "@/src/shared/ui/input";
import {
	Select,
	SelectContent,
	SelectItem,
	SelectTrigger,
	SelectValue,
} from "@/src/shared/ui/select";
import { Skeleton } from "@/src/shared/ui/skeleton";
import { RiskSignalMap } from "@/src/features/agency/risk-signals/risk-map";
import {
	getAgencyRegistry,
	getJurisdictions,
	getRiskSignals,
} from "@/src/shared/api/client";
import { useAgencySession } from "@/src/features/auth/session-context";
import type { RiskSignalItem } from "@/src/shared/types/api";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Eye, Plus, Search } from "lucide-react";
import { useMemo, useState } from "react";
import { RecordFollowUpDialog } from "./record-follow-up-dialog";
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

function riskVariant(
	level: string,
): "default" | "secondary" | "destructive" | "outline" {
	if (level === "possible_increased_risk" || level === "high")
		return "destructive";
	if (level === "medium") return "secondary";
	return "outline";
}

function riskLabel(level: string): string {
	const map: Record<string, string> = {
		possible_increased_risk: "Possible increased risk",
		baseline_monitoring: "Baseline monitoring",
		high: "High",
		medium: "Medium",
		low: "Low",
	};
	return map[level] ?? level.replace(/_/g, " ");
}

export function RiskSignalsClient() {
	const { token, agencyUserId } = useAgencySession();
	const queryClient = useQueryClient();
	const enabled = Boolean(token && agencyUserId);
	const [sorting, setSorting] = useState<SortingState>([]);
	const [globalFilter, setGlobalFilter] = useState("");
	const [riskFilter, setRiskFilter] = useState("all");
	const [selected, setSelected] = useState<RiskSignalItem | null>(null);
	const [followUpSignal, setFollowUpSignal] = useState<RiskSignalItem | null>(
		null,
	);

	const query = useQuery({
		queryKey: ["risk-signals"],
		queryFn: () => getRiskSignals(token, agencyUserId),
		enabled,
	});
	const jurisdictionsQuery = useQuery({
		queryKey: ["jurisdictions"],
		queryFn: () => getJurisdictions(token, agencyUserId),
		enabled,
	});
	const registryQuery = useQuery({
		queryKey: ["registry"],
		queryFn: () => getAgencyRegistry(token, agencyUserId),
		enabled,
	});

	const signals = useMemo(() => {
		const list = query.data?.signals ?? [];
		if (riskFilter === "all") return list;
		return list.filter((s) => s.risk_level === riskFilter);
	}, [query.data?.signals, riskFilter]);

	const riskLevels = useMemo(() => {
		const all = query.data?.signals ?? [];
		return [...new Set(all.map((s) => s.risk_level))].sort();
	}, [query.data?.signals]);

	const columns: ColumnDef<RiskSignalItem>[] = useMemo(
		() => [
			{ accessorKey: "jurisdiction_id", header: "District" },
			{
				accessorKey: "disease_class",
				header: "Class",
				cell: ({ row }) => (
					<span className="capitalize">
						{row.original.disease_class.replace(/_/g, " ")}
					</span>
				),
			},
			{
				accessorKey: "signal_count",
				header: "Signals",
				meta: { align: "center" },
				cell: ({ row }) => (
					<div className="text-center tabular-nums">
						{row.original.signal_count}
					</div>
				),
			},
			{
				accessorKey: "risk_level",
				header: "Risk Level",
				meta: { align: "center" },
				cell: ({ row }) => (
					<div className="text-center">
						<Badge variant={riskVariant(row.original.risk_level)}>
							{riskLabel(row.original.risk_level)}
						</Badge>
					</div>
				),
			},
			{
				accessorKey: "priority",
				header: "Priority",
				meta: { align: "center" },
				cell: ({ row }) => (
					<div className="text-center">{row.original.priority}</div>
				),
			},
			{
				id: "actions",
				header: "Actions",
				meta: { align: "right" },
				cell: ({ row }) => (
					<div className="flex items-center justify-end gap-1">
						<Button
							variant="ghost"
							size="sm"
							className="h-7 gap-1 text-xs"
							onClick={() => setFollowUpSignal(row.original)}
						>
							<Plus className="h-3 w-3" /> Follow-up
						</Button>
						<Button
							variant="ghost"
							size="icon"
							className="h-7 w-7"
							aria-label="View detail"
							onClick={() => setSelected(row.original)}
						>
							<Eye className="h-3.5 w-3.5" />
						</Button>
					</div>
				),
				enableSorting: false,
			},
		],
		[],
	);

	const table = useReactTable({
		data: signals,
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
				<Skeleton className="h-[360px] w-full rounded-lg" />
				<Skeleton className="h-9 w-full" />
				<Skeleton className="h-48 w-full" />
			</div>
		);
	}

	if (query.isError) {
		return (
			<div className="rounded-md border border-destructive/50 bg-destructive/5 p-4 text-sm text-destructive">
				Could not load risk signals: {query.error.message}
			</div>
		);
	}

	return (
		<>
			<div className="space-y-4">
				{/* Map */}
				<RiskSignalMap
					signals={query.data?.signals ?? []}
					jurisdictions={jurisdictionsQuery.data?.jurisdictions ?? []}
				/>

				{/* Filter bar */}
				<div className="flex flex-col gap-3 sm:flex-row sm:items-center">
					<div className="relative flex-1 sm:max-w-xs">
						<Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
						<Input
							placeholder="Search signals..."
							value={globalFilter}
							onChange={(e) => setGlobalFilter(e.target.value)}
							className="pl-9"
						/>
					</div>
					<Select value={riskFilter} onValueChange={setRiskFilter}>
						<SelectTrigger className="w-[160px]">
							<SelectValue placeholder="All risk levels" />
						</SelectTrigger>
						<SelectContent>
							<SelectItem value="all">All risk levels</SelectItem>
							{riskLevels.map((r) => (
								<SelectItem key={r} value={r} className="capitalize">
									{r}
								</SelectItem>
							))}
						</SelectContent>
					</Select>
					<span className="text-sm text-muted-foreground ml-auto">
						{table.getFilteredRowModel().rows.length} signals
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
										No district-level risk signals are active for this agency
										scope.
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

			<RiskSignalDetailDialog
				item={selected}
				open={!!selected}
				onClose={() => setSelected(null)}
			/>
			<RecordFollowUpDialog
				signal={followUpSignal}
				farmers={registryQuery.data?.farmers ?? []}
				open={!!followUpSignal}
				onClose={() => setFollowUpSignal(null)}
				onSaved={() => {
					setFollowUpSignal(null);
					queryClient.invalidateQueries({ queryKey: ["follow-ups"] });
				}}
			/>
		</>
	);
}

function RiskSignalDetailDialog({
	item,
	open,
	onClose,
}: {
	item: RiskSignalItem | null;
	open: boolean;
	onClose: () => void;
}) {
	if (!item) return null;

	return (
		<Dialog
			open={open}
			onOpenChange={(v) => {
				if (!v) onClose();
			}}
		>
			<DialogContent className="sm:max-w-lg">
				<DialogHeader>
					<DialogTitle className="capitalize">
						{item.disease_class.replace(/_/g, " ")} signal ·{" "}
						{item.jurisdiction_id}
					</DialogTitle>
				</DialogHeader>

				<div className="mt-2 grid grid-cols-2 overflow-hidden rounded-md border">
					<DetailCell label="Signal ID" value={item.id} mono />
					<DetailCell label="Jurisdiction" value={item.jurisdiction_id} />
					<DetailCell label="Disease Class">
						<span className="capitalize text-sm font-medium">
							{item.disease_class.replace(/_/g, " ")}
						</span>
					</DetailCell>
					<DetailCell label="Signal Count" value={String(item.signal_count)} />
					<DetailCell label="Risk Level">
						<Badge variant={riskVariant(item.risk_level)}>
							{riskLabel(item.risk_level)}
						</Badge>
					</DetailCell>
					<DetailCell label="Priority" value={item.priority} />
				</div>

				<div className="mt-3 space-y-2">
					<p className="text-xs font-medium text-muted-foreground">
						Source detection IDs ({item.source_result_ids.length})
					</p>
					{item.source_result_ids.length === 0 ? (
						<p className="text-sm text-muted-foreground">
							No source results recorded.
						</p>
					) : (
						<div className="flex flex-wrap gap-1.5">
							{item.source_result_ids.map((id) => (
								<Badge key={id} variant="outline" className="font-mono text-xs">
									{id}
								</Badge>
							))}
						</div>
					)}
				</div>
			</DialogContent>
		</Dialog>
	);
}

function DetailCell({
	label,
	value,
	mono,
	children,
}: {
	label: string;
	value?: string;
	mono?: boolean;
	children?: React.ReactNode;
}) {
	return (
		<div className="flex overflow-hidden border-b border-r">
			<div className="flex w-2/5 shrink-0 items-center bg-muted/50 px-3 py-2 text-xs text-muted-foreground">
				{label}
			</div>
			<div className="flex flex-1 items-center overflow-hidden px-3 py-2">
				{children ?? (
					<span
						className={`text-sm font-medium truncate ${mono ? "font-mono text-xs" : ""}`}
					>
						{value}
					</span>
				)}
			</div>
		</div>
	);
}
