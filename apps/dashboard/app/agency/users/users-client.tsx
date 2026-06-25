"use client";

import { useAgencySession } from "@/src/features/auth/session-context";
import { useDebouncedValue } from "@/src/shared/hooks/use-debounced-value";
import {
	AlertDialog,
	AlertDialogAction,
	AlertDialogCancel,
	AlertDialogContent,
	AlertDialogDescription,
	AlertDialogFooter,
	AlertDialogHeader,
	AlertDialogTitle,
} from "@/src/shared/ui/alert-dialog";
import { Badge } from "@/src/shared/ui/badge";
import { Button } from "@/src/shared/ui/button";
import {
	Dialog,
	DialogContent,
	DialogDescription,
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
import {
	keepPreviousData,
	useMutation,
	useQuery,
	useQueryClient,
} from "@tanstack/react-query";
import { Pencil, Plus, Search, Trash2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import {
	useReactTable,
	getCoreRowModel,
	getPaginationRowModel,
	getSortedRowModel,
	flexRender,
	type ColumnDef,
	type SortingState,
} from "@tanstack/react-table";

type AgencyUserItem = { id: string; role: string; jurisdiction_id: string };
type JurisdictionItem = {
	id: string;
	name: string;
	level: string;
	parent_id: string | null;
};

const ROLES = [
	"admin",
	"province_officer",
	"district_officer",
	"village_officer",
	"viewer",
];

function roleVariant(role: string): "default" | "secondary" | "outline" {
	if (role === "admin") return "default";
	if (role.endsWith("officer")) return "secondary";
	return "outline";
}

async function fetchUsers(
	token: string,
	agencyUserId: string,
	params: { search?: string; role?: string } = {},
): Promise<{ users: AgencyUserItem[] }> {
	const query = new URLSearchParams();
	if (params.search) query.set("search", params.search);
	if (params.role && params.role !== "all") query.set("role", params.role);
	const path = query.toString()
		? `/api/agency/users?${query.toString()}`
		: "/api/agency/users";
	const res = await fetch(path, {
		headers: {
			Authorization: `Bearer ${token}`,
			"X-Agency-User-Id": agencyUserId,
		},
	});
	if (!res.ok) throw new Error("Failed to fetch users");
	return res.json();
}

async function fetchJurisdictions(
	token: string,
	agencyUserId: string,
): Promise<{ jurisdictions: JurisdictionItem[] }> {
	const res = await fetch("/api/agency/jurisdictions", {
		headers: {
			Authorization: `Bearer ${token}`,
			"X-Agency-User-Id": agencyUserId,
		},
	});
	if (!res.ok) throw new Error("Failed to fetch jurisdictions");
	return res.json();
}

async function createUser(
	token: string,
	agencyUserId: string,
	data: AgencyUserItem,
) {
	const res = await fetch("/api/agency/users", {
		method: "POST",
		headers: {
			"Content-Type": "application/json",
			Authorization: `Bearer ${token}`,
			"X-Agency-User-Id": agencyUserId,
		},
		body: JSON.stringify(data),
	});
	if (!res.ok) throw new Error("Failed to create user");
	return res.json();
}

async function updateUser(
	token: string,
	agencyUserId: string,
	userId: string,
	data: { role: string; jurisdiction_id?: string },
) {
	const res = await fetch(`/api/agency/users/${userId}`, {
		method: "PUT",
		headers: {
			"Content-Type": "application/json",
			Authorization: `Bearer ${token}`,
			"X-Agency-User-Id": agencyUserId,
		},
		body: JSON.stringify(data),
	});
	if (!res.ok) throw new Error("Failed to update user");
	return res.json();
}

async function deleteUser(token: string, agencyUserId: string, userId: string) {
	const res = await fetch(`/api/agency/users/${userId}`, {
		method: "DELETE",
		headers: {
			Authorization: `Bearer ${token}`,
			"X-Agency-User-Id": agencyUserId,
		},
	});
	if (!res.ok) throw new Error("Failed to delete user");
	return res.json();
}

export function UsersClient() {
	const { token, agencyUserId } = useAgencySession();
	const queryClient = useQueryClient();
	const enabled = Boolean(token && agencyUserId);

	const [sorting, setSorting] = useState<SortingState>([]);
	const [globalFilter, setGlobalFilter] = useState("");
	const debouncedGlobalFilter = useDebouncedValue(globalFilter);
	const [roleFilter, setRoleFilter] = useState("all");
	const [formOpen, setFormOpen] = useState(false);
	const [editing, setEditing] = useState<AgencyUserItem | null>(null);
	const [deleteTarget, setDeleteTarget] = useState<AgencyUserItem | null>(null);

	const usersQuery = useQuery({
		queryKey: ["agency-users", debouncedGlobalFilter, roleFilter],
		queryFn: () =>
			fetchUsers(token, agencyUserId, {
				search: debouncedGlobalFilter,
				role: roleFilter,
			}),
		enabled,
		placeholderData: keepPreviousData,
	});
	const jurisdictionsQuery = useQuery({
		queryKey: ["jurisdictions"],
		queryFn: () => fetchJurisdictions(token, agencyUserId),
		enabled,
	});

	const deleteMutation = useMutation({
		mutationFn: (userId: string) => deleteUser(token, agencyUserId, userId),
		onSuccess: () => {
			toast.success("User deleted.");
			queryClient.invalidateQueries({ queryKey: ["agency-users"] });
			setDeleteTarget(null);
		},
		onError: (error) => {
			toast.error(error instanceof Error ? error.message : "Failed to delete user.");
		},
	});

	const users = useMemo(() => {
		return usersQuery.data?.users ?? [];
	}, [usersQuery.data?.users]);

	const roles = useMemo(() => {
		const all = usersQuery.data?.users ?? [];
		return [...new Set(all.map((u) => u.role))].sort();
	}, [usersQuery.data?.users]);

	const columns: ColumnDef<AgencyUserItem>[] = useMemo(
		() => [
			{
				accessorKey: "id",
				header: "ID",
				cell: ({ row }) => (
					<span className="font-mono text-xs">{row.original.id}</span>
				),
			},
			{
				accessorKey: "role",
				header: "Role",
				meta: { align: "center" },
				cell: ({ row }) => (
					<div className="text-center">
						<Badge variant={roleVariant(row.original.role)}>
							{row.original.role.replace(/_/g, " ")}
						</Badge>
					</div>
				),
			},
			{ accessorKey: "jurisdiction_id", header: "Jurisdiction" },
			{
				id: "actions",
				header: "Actions",
				meta: { align: "right" },
				cell: ({ row }) => (
					<div className="flex items-center justify-end gap-1">
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
						<Button
							variant="ghost"
							size="icon"
							className="h-7 w-7 text-destructive hover:text-destructive"
							aria-label="Delete"
							onClick={() => setDeleteTarget(row.original)}
						>
							<Trash2 className="h-3.5 w-3.5" />
						</Button>
					</div>
				),
				enableSorting: false,
			},
		],
		[],
	);

	const table = useReactTable({
		data: users,
		columns,
		state: { sorting },
		onSortingChange: setSorting,
		getCoreRowModel: getCoreRowModel(),
		getPaginationRowModel: getPaginationRowModel(),
		getSortedRowModel: getSortedRowModel(),
		initialState: { pagination: { pageSize: 10 } },
	});

	if (usersQuery.isPending) {
		return (
			<div className="space-y-3">
				<Skeleton className="h-9 w-full" />
				<Skeleton className="h-64 w-full" />
			</div>
		);
	}

	if (usersQuery.isError) {
		return (
			<div className="rounded-md border border-destructive/50 bg-destructive/5 p-4 text-sm text-destructive">
				Could not load users: {(usersQuery.error as Error).message}
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
							placeholder="Search users..."
							value={globalFilter}
							onChange={(e) => setGlobalFilter(e.target.value)}
							className="pl-9"
						/>
					</div>
					<Select value={roleFilter} onValueChange={setRoleFilter}>
						<SelectTrigger className="w-[170px]">
							<SelectValue placeholder="All roles" />
						</SelectTrigger>
						<SelectContent>
							<SelectItem value="all">All roles</SelectItem>
							{roles.map((r) => (
								<SelectItem key={r} value={r}>
									{r.replace(/_/g, " ")}
								</SelectItem>
							))}
						</SelectContent>
					</Select>
					<Button
						size="sm"
						className="gap-1.5 sm:ml-auto"
						onClick={() => {
							setEditing(null);
							setFormOpen(true);
						}}
					>
						<Plus className="h-3.5 w-3.5" /> Add user
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
										No users found.
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

			<UserFormDialog
				open={formOpen}
				editing={editing}
				jurisdictions={jurisdictionsQuery.data?.jurisdictions ?? []}
				onClose={() => {
					setFormOpen(false);
					setEditing(null);
				}}
				onSaved={() => {
					setFormOpen(false);
					setEditing(null);
					queryClient.invalidateQueries({ queryKey: ["agency-users"] });
				}}
			/>

			<AlertDialog
				open={!!deleteTarget}
				onOpenChange={(v) => {
					if (!v) setDeleteTarget(null);
				}}
			>
				<AlertDialogContent>
					<AlertDialogHeader>
						<AlertDialogTitle>Delete user?</AlertDialogTitle>
						<AlertDialogDescription>
							This will permanently remove agency user{" "}
							<span className="font-mono">{deleteTarget?.id}</span> and revoke
							their access. This cannot be undone.
						</AlertDialogDescription>
					</AlertDialogHeader>
					<AlertDialogFooter>
						<AlertDialogCancel>Cancel</AlertDialogCancel>
						<AlertDialogAction
							onClick={() =>
								deleteTarget && deleteMutation.mutate(deleteTarget.id)
							}
							className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
						>
							{deleteMutation.isPending ? "Deleting..." : "Delete"}
						</AlertDialogAction>
					</AlertDialogFooter>
				</AlertDialogContent>
			</AlertDialog>
		</>
	);
}

function UserFormDialog({
	open,
	editing,
	jurisdictions,
	onClose,
	onSaved,
}: {
	open: boolean;
	editing: AgencyUserItem | null;
	jurisdictions: JurisdictionItem[];
	onClose: () => void;
	onSaved: () => void;
}) {
	const { token, agencyUserId } = useAgencySession();
	const isEdit = !!editing;

	const [id, setId] = useState("");
	const [role, setRole] = useState("district_officer");
	const [jurisdiction, setJurisdiction] = useState("");

	useEffect(() => {
		if (editing) {
			setId(editing.id);
			setRole(editing.role);
			setJurisdiction(editing.jurisdiction_id);
		} else {
			setId("");
			setRole("district_officer");
			setJurisdiction("");
		}
	}, [editing, open]);

	const mutation = useMutation({
		mutationFn: () => {
			if (isEdit && editing) {
				return updateUser(token, agencyUserId, editing.id, {
					role,
					jurisdiction_id: jurisdiction,
				});
			}
			return createUser(token, agencyUserId, {
				id,
				role,
				jurisdiction_id: jurisdiction,
			});
		},
		onSuccess: () => {
			toast.success(isEdit ? "User updated." : "User added.");
			onSaved();
		},
		onError: (error) => {
			toast.error(
				error instanceof Error
					? error.message
					: isEdit
						? "Failed to update user."
						: "Failed to add user.",
			);
		},
	});

	return (
		<Dialog
			open={open}
			onOpenChange={(v) => {
				if (!v) onClose();
			}}
		>
			<DialogContent className="sm:max-w-md">
				<DialogHeader>
					<DialogTitle>
						{isEdit ? `Edit ${editing?.id}` : "New agency user"}
					</DialogTitle>
					<DialogDescription className="sr-only">
						{isEdit
							? "Update agency user role and jurisdiction."
							: "Create a new agency user account."}
					</DialogDescription>
				</DialogHeader>

				<form
					className="space-y-3"
					onSubmit={(e) => {
						e.preventDefault();
						mutation.mutate();
					}}
				>
					{!isEdit && (
						<div className="space-y-1.5">
							<Label htmlFor="user-id">User ID</Label>
							<Input
								id="user-id"
								value={id}
								onChange={(e) => setId(e.target.value)}
								placeholder="e.g. agency-6"
								required
							/>
						</div>
					)}
					<div className="space-y-1.5">
						<Label htmlFor="role">Role</Label>
						<Select value={role} onValueChange={setRole}>
							<SelectTrigger id="role">
								<SelectValue placeholder="Select role" />
							</SelectTrigger>
							<SelectContent>
								{ROLES.map((r) => (
									<SelectItem key={r} value={r}>
										{r.replace(/_/g, " ")}
									</SelectItem>
								))}
							</SelectContent>
						</Select>
					</div>
					<div className="space-y-1.5">
						<Label htmlFor="jurisdiction">Jurisdiction</Label>
						<Select value={jurisdiction} onValueChange={setJurisdiction}>
							<SelectTrigger id="jurisdiction">
								<SelectValue placeholder="Select jurisdiction" />
							</SelectTrigger>
							<SelectContent>
								{jurisdictions.map((j) => (
									<SelectItem key={j.id} value={j.id}>
										{j.name} ({j.level})
									</SelectItem>
								))}
							</SelectContent>
						</Select>
					</div>

					{mutation.isError && (
						<p className="text-sm text-destructive">
							{(mutation.error as Error).message}
						</p>
					)}

					<DialogFooter>
						<Button type="button" variant="ghost" onClick={onClose}>
							Cancel
						</Button>
						<Button
							type="submit"
							disabled={mutation.isPending || (!isEdit && !id) || !jurisdiction}
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
