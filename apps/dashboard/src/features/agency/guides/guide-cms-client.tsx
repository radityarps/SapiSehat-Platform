"use client";

import { useAgencySession } from "@/src/features/auth/session-context";
import {
	archiveGuideCategory,
	getGuideArticles,
	getGuideAuditEvents,
	getGuideCategories,
	getGuideMedia,
	getGuideMediaPreview,
	saveGuideArticle,
	saveGuideCategory,
	transitionGuideArticle,
	uploadGuideMedia,
} from "@/src/shared/api/client";
import type {
	GuideArticle,
	GuideAuditEvent,
	GuideBlock,
	GuideCategory,
	GuideMedia,
	GuideTranslation,
} from "@/src/shared/types/api";
import { useCallback, useEffect, useMemo, useState } from "react";

const emptyBlock: GuideBlock = { type: "paragraph", text: "" };
const emptyTranslation = (locale: string): GuideTranslation => ({
	locale,
	title: "",
	summary: "",
	blocks: [{ ...emptyBlock }],
});

export function GuideCmsClient() {
	const { token, agency, agencyUserId } = useAgencySession();
	const [articles, setArticles] = useState<GuideArticle[]>([]);
	const [categories, setCategories] = useState<GuideCategory[]>([]);
	const [media, setMedia] = useState<GuideMedia[]>([]);
	const [events, setEvents] = useState<GuideAuditEvent[]>([]);
	const [editing, setEditing] = useState<GuideArticle | null>(null);
	const [search, setSearch] = useState("");
	const [category, setCategory] = useState("");
	const [locale, setLocale] = useState("");
	const [state, setState] = useState("");
	const [error, setError] = useState("");

	const reload = useCallback(async () => {
		if (!token || !agencyUserId || agency?.role !== "admin") return;
		try {
			const [articleData, categoryData, mediaData, auditData] = await Promise.all([
				getGuideArticles(token, agencyUserId),
				getGuideCategories(token, agencyUserId),
				getGuideMedia(token, agencyUserId),
				getGuideAuditEvents(token, agencyUserId),
			]);
			setArticles(articleData.items);
			setCategories(categoryData.items);
			setMedia(mediaData.items);
			setEvents(auditData.items);
			setError("");
		} catch (cause) {
			setError(message(cause));
		}
	}, [agency?.role, agencyUserId, token]);

	useEffect(() => void reload(), [reload]);
	const visible = useMemo(() => {
		const needle = search.trim().toLowerCase();
		return articles.filter(
			(article) =>
				(!needle ||
					article.translations.some((item) =>
						item.title.toLowerCase().includes(needle),
					)) &&
				(!category || article.category_id === category) &&
				(!locale || article.translations.some((item) => item.locale === locale)) &&
				(!state || article.state === state),
		);
	}, [articles, category, locale, search, state]);

	if (agency?.role !== "admin")
		return (
			<p className="rounded-md border border-destructive p-4">
				Hanya global admin yang dapat membuka CMS.
			</p>
		);
	return (
		<div className="grid gap-6 xl:grid-cols-[2fr_1fr]">
			<div className="space-y-4">
				{error && (
					<p
						role="alert"
						className="rounded-md border border-destructive p-3 text-sm"
					>
						{error}
					</p>
				)}
				<div className="grid gap-2 md:grid-cols-5">
					<input
						aria-label="Cari Guide Article"
						value={search}
						onChange={(event) => setSearch(event.target.value)}
						placeholder="Cari judul..."
						className="rounded-md border px-3 py-2"
					/>
					<select
						aria-label="Filter kategori"
						value={category}
						onChange={(event) => setCategory(event.target.value)}
						className="rounded-md border px-2"
					>
						<option value="">Semua kategori</option>
						{categories.map((item) => (
							<option key={item.id} value={item.id}>
								{categoryLabel(item)}
							</option>
						))}
					</select>
					<input
						aria-label="Filter locale"
						value={locale}
						onChange={(event) => setLocale(event.target.value)}
						placeholder="Locale (id/en)"
						className="rounded-md border px-3 py-2"
					/>
					<select
						aria-label="Filter lifecycle"
						value={state}
						onChange={(event) => setState(event.target.value)}
						className="rounded-md border px-2"
					>
						<option value="">Semua state</option>
						{["draft", "published", "unpublished", "archived"].map((value) => (
							<option key={value}>{value}</option>
						))}
					</select>
					<button
						type="button"
						onClick={() => setEditing(newDraft(categories))}
						className="rounded-md bg-primary px-4 py-2 text-primary-foreground"
					>
						Artikel baru
					</button>
				</div>
				{editing && (
					<ArticleEditor
						article={editing}
						categories={categories}
						media={media}
						token={token}
						agencyUserId={agencyUserId}
						onCancel={() => setEditing(null)}
						onSaved={async () => {
							setEditing(null);
							await reload();
						}}
						onError={setError}
					/>
				)}
				<div className="space-y-2">
					{visible.map((article) => (
						<ArticleRow
							key={article.id}
							article={article}
							edit={() => setEditing(article)}
							run={async (action) => {
								try {
									await transitionGuideArticle(token, agencyUserId, article.id, action);
									await reload();
								} catch (cause) {
									setError(message(cause));
								}
							}}
						/>
					))}
				</div>
			</div>
			<aside className="space-y-6">
				<CategoryManager
					categories={categories}
					token={token}
					agencyUserId={agencyUserId}
					reload={reload}
					onError={setError}
				/>
				<section className="rounded-md border p-4">
					<h2 className="font-semibold">Editorial audit</h2>
					<ul className="mt-3 space-y-2 text-sm">
						{events.slice(0, 12).map((event) => (
							<li key={event.id}>
								<strong>{event.action}</strong> {event.target_type}
								<br />
								<span className="text-muted-foreground">{event.target_id}</span>
							</li>
						))}
					</ul>
				</section>
			</aside>
		</div>
	);
}

