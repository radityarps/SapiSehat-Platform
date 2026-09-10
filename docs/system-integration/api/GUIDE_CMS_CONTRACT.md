# Guide Article CMS Implementation Contract

This contract makes the transport and persistence details of Issue #94 concrete. Product intent remains owned by `product/GUIDE_CMS_PRD.md`; snapshot architecture remains owned by ADR-0006.

## Authorization

All `/api/agency/guide/**` endpoints require an Agency bearer token, a matching `X-Agency-User-Id`, and the global `admin` role. All `/api/guide/**` endpoints require a Farmer bearer token. Guide content is global and has no jurisdiction or cattle scope.

## Editorial entities and lifecycle

- `guide_categories` and `guide_category_translations` hold editable category records. `guide-category-umum` is system-owned: the record cannot be archived, while translations and display order may be edited.
- `guide_articles` and `guide_article_translations` hold the current editorial draft. Article lifecycle is `draft | published | unpublished | archived`.
- A published article also stores an immutable `published_document` JSON value. Saving the editorial draft never changes this value. `publish` validates the draft and atomically replaces `published_document`; it does not create another article ID.
- `guide_media` describes optimized CMS assets under `cms/guides/`. It is separate from Stored Scan Image consent and retention.
- `guide_manifests` stores immutable complete membership plus document/media hashes. Its database-generated identity is the monotonically ordered version token.
- `guide_editorial_audit_events` stores immutable action metadata, not restorable revisions.

Creating an active category and changing an active category's translations or display order each emit one manifest, even when the category has no articles. Archiving a non-system category moves all editorial articles to `Umum`. For published articles, the operation copies the existing immutable `published_document` and changes only its `category_id`; unpublished editorial changes are never captured implicitly. Published documents for affected published articles and all audit events are updated with one manifest in the same transaction. A missing or invalid published document aborts the category archive. Publish, unpublish, article archive, category archive, and every mobile-visible category mutation emit exactly one manifest.

## Admin endpoints

- `GET /api/agency/guide/articles?search=&category_id=&locale=&state=` → `{items: GuideArticle[]}`.
- `POST /api/agency/guide/articles` and `PUT /api/agency/guide/articles/{id}` accept `{category_id, translations:[{locale,title,summary,blocks}]}`. PUT is a complete replacement of translations; clients must send retained locales. Both save editorial draft only.
- `POST /api/agency/guide/articles/{id}/{publish|unpublish|archive}` performs the explicit lifecycle transition.
- `GET|POST /api/agency/guide/categories`, `PUT /api/agency/guide/categories/{id}`, and `POST /api/agency/guide/categories/{id}/archive` manage multilingual categories.
- `GET /api/agency/guide/media` lists ready uploaded assets. `POST /api/agency/guide/media` accepts one JPEG, PNG, or WebP multipart `file` and returns optimized media metadata.
- `GET /api/agency/guide/media/{id}/preview` returns optimized image bytes to a global admin with `Cache-Control: private, no-store`; it never makes the object public or issues a long-lived URL.
- `GET /api/agency/guide/audit-events` → `{items: GuideEditorialAuditEvent[]}`.

Unknown request and structured-block fields are rejected. Blocks are exactly `heading {text}`, `paragraph {text}`, `bullet_list {items}`, or `image {media_id,alt}`. Published Bahasa Indonesia requires title, summary, at least one block, safe non-diagnostic wording, and ready referenced media.

## Farmer manifest and delta

`GET /api/guide/manifest?version={activeVersion}` returns either:

```json
{"changed": false, "version": 12}
```

or a changed response containing:

```json
{
  "changed": true,
  "version": 13,
  "documents": {
    "categories": [{"id":"...","sha256":"...","url":"/api/guide/documents/categories/...?version=13"}],
    "articles": [{"id":"...","sha256":"...","url":"/api/guide/documents/articles/...?version=13"}]
  },
  "media": [{"id":"...","sha256":"...","mime_type":"image/webp","byte_size":123,"width":800,"height":600,"url":"/api/guide/media/..."}],
  "changed_document_ids": ["..."],
  "changed_media_ids": ["..."],
  "removed_document_ids": ["..."],
  "removed_media_ids": ["..."]
}
```

`documents.categories` and `documents.articles` are complete membership, not only the delta. Changed IDs compare the requested retained manifest with the current manifest; when the requested version is unknown, every member is changed. Removed IDs are tombstones relative to the requested retained manifest. Media membership is also complete.

`GET /api/guide/documents/{categories|articles}/{id}?version={version}` returns one canonical JSON document. `GET /api/guide/media/{id}` returns an optimized asset only when at least one retained manifest references it. Draft-only media is not farmer-readable.

Manifest creation, published-document replacement, and audit writes commit atomically. PostgreSQL publication transactions take one database advisory transaction lock, while manifest versions come from the native identity sequence; no `max(version) + 1` allocation is permitted.

## Flutter snapshot activation

The APK bundle is version `0`. On refresh, Flutter renders the active snapshot first, creates `candidate-{version}`, reuses active files only when their SHA-256 matches a complete-membership descriptor, downloads only changed/missing documents and media through its configured `ApiTransport`, verifies every SHA-256, decodes every document, validates category/article/media complete membership and references, writes the assembled catalog, and only then renames the candidate and atomically replaces the `active` pointer.

Request, status, decode, hash, validation, or write failure deletes the candidate where possible and leaves the prior pointer and snapshot unchanged. Media hash verification happens before byte-level JPEG/PNG/WebP decode, and every candidate media file is decoded, including a verified file copied from the active snapshot. Complete membership removes unpublished/archived/tombstoned items only after successful activation. Snapshot directories and referenced media are retained; cleanup must not invalidate an active or potentially retained manifest.
