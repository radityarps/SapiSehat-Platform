"use client";

import { useAgencySession } from "@/src/features/auth/session-context";
import { useDebouncedValue } from "@/src/shared/hooks/use-debounced-value";
import {
	getGuideArticles,
	getGuideCategories,
	getGuideMediaPreview,
	transitionGuideArticle,
} from "@/src/shared/api/client";
import type {
	GuideArticle,
	GuideBlock,
	GuideCategory,
	GuideTranslation,
} from "@/src/shared/types/api";
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
	Eye,
	FolderTree,
	Pencil,
	Plus,
	Search,
	XCircle,
} from "lucide-react";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";

function statusVariant(
	status: string,
): "default" | "secondary" | "outline" | "destructive" {
	if (status === "published") return "default";
	if (status === "draft") return "secondary";
	if (status === "archived") return "destructive";
	return "outline";
}

function articleTranslation(article: GuideArticle, locale?: string): GuideTranslation {
	if (locale) {
		const match = article.translations.find((item) => item.locale === locale);
		if (match) return match;
	}
	return (
		article.translations.find((item) => item.locale === "id") ??
		article.translations.find((item) => item.locale === "en") ??
		article.translations[0] ?? {
			locale: "id",
			title: "",
			summary: "",
			blocks: [],
		}
	);
}

function categoryLabel(category: GuideCategory, locale = "id"): string {
	return (
		category.translations.find((item) => item.locale === locale)?.label ??
		category.translations.find((item) => item.locale === "id")?.label ??
		category.translations.find((item) => item.locale === "en")?.label ??
		category.translations[0]?.label ??
		"General"
	);
}

