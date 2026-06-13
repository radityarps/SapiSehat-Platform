"use client";

import { Badge } from "@/src/shared/ui/badge";
import { Button } from "@/src/shared/ui/button";
import {
	Dialog,
	DialogContent,
	DialogFooter,
	DialogHeader,
	DialogTitle,
} from "@/src/shared/ui/dialog";
import { Input } from "@/src/shared/ui/input";
import { Label } from "@/src/shared/ui/label";
import {
	Select,
	SelectContent,
	SelectItem,
	SelectTrigger,
	SelectValue,
} from "@/src/shared/ui/select";
import { Skeleton } from "@/src/shared/ui/skeleton";
import { Textarea } from "@/src/shared/ui/textarea";
import {
	createAgencyFollowUp,
	getAgencyFollowUps,
	getAgencyRegistry,
	updateAgencyFollowUp,
} from "@/src/shared/api/client";
import { useAgencySession } from "@/src/features/auth/session-context";
import type { AgencyFollowUpItem } from "@/src/shared/types/api";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
	DropdownMenu,
	DropdownMenuContent,
	DropdownMenuItem,
	DropdownMenuLabel,
	DropdownMenuSeparator,
	DropdownMenuTrigger,
} from "@/src/shared/ui/dropdown-menu";
import { ChevronDown, Eye, Pencil, Plus, Search } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
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

const STATUSES = ["needs_follow_up", "in_progress", "completed", "escalated"];
const DEFAULT_MESSAGE =
	"Petugas akan meninjau sinyal risiko ini. Ini bukan diagnosis.";

function statusVariant(
	status: string,
): "default" | "secondary" | "destructive" | "outline" {
	if (status === "completed") return "default";
	if (status === "escalated") return "destructive";
	if (status === "in_progress") return "secondary";
	return "outline";
}

