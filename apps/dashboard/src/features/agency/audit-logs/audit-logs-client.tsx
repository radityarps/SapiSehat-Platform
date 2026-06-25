"use client";

import { Badge } from "@/src/shared/ui/badge";
import { Button } from "@/src/shared/ui/button";
import {
	Dialog,
	DialogContent,
	DialogDescription,
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
import { getAuditLogs } from "@/src/shared/api/client";
import { useAgencySession } from "@/src/features/auth/session-context";
import { useDebouncedValue } from "@/src/shared/hooks/use-debounced-value";
import type { AuditLogItem } from "@/src/shared/types/api";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { Eye, Search } from "lucide-react";
import { useMemo, useState } from "react";
import {
	useReactTable,
	getCoreRowModel,
	getPaginationRowModel,
	getSortedRowModel,
	flexRender,
	type ColumnDef,
	type SortingState,
} from "@tanstack/react-table";

export function AuditLogsClient() {
	const { token, agencyUserId } = useAgencySession();
	const enabled = Boolean(token && agencyUserId);

	const [sorting, setSorting] = useState<SortingState>([
		{ id: "created_at", desc: true },
	]);
	const [globalFilter, setGlobalFilter] = useState("");
	const debouncedGlobalFilter = useDebouncedValue(globalFilter);
	const [actionFilter, setActionFilter] = useState("all");
	const [selected, setSelected] = useState<AuditLogItem | null>(null);

	const query = useQuery({
		queryKey: ["audit-logs", debouncedGlobalFilter, actionFilter],
		queryFn: () =>
			getAuditLogs(token, agencyUserId, {
				search: debouncedGlobalFilter,
				action: actionFilter,
			}),
		enabled,
		placeholderData: keepPreviousData,
	});

	const logs = useMemo(() => {
		return query.data?.logs ?? [];
	}, [query.data?.logs]);

	const actions = useMemo(() => {
		const all = query.data?.logs ?? [];
		return [...new Set(all.map((l) => l.action))].sort();
	}, [query.data?.logs]);

	const columns: ColumnDef<AuditLogItem>[] = useMemo(
		() => [
			{
				accessorKey: "created_at",
				header: "Time",
				cell: ({ row }) => (
					<span className="whitespace-nowrap text-xs tabular-nums">
						{new Date(row.original.created_at).toLocaleString()}
					</span>
				),
			},
			{
				accessorKey: "action",
				header: "Action",
				cell: ({ row }) => (
					<Badge variant="outline" className="font-mono text-xs">
						{row.original.action}
					</Badge>
				),
			},
			{
				accessorKey: "actor_id",
				header: "Actor",
				cell: ({ row }) => (
					<span className="font-mono text-xs">{row.original.actor_id}</span>
				),
			},
			{ accessorKey: "resource_type", header: "Resource" },
			{
				accessorKey: "resource_id",
				header: "Resource ID",
				cell: ({ row }) => (
					<span className="font-mono text-xs">{row.original.resource_id}</span>
				),
			},
			{
				id: "actions",
				header: "Actions",
				meta: { align: "right" },
				cell: ({ row }) => (
					<div className="flex items-center justify-end">
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
		data: logs,
		columns,
		state: { sorting },
		onSortingChange: setSorting,
		getCoreRowModel: getCoreRowModel(),
		getPaginationRowModel: getPaginationRowModel(),
		getSortedRowModel: getSortedRowModel(),
		initialState: { pagination: { pageSize: 15 } },
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
				Could not load audit logs: {query.error.message}
			</div>
		);
	}

	return (
		<>
			<div className="space-y-4">
				{/* Filter bar */}
				<div className="flex flex-col gap-3 sm:flex-row sm:items-center">
					<div className="relative flex-1 sm:max-w-xs">
						<Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
						<Input
							placeholder="Search audit logs..."
							value={globalFilter}
							onChange={(e) => setGlobalFilter(e.target.value)}
							className="pl-9"
						/>
					</div>
					<Select value={actionFilter} onValueChange={setActionFilter}>
						<SelectTrigger className="w-[200px]">
							<SelectValue placeholder="All actions" />
						</SelectTrigger>
						<SelectContent>
							<SelectItem value="all">All actions</SelectItem>
							{actions.map((a) => (
								<SelectItem key={a} value={a}>
									{a}
								</SelectItem>
							))}
						</SelectContent>
					</Select>
					<span className="text-sm text-muted-foreground ml-auto">
						{table.getRowModel().rows.length} entries
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
												className={`px-4 py-2.5 text-xs font-medium text-muted-foreground cursor-pointer select-none ${align === "right" ? "text-right" : "text-left"}`}
												onClick={header.column.getToggleSortingHandler()}
											>
												<div
													className={`flex items-center gap-1 ${align === "right" ? "justify-end" : ""}`}
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
										No audit logs are available yet.
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

			<AuditLogDetailDialog
				item={selected}
				open={!!selected}
				onClose={() => setSelected(null)}
			/>
		</>
	);
}

function AuditLogDetailDialog({
	item,
	open,
	onClose,
}: {
	item: AuditLogItem | null;
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
					<DialogTitle className="font-mono text-base">
						{item.action}
					</DialogTitle>
					<DialogDescription className="sr-only">
						View detailed audit log entry.
					</DialogDescription>
				</DialogHeader>

				<div className="mt-2 grid grid-cols-2 overflow-hidden rounded-md border">
					<DetailCell label="Log ID" value={item.id} mono />
					<DetailCell
						label="Time"
						value={new Date(item.created_at).toLocaleString()}
					/>
					<DetailCell label="Actor Type" value={item.actor_type} />
					<DetailCell label="Actor ID" value={item.actor_id} mono />
					<DetailCell label="Resource Type" value={item.resource_type} />
					<DetailCell label="Resource ID" value={item.resource_id} mono />
				</div>

				<div className="mt-3 space-y-1">
					<p className="text-xs text-muted-foreground">Metadata</p>
					<pre className="overflow-auto rounded-md border bg-muted/20 p-3 text-xs">
						{JSON.stringify(item.metadata_json, null, 2)}
					</pre>
				</div>
			</DialogContent>
		</Dialog>
	);
}

function DetailCell({
	label,
	value,
	mono,
}: {
	label: string;
	value: string;
	mono?: boolean;
}) {
	return (
		<div className="flex min-w-0 overflow-hidden border-b border-r">
			<div className="flex w-2/5 shrink-0 items-start bg-muted/50 px-3 py-2 text-xs text-muted-foreground">
				{label}
			</div>
			<div className="flex flex-1 min-w-0 items-start px-3 py-2">
				<span
					className={`text-sm font-medium break-words min-w-0 w-full ${mono ? "font-mono text-xs" : ""}`}
				>
					{value}
				</span>
			</div>
		</div>
	);
}