export function GuideCmsClient() {
	const { token, agency, agencyUserId } = useAgencySession();
	const queryClient = useQueryClient();
	const enabled = Boolean(token && agencyUserId && agency?.role === "admin");

	const [sorting, setSorting] = useState<SortingState>([]);
	const [globalFilter, setGlobalFilter] = useState("");
	const debouncedGlobalFilter = useDebouncedValue(globalFilter);
	const [categoryFilter, setCategoryFilter] = useState("all");
	const [statusFilter, setStatusFilter] = useState("all");

	// Modal States
	const [previewArticle, setPreviewArticle] = useState<GuideArticle | null>(null);
	const [previewLocale, setPreviewLocale] = useState<"id" | "en">("id");
	const [archiveTarget, setArchiveTarget] = useState<GuideArticle | null>(null);

	const articlesQuery = useQuery({
		queryKey: ["agency-guides", debouncedGlobalFilter, categoryFilter, statusFilter],
		queryFn: async () => {
			const res = await getGuideArticles(token, agencyUserId);
			return res.items;
		},
		enabled,
		placeholderData: keepPreviousData,
	});

	const categoriesQuery = useQuery({
		queryKey: ["guide-categories"],
		queryFn: async () => {
			const res = await getGuideCategories(token, agencyUserId);
			return res.items;
		},
		enabled,
		placeholderData: keepPreviousData,
	});

	const transitionMutation = useMutation({
		mutationFn: ({
			articleId,
			action,
		}: {
			articleId: string;
			action: "publish" | "unpublish" | "archive";
		}) => transitionGuideArticle(token, agencyUserId, articleId, action),
		onSuccess: (_, { action }) => {
			toast.success(`Article ${action}ed successfully.`);
			queryClient.invalidateQueries({ queryKey: ["agency-guides"] });
			queryClient.invalidateQueries({ queryKey: ["guide-categories"] });
			setArchiveTarget(null);
		},
		onError: (error, { action }) => {
			toast.error(
				error instanceof Error
					? error.message
					: `Failed to ${action} article.`,
			);
		},
	});

	const categories = useMemo(() => {
		return categoriesQuery.data ?? [];
	}, [categoriesQuery.data]);

	const articles = useMemo(() => {
		const all = articlesQuery.data ?? [];
		const needle = debouncedGlobalFilter.trim().toLowerCase();
		return all.filter((article) => {
			const matchesSearch =
				!needle ||
				article.id.toLowerCase().includes(needle) ||
				article.translations.some(
					(t) =>
						t.title.toLowerCase().includes(needle) ||
						t.summary.toLowerCase().includes(needle),
				);
			const matchesCategory =
				categoryFilter === "all" || article.category_id === categoryFilter;
			const matchesStatus =
				statusFilter === "all" || article.state === statusFilter;

			return matchesSearch && matchesCategory && matchesStatus;
		});
	}, [articlesQuery.data, categoryFilter, debouncedGlobalFilter, statusFilter]);

	const columns: ColumnDef<GuideArticle>[] = useMemo(
		() => [
			{
				accessorKey: "title",
				header: "Article",
				cell: ({ row }) => {
					// Always prioritize Indonesian translation in the table
					const primary = articleTranslation(row.original, "id");
					return (
						<div className="flex flex-col">
							<span className="font-medium text-sm text-foreground">
								{primary.title || row.original.id}
							</span>
							<span className="text-xs text-muted-foreground line-clamp-1 max-w-md">
								{primary.summary || "No summary provided."}
							</span>
						</div>
					);
				},
			},
			{
				accessorKey: "category_id",
				header: "Category",
				meta: { align: "center" },
				cell: ({ row }) => {
					const cat = categories.find((c) => c.id === row.original.category_id);
					return (
						<div className="text-center">
							<Badge variant="outline">
								{cat ? categoryLabel(cat, "id") : row.original.category_id}
							</Badge>
						</div>
					);
				},
			},
			{
				accessorKey: "languages",
				header: "Languages",
				meta: { align: "center" },
				cell: ({ row }) => (
					<div className="flex items-center justify-center gap-1">
						{row.original.translations.map((t) => (
							<span
								key={t.locale}
								className="rounded bg-muted px-1.5 py-0.5 text-[10px] font-mono font-medium text-muted-foreground uppercase"
							>
								{t.locale}
							</span>
						))}
					</div>
				),
			},
			{
				accessorKey: "state",
				header: "Status",
				meta: { align: "center" },
				cell: ({ row }) => (
					<div className="text-center">
						<Badge variant={statusVariant(row.original.state)}>
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
					const article = row.original;
					return (
						<div className="flex items-center justify-end gap-1">
							<Button
								variant="ghost"
								size="icon"
								className="h-7 w-7 text-muted-foreground hover:text-foreground"
								aria-label="Preview"
								title="Preview article"
								onClick={() => {
									setPreviewArticle(article);
									setPreviewLocale("id");
								}}
							>
								<Eye className="h-3.5 w-3.5" />
							</Button>

							<Button
								variant="ghost"
								size="icon"
								className="h-7 w-7"
								aria-label="Edit"
								title="Edit article"
								asChild
							>
								<Link href={`/agency/guides/${article.id}/edit`}>
									<Pencil className="h-3.5 w-3.5" />
								</Link>
							</Button>

							{article.state === "published" ? (
								<Button
									variant="ghost"
									size="icon"
									className="h-7 w-7 text-amber-600 hover:text-amber-700 dark:text-amber-500"
									aria-label="Unpublish"
									title="Unpublish article"
									disabled={transitionMutation.isPending}
									onClick={() =>
										transitionMutation.mutate({
											articleId: article.id,
											action: "unpublish",
										})
									}
								>
									<XCircle className="h-3.5 w-3.5" />
								</Button>
							) : article.state === "archived" ? null : (
								<Button
									variant="ghost"
									size="icon"
									className="h-7 w-7 text-emerald-600 hover:text-emerald-700 dark:text-emerald-500"
									aria-label="Publish"
									title="Publish article"
									disabled={transitionMutation.isPending}
									onClick={() =>
										transitionMutation.mutate({
											articleId: article.id,
											action: "publish",
										})
									}
								>
									<CheckCircle2 className="h-3.5 w-3.5" />
								</Button>
							)}

							{article.state !== "archived" && (
								<Button
									variant="ghost"
									size="icon"
									className="h-7 w-7 text-destructive hover:text-destructive"
									aria-label="Archive"
									title="Archive article"
									disabled={transitionMutation.isPending}
									onClick={() => setArchiveTarget(article)}
								>
									<Archive className="h-3.5 w-3.5" />
								</Button>
							)}
						</div>
					);
				},
				enableSorting: false,
			},
		],
		[categories, transitionMutation],
	);

	const table = useReactTable({
		data: articles,
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

	if (articlesQuery.isPending) {
		return (
			<div className="space-y-3">
				<Skeleton className="h-9 w-full" />
				<Skeleton className="h-64 w-full" />
			</div>
		);
	}

	if (articlesQuery.isError) {
		return (
			<div className="rounded-md border border-destructive/50 bg-destructive/5 p-4 text-sm text-destructive">
				Could not load guide articles: {(articlesQuery.error as Error).message}
			</div>
		);
	}

	const activePreviewTranslation = previewArticle?.translations.find(
		(t) => t.locale === previewLocale,
	);
	const activePreviewCategory = previewArticle
		? categories.find((c) => c.id === previewArticle.category_id)
		: null;

	return (
		<>
			<div className="space-y-4">
				{/* Filter bar + Actions */}
				<div className="flex flex-col gap-3 sm:flex-row sm:items-center">
					<div className="relative flex-1 sm:max-w-xs">
						<Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
						<Input
							placeholder="Search articles..."
							value={globalFilter}
							onChange={(e) => setGlobalFilter(e.target.value)}
							className="pl-9"
						/>
					</div>

					<Select value={categoryFilter} onValueChange={setCategoryFilter}>
						<SelectTrigger className="w-[180px]">
							<SelectValue placeholder="All categories" />
						</SelectTrigger>
						<SelectContent>
							<SelectItem value="all">All categories</SelectItem>
							{categories.map((c) => (
								<SelectItem key={c.id} value={c.id}>
									{categoryLabel(c)}
								</SelectItem>
							))}
						</SelectContent>
					</Select>

					<Select value={statusFilter} onValueChange={setStatusFilter}>
						<SelectTrigger className="w-[160px]">
							<SelectValue placeholder="All statuses" />
						</SelectTrigger>
						<SelectContent>
							<SelectItem value="all">All statuses</SelectItem>
							<SelectItem value="draft">Draft</SelectItem>
							<SelectItem value="published">Published</SelectItem>
							<SelectItem value="unpublished">Unpublished</SelectItem>
							<SelectItem value="archived">Archived</SelectItem>
						</SelectContent>
					</Select>

					<div className="flex items-center gap-2 sm:ml-auto">
						<Button variant="outline" size="sm" asChild className="gap-1.5">
							<Link href="/agency/guides/categories">
								<FolderTree className="h-3.5 w-3.5" /> Manage categories
							</Link>
						</Button>
						<Button size="sm" asChild className="gap-1.5">
							<Link href="/agency/guides/new">
								<Plus className="h-3.5 w-3.5" /> Create article
							</Link>
						</Button>
					</div>
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
										No guide articles found.
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

			{/* Article Preview Modal Dialog (Mobile Frame) */}
			<Dialog
				open={!!previewArticle}
				onOpenChange={(open) => !open && setPreviewArticle(null)}
			>
				<DialogContent className="sm:max-w-[440px] max-h-[96vh] flex flex-col p-4 overflow-y-auto">
					<DialogHeader className="pb-3 border-b">
						<div className="flex items-center justify-between gap-3 pr-8">
							<div>
								<DialogTitle className="text-base font-semibold">Mobile Preview</DialogTitle>
								<DialogDescription className="text-xs">
									Simulated mobile app screen
								</DialogDescription>
							</div>

							{/* Language Switcher Buttons (ID and EN) */}
							<div className="flex items-center gap-1 rounded-md border bg-muted/50 p-0.5 shrink-0">
								<button
									type="button"
									onClick={() => setPreviewLocale("id")}
									className={`rounded px-2.5 py-0.5 text-xs font-semibold transition-colors ${
										previewLocale === "id"
											? "bg-primary text-primary-foreground shadow-xs"
											: "text-muted-foreground hover:text-foreground"
									}`}
								>
									ID
								</button>
								<button
									type="button"
									onClick={() => setPreviewLocale("en")}
									className={`rounded px-2.5 py-0.5 text-xs font-semibold transition-colors ${
										previewLocale === "en"
											? "bg-primary text-primary-foreground shadow-xs"
											: "text-muted-foreground hover:text-foreground"
									}`}
								>
									EN
								</button>
							</div>
						</div>
					</DialogHeader>

					{/* Mobile Device Frame with Realistic Smartphone Aspect Ratio */}
					<div className="py-2 flex justify-center">
						<div className="w-[320px] h-[580px] sm:w-[340px] sm:h-[620px] rounded-[2.8rem] border-[6px] border-slate-900 dark:border-slate-700 bg-background shadow-2xl p-4 flex flex-col">
							{/* Phone Notch */}
							<div className="mx-auto mb-3 h-4 w-24 rounded-full bg-slate-900 dark:bg-slate-700 flex items-center justify-center shrink-0">
								<div className="h-1.5 w-1.5 rounded-full bg-slate-700 dark:bg-slate-500" />
							</div>

							{/* Screen Reader Area (Flex-1 fills full phone screen) */}
							<div className="flex-1 overflow-y-auto pr-1 space-y-3 text-left">
								{activePreviewTranslation &&
								(activePreviewTranslation.title.trim() ||
									activePreviewTranslation.blocks.length > 0) ? (
									<div className="space-y-3">
										<div className="flex flex-wrap items-center gap-1.5">
											{activePreviewCategory && (
												<span className="rounded bg-primary/10 px-2 py-0.5 text-[10px] font-semibold text-primary uppercase tracking-wide">
													{categoryLabel(activePreviewCategory, previewLocale)}
												</span>
											)}
											{previewArticle && (
												<span className="rounded bg-muted px-1.5 py-0.5 text-[10px] text-muted-foreground uppercase">
													{previewArticle.state}
												</span>
											)}
										</div>

										<h2 className="text-base font-bold text-foreground leading-snug">
											{activePreviewTranslation.title || "Untitled Article"}
										</h2>

										{activePreviewTranslation.summary && (
											<p className="text-xs text-muted-foreground leading-relaxed italic border-b pb-2.5">
												{activePreviewTranslation.summary}
											</p>
										)}

										<div className="space-y-2.5 pt-0.5">
											{activePreviewTranslation.blocks.map((block, idx) => (
												<PreviewBlockRenderer
													key={`${block.type}-${idx}`}
													block={block}
													token={token}
													agencyUserId={agencyUserId}
												/>
											))}
										</div>
									</div>
								) : (
									<div className="rounded-lg border border-dashed p-6 text-center text-xs text-muted-foreground my-8">
										No {previewLocale === "id" ? "Indonesian (ID)" : "English (EN)"}{" "}
										translation available for this article.
									</div>
								)}
							</div>

							{/* Home Indicator Bar */}
							<div className="mx-auto mt-3 h-1 w-20 rounded-full bg-slate-300 dark:bg-slate-600 shrink-0" />
						</div>
					</div>

					<DialogFooter className="pt-2 border-t">
						<Button variant="outline" size="sm" onClick={() => setPreviewArticle(null)} className="w-full">
							Close Preview
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
						<AlertDialogTitle>Archive guide article?</AlertDialogTitle>
						<AlertDialogDescription>
							Are you sure you want to archive{" "}
							<span className="font-semibold text-foreground">
								"{archiveTarget ? articleTranslation(archiveTarget, "id").title : ""}"
							</span>
							? It will be retired and no longer accessible to farmers.
						</AlertDialogDescription>
					</AlertDialogHeader>
					<AlertDialogFooter>
						<AlertDialogCancel>Cancel</AlertDialogCancel>
						<AlertDialogAction
							onClick={() =>
								archiveTarget &&
								transitionMutation.mutate({
									articleId: archiveTarget.id,
									action: "archive",
								})
							}
							className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
						>
							{transitionMutation.isPending ? "Archiving..." : "Archive"}
						</AlertDialogAction>
					</AlertDialogFooter>
				</AlertDialogContent>
			</AlertDialog>
		</>
	);
}

function PreviewBlockRenderer({
	block,
	token,
	agencyUserId,
}: {
	block: GuideBlock;
	token: string;
	agencyUserId: string;
}) {
	if (block.type === "heading") {
		return <h3 className="text-base font-semibold text-foreground mt-3">{block.text || "Heading"}</h3>;
	}
	if (block.type === "bullet_list") {
		return (
			<ul className="list-disc pl-5 text-sm space-y-1 text-foreground">
				{(block.items ?? []).map((item, i) => (
					<li key={i}>{item}</li>
				))}
			</ul>
		);
	}
	if (block.type === "image") {
		return (
			<PreviewImage
				mediaId={block.media_id}
				alt={block.alt || "Article image"}
				token={token}
				agencyUserId={agencyUserId}
			/>
		);
	}
	return <p className="text-sm leading-relaxed text-foreground whitespace-pre-wrap">{block.text}</p>;
}

function PreviewImage({
	mediaId,
	alt,
	token,
	agencyUserId,
}: {
	mediaId?: string;
	alt: string;
	token: string;
	agencyUserId: string;
}) {
	const [source, setSource] = useState<string>();
	const [failed, setFailed] = useState(false);

	useEffect(() => {
		if (!mediaId) return;
		let current = true;
		let objectUrl: string | undefined;
		setSource(undefined);
		setFailed(false);
		void getGuideMediaPreview(token, agencyUserId, mediaId)
			.then((blob) => {
				if (!current) return;
				objectUrl = URL.createObjectURL(blob);
				setSource(objectUrl);
			})
			.catch(() => current && setFailed(true));
		return () => {
			current = false;
			if (objectUrl) URL.revokeObjectURL(objectUrl);
		};
	}, [agencyUserId, mediaId, token]);

	if (!mediaId || failed) {
		return (
			<div className="rounded border border-dashed bg-muted p-4 text-center text-xs text-muted-foreground">
				Image unavailable: {alt}
			</div>
		);
	}
	if (!source) {
		return (
			<div className="rounded bg-muted p-4 text-center text-xs text-muted-foreground animate-pulse">
				Loading image...
			</div>
		);
	}
	return (
		<img
			className="w-full rounded-md object-cover shadow-xs my-2"
			src={source}
			alt={alt}
		/>
	);
}