export function FollowUpsClient() {
	const { token, agencyUserId } = useAgencySession();
	const enabled = Boolean(token && agencyUserId);
	const queryClient = useQueryClient();

	const [sorting, setSorting] = useState<SortingState>([]);
	const [globalFilter, setGlobalFilter] = useState("");
	const [statusFilter, setStatusFilter] = useState("all");
	const [formOpen, setFormOpen] = useState(false);
	const [editing, setEditing] = useState<AgencyFollowUpItem | null>(null);
	const [viewing, setViewing] = useState<AgencyFollowUpItem | null>(null);

	const query = useQuery({
		queryKey: ["follow-ups", agencyUserId],
		queryFn: () => getAgencyFollowUps(token, agencyUserId),
		enabled,
	});
	const registry = useQuery({
		queryKey: ["registry"],
		queryFn: () => getAgencyRegistry(token, agencyUserId),
		enabled,
	});

	const statusMutation = useMutation({
		mutationFn: ({ id, status }: { id: string; status: string }) =>
			updateAgencyFollowUp(token, agencyUserId, id, { status }),
		onSuccess: () => queryClient.invalidateQueries({ queryKey: ["follow-ups"] }),
	});

	const followUps = useMemo(() => {
		const list = query.data?.followUps ?? [];
		if (statusFilter === "all") return list;
		return list.filter((f) => f.status === statusFilter);
	}, [query.data?.followUps, statusFilter]);

	const statuses = useMemo(() => {
		const all = query.data?.followUps ?? [];
		return [...new Set(all.map((f) => f.status))].sort();
	}, [query.data?.followUps]);

	const columns: ColumnDef<AgencyFollowUpItem>[] = useMemo(
		() => [
			{
				accessorKey: "status",
				header: "Status",
				meta: { align: "center" },
				cell: ({ row }) => (
					<div className="text-center">
						<Badge variant={statusVariant(row.original.status)}>
							{row.original.status.replace(/_/g, " ")}
						</Badge>
					</div>
				),
			},
			{
				accessorKey: "farmer_id",
				header: "Farmer",
				cell: ({ row }) => (
					<span className="font-mono text-xs">{row.original.farmer_id}</span>
				),
			},
			{
				accessorKey: "cattle_id",
				header: "Cattle",
				cell: ({ row }) => (
					<span className="font-mono text-xs">
						{row.original.cattle_id ?? "not linked"}
					</span>
				),
			},
			{
				accessorKey: "public_message",
				header: "Farmer message",
				cell: ({ row }) => (
					<span className="line-clamp-1 max-w-xs">
						{row.original.public_message}
					</span>
				),
			},
			{
				id: "actions",
				header: "Actions",
				meta: { align: "right" },
				cell: ({ row }) => (
					<div className="flex items-center justify-end gap-1">
						<DropdownMenu>
							<DropdownMenuTrigger asChild>
								<Button
									variant="ghost"
									size="sm"
									className="h-7 gap-1 text-xs"
									aria-label="Change status"
								>
									Status <ChevronDown className="h-3 w-3" />
								</Button>
							</DropdownMenuTrigger>
							<DropdownMenuContent align="end">
								<DropdownMenuLabel>Set status</DropdownMenuLabel>
								<DropdownMenuSeparator />
								{STATUSES.map((s) => (
									<DropdownMenuItem
										key={s}
										disabled={s === row.original.status}
										onClick={() =>
											statusMutation.mutate({
												id: row.original.id,
												status: s,
											})
										}
									>
										{s.replace(/_/g, " ")}
									</DropdownMenuItem>
								))}
							</DropdownMenuContent>
						</DropdownMenu>
						<Button
							variant="ghost"
							size="icon"
							className="h-7 w-7"
							aria-label="View"
							onClick={() => setViewing(row.original)}
						>
							<Eye className="h-3.5 w-3.5" />
						</Button>
						<Button
							variant="ghost"
							size="icon"
							className="h-7 w-7"
							aria-label="Edit"
							onClick={() => {
								setEditing(row.original);
								setFormOpen(true);
							}}
						>
							<Pencil className="h-3.5 w-3.5" />
						</Button>
					</div>
				),
				enableSorting: false,
			},
		],
		[statusMutation],
	);

	const table = useReactTable({
		data: followUps,
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
				Could not load follow-ups: {query.error.message}
			</div>
		);
	}

	return (
		<>
			<div className="space-y-4">
				{/* Filter bar + create */}
				<div className="flex flex-col gap-3 sm:flex-row sm:items-center">
					<div className="relative flex-1 sm:max-w-xs">
						<Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
						<Input
							placeholder="Search follow-ups..."
							value={globalFilter}
							onChange={(e) => setGlobalFilter(e.target.value)}
							className="pl-9"
						/>
					</div>
					<Select value={statusFilter} onValueChange={setStatusFilter}>
						<SelectTrigger className="w-[170px]">
							<SelectValue placeholder="All statuses" />
						</SelectTrigger>
						<SelectContent>
							<SelectItem value="all">All statuses</SelectItem>
							{statuses.map((s) => (
								<SelectItem key={s} value={s}>
									{s.replace(/_/g, " ")}
								</SelectItem>
							))}
						</SelectContent>
					</Select>
					<Button
						size="sm"
						className="gap-1.5"
						onClick={() => {
							setEditing(null);
							setFormOpen(true);
						}}
					>
						<Plus className="h-3.5 w-3.5" /> Record follow-up
					</Button>
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
										No agency follow-ups have been created yet.
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

			<FollowUpFormDialog
				open={formOpen}
				editing={editing}
				farmers={registry.data?.farmers ?? []}
				onClose={() => {
					setFormOpen(false);
					setEditing(null);
				}}
				onSaved={() => {
					setFormOpen(false);
					setEditing(null);
					queryClient.invalidateQueries({ queryKey: ["follow-ups"] });
				}}
			/>

			<FollowUpDetailDialog
				item={viewing}
				open={!!viewing}
				onClose={() => setViewing(null)}
			/>
		</>
	);
}

