# Production Rebuild Plan

## Purpose

Production Rebuild Phase graduates the FastAPI in-memory tracer into target SapiSehat production architecture while preserving the Tracer Acceptance Contract.

This is a big-bang rewrite, not a strangler migration. Current tracer remains behavioral reference until production stack satisfies same acceptance contract.

## Source of Truth

- `CONTEXT.md`
- `docs/system-integration/product/PRD-platform-rebuild.md`
- `docs/adr/0002-go-gateway-python-inference.md`
- `docs/adr/0003-big-bang-production-rebuild.md`
- `docs/adr/0004-private-media-escrow-risk-follow-up.md`
- `docs/system-integration/api-contracts/FUSION_CONTRACT.md`

## Target Architecture

```text
Farmer Android app ─┐
                    ├─ public HTTPS ─> Go gateway ─┬─ PostgreSQL
Agency dashboard ───┘                               ├─ object/media storage
                                                     ├─ image-inference service (internal Python)
                                                     └─ nlp-inference service (internal Python)
```

Go gateway owns all public APIs. Mobile and dashboard never call Python services directly.

Go gateway owns auth, RBAC, jurisdiction, consent, risk follow-up checks, farmer/cattle/media/detection/fusion/risk APIs, PostgreSQL persistence, disease catalog, NLP questionnaire schema, safe-language templates, and canonical fusion.

Python services are internal only:

- `image-inference`: Team 1 image evidence
- `nlp-inference`: Team 2 NLP evidence

## Identity and Authorization

Use RBAC plus domain profiles.

Core tables: `users`, `user_credentials`, `user_profiles`, `roles`, `permissions`, `user_roles`, `role_permissions`.

Domain tables: `farmer_profiles`, `agency_profiles`, `agency_jurisdictions`.

Rules:

1. One user may have multiple roles.
2. Active workspace controls current role context.
3. Farmer users may sign in with Google OAuth or phone credential.
4. Farmer users must verify phone before cattle registration or detection submission.
5. Agency users may sign in with Google OAuth, but dashboard access requires invitation or admin approval.
6. Agency access uses RBAC permissions, hierarchical jurisdiction, and consent tier.
7. No jurisdiction assignment means no agency data access.

## Consent and Media

| Tier | Routine agency visibility | Media handling | Research/model access |
| --- | --- | --- | --- |
| `private` | Hidden except risk follow-up | Private Media Escrow | No |
| `monitoring` | Visible to authorized agency | Stored follow-up/audit media | No |
| `research_and_monitoring` | Visible to authorized agency | Stored follow-up/audit media | Controlled raw model-team dashboard access |

Private Media Escrow:

- encrypted at rest with server-managed keys for MVP
- hidden from routine agency access
- revealed only when threshold triggers follow-up
- purged after 30 days if no threshold trigger occurs
- offline private media escrow countdown starts from capture time
- offline private media older than 30 days at sync is not stored

Consent changes affect new records. Routine dashboard/media access changes immediately. Historical records remain for audit unless deletion policy says otherwise.

## Risk Signal and Follow-Up Rule

Threshold:

- same district
- same disease class
- within 7 days
- 2+ non-healthy detections
- `reliable` or `needs_review`
- offline detections use capture time

Private follow-up reveal:

- same 2+ threshold reveals full follow-up record
- record includes farmer, cattle, detection metadata, image evidence, NLP evidence, fusion result, risk reason, and escrowed media
- access requires agency permission, jurisdiction match, and threshold reason
- access audited
- wording: possible disease risk signal, never diagnosis/confirmed outbreak

## Model Team Access

Model team uses same dashboard app with role-based sections.

Rules:

- only `research_and_monitoring` records
- raw media allowed for model-improvement work
- no phone/email unless also authorized agency role
- views/downloads/exports audited
- export/download permissions separate from view permission

## Versioned Catalogs and Questionnaires

Go gateway owns versioned disease catalog, versioned NLP questionnaire schema, and safe-language message templates.

Image/NLP services return `model_version`, `catalog_version`, supported disease scores, `top_class`, confidence, and evidence metadata. Gateway validates outputs against active catalog.

Mobile fetches active catalog and questionnaire. Offline mobile uses pinned bundled versions and reports versions on sync.

## Acceptance-Contract Schema First

Initial PostgreSQL groups:

1. identity/RBAC
2. farmer/agency profiles
3. jurisdiction hierarchy
4. consent/media/escrow
5. cattle/timeline
6. detection/evidence/fusion/offline sync
7. disease catalog/questionnaire
8. risk events/audit events

Risk summaries may start as queries/views. Threshold-triggered follow-up events must be persisted for audit.

## Milestones

1. Freeze Tracer Acceptance Contract and production API contract.
2. Scaffold Go gateway, config, logging, errors, CORS, auth middleware.
3. Add PostgreSQL migrations and RBAC seed data.
4. Implement Google OAuth, phone credentials, farmer phone gate, agency invite/approval, active workspace.
5. Implement jurisdiction hierarchy and scoped access checks.
6. Implement consent tiers, media storage, Private Media Escrow, 30-day purge.
7. Create internal `image-inference` and `nlp-inference` Python services.
8. Implement disease catalog and NLP questionnaire APIs.
9. Implement cattle, timeline, detection, evidence, and Go-owned fusion.
10. Implement offline sync using capture time.
11. Implement district same-disease 2+ risk-signal engine and private follow-up unlock.
12. Implement immutable audit events.
13. Integrate Next.js/TanStack dashboard with role-based agency/research sections.
14. Integrate Android auth, phone verification, cattle selection, consent tiers, image+NLP detection, offline sync.
15. Replay tracer acceptance scenarios against production stack.
16. Mark FastAPI tracer reference-only after production stack passes.

## Initial Issue Slices

1. Define production API contract and acceptance replay list.
2. Scaffold Go gateway and PostgreSQL migration tooling.
3. Add RBAC schema and seed roles/permissions.
4. Add Google OAuth and phone credential contracts.
5. Add farmer profile completion with verified-phone gate.
6. Add agency invitation/approval and active workspace.
7. Add jurisdiction hierarchy and scoped access checks.
8. Add consent tier and Private Media Escrow schema.
9. Add cattle profile and timeline persistence.
10. Add image-inference internal Python service contract.
11. Add NLP-inference internal Python service contract.
12. Add versioned disease catalog and questionnaire APIs.
13. Add detection/evidence persistence.
14. Add Go-owned fusion engine.
15. Add media storage, escrow unlock, 30-day purge.
16. Add immutable audit events.
17. Add offline sync with capture-time risk behavior.
18. Add district same-disease 2+ risk-signal engine.
19. Add agency monitoring dashboard APIs.
20. Add research/model-team dashboard sections.
21. Integrate Next.js/TanStack dashboard with Go gateway.
22. Integrate Android auth/profile/cattle/consent flow.
23. Integrate Android image+NLP detection and sync.
24. Port tracer acceptance scenarios to production stack.
25. Retire FastAPI tracer to reference-only status.
