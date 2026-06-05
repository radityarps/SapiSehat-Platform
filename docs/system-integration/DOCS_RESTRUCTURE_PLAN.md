# SapiSehat Docs Restructure Plan

## Status

Draft for approval before moving existing documentation.

## Goal

Restructure `docs/` so SapiSehat documentation matches the new platform scope:

- Team 1: image-based cattle disease early detection.
- Team 2: NLP-based symptom screening.
- System Integration: shared farmer mobile flow, complete livestock management scope, backend, database, web dashboard, privacy, deployment, and cross-team contracts.

## Target Documentation Structure

```text
docs/
├── team-1-image/
│   ├── README.md
│   ├── model/
│   ├── backend/
│   ├── validation/
│   └── experiments/
├── team-2-nlp/
│   ├── README.md
│   ├── symptom-questionnaire/
│   ├── model/
│   ├── validation/
│   └── experiments/
├── system-integration/
│   ├── README.md
│   ├── DOCS_RESTRUCTURE_PLAN.md
│   ├── product/
│   ├── architecture/
│   ├── backend/
│   ├── database/
│   ├── mobile/
│   ├── web-dashboard/
│   ├── api-contracts/
│   ├── privacy-security/
│   ├── deployment/
│   └── validation/
├── adr/
├── changelog.md
└── plans/
```

## Ownership Rules

### `docs/team-1-image`

Owns image-based early detection only:

- image classification model documentation
- symptom-region detector documentation
- dataset preparation for image data
- image model evaluation reports
- image model training/export scripts and guides
- image inference implementation details
- image-specific validation protocol

### `docs/team-2-nlp`

Owns NLP-based symptom screening only:

- symptom questionnaire design
- Indonesian farmer symptom wording
- free-text notes processing
- NLP model or rules documentation
- NLP dataset and labeling method
- NLP evaluation reports
- NLP-specific validation protocol

### `docs/system-integration`

Owns shared platform documentation:

- SapiSehat product scope and MVP phases
- farmer mobile app end-to-end flow
- complete livestock profile scope
- farmer, cattle, disease, detection, and agency data model
- backend and database architecture
- API contracts used by mobile, dashboard, Team 1, and Team 2
- image + NLP parallel evidence fusion contract
- agency web dashboard requirements
- privacy, consent, retention, and data access rules
- deployment and operational plan
- cross-team testing and validation

## Proposed File Migration Map

| Current path | Proposed path | Notes |
| --- | --- | --- |
| `docs/team-1-image/model/**` | `docs/team-1-image/model/**` | Image model docs/scripts/results. |
| `docs/team-1-image/backend/README.md` | `docs/system-integration/backend/README.md` + `docs/team-1-image/backend/README.md` | Split shared API/backend from image inference detail. |
| `docs/system-integration/backend/development.md` | `docs/system-integration/backend/development.md` | Shared backend development unless image-only. |
| `docs/Backend/migration/**` | `docs/system-integration/deployment/backend-migration/**` | Shared deployment/migration. |
| `docs/Mobile/**` | `docs/system-integration/mobile/**` | Farmer app flow shared across image + NLP. |
| `docs/architecture/**` | `docs/system-integration/architecture/**` | Shared architecture. |
| `docs/system-integration/validation/**` | `docs/system-integration/validation/**` | Shared validation; team-specific parts later copied or split. |
| `docs/system-integration/product/PRD.md` | `docs/system-integration/product/PRD.md` | Product scope must include platform, not image-only app. |
| `docs/system-integration/product/PRD-proposal-based.md` | `docs/system-integration/product/PRD-proposal-based.md` | Review before move. |
| `docs/team-1-image/model/PRD-two-stage-real-world-model.md` | `docs/team-1-image/model/PRD-two-stage-real-world-model.md` | Image/model-specific. |
| `docs/team-1-image/model/preprocessing-mismatch-analysis.md` | `docs/team-1-image/model/preprocessing-mismatch-analysis.md` | Image preprocessing-specific. |
| `docs/Postman/**` | `docs/system-integration/api-contracts/postman/**` | Shared API contract artifacts. |
| `docs/system-integration/mobile/mobile-full-version-spec.md` | `docs/system-integration/mobile/mobile-full-version-spec.md` | Farmer mobile app shared flow. |
| `docs/adr/0001-yolo-symptom-region-detector.md` | `docs/adr/0001-yolo-symptom-region-detector.md` or `docs/team-1-image/adr/0001-yolo-symptom-region-detector.md` | Keep system-wide until ADR policy decided. |
| `docs/plans/**` | `docs/plans/**` | Keep until plan ownership reviewed. |
| `docs/changelog.md` | `docs/changelog.md` | Keep global changelog. |

## Required New Docs Before File Moves

1. `docs/../README.md`
   - New platform overview.
   - Explain team split.
   - Link to Team 1 and Team 2 folders.

2. `docs/system-integration/product/PLATFORM_SCOPE.md`
   - Product identity: disease early detection platform.
   - Target system with MVP phases.
   - Farmer primary, agency secondary.

3. `docs/system-integration/api-contracts/FUSION_CONTRACT.md`
   - Image model output schema.
   - NLP symptom output schema.
   - Parallel evidence fusion output schema.
   - Conflict/reliability rules.

4. `docs/system-integration/database/DATA_MODEL.md`
   - Farmer, cattle, livestock profile, health event, detection event, agency user.

5. `docs/team-2-nlp/README.md`
   - Team 2 scope.
   - Symptom questionnaire with notes.
   - MVP disease coverage: `healthy`, `FMD`, `LSD`.

## Open Decisions

- Exact MVP phase boundary for complete livestock profile.
- Whether agency dashboard needs role levels: national, province, district, officer.
- Whether farmer data upload is mandatory or consent-based per feature.
- Whether NLP model is ML classifier, rule-based triage, LLM-assisted, or hybrid.
- Whether image + NLP fusion happens in mobile app or backend only.
- Whether old no-retention image policy remains compatible with platform data collection.

## Migration Guardrails

- Do not move files until this plan is approved.
- Preserve old paths with redirect notes or update all links in same migration commit.
- Do not duplicate API schemas across team folders.
- Keep shared contracts in `docs/system-integration`.
- Keep `CONTEXT.md` as glossary only, not full specification.
