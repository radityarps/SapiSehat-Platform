# ADR 0006: Atomic Versioned Guide Snapshots

## Status

Accepted

## Context

Guide Articles must be editable from the agency dashboard without an APK release, while the Flutter Farmer App must retain every published article and required image offline. Fetching live pages or updating cached records individually can leave farmers with missing media, mixed translations, or a partially updated catalog after an interrupted synchronization.

## Decision

The FastAPI Platform Backend publishes each complete guide catalog as a monotonically versioned manifest containing stable article/category membership and SHA-256 hashes for structured documents and optimized media. The authenticated Flutter Farmer App renders its current local snapshot immediately, downloads changed files into a separate candidate snapshot when Panduan opens, verifies every required hash, and atomically switches versions only when the candidate is complete. The APK carries a Bundled Guide Catalog with IDs shared by idempotently seeded CMS records, guaranteeing first-install offline access without creating a second content source.

Guide content uses allowlisted structured blocks rather than arbitrary HTML or remote web pages. CMS images use the existing S3-compatible storage under a separate CMS prefix and are downloaded into the snapshot; they do not inherit Stored Scan Image consent or retention rules.

## Considered Options

- **Online-only CMS:** rejected because Panduan would disappear without connectivity.
- **Cache articles independently:** rejected because interruption could expose mixed catalog versions or missing media.
- **Bundle content only:** rejected because every editorial correction would require a new APK.
- **Arbitrary HTML:** rejected because native structured blocks are safer, deterministic offline, and easier to validate across mobile versions.

## Consequences

Positive: first-install guidance works offline; updates do not require APK releases; failed refreshes preserve a known-complete catalog; content and media integrity are auditable.

Negative: publication must build consistent manifests, old media cannot be removed while a retained snapshot may reference it, and mobile needs duplicate storage during candidate download. New block types require coordinated backend/dashboard/mobile contract changes rather than editor-defined runtime extensions.