function ArticleRow({
	article,
	edit,
	run,
}: {
	article: GuideArticle;
	edit: () => void;
	run: (action: "publish" | "unpublish" | "archive") => Promise<void>;
}) {
	const value = articleTranslation(article, "id");
	return (
		<div className="rounded-md border p-4">
			<div className="flex flex-wrap items-center gap-2">
				<strong className="flex-1">{value.title}</strong>
				<span className="rounded bg-muted px-2 py-1 text-xs">{article.state}</span>
				<button type="button" className="underline" onClick={edit}>
					Edit
				</button>
				{article.state === "published" ? (
					<Action label="Unpublish" run={() => run("unpublish")} />
				) : article.state === "archived" ? null : (
					<Action label="Publish" run={() => run("publish")} />
				)}
				{article.state !== "archived" && (
					<Action label="Archive" run={() => run("archive")} />
				)}
			</div>
			<p className="mt-2 text-sm text-muted-foreground">{value.summary}</p>
		</div>
	);
}

function ArticleEditor({
	article,
	categories,
	media,
	token,
	agencyUserId,
	onCancel,
	onSaved,
	onError,
}: {
	article: GuideArticle;
	categories: GuideCategory[];
	media: GuideMedia[];
	token: string;
	agencyUserId: string;
	onCancel: () => void;
	onSaved: () => Promise<void>;
	onError: (value: string) => void;
}) {
	const [translations, setTranslations] = useState(
		article.translations.length
			? structuredClone(article.translations)
			: [emptyTranslation("id")],
	);
	const [activeLocale, setActiveLocale] = useState(
		translations[0]?.locale ?? "id",
	);
	const [categoryId, setCategoryId] = useState(article.category_id);
	const [preview, setPreview] = useState(false);
	const [availableMedia, setAvailableMedia] = useState(media);
	const [busy, setBusy] = useState(false);
	const active =
		translations.find((item) => item.locale === activeLocale) ?? translations[0];
	const update = (patch: Partial<GuideTranslation>) =>
		setTranslations(
			translations.map((item) =>
				item.locale === activeLocale ? { ...item, ...patch } : item,
			),
		);
	const save = async () => {
		setBusy(true);
		try {
			await saveGuideArticle(token, agencyUserId, {
				id: article.id.startsWith("new-") ? undefined : article.id,
				category_id: categoryId,
				translations,
			});
			await onSaved();
		} catch (cause) {
			onError(message(cause));
		} finally {
			setBusy(false);
		}
	};
	if (!active) return null;
	return (
		<section className="space-y-3 rounded-md border p-4">
			<div className="flex flex-wrap items-center gap-2">
				<h2 className="flex-1 font-semibold">Editor translation</h2>
				<select
					aria-label="Translation aktif"
					value={activeLocale}
					onChange={(event) => setActiveLocale(event.target.value)}
					className="rounded border px-2"
				>
					{translations.map((item) => (
						<option key={item.locale}>{item.locale}</option>
					))}
				</select>
				<button
					type="button"
					className="underline"
					onClick={() => {
						const value = prompt("Locale baru (contoh: en)")?.trim();
						if (value && !translations.some((item) => item.locale === value)) {
							setTranslations([...translations, emptyTranslation(value)]);
							setActiveLocale(value);
						}
					}}
				>
					Tambah locale
				</button>
				{activeLocale !== "id" && (
					<button
						type="button"
						className="underline"
						onClick={() => {
							setTranslations(
								translations.filter((item) => item.locale !== activeLocale),
							);
							setActiveLocale("id");
						}}
					>
						Hapus locale
					</button>
				)}
				<button
					type="button"
					className="underline"
					onClick={() => setPreview(!preview)}
				>
					{preview ? "Edit" : "Preview"}
				</button>
			</div>
			{preview ? (
				<div className="mx-auto max-w-sm rounded-3xl border p-5">
					<h2 className="text-xl font-bold">{active.title}</h2>
					<p className="my-3 text-muted-foreground">{active.summary}</p>
					{active.blocks.map((block, index) => (
						<BlockPreview
							key={`${block.type}-${index}`}
							block={block}
							token={token}
							agencyUserId={agencyUserId}
						/>
					))}
				</div>
			) : (
				<>
					<input
						aria-label="Judul translation"
						value={active.title}
						maxLength={160}
						onChange={(event) => update({ title: event.target.value })}
						placeholder="Judul"
						className="w-full rounded-md border px-3 py-2"
					/>
					<textarea
						aria-label="Ringkasan translation"
						value={active.summary}
						maxLength={500}
						onChange={(event) => update({ summary: event.target.value })}
						placeholder="Ringkasan"
						className="w-full rounded-md border px-3 py-2"
					/>
					<select
						aria-label="Guide Category"
						value={categoryId}
						onChange={(event) => setCategoryId(event.target.value)}
						className="w-full rounded-md border px-3 py-2"
					>
						{categories
							.filter((item) => item.state === "active")
							.map((item) => (
								<option key={item.id} value={item.id}>
									{categoryLabel(item)}
								</option>
							))}
					</select>
					<label className="block rounded-md border p-3 text-sm">
						Unggah gambar (JPEG/PNG/WebP, maks. 5 MB)
						<input
							type="file"
							accept="image/jpeg,image/png,image/webp"
							className="mt-2 block w-full"
							onChange={async (event) => {
								const file = event.target.files?.[0];
								if (!file) return;
								try {
									const uploaded = await uploadGuideMedia(token, agencyUserId, file);
									setAvailableMedia([
										...availableMedia,
										{
											...uploaded,
											mime_type: file.type as GuideMedia["mime_type"],
											width: 0,
											height: 0,
											byte_size: file.size,
										},
									]);
								} catch (cause) {
									onError(message(cause));
								}
							}}
						/>
					</label>
					{active.blocks.map((block, index) => (
						<BlockEditor
							key={`${block.type}-${index}`}
							block={block}
							media={availableMedia}
							onChange={(next) =>
								update({
									blocks: active.blocks.map((item, itemIndex) =>
										itemIndex === index ? next : item,
									),
								})
							}
							onRemove={() =>
								update({
									blocks: active.blocks.filter((_, itemIndex) => itemIndex !== index),
								})
							}
							move={(offset) =>
								update({ blocks: moveBlock(active.blocks, index, offset) })
							}
						/>
					))}
					<div className="flex flex-wrap gap-2">
						{(
							["heading", "paragraph", "bullet_list", "image"] as GuideBlock["type"][]
						).map((type) => (
							<button
								type="button"
								key={type}
								className="rounded border px-2 py-1 text-sm"
								onClick={() => update({ blocks: [...active.blocks, blockFor(type)] })}
							>
								+ {type}
							</button>
						))}
					</div>
				</>
			)}
			<div className="flex gap-2">
				<button
					type="button"
					disabled={busy}
					onClick={() => void save()}
					className="rounded-md bg-primary px-4 py-2 text-primary-foreground"
				>
					{busy ? "Menyimpan..." : "Simpan draft"}
				</button>
				<button
					type="button"
					onClick={onCancel}
					className="rounded-md border px-4 py-2"
				>
					Batal
				</button>
			</div>
		</section>
	);
}

