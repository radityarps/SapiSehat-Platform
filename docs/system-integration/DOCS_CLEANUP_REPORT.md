# Docs Cleanup Report

Cleanup rule: keep latest system-integration docs and docs tied to `apps/backend`, `apps/mobile`, or `apps/dashboard` implementation. Remove docs that are legacy-only, duplicate current entrypoints, or completed migration bookkeeping.

## Removed

| Removed path | Reason | Current source of truth |
| --- | --- | --- |
| `docs/system-integration/DOCS_CLEANUP_REPORT.md` | Migration completed; plan no longer needed as future doc. | `docs/README.md` routing rules |
| `docs/system-integration/architecture/legacy-architecture-overview.md` | Legacy architecture duplicates current platform routing and ADRs. | `docs/system-integration/README.md`, `docs/adr/0002-go-gateway-python-inference.md` |
| `docs/system-integration/mobile/legacy-mobile-readme.md` | Legacy mobile implementation start duplicates current mobile contracts and app docs. | `docs/system-integration/mobile/README.md`, `apps/mobile/SMOKE_TEST_CHECKLIST.md`, `apps/mobile/TFLITE_PARITY.md` |
| `docs/system-integration/validation/legacy-validation-readme.md` | Duplicate wrapper around validation package. | `docs/system-integration/validation/README.md` |
| `docs/system-integration/product/PRD-platform-rebuild.md` | Old image-only PRD conflicts with current platform framing. | `docs/system-integration/product/PRD-platform-rebuild.md`, `docs/system-integration/product/PLATFORM_SCOPE.md` |
| `docs/system-integration/product/PRD-proposal-based.md` | Old proposal PRD superseded by platform rebuild PRD. | `docs/system-integration/product/PRD-platform-rebuild.md` |
| `docs/plans/2026-05-05-prompt*.md` | Completed old mobile screen implementation prompts; not needed for future maintenance. | `docs/system-integration/mobile/mobile-full-version-spec.md`, `apps/mobile/**` docs |
| `docs/plans/2026-05-05-mobile-full-version.md` | Duplicate implementation plan superseded by mobile spec and app docs. | `docs/system-integration/mobile/mobile-full-version-spec.md`, `apps/mobile/**` docs |
| `docs/plans/2026-05-04-backend-model-integration.md` | Old integration plan superseded by current backend/model docs and platform contracts. | `docs/system-integration/backend/README.md`, `docs/team-1-image/backend/README.md`, `apps/backend/model/README.md` |
| `docs/team-1-image/model/__pycache__/` | Generated Python cache files. | Source `.py` files in same folder |

## Kept

- Current platform source of truth under `docs/system-integration/**`.
- Team-specific image docs under `docs/team-1-image/**`.
- Team-specific NLP docs under `docs/team-2-nlp/**`.
- App implementation docs under `apps/**`.
- Model scripts, reports, fixtures, and result artifacts used by backend tests.
- Backend migration/deployment docs for future Go gateway + Python inference rebuild.
