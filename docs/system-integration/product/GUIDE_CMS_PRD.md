# Guide Content Management PRD

## Problem

The Flutter Farmer App currently defines every Panduan article and category inside `apps/mobile/lib/features/guide/guide_screen.dart`. Changing guidance such as cattle-profile instructions therefore requires a mobile code change and a new APK. Replacing those constants with online-only content would solve editorial control but would remove guidance when a farmer has no connection.

SapiSehat needs admin-managed Guide Articles that can change without an app release while preserving a complete, consistent Panduan experience offline.

## Goal

Enable a global admin to manage multilingual Guide Articles and Guide Categories in the agency dashboard. The Flutter Farmer App must display the latest successfully synchronized published catalog and must retain a complete bundled or cached catalog when offline.

## Users

- **Farmer User** reads and searches published guidance in the Flutter Farmer App, online or offline.
- **Agency User with global `admin` role** manages Guide Categories, translations, article blocks, media, and publication state in the dashboard.
- Other agency roles may not access CMS management operations.

## Product Decisions

- The canonical content is a **Guide Article**, not a public Blog Post or Farmer-Owned Cattle Record.
- An article has one lifecycle: `draft`, `published`, `unpublished`, or `archived`.
- Publishing requires a complete Bahasa Indonesia translation. Other translations are optional.
- Mobile selects the application locale and falls back to Bahasa Indonesia when that translation is absent.
- Article content uses an allowlist of structured blocks: heading, paragraph, bullet list, and image.
- External links, arbitrary HTML, embedded scripts, video, attachments, comments, author display, reader analytics, scheduling, approval chains, and full revision rollback are out of scope.
- Admins manage categories. The system-owned `Umum` category always exists and cannot be archived or deleted.
- Archiving a category moves its articles to `Umum` without changing their publication state.
- Within a category, published articles are ordered by `published_at` descending.
- Articles are archived rather than permanently deleted.
- Every editorial mutation creates a Guide Editorial Audit Event; full content revision history is not retained.

## Dashboard Requirements

### Article management

The dashboard must let a global admin:

1. List and filter articles by title, category, locale availability, and lifecycle state.
2. Create and edit a draft with a stable ID.
3. Enter title, summary, category, translations, and ordered structured blocks.
4. Add, remove, and reorder allowlisted blocks.
5. Upload and select optimized guide images.
6. Preview the selected translation in a mobile-like layout before publication.
7. Publish only when the Bahasa Indonesia title, summary, and valid content blocks are complete and all referenced media are ready.
8. Unpublish a published article immediately.
9. Archive an article without hard deletion.
10. View creation, update, publish, unpublish, archive, and category-move audit events.

Publishing an edited article replaces the currently published representation; it does not create a user-visible duplicate.

### Category management

The dashboard must let a global admin:

1. Create and rename multilingual categories.
2. Archive a category.
3. See how many articles use each category.
4. Keep the system-owned `Umum` category immutable as a record; its translated labels may be edited.

Archiving a category atomically moves all its articles to `Umum`, keeps published articles published, and records audit events.

### Validation and safety

- Reject unknown block types and unknown fields at the API boundary.
- Set explicit limits for title, summary, block count, text length, list items, image count, upload size, dimensions, and accepted MIME types.
- Accept only JPEG, PNG, or WebP images whose decoded content matches the declared type.
- Generate optimized mobile assets rather than serving the original upload as the offline asset.
- Preserve SapiSehat's non-diagnostic language rules. CMS content must not claim confirmed diagnosis or outbreak.
- Render structured content as native components; do not execute HTML or script supplied by an editor.

## Mobile Requirements

### Reading experience

The Panduan screen must:

1. Continue to show searchable article cards and category filters.
2. Render heading, paragraph, bullet-list, and image blocks natively.
3. Choose the application locale and fall back per article/category to Bahasa Indonesia.
4. Show no author or reader-count field.
5. Order categories according to CMS category order and articles by latest `published_at` within each category.

### First install and offline behavior

- Package a **Bundled Guide Catalog** in the APK containing the current static articles, categories, translations, and required media.
- Seed the backend CMS with matching stable article/category IDs so bundled and server content never appear as parallel duplicates.
- On first launch with no cache, activate the bundled catalog.
- Every active catalog must contain all published article metadata, all translations included in that version, all content blocks, and every referenced optimized image.
- Reading, searching, filtering, and opening every active article must work without network access.

### Synchronization

When the Farmer User opens Panduan while authenticated:

1. Render the active local snapshot immediately.
2. If online, request the current published manifest using the last active version token.
3. If unchanged, retain the active snapshot without redownloading content.
4. If changed, download only changed article/category documents and media identified by the manifest.
5. Verify document and media SHA-256 values.
6. Build the candidate snapshot separately from the active snapshot.
7. Activate the candidate atomically only after all required files validate.
8. Remove unpublished, archived, and deleted-from-manifest content when the new snapshot becomes active.
9. Retain the previous complete snapshot if any request, storage write, decode, or integrity check fails.
10. Show a lightweight refresh-failed state without replacing cached content with an error page.