function BlockEditor({
	block,
	media,
	onChange,
	onRemove,
	move,
}: {
	block: GuideBlock;
	media: GuideMedia[];
	onChange: (block: GuideBlock) => void;
	onRemove: () => void;
	move: (offset: number) => void;
}) {
	return (
		<div className="rounded border p-3">
			<div className="flex gap-2 text-xs">
				<strong className="flex-1">{block.type}</strong>
				<button type="button" aria-label="Naikkan block" onClick={() => move(-1)}>
					↑
				</button>
				<button type="button" aria-label="Turunkan block" onClick={() => move(1)}>
					↓
				</button>
				<button type="button" onClick={onRemove}>
					Hapus
				</button>
			</div>
			{block.type === "bullet_list" ? (
				<textarea
					aria-label="Item bullet, satu per baris"
					value={(block.items ?? []).join("\n")}
					onChange={(event) =>
						onChange({
							type: "bullet_list",
							items: event.target.value.split("\n").filter(Boolean),
						})
					}
					className="mt-2 w-full rounded border px-2 py-1"
				/>
			) : block.type === "image" ? (
				<div className="grid gap-2 sm:grid-cols-2">
					<select
						aria-label="Pilih Guide Media"
						value={block.media_id ?? ""}
						onChange={(event) => onChange({ ...block, media_id: event.target.value })}
						className="mt-2 rounded border px-2 py-1"
					>
						<option value="">Pilih gambar</option>
						{media.map((item) => (
							<option key={item.id} value={item.id}>
								{item.id} ({item.width}×{item.height})
							</option>
						))}
					</select>
					<input
						aria-label="Teks alternatif"
						value={block.alt ?? ""}
						onChange={(event) => onChange({ ...block, alt: event.target.value })}
						placeholder="Teks alternatif"
						className="mt-2 rounded border px-2 py-1"
					/>
				</div>
			) : (
				<textarea
					aria-label={`Isi ${block.type}`}
					value={block.text ?? ""}
					onChange={(event) => onChange({ ...block, text: event.target.value })}
					className="mt-2 w-full rounded border px-2 py-1"
				/>
			)}
		</div>
	);
}

