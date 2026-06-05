# SapiSehat Documentation

SapiSehat documentation is split by ownership so Team 1 image, Team 2 NLP, and shared platform work do not duplicate contracts.

## Start Here

- [System Integration](../README.md) — shared product scope, architecture, backend/database, mobile flow, web dashboard, privacy, deployment, and cross-team contracts.
- [Team 1 Image](team-1-image/README.md) — image-based early detection subsystem.
- [Team 2 NLP](team-2-nlp/README.md) — NLP-based symptom screening subsystem.
- [ADRs](adr/) — hard-to-reverse architecture decisions.
- [Docs Restructure Plan](system-integration/DOCS_RESTRUCTURE_PLAN.md) — approved migration map and routing record.

## Routing Rules

Use this table when creating or updating docs.

| Topic | Write here |
| --- | --- |
| Product scope, MVP phases, user roles | `docs/system-integration/product/` |
| Shared API contracts | `docs/system-integration/api-contracts/` |
| Shared database/data model | `docs/system-integration/database/` |
| Farmer mobile app end-to-end flow | `docs/system-integration/mobile/` |
| Agency dashboard behavior | `docs/system-integration/web-dashboard/` |
| Privacy, consent, retention, access control | `docs/system-integration/privacy-security/` |
| Deployment and operations | `docs/system-integration/deployment/` |
| Cross-team validation | `docs/system-integration/validation/` |
| Image model, image inference, image validation | `docs/team-1-image/` |
| NLP model, symptom questionnaire, NLP validation | `docs/team-2-nlp/` |
| Hard-to-reverse architecture decisions | `docs/adr/` |

## Shared Contract Approval Rule

Before implementing or releasing any shared backend, mobile, dashboard, API, data model, privacy, deployment, or fusion-flow change:

1. Update the relevant `docs/system-integration` contract.
2. Link impacted Team 1 and Team 2 docs when model-specific behavior changes.
3. Add or update an ADR when the decision is hard to reverse, surprising without context, and based on a real trade-off.
4. Keep implementation aligned with the approved contract.

Do not duplicate shared schemas in team folders. Team folders may reference shared contracts and add model-specific details only.

## Legacy Docs

Legacy docs have been migrated into owned folders per [Docs Restructure Plan](system-integration/DOCS_RESTRUCTURE_PLAN.md). Old image/model docs now live under `docs/team-1-image/model`; shared backend/mobile/architecture/validation docs live under `docs/system-integration/**`.

When editing migrated legacy docs, keep pointers to the new entrypoints instead of creating another shared contract location.
