"use client";

import { useAgencySession } from "@/src/features/auth/session-context";
import {
	getGuideArticle,
	getGuideCategories,
	getGuideMediaPreview,
	saveGuideArticle,
	transitionGuideArticle,
} from "@/src/shared/api/client";
import type {
	GuideArticle,
	GuideBlock,
	GuideCategory,
	GuideTranslation,
} from "@/src/shared/types/api";
import { Badge } from "@/src/shared/ui/badge";
import { Button } from "@/src/shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/src/shared/ui/card";
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
	ArrowDown,
	ArrowLeft,
	ArrowUp,
	Eye,
	EyeOff,
	FileText,
	Globe,
	Heading,
	Image as ImageIcon,
	List,
	Loader2,
	Plus,
	Trash2,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";

const emptyBlock: GuideBlock = { type: "paragraph", text: "" };

const emptyTranslation = (locale: string): GuideTranslation => ({
	locale,
	title: "",
	summary: "",
	blocks: [{ ...emptyBlock }],
});

interface ArticleEditorPageProps {
	mode: "create" | "edit";
	articleId?: string;
}

export function ArticleEditorPage({ mode, articleId }: ArticleEditorPageProps) {
	const router = useRouter();
	const { token, agency, agencyUserId } = useAgencySession();

	const [loading, setLoading] = useState(true);
	const [busy, setBusy] = useState(false);
	const [categories, setCategories] = useState<GuideCategory[]>([]);
	const [article, setArticle] = useState<GuideArticle | null>(null);

	const [translations, setTranslations] = useState<GuideTranslation[]>([
		emptyTranslation("id"),
	]);
	const [activeLocale, setActiveLocale] = useState("id");
	const [categoryId, setCategoryId] = useState("");
	const [preview, setPreview] = useState(false);

	const loadData = useCallback(async () => {
		if (!token || !agencyUserId || agency?.role !== "admin") return;
		setLoading(true);
		try {
			const [categoryData, existingArticle] = await Promise.all([
				getGuideCategories(token, agencyUserId),
				mode === "edit" && articleId
					? getGuideArticle(token, agencyUserId, articleId)
					: Promise.resolve(null),
			]);

			setCategories(categoryData.items);

			if (existingArticle) {
				setArticle(existingArticle);
				setCategoryId(existingArticle.category_id);
				const idTrans =
					existingArticle.translations.find((item) => item.locale === "id") ??
					emptyTranslation("id");
				const enTrans =
					existingArticle.translations.find((item) => item.locale === "en") ??
					emptyTranslation("en");
				setTranslations([idTrans, enTrans]);
				setActiveLocale("id");
			} else {
				const defaultCat =
					categoryData.items.find((item) => item.state === "active")?.id ??
					"guide-category-umum";
				setCategoryId(defaultCat);
				setTranslations([emptyTranslation("id"), emptyTranslation("en")]);
			}
		} catch (cause) {
			toast.error(cause instanceof Error ? cause.message : "Failed to load article data");
		} finally {
			setLoading(false);
		}
	}, [agency?.role, agencyUserId, articleId, mode, token]);

	useEffect(() => {
		void loadData();
	}, [loadData]);

	if (agency?.role !== "admin") {
		return (
			<div className="rounded-lg border border-destructive/50 bg-destructive/10 p-6 text-center">
				<p className="font-medium text-destructive">
					Only global administrators can access the Guide CMS.
				</p>
			</div>
		);
	}

	if (loading) {
		return (
			<div className="space-y-6">
				<div className="flex items-center gap-4">
					<Skeleton className="h-9 w-24" />
					<Skeleton className="h-8 w-48" />
				</div>
				<Card>
					<CardContent className="space-y-4 pt-6">
						<Skeleton className="h-10 w-full" />
						<Skeleton className="h-24 w-full" />
						<Skeleton className="h-40 w-full" />
					</CardContent>
				</Card>
			</div>
		);
	}

	const active =
		translations.find((item) => item.locale === activeLocale) ?? translations[0];

	const updateActiveTranslation = (patch: Partial<GuideTranslation>) => {
		if (!active) return;
		setTranslations((prev) =>
			prev.map((item) =>
				item.locale === activeLocale ? { ...item, ...patch } : item,
			),
		);
	};

	const handleSave = async (andPublish = false) => {
		if (!token || !agencyUserId) return;
		if (!categoryId) {
			toast.error("Please select a category.");
			return;
		}
		const idTrans = translations.find((item) => item.locale === "id");
		if (!idTrans?.title.trim()) {
			toast.error("Indonesian title (ID) is required.");
			return;
		}

		// Include English translation if title or blocks have content
		const enTrans = translations.find((item) => item.locale === "en");
		const hasEn = Boolean(
			enTrans &&
				(enTrans.title.trim() ||
					enTrans.summary.trim() ||
					enTrans.blocks.some((b) => b.text?.trim() || b.items?.length)),
		);

		const savePayload = [idTrans];
		if (hasEn && enTrans) {
			savePayload.push(enTrans);
		}

		setBusy(true);
		try {
			const saved = await saveGuideArticle(token, agencyUserId, {
				id: mode === "edit" && articleId ? articleId : undefined,
				category_id: categoryId,
				translations: savePayload,
			});

			if (andPublish) {
				await transitionGuideArticle(token, agencyUserId, saved.id, "publish");
				toast.success("Article saved and published.");
			} else {
				toast.success(
					mode === "edit"
						? "Article updated successfully."
						: "Article created successfully as draft.",
				);
			}

			router.push("/agency/guides");
		} catch (cause) {
			toast.error(cause instanceof Error ? cause.message : "Failed to save article");
		} finally {
			setBusy(false);
		}
	};

	const handleTransition = async (action: "publish" | "unpublish" | "archive") => {
		if (!token || !agencyUserId || !articleId) return;
		setBusy(true);
		try {
			await transitionGuideArticle(token, agencyUserId, articleId, action);
			toast.success(`Article ${action}ed successfully.`);
			router.push("/agency/guides");
		} catch (cause) {
			toast.error(cause instanceof Error ? cause.message : `Failed to ${action} article`);
		} finally {
			setBusy(false);
		}
	};

	return (
		<div className="space-y-6">
			{/* Top Bar Navigation & Header */}
			<div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
				<div className="space-y-1">
					<div className="flex items-center gap-2">
						<Button variant="ghost" size="sm" asChild className="-ml-2">
							<Link href="/agency/guides">
								<ArrowLeft className="mr-1 h-4 w-4" />
								Back to Guides
							</Link>
						</Button>
					</div>
					<div className="flex items-center gap-3">
						<h1 className="text-2xl font-semibold tracking-tight">
							{mode === "create" ? "Create Guide Article" : "Edit Guide Article"}
						</h1>
						{article && (
							<Badge
								variant={
									article.state === "published"
										? "default"
										: article.state === "archived"
											? "destructive"
											: "secondary"
								}
								className="capitalize"
							>
								{article.state}
							</Badge>
						)}
					</div>
					<p className="text-sm text-muted-foreground">
						{mode === "create"
							? "Create and organize instructional content for farmers across web and mobile."
							: "Update translations and content structure for this guide article."}
					</p>
				</div>

				<div className="flex items-center gap-2">
					<Button
						type="button"
						variant="outline"
						size="sm"
						onClick={() => setPreview(!preview)}
					>
						{preview ? (
							<>
								<EyeOff className="mr-1.5 h-4 w-4" />
								Edit Mode
							</>
						) : (
							<>
								<Eye className="mr-1.5 h-4 w-4" />
								Live Preview
							</>
						)}
					</Button>
					<Button
						type="button"
						variant="outline"
						size="sm"
						asChild
					>
						<Link href="/agency/guides">Cancel</Link>
					</Button>
					<Button
						type="button"
						size="sm"
						disabled={busy}
						onClick={() => void handleSave(false)}
					>
						{busy && <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />}
						Save Draft
					</Button>
					{mode === "edit" && article?.state === "draft" && (
						<Button
							type="button"
							size="sm"
							variant="default"
							disabled={busy}
							onClick={() => void handleSave(true)}
						>
							Save & Publish
						</Button>
					)}
				</div>
			</div>

			{/* Main Editor Layout */}
			<div className={`grid gap-6 ${preview ? "lg:grid-cols-2" : "grid-cols-1"}`}>
				{/* Editor Panel */}
				<div className="space-y-6">
					{/* Category Selection Card */}
					<Card>
						<CardHeader className="pb-3">
							<CardTitle className="text-base">Article Category</CardTitle>
							<CardDescription>
								Assign this article to an active guide category for farmer discovery.
							</CardDescription>
						</CardHeader>
						<CardContent>
							<div className="max-w-md space-y-2">
								<Label htmlFor="guide-category-select">Category</Label>
								<Select value={categoryId} onValueChange={setCategoryId}>
									<SelectTrigger id="guide-category-select" className="w-full">
										<SelectValue placeholder="Select a category" />
									</SelectTrigger>
									<SelectContent>
										{categories
											.filter((item) => item.state === "active")
											.map((cat) => (
												<SelectItem key={cat.id} value={cat.id}>
													{categoryLabel(cat)}
												</SelectItem>
											))}
									</SelectContent>
								</Select>
							</div>
						</CardContent>
					</Card>

					{/* Translation Tabs & Content */}
					<Card>
						<CardHeader className="pb-3">
							<div>
								<CardTitle className="text-base">Content & Translations</CardTitle>
								<CardDescription>
									Manage Indonesian (ID) and English (EN) titles, summaries, and content blocks.
								</CardDescription>
							</div>

							{/* Locale Switcher Tabs (ID & EN only) */}
							<div className="mt-3 flex gap-2 border-b pb-2">
								<button
									type="button"
									onClick={() => setActiveLocale("id")}
									className={`inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
										activeLocale === "id"
											? "bg-primary text-primary-foreground shadow-xs"
											: "bg-muted text-muted-foreground hover:bg-muted/80 hover:text-foreground"
									}`}
								>
									<Globe className="h-3.5 w-3.5" />
									Indonesian (ID)
									{translations.find((t) => t.locale === "id")?.title.trim() && (
										<span className="ml-1 text-[10px] opacity-75">✓</span>
									)}
								</button>
								<button
									type="button"
									onClick={() => setActiveLocale("en")}
									className={`inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
										activeLocale === "en"
											? "bg-primary text-primary-foreground shadow-xs"
											: "bg-muted text-muted-foreground hover:bg-muted/80 hover:text-foreground"
									}`}
								>
									<Globe className="h-3.5 w-3.5" />
									English (EN)
									{translations.find((t) => t.locale === "en")?.title.trim() && (
										<span className="ml-1 text-[10px] opacity-75">✓</span>
									)}
								</button>
							</div>
						</CardHeader>

						<CardContent className="space-y-4">
							{active ? (
								<>
									<div className="space-y-2">
										<Label htmlFor="article-title">
											Title ({activeLocale.toUpperCase()})
										</Label>
										<Input
											id="article-title"
											value={active.title}
											maxLength={160}
											placeholder="e.g. Panduan Pencegahan PMK pada Sapi Perah"
											onChange={(e) => updateActiveTranslation({ title: e.target.value })}
										/>
										<p className="text-right text-xs text-muted-foreground">
											{active.title.length}/160 characters
										</p>
									</div>

									<div className="space-y-2">
										<Label htmlFor="article-summary">
											Summary ({activeLocale.toUpperCase()})
										</Label>
										<Textarea
											id="article-summary"
											value={active.summary}
											maxLength={500}
											placeholder="Brief overview explaining what the farmer will learn..."
											className="min-h-20"
											onChange={(e) =>
												updateActiveTranslation({ summary: e.target.value })
											}
										/>
										<p className="text-right text-xs text-muted-foreground">
											{active.summary.length}/500 characters
										</p>
									</div>

									{/* Content Blocks Section */}
									<div className="space-y-3 pt-2">
										<div className="flex items-center justify-between">
											<Label className="text-sm font-semibold">
												Content Blocks ({active.blocks.length})
											</Label>
											<div className="flex flex-wrap gap-1">
												<Button
													type="button"
													variant="outline"
													size="xs"
													onClick={() =>
														updateActiveTranslation({
															blocks: [...active.blocks, { type: "heading", text: "" }],
														})
													}
												>
													<Heading className="mr-1 h-3 w-3" />
													+ Heading
												</Button>
												<Button
													type="button"
													variant="outline"
													size="xs"
													onClick={() =>
														updateActiveTranslation({
															blocks: [...active.blocks, { type: "paragraph", text: "" }],
														})
													}
												>
													<FileText className="mr-1 h-3 w-3" />
													+ Paragraph
												</Button>
												<Button
													type="button"
													variant="outline"
													size="xs"
													onClick={() =>
														updateActiveTranslation({
															blocks: [...active.blocks, { type: "bullet_list", items: [] }],
														})
													}
												>
													<List className="mr-1 h-3 w-3" />
													+ Bullet List
												</Button>
											</div>
										</div>

										<div className="space-y-3">
											{active.blocks.map((block, index) => (
												<BlockEditorItem
													key={`${block.type}-${index}`}
													block={block}
													index={index}
													total={active.blocks.length}
													onChange={(updated) =>
														updateActiveTranslation({
															blocks: active.blocks.map((b, i) =>
																i === index ? updated : b,
															),
														})
													}
													onRemove={() =>
														updateActiveTranslation({
															blocks: active.blocks.filter((_, i) => i !== index),
														})
													}
													onMove={(offset) => {
														const target = index + offset;
														if (target < 0 || target >= active.blocks.length) return;
														const next = [...active.blocks];
														[next[index], next[target]] = [next[target], next[index]];
														updateActiveTranslation({ blocks: next });
													}}
												/>
											))}
										</div>
									</div>
								</>
							) : null}
						</CardContent>
					</Card>

					{/* Bottom Actions Card */}
					<Card>
						<CardContent className="flex flex-wrap items-center justify-between gap-3 pt-6">
							<div className="flex items-center gap-2">
								{mode === "edit" && article && (
									<>
										{article.state === "published" ? (
											<Button
												type="button"
												variant="outline"
												size="sm"
												disabled={busy}
												onClick={() => void handleTransition("unpublish")}
											>
												Unpublish Article
											</Button>
										) : article.state === "archived" ? null : (
											<Button
												type="button"
												variant="outline"
												size="sm"
												disabled={busy}
												onClick={() => void handleTransition("publish")}
											>
												Publish Article
											</Button>
										)}
										{article.state !== "archived" && (
											<Button
												type="button"
												variant="ghost"
												size="sm"
												className="text-destructive hover:text-destructive"
												disabled={busy}
												onClick={() => void handleTransition("archive")}
											>
												Archive Article
											</Button>
										)}
									</>
								)}
							</div>

							<div className="flex items-center gap-2">
								<Button variant="outline" size="sm" asChild>
									<Link href="/agency/guides">Cancel</Link>
								</Button>
								<Button
									type="button"
									size="sm"
									disabled={busy}
									onClick={() => void handleSave(false)}
								>
									{busy && <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />}
									Save Draft
								</Button>
							</div>
						</CardContent>
					</Card>
				</div>

				{/* Live Mobile Preview */}
				{preview && (
					<div className="sticky top-6 self-start">
						<Card className="border-2 border-primary/20 shadow-md">
							<CardHeader className="pb-3 border-b bg-muted/20">
								<div className="flex items-center justify-between">
									<div>
										<CardTitle className="text-sm font-semibold">Farmer Mobile Preview</CardTitle>
										<CardDescription className="text-xs">
											Simulating app view for locale: {activeLocale.toUpperCase()}
										</CardDescription>
									</div>
									<Badge variant="outline" className="text-xs">
										{activeLocale}
									</Badge>
								</div>
							</CardHeader>
							<CardContent className="p-6">
								<div className="mx-auto max-w-sm rounded-[2.5rem] border-4 border-slate-800 bg-background p-4 shadow-xl">
									<div className="mx-auto mb-4 h-4 w-28 rounded-full bg-slate-800" />
									<div className="max-h-[560px] overflow-y-auto pr-1">
										<div className="mb-2">
											<span className="rounded bg-primary/10 px-2 py-0.5 text-[10px] font-semibold text-primary uppercase">
												{categories.find((c) => c.id === categoryId)
													? categoryLabel(categories.find((c) => c.id === categoryId)!)
													: "Guide"}
											</span>
										</div>
										<h2 className="text-lg font-bold leading-tight tracking-tight">
											{active?.title || "Untitled Guide Article"}
										</h2>
										<p className="mt-2 text-xs leading-relaxed text-muted-foreground border-b pb-3">
											{active?.summary || "No summary provided yet."}
										</p>
										<div className="mt-3 space-y-3">
											{active?.blocks.map((block, idx) => (
												<BlockRenderer
													key={`${block.type}-${idx}`}
													block={block}
													token={token}
													agencyUserId={agencyUserId}
												/>
											))}
										</div>
									</div>
								</div>
							</CardContent>
						</Card>
					</div>
				)}
			</div>
		</div>
	);
}