function CategoryManager({
	categories,
	token,
	agencyUserId,
	reload,
	onError,
}: {
	categories: GuideCategory[];
	token: string;
	agencyUserId: string;
	reload: () => Promise<void>;
	onError: (value: string) => void;
}) {
	const [editing, setEditing] = useState<GuideCategory | null>(null);
	const [translations, setTranslations] = useState([
		{ locale: "id", label: "" },
	]);
	const save = async () => {
		try {
			await saveGuideCategory(token, agencyUserId, {
				id: editing?.id,
				display_order: editing?.display_order ?? categories.length * 10,
				translations,
			});
			setEditing(null);
			setTranslations([{ locale: "id", label: "" }]);
			await reload();
		} catch (cause) {
			onError(message(cause));
		}
	};
	return (
		<section className="rounded-md border p-4">
			<h2 className="font-semibold">Guide Categories</h2>
			<div className="mt-3 space-y-2">
				{translations.map((item, index) => (
					<div key={`${item.locale}-${index}`} className="flex gap-2">
						<input
							aria-label="Locale kategori"
							value={item.locale}
							onChange={(event) =>
								setTranslations(
									translations.map((value, i) =>
										i === index ? { ...value, locale: event.target.value } : value,
									),
								)
							}
							className="w-20 rounded border px-2"
						/>
						<input
							aria-label="Label kategori"
							value={item.label}
							onChange={(event) =>
								setTranslations(
									translations.map((value, i) =>
										i === index ? { ...value, label: event.target.value } : value,
									),
								)
							}
							className="min-w-0 flex-1 rounded border px-2"
						/>
						{item.locale !== "id" && (
							<button
								type="button"
								onClick={() =>
									setTranslations(translations.filter((_, i) => i !== index))
								}
							>
								Hapus
							</button>
						)}
					</div>
				))}
				<div className="flex gap-2">
					<button
						type="button"
						className="underline"
						onClick={() =>
							setTranslations([...translations, { locale: "en", label: "" }])
						}
					>
						Tambah translation
					</button>
					<button
						type="button"
						onClick={() => void save()}
						className="rounded bg-primary px-3 py-2 text-primary-foreground"
					>
						{editing ? "Simpan rename" : "Tambah"}
					</button>
				</div>
			</div>
			<ul className="mt-3 space-y-2 text-sm">
				{categories.map((item) => (
					<li key={item.id} className="flex gap-2">
						<span className="flex-1">
							{categoryLabel(item)} ({item.article_count})
						</span>
						<button
							type="button"
							className="underline"
							onClick={() => {
								setEditing(item);
								setTranslations(structuredClone(item.translations));
							}}
						>
							Rename
						</button>
						{!item.system_owned && item.state === "active" && (
							<Action
								label="Archive"
								run={async () => {
									try {
										await archiveGuideCategory(token, agencyUserId, item.id);
										await reload();
									} catch (cause) {
										onError(message(cause));
									}
								}}
							/>
						)}
					</li>
				))}
			</ul>
		</section>
	);
}