function FollowUpFormDialog({
	open,
	editing,
	farmers,
	onClose,
	onSaved,
}: {
	open: boolean;
	editing: AgencyFollowUpItem | null;
	farmers: { id: string; name: string }[];
	onClose: () => void;
	onSaved: () => void;
}) {
	const { token, agencyUserId } = useAgencySession();
	const isEdit = !!editing;

	const [farmerId, setFarmerId] = useState("");
	const [cattleId, setCattleId] = useState("");
	const [status, setStatus] = useState("needs_follow_up");
	const [publicMessage, setPublicMessage] = useState(DEFAULT_MESSAGE);
	const [internalNotes, setInternalNotes] = useState("");

	// Sync form when dialog opens or editing target changes.
	useEffect(() => {
		if (editing) {
			setFarmerId(editing.farmer_id);
			setCattleId(editing.cattle_id ?? "");
			setStatus(editing.status);
			setPublicMessage(editing.public_message);
			setInternalNotes(editing.internal_notes);
		} else {
			setFarmerId("");
			setCattleId("");
			setStatus("needs_follow_up");
			setPublicMessage(DEFAULT_MESSAGE);
			setInternalNotes("");
		}
	}, [editing, open]);

	const mutation = useMutation({
		mutationFn: () => {
			if (isEdit && editing) {
				return updateAgencyFollowUp(token, agencyUserId, editing.id, {
					status,
					public_message: publicMessage,
					internal_notes: internalNotes,
				});
			}
			return createAgencyFollowUp(token, agencyUserId, {
				farmer_id: farmerId,
				cattle_id: cattleId || undefined,
				status,
				public_message: publicMessage,
				internal_notes: internalNotes,
			});
		},
		onSuccess: onSaved,
	});

	return (
		<Dialog
			open={open}
			onOpenChange={(v) => {
				if (!v) onClose();
			}}
		>
			<DialogContent className="sm:max-w-lg">
				<DialogHeader>
					<DialogTitle>
						{isEdit ? "Edit follow-up" : "Record follow-up"}
					</DialogTitle>
				</DialogHeader>

				<form
					className="space-y-3"
					onSubmit={(e) => {
						e.preventDefault();
						mutation.mutate();
					}}
				>
					{!isEdit && (
						<>
							<div className="space-y-1.5">
								<Label htmlFor="farmer">Farmer</Label>
								<Select value={farmerId} onValueChange={setFarmerId}>
									<SelectTrigger id="farmer">
										<SelectValue placeholder="Select farmer" />
									</SelectTrigger>
									<SelectContent>
										{farmers.map((f) => (
											<SelectItem key={f.id} value={f.id}>
												{f.name} ({f.id})
											</SelectItem>
										))}
									</SelectContent>
								</Select>
							</div>
							<div className="space-y-1.5">
								<Label htmlFor="cattle">Cattle ID (optional)</Label>
								<Input
									id="cattle"
									value={cattleId}
									onChange={(e) => setCattleId(e.target.value)}
									placeholder="e.g. cattle-1"
								/>
							</div>
						</>
					)}
					<div className="space-y-1.5">
						<Label htmlFor="status">Status</Label>
						<Select value={status} onValueChange={setStatus}>
							<SelectTrigger id="status">
								<SelectValue placeholder="Select status" />
							</SelectTrigger>
							<SelectContent>
								{STATUSES.map((s) => (
									<SelectItem key={s} value={s}>
										{s.replace(/_/g, " ")}
									</SelectItem>
								))}
							</SelectContent>
						</Select>
					</div>
					<div className="space-y-1.5">
						<Label htmlFor="message">Farmer-safe message</Label>
						<Textarea
							id="message"
							value={publicMessage}
							onChange={(e) => setPublicMessage(e.target.value)}
							rows={2}
							required
						/>
					</div>
					<div className="space-y-1.5">
						<Label htmlFor="notes">Internal notes</Label>
						<Textarea
							id="notes"
							value={internalNotes}
							onChange={(e) => setInternalNotes(e.target.value)}
							rows={2}
							placeholder="Agency-only note; avoid diagnosis or outbreak confirmation."
						/>
					</div>

					{mutation.isError && (
						<p className="text-sm text-destructive">{mutation.error.message}</p>
					)}

					<DialogFooter>
						<Button type="button" variant="ghost" onClick={onClose}>
							Cancel
						</Button>
						<Button
							type="submit"
							disabled={mutation.isPending || (!isEdit && !farmerId)}
						>
							{mutation.isPending
								? "Saving..."
								: isEdit
									? "Save changes"
									: "Create"}
						</Button>
					</DialogFooter>
				</form>
			</DialogContent>
		</Dialog>
	);
}

function FollowUpDetailDialog({
	item,
	open,
	onClose,
}: {
	item: AgencyFollowUpItem | null;
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
					<DialogTitle>Follow-up detail</DialogTitle>
				</DialogHeader>

				<div className="mt-2 grid grid-cols-2 overflow-hidden rounded-md border">
					<DetailCell label="Follow-up ID" value={item.id} mono />
					<DetailCell label="Status">
						<Badge variant={statusVariant(item.status)}>
							{item.status.replace(/_/g, " ")}
						</Badge>
					</DetailCell>
					<DetailCell label="Farmer ID" value={item.farmer_id} mono />
					<DetailCell
						label="Cattle ID"
						value={item.cattle_id ?? "not linked"}
						mono
					/>
				</div>

				<div className="mt-3 space-y-3">
					<div className="space-y-1">
						<p className="text-xs text-muted-foreground">Farmer-safe message</p>
						<p className="rounded-md border bg-muted/20 px-3 py-2 text-sm">
							{item.public_message}
						</p>
					</div>
					<div className="space-y-1">
						<p className="text-xs text-muted-foreground">
							Internal notes (agency-only)
						</p>
						<p className="rounded-md border bg-muted/20 px-3 py-2 text-sm">
							{item.internal_notes || "—"}
						</p>
					</div>
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