function BlockEditorItem({
	block,
	index,
	total,
	onChange,
	onRemove,
	onMove,
}: {
	block: GuideBlock;
	index: number;
	total: number;
	onChange: (block: GuideBlock) => void;
	onRemove: () => void;
	onMove: (offset: number) => void;
}) {
	return (
		<div className="rounded-lg border bg-card p-3 shadow-xs">
			<div className="flex items-center justify-between pb-2 border-b mb-2 text-xs text-muted-foreground">
				<div className="flex items-center gap-1.5 font-medium text-foreground">
					{block.type === "heading" && <Heading className="h-3.5 w-3.5" />}
					{block.type === "paragraph" && <FileText className="h-3.5 w-3.5" />}
					{block.type === "bullet_list" && <List className="h-3.5 w-3.5" />}
					{block.type === "image" && <ImageIcon className="h-3.5 w-3.5" />}
					<span className="capitalize">{block.type.replace("_", " ")} Block</span>
				</div>
				<div className="flex items-center gap-1">
					<Button
						type="button"
						variant="ghost"
						size="icon-xs"
						disabled={index === 0}
						onClick={() => onMove(-1)}
						title="Move block up"
					>
						<ArrowUp className="h-3 w-3" />
					</Button>
					<Button
						type="button"
						variant="ghost"
						size="icon-xs"
						disabled={index === total - 1}
						onClick={() => onMove(1)}
						title="Move block down"
					>
						<ArrowDown className="h-3 w-3" />
					</Button>
					<Button
						type="button"
						variant="ghost"
						size="icon-xs"
						className="text-destructive hover:text-destructive"
						onClick={onRemove}
						title="Delete block"
					>
						<Trash2 className="h-3 w-3" />
					</Button>
				</div>
			</div>

			{block.type === "heading" && (
				<Input
					value={block.text ?? ""}
					placeholder="Enter heading text..."
					onChange={(e) => onChange({ ...block, text: e.target.value })}
				/>
			)}

			{block.type === "paragraph" && (
				<Textarea
					value={block.text ?? ""}
					placeholder="Enter paragraph text..."
					rows={3}
					onChange={(e) => onChange({ ...block, text: e.target.value })}
				/>
			)}

			{block.type === "bullet_list" && (
				<Textarea
					value={(block.items ?? []).join("\n")}
					placeholder="Enter list items (one per line)..."
					rows={4}
					onChange={(e) =>
						onChange({
							...block,
							items: e.target.value.split("\n").filter(Boolean),
						})
					}
				/>
			)}

			{block.type === "image" && (
				<div className="rounded-md border border-dashed p-3 text-xs text-muted-foreground">
					Legacy image block (Media ID: {block.media_id || "none"}). You can remove this block using the delete button.
				</div>
			)}
		</div>
	);
}

function BlockRenderer({
	block,
	token,
	agencyUserId,
}: {
	block: GuideBlock;
	token: string;
	agencyUserId: string;
}) {
	if (block.type === "heading") {
		return <h3 className="text-sm font-bold text-foreground">{block.text || "Heading"}</h3>;
	}
	if (block.type === "bullet_list") {
		return (
			<ul className="list-disc pl-4 text-xs text-foreground space-y-1">
				{(block.items ?? []).map((item, i) => (
					<li key={i}>{item}</li>
				))}
			</ul>
		);
	}
	if (block.type === "image") {
		return (
			<GuideImagePreview
				mediaId={block.media_id}
				alt={block.alt || "Guide illustration"}
				token={token}
				agencyUserId={agencyUserId}
			/>
		);
	}
	return <p className="text-xs leading-relaxed text-foreground">{block.text}</p>;
}

function GuideImagePreview({
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
			className="w-full rounded-md object-cover shadow-xs"
			src={source}
			alt={alt}
		/>
	);
}

function categoryLabel(category: GuideCategory, locale = "id") {
	return (
		category.translations.find((item) => item.locale === locale)?.label ??
		category.translations.find((item) => item.locale === "en")?.label ??
		category.translations[0]?.label ??
		"General"
	);
}