An article unpublished while a device is offline may remain visible until that device completes a successful refresh. After successful refresh it must be absent.

## Backend Requirements

### Ownership and access

- The FastAPI Platform Backend owns Guide Article, translation, block, category, media, snapshot-manifest, and editorial-audit persistence.
- CMS mutations require an authenticated Agency User with global `admin` role.
- Published catalog and media reads require an authenticated Farmer User.
- Guide content is global in the first version; it is not targeted by jurisdiction, farmer, or cattle.

### Storage

- Store CMS records and active publication metadata in PostgreSQL.
- Store image bytes in the existing S3-compatible object storage under a separate CMS object-key prefix.
- Do not reuse Stored Scan Image records, retention policy, or consent semantics for guide media.
- Published media must remain available for every manifest that may still be the active mobile snapshot; cleanup must not break an in-progress or retained snapshot.

### Publication and manifest

- Publishing, unpublishing, archiving, category archival, and any change visible to mobile must create a new monotonically ordered manifest version.
- A manifest identifies the complete published catalog and includes stable IDs, locale availability, publication timestamps, document hashes, media hashes, and tombstones or an equivalent complete-membership rule.
- The backend must never expose draft or archived content through the farmer catalog endpoint.
- Concurrent publication operations must not produce a manifest referring to missing article documents or media.

## Conceptual Data

- **GuideArticle**: stable ID, category ID, lifecycle state, `published_at`, created/updated metadata.
- **GuideArticleTranslation**: article ID, locale, title, summary, ordered structured blocks.
- **GuideCategory**: stable ID, system-owned flag, lifecycle state, display order.
- **GuideCategoryTranslation**: category ID, locale, label.
- **GuideMedia**: stable ID, optimized object key, MIME type, dimensions, byte size, SHA-256.
- **GuideManifest**: version token, creation timestamp, complete published membership and hashes.
- **GuideEditorialAuditEvent**: actor, action, target type/ID, timestamp, and non-content metadata.

Exact SQL and transport schemas belong in the implementation issue and API/data-model contract updates.

## Migration

1. Assign stable IDs to the current hard-coded categories and six Guide Articles.
2. Represent their text as structured blocks and provide Bahasa Indonesia translations.
3. Package that data as the Bundled Guide Catalog.
4. Seed the same records into backend CMS storage idempotently.
5. Ensure the first server manifest updates the bundled records by ID rather than duplicating them.
6. Remove hard-coded rendering as an independent source only after bundled fallback and synchronized cache tests pass.

## Acceptance Criteria

1. A global admin can create a draft Bahasa Indonesia Guide Article, preview it, publish it, and see it on mobile after refresh without releasing a new APK.
2. Non-admin agency roles receive a forbidden response and cannot access CMS management UI.
3. An article cannot publish without valid Bahasa Indonesia content or with an invalid block/media reference.
4. A Farmer User can open, search, filter, and read every article after enabling airplane mode on a first install using bundled content.
5. After one successful refresh, a Farmer User can restart the app offline and read every article and image from that synchronized snapshot.
6. A failed or interrupted refresh leaves the previous snapshot fully usable and does not expose a partially updated catalog.
7. A tampered article or media file fails SHA-256 validation and cannot become active.
8. An unpublished or archived article disappears only after a successful refresh; other cached articles remain available.
9. Archiving a category moves its articles to `Umum`, preserves publication state, and reaches mobile in one consistent snapshot.
10. Locale selection uses the application locale and falls back to Bahasa Indonesia per missing translation.
11. Current hard-coded articles migrate without duplicates because bundled and seeded records share stable IDs.
12. Create, update, publish, unpublish, archive, and category-move actions are visible in admin audit history.
13. Dashboard, backend, and Flutter tests cover authorization, validation, manifest generation, atomic cache activation, migration, locale fallback, and offline rendering.

## Success Measures

- Published guidance changes reach a connected mobile client without an APK release.
- One hundred percent of the active published catalog remains readable after network removal.
- Interrupted synchronization never replaces a complete snapshot with an incomplete one.
- Existing bundled articles appear exactly once before and after first synchronization.

## Out of Scope

- Public web blog or SEO pages.
- Farmer-authored content, comments, likes, bookmarks, or sharing analytics.
- Jurisdiction-specific targeting or personalization.
- Scheduled publication and multi-person approval.
- Full revision history and rollback.
- Arbitrary HTML, scripts, external links, video, audio, PDF, and attachments.
- Background push synchronization; refresh occurs when Panduan is opened.