function Action({
	label,
	run,
}: {
	label: string;
	run: () => Promise<unknown>;
}) {
	const [busy, setBusy] = useState(false);
	return (
		<button
			type="button"
			disabled={busy}
			className="text-sm underline"
			onClick={async () => {
				setBusy(true);
				try {
					await run();
				} finally {
					setBusy(false);
				}
			}}
		>
			{busy ? "Memproses..." : label}
		</button>
	);
}
function articleTranslation(article: GuideArticle, locale: string) {
	return (
		article.translations.find((item) => item.locale === locale) ??
		article.translations.find((item) => item.locale === "id") ??
		emptyTranslation("id")
	);
}
function categoryLabel(category: GuideCategory) {
	return (
		category.translations.find((item) => item.locale === "id")?.label ??
		category.translations[0]?.label ??
		"Umum"
	);
}
function newDraft(categories: GuideCategory[]): GuideArticle {
	return {
		id: `new-${Date.now()}`,
		category_id:
			categories.find((item) => item.state === "active")?.id ??
			"guide-category-umum",
		state: "draft",
		translations: [emptyTranslation("id")],
	};
}
function blockFor(type: GuideBlock["type"]): GuideBlock {
	return type === "bullet_list"
		? { type, items: [] }
		: type === "image"
			? { type, media_id: "", alt: "" }
			: { type, text: "" };
}
function moveBlock(blocks: GuideBlock[], index: number, offset: number) {
	const target = index + offset;
	if (target < 0 || target >= blocks.length) return blocks;
	const next = [...blocks];
	[next[index], next[target]] = [next[target], next[index]];
	return next;
}
function BlockPreview({
	block,
	token,
	agencyUserId,
}: {
	block: GuideBlock;
	token: string;
	agencyUserId: string;
}) {
	if (block.type === "heading")
		return <h3 className="mt-4 text-lg font-semibold">{block.text}</h3>;
	if (block.type === "bullet_list")
		return (
			<ul className="list-disc pl-5">
				{block.items?.map((item) => (
					<li key={item}>{item}</li>
				))}
			</ul>
		);
	if (block.type === "image")
		return (
			<GuideImagePreview
				mediaId={block.media_id}
				alt={block.alt || "Gambar panduan"}
				token={token}
				agencyUserId={agencyUserId}
			/>
		);
	return <p className="my-3">{block.text}</p>;
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
	if (!mediaId || failed)
		return (
			<div className="my-3 rounded bg-muted p-6 text-center text-sm">
				Gambar tidak tersedia — {alt}
			</div>
		);
	if (!source)
		return (
			<div className="my-3 rounded bg-muted p-6 text-center text-sm">
				Memuat gambar…
			</div>
		);
	return (
		<img className="my-3 w-full rounded object-cover" src={source} alt={alt} />
	);
}

function message(cause: unknown) {
	return cause instanceof Error ? cause.message : "Operasi Guide CMS gagal";
}
