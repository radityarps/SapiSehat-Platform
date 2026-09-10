"use client";

import { useAgencySession } from "@/src/features/auth/session-context";
import { useDebouncedValue } from "@/src/shared/hooks/use-debounced-value";
import {
	activateGuideCategory,
	archiveGuideCategory,
	getGuideCategories,
	saveGuideCategory,
} from "@/src/shared/api/client";
import type { GuideCategory } from "@/src/shared/types/api";
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
import {
	type ColumnDef,
	flexRender,
	getCoreRowModel,
	getPaginationRowModel,
	getSortedRowModel,
	type SortingState,
	useReactTable,
} from "@tanstack/react-table";
import {
	Archive,
	CheckCircle2,
	Loader2,
	Pencil,
	Plus,
	Search,
} from "lucide-react";
import { useMemo, useState } from "react";
import { toast } from "sonner";

export function GuideCategoriesClient() {
	const { token, agency, agencyUserId } = useAgencySession();
	const queryClient = useQueryClient();
	const enabled = Boolean(token && agencyUserId && agency?.role === "admin");

	const [sorting, setSorting] = useState<SortingState>([]);
	const [globalFilter, setGlobalFilter] = useState("");
	const debouncedGlobalFilter = useDebouncedValue(globalFilter);
	const [statusFilter, setStatusFilter] = useState("all");

	// Dialog States (ID and EN only)
	const [dialogOpen, setDialogOpen] = useState(false);
	const [editingCategory, setEditingCategory] = useState<GuideCategory | null>(null);
	const [labelId, setLabelId] = useState("");
	const [labelEn, setLabelEn] = useState("");
	const [displayOrder, setDisplayOrder] = useState<number>(0);

	// Confirmation States
	const [archiveTarget, setArchiveTarget] = useState<GuideCategory | null>(null);

	const categoriesQuery = useQuery({
		queryKey: ["guide-categories"],
		queryFn: async () => {
			const res = await getGuideCategories(token, agencyUserId);
			return res.items;
		},
		enabled,
		placeholderData: keepPreviousData,
	});

	const saveMutation = useMutation({
		mutationFn: async (payload: {
			id?: string;
			display_order: number;
			translations: { locale: string; label: string }[];
		}) => {
			return saveGuideCategory(token, agencyUserId, payload);
		},
		onSuccess: () => {
			toast.success(
				editingCategory ? "Category updated." : "Category created.",
			);
			queryClient.invalidateQueries({ queryKey: ["guide-categories"] });
			queryClient.invalidateQueries({ queryKey: ["agency-guides"] });
			setDialogOpen(false);
			setEditingCategory(null);
		},
		onError: (error) => {
			toast.error(
				error instanceof Error ? error.message : "Failed to save category.",
			);
		},
	});

	const archiveMutation = useMutation({
		mutationFn: (categoryId: string) =>
			archiveGuideCategory(token, agencyUserId, categoryId),
		onSuccess: () => {
			toast.success("Category archived.");
			queryClient.invalidateQueries({ queryKey: ["guide-categories"] });
			queryClient.invalidateQueries({ queryKey: ["agency-guides"] });
			setArchiveTarget(null);
		},
		onError: (error) => {
			toast.error(
				error instanceof Error ? error.message : "Failed to archive category.",
			);
		},
	});

	const activateMutation = useMutation({
		mutationFn: (categoryId: string) =>
			activateGuideCategory(token, agencyUserId, categoryId),
		onSuccess: () => {
			toast.success("Category activated.");
			queryClient.invalidateQueries({ queryKey: ["guide-categories"] });
			queryClient.invalidateQueries({ queryKey: ["agency-guides"] });
		},
		onError: (error) => {
			toast.error(
				error instanceof Error ? error.message : "Failed to activate category.",
			);
		},
	});

	const categories = useMemo(() => {
		const all = categoriesQuery.data ?? [];
		const needle = debouncedGlobalFilter.trim().toLowerCase();
		return all.filter((item) => {
			const matchesSearch =
				!needle ||
				item.id.toLowerCase().includes(needle) ||
				item.translations.some((t) => t.label.toLowerCase().includes(needle));
			const matchesStatus =
				statusFilter === "all" || item.state === statusFilter;
			return matchesSearch && matchesStatus;
		});
	}, [categoriesQuery.data, debouncedGlobalFilter, statusFilter]);

	const openAddDialog = () => {
		setEditingCategory(null);
		setLabelId("");
		setLabelEn("");
		setDisplayOrder(((categoriesQuery.data?.length ?? 0) + 1) * 10);
		setDialogOpen(true);
	};

	const openEditDialog = (category: GuideCategory) => {
		setEditingCategory(category);
		setLabelId(category.translations.find((t) => t.locale === "id")?.label || "");
		setLabelEn(category.translations.find((t) => t.locale === "en")?.label || "");
		setDisplayOrder(category.display_order);
		setDialogOpen(true);
	};

	const handleSaveCategory = () => {
		if (!labelId.trim()) {
			toast.error("Indonesian category label (ID) is required.");
			return;
		}

		const translations = [
			{ locale: "id", label: labelId.trim() },
			...(labelEn.trim() ? [{ locale: "en", label: labelEn.trim() }] : []),
		];

		saveMutation.mutate({
			id: editingCategory?.id,
			display_order: displayOrder,
			translations,
		});
	};

	const columns: ColumnDef<GuideCategory>[] = useMemo(
		() => [
			{
				accessorKey: "label",
				header: "Category",
				cell: ({ row }) => {
					const cat = row.original;
					const primary =
						cat.translations.find((t) => t.locale === "id")?.label ||
						cat.translations[0]?.label ||
						"Untitled";
					return (
						<div className="flex flex-col">
							<span className="font-medium text-sm text-foreground">
								{primary}
							</span>
							<div className="flex flex-wrap items-center gap-1 mt-0.5">
								{cat.translations.map((t) => (
									<span
										key={t.locale}
										className="inline-flex items-center gap-1 rounded bg-muted px-1.5 py-0.5 text-[10px] text-muted-foreground"
									>
										<span className="font-mono font-semibold uppercase">{t.locale}:</span>
										<span>{t.label}</span>
									</span>
								))}
							</div>
						</div>
					);
				},
			},
			{
				accessorKey: "article_count",
				header: "Articles",
				meta: { align: "center" },
				cell: ({ row }) => (
					<div className="text-center">
						<Badge variant="secondary" className="font-mono text-xs">
							{row.original.article_count}
						</Badge>
					</div>
				),
			},
			{
				accessorKey: "display_order",
				header: "Order",
				meta: { align: "center" },
				cell: ({ row }) => (
					<div className="text-center font-mono text-xs text-muted-foreground">
						{row.original.display_order}
					</div>
				),
			},
			{
				accessorKey: "system_owned",
				header: "Type",
				meta: { align: "center" },
				cell: ({ row }) => (
					<div className="text-center">
						<Badge
							variant={row.original.system_owned ? "default" : "outline"}
							className="text-[11px]"
						>
							{row.original.system_owned ? "System" : "Custom"}
						</Badge>
					</div>
				),
			},
			{
				accessorKey: "state",
				header: "Status",
				meta: { align: "center" },
				cell: ({ row }) => (
					<div className="text-center">
						<Badge
							variant={row.original.state === "active" ? "secondary" : "destructive"}
							className="capitalize text-[11px]"
						>
							{row.original.state}
						</Badge>
					</div>
				),
			},
			{
				id: "actions",
				header: "Actions",
				meta: { align: "right" },
				cell: ({ row }) => {
					const cat = row.original;
					return (
						<div className="flex items-center justify-end gap-1">
							<Button
								variant="ghost"
								size="icon"
								className="h-7 w-7"
								aria-label="Edit"
								title="Edit category"
								onClick={() => openEditDialog(cat)}
							>
								<Pencil className="h-3.5 w-3.5" />
							</Button>

							{cat.state === "archived" ? (
								<Button
									variant="ghost"
									size="icon"
									className="h-7 w-7 text-emerald-600 hover:text-emerald-700 dark:text-emerald-500"
									aria-label="Activate"
									title="Activate category"
									disabled={activateMutation.isPending}
									onClick={() => activateMutation.mutate(cat.id)}
								>
									<CheckCircle2 className="h-3.5 w-3.5" />
								</Button>
							) : !cat.system_owned && cat.state === "active" ? (
								<Button
									variant="ghost"
									size="icon"
									className="h-7 w-7 text-destructive hover:text-destructive"
									aria-label="Archive"
									title="Archive category"
									disabled={archiveMutation.isPending}
									onClick={() => setArchiveTarget(cat)}
								>
									<Archive className="h-3.5 w-3.5" />
								</Button>
							) : null}
						</div>
					);
				},
				enableSorting: false,
			},
		],
		[activateMutation, archiveMutation],
	);

	const table = useReactTable({
		data: categories,
		columns,
		state: { sorting },
		onSortingChange: setSorting,
		getCoreRowModel: getCoreRowModel(),
		getPaginationRowModel: getPaginationRowModel(),
		getSortedRowModel: getSortedRowModel(),
		initialState: { pagination: { pageSize: 10 } },
	});

	if (agency?.role !== "admin") {
		return (
			<div className="rounded-md border border-destructive/50 bg-destructive/5 p-4 text-sm text-destructive">
				Only global administrators can access the Guide CMS.
			</div>
		);
	}

	if (categoriesQuery.isPending) {
		return (
			<div className="space-y-3">
				<Skeleton className="h-9 w-full" />
				<Skeleton className="h-64 w-full" />
			</div>
		);
	}

	if (categoriesQuery.isError) {
		return (
			<div className="rounded-md border border-destructive/50 bg-destructive/5 p-4 text-sm text-destructive">
				Could not load guide categories: {(categoriesQuery.error as Error).message}
			</div>
		);
	}

	return (
		<>
			<div className="space-y-4">
				{/* Filter bar + Actions (No Back Button) */}
				<div className="flex flex-col gap-3 sm:flex-row sm:items-center">
					<div className="relative flex-1 sm:max-w-xs">
						<Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
						<Input
							placeholder="Search categories..."
							value={globalFilter}
							onChange={(e) => setGlobalFilter(e.target.value)}
							className="pl-9"
						/>
					</div>

					<Select value={statusFilter} onValueChange={setStatusFilter}>
						<SelectTrigger className="w-[160px]">
							<SelectValue placeholder="All statuses" />
						</SelectTrigger>
						<SelectContent>
							<SelectItem value="all">All statuses</SelectItem>
							<SelectItem value="active">Active</SelectItem>
							<SelectItem value="archived">Archived</SelectItem>
						</SelectContent>
					</Select>

					<Button
						size="sm"
						className="gap-1.5 sm:ml-auto"
						onClick={openAddDialog}
					>
						<Plus className="h-3.5 w-3.5" /> Add category
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
										No guide categories found.
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

			{/* Add/Edit Category Modal Dialog (Fixed ID & EN labels) */}
			<Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
				<DialogContent className="sm:max-w-md">
					<DialogHeader>
						<DialogTitle>
							{editingCategory ? "Edit Category" : "Add New Category"}
						</DialogTitle>
						<DialogDescription>
							{editingCategory
								? `Update Indonesian and English category names.`
								: "Provide category labels for Indonesian and English."}
						</DialogDescription>
					</DialogHeader>

					<div className="space-y-4 py-2">
						<div className="space-y-1.5">
							<Label htmlFor="category-label-id">
								Indonesian Name (ID) <span className="text-destructive">*</span>
							</Label>
							<Input
								id="category-label-id"
								value={labelId}
								onChange={(e) => setLabelId(e.target.value)}
								placeholder="e.g. Kesehatan Sapi"
							/>
						</div>

						<div className="space-y-1.5">
							<Label htmlFor="category-label-en">
								English Name (EN)
							</Label>
							<Input
								id="category-label-en"
								value={labelEn}
								onChange={(e) => setLabelEn(e.target.value)}
								placeholder="e.g. Cattle Health"
							/>
						</div>

						<div className="space-y-1.5">
							<Label htmlFor="display-order-input">Display Order</Label>
							<Input
								id="display-order-input"
								type="number"
								value={displayOrder}
								onChange={(e) => setDisplayOrder(parseInt(e.target.value, 10) || 0)}
								placeholder="e.g. 10"
								className="w-32"
							/>
							<p className="text-xs text-muted-foreground">
								Lower numbers appear first in the farmer guide list.
							</p>
						</div>
					</div>

					<DialogFooter className="gap-2 sm:gap-0">
						<Button
							type="button"
							variant="outline"
							onClick={() => setDialogOpen(false)}
						>
							Cancel
						</Button>
						<Button
							type="button"
							disabled={saveMutation.isPending}
							onClick={handleSaveCategory}
						>
							{saveMutation.isPending && (
								<Loader2 className="mr-1.5 h-4 w-4 animate-spin" />
							)}
							{editingCategory ? "Save Changes" : "Create Category"}
						</Button>
					</DialogFooter>
				</DialogContent>
			</Dialog>

			{/* Archive Confirmation Modal */}
			<AlertDialog
				open={!!archiveTarget}
				onOpenChange={(v) => {
					if (!v) setArchiveTarget(null);
				}}
			>
				<AlertDialogContent>
					<AlertDialogHeader>
						<AlertDialogTitle>Archive category?</AlertDialogTitle>
						<AlertDialogDescription>
							Are you sure you want to archive category{" "}
							<span className="font-semibold text-foreground">
								"{archiveTarget ? (archiveTarget.translations.find((t) => t.locale === "id")?.label || archiveTarget.translations[0]?.label || archiveTarget.id) : ""}"
							</span>
							? Articles under this category will be preserved under General, and this category will become inactive.
						</AlertDialogDescription>
					</AlertDialogHeader>
					<AlertDialogFooter>
						<AlertDialogCancel>Cancel</AlertDialogCancel>
						<AlertDialogAction
							onClick={() =>
								archiveTarget && archiveMutation.mutate(archiveTarget.id)
							}
							className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
						>
							{archiveMutation.isPending ? "Archiving..." : "Archive"}
						</AlertDialogAction>
					</AlertDialogFooter>
				</AlertDialogContent>
			</AlertDialog>
		</>
	);
}
