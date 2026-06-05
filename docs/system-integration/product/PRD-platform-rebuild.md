# PRD: SapiSehat Platform Rebuild

## Problem Statement

SapiSehat currently reads as an Android image-classification app for early cattle disease detection. That framing is too narrow for the intended system.

The intended product is a cattle disease early detection platform for farmers and local agencies in Indonesia. Farmers need a mobile app to register cattle, maintain livestock records, submit image evidence, answer symptom questions, receive early detection results, and sync offline results. Local agencies need a web dashboard to monitor disease risk signals, farmer reports, cattle records, and jurisdiction-level trends.

Two teams will work in parallel. Team 1 owns image classification integration across mobile and backend. Team 2 owns NLP symptom screening integration across mobile and backend. Both teams may contribute to shared backend, mobile, and dashboard features, but shared API, data model, fusion, and access-control contracts must stay centralized.

Without restructuring docs and architecture, the project will keep drifting toward an image-only app, duplicate contracts across teams, and make backend/dashboard integration unclear.

## Solution

Reposition SapiSehat as a disease early detection platform with three documentation and implementation areas:

1. Team 1 image subsystem.
2. Team 2 NLP subsystem.
3. System integration for shared platform contracts.

The platform will use a Go gateway with Python inference services. The Go gateway owns platform APIs, authentication, authorization, PostgreSQL persistence, dashboard endpoints, fusion orchestration, and offline sync. Python services own model-specific image and NLP inference.

The farmer mobile app will use a cattle-first detection flow with a quick-scan escape path. Online detection uses backend-primary image-plus-NLP fusion. Offline detection can use bundled image and NLP models, produce local fused results, and sync them later.

The agency dashboard will focus on disease risk signals, not confirmed outbreak declarations. Access will be role-jurisdiction-consent based.

## User Stories

1. As a farmer, I want to create an account with my phone number, so that my cattle records and detection history can be linked to me.
2. As a farmer, I want to register my cattle, so that detection results are tied to the correct animal.
3. As a farmer, I want to maintain a complete livestock profile, so that cattle identity, health, reproduction, feeding, productivity, transfer, and sale records are organized.
4. As a farmer, I want to select cattle before detection, so that each early detection event belongs to a cattle profile.
5. As a farmer, I want an emergency quick-scan option, so that I can check disease risk even before attaching the result to cattle.
6. As a farmer, I want to capture or upload cattle images, so that the image model can evaluate visual disease evidence.
7. As a farmer, I want guided capture, so that I know which symptoms or cattle areas to photograph.
8. As a farmer, I want image quality warnings, so that blurry or dark images do not create misleading results.
9. As a farmer, I want to answer guided symptom questions, so that NLP detection can evaluate non-visual symptom evidence.
10. As a farmer, I want to add optional symptom notes, so that I can describe observations not covered by the questionnaire.
11. As a farmer, I want online image-plus-NLP detection, so that I receive a unified early detection result.
12. As a farmer, I want offline detection support, so that I can still use the app in poor connectivity areas.
13. As a farmer, I want offline results to sync later, so that agencies can still monitor reports after connectivity returns.
14. As a farmer, I want clear confidence and reliability labels, so that I understand whether follow-up is needed.
15. As a farmer, I want handling advice, so that I know whether to retake input, isolate cattle, or contact an animal health officer.
16. As a farmer, I want results to avoid clinical-diagnosis wording, so that I do not mistake early detection for veterinary confirmation.
17. As a farmer, I want consent controls, so that I understand how my farmer data, cattle records, detection results, NLP notes, and images may be stored or shared.
18. As a farmer, I want my data access limited by agency role, jurisdiction, and consent, so that my records are not globally visible.
19. As a farmer, I want to view detection history, so that I can follow up on previous reports.
20. As a farmer, I want to attach quick-scan results to cattle later, so that emergency results do not remain disconnected.
21. As a farmer, I want cattle photos and media to be stored when policy permits, so that records and detection events are easier to review.
22. As a farmer, I want the app to support Indonesian local context, so that symptom wording and dashboard geography match real use.
23. As an agency user, I want to sign in with a role and assigned jurisdiction, so that I only access records I am authorized to view.
24. As an agency user, I want to view farmer records in my jurisdiction, so that I can monitor local reporting activity.
25. As an agency user, I want to view cattle records in my jurisdiction, so that I can understand livestock distribution and status.
26. As an agency user, I want to view early detection events, so that I can prioritize follow-up.
27. As an agency user, I want to see disease risk signals, so that possible increased risk can be investigated.
28. As an agency user, I want dashboard language to avoid confirmed outbreak claims, so that the system does not overstate model output.
29. As an agency user, I want trends by administrative jurisdiction, so that I can monitor province, regency/city, district/subdistrict, and village-level patterns.
30. As an agency user, I want to see image and NLP evidence breakdowns, so that I can understand why a result needs review.
31. As an agency user, I want conflicting image and NLP outputs marked clearly, so that uncertain cases are not treated as reliable.
32. As an agency user, I want low-confidence results separated from reliable results, so that follow-up priority is clearer.
33. As an agency user, I want dashboard tables for farmers, cattle, and detection events, so that operational monitoring is efficient.
34. As an agency user, I want maps or area summaries, so that clusters and jurisdiction trends are visible.
35. As an agency user, I want access to be filtered by consent tier, so that data governance rules are respected.
36. As Team 1, I want image classification contracts separated from platform contracts, so that image implementation can evolve without owning the entire platform.
37. As Team 1, I want mobile and backend image integration documented, so that image model behavior is consistent online and offline.
38. As Team 1, I want image evidence output schema defined, so that fusion can consume image scores reliably.
39. As Team 1, I want image preprocessing and quality rules documented, so that backend and mobile inference stay aligned.
40. As Team 1, I want image validation scope separated, so that image model tests do not depend on NLP implementation details.
41. As Team 2, I want NLP symptom questionnaire contracts separated from platform contracts, so that NLP implementation can evolve without owning image features.
42. As Team 2, I want offline NLP model responsibilities defined, so that mobile fusion can work without network connectivity.
43. As Team 2, I want NLP evidence output schema defined, so that fusion can consume symptom scores reliably.
44. As Team 2, I want symptom wording and note-processing documented, so that farmer input is consistent and testable.
45. As a backend developer, I want a Go gateway platform API, so that auth, data, dashboard endpoints, and fusion orchestration are centralized.
46. As a backend developer, I want Python inference services, so that image and NLP models can use Python ML stacks.
47. As a backend developer, I want PostgreSQL as the platform database, so that farmer, cattle, jurisdiction, consent, detection, and media data are relationally modeled.
48. As a backend developer, I want shared API contracts centralized, so that mobile, dashboard, Team 1, and Team 2 do not duplicate schemas.
49. As a backend developer, I want offline sync endpoints, so that mobile offline results become backend-visible.
50. As a dashboard developer, I want a Next.js TanStack dashboard, so that data-heavy agency interfaces can be built with strong table and query tooling.
51. As a project maintainer, I want docs split into team and system-integration areas, so that readers understand ownership.
52. As a project maintainer, I want a docs migration plan before moving files, so that existing links and thesis artifacts do not break unexpectedly.
53. As a project maintainer, I want shared contract approval before shared implementation changes, so that both teams remain aligned.
54. As a project maintainer, I want ADRs for hard-to-reverse architecture choices, so that future readers know why Go gateway and Python inference were chosen.

## Implementation Decisions

- SapiSehat is now a disease early detection platform, not an image-only Android app.
- Farmer user remains the primary user for mobile workflows.
- Agency user is the secondary dashboard user for monitoring and follow-up.
- The platform supports full cattle management and complete livestock profiles.
- Documentation describes target system and MVP phases.
- MVP disease classes remain `healthy`, `FMD`, and `LSD`, with extensible disease catalog later.
- Team documentation split uses `docs/team-1-image`, `docs/team-2-nlp`, and `docs/system-integration`.
- Shared contracts live in system integration docs.
- File moves are deferred until restructure plan approval.
- Shared changes require system integration contract updates before implementation or release.
- Team 1 focuses on image classification implementation across mobile and backend.
- Team 2 focuses on NLP model integration across mobile and backend.
- Both teams may contribute to shared backend, mobile, and dashboard features while respecting model ownership.
- Backend will be rebuilt as Go gateway with Python inference services.
- PostgreSQL is primary platform database.
- Agency dashboard uses Next.js and TanStack libraries.
- Farmer identity uses phone-number accounts.
- Agency identity uses role-jurisdiction accounts.
- Agency access is role-jurisdiction-consent based.
- Administrative jurisdiction follows Indonesia hierarchy.
- Backend data retention can include farmer data, cattle records, detection results, questionnaire answers, NLP notes, and uploaded images according to consent and governance.
- Existing no-retention inference policy must be revised in legacy docs.
- Mobile flow is cattle-first, with quick-scan escape.
- Online fusion is backend-primary.
- Offline mobile fusion is supported with later sync.
- Team 2 owns offline NLP model implementation.
- Parallel evidence fusion combines image evidence and NLP evidence into one result with evidence breakdown, confidence, reliability, and conflict status.
- Dashboard scope is disease risk signal monitoring, not confirmed outbreak declaration.

## Major Modules To Build Or Modify

- Platform Gateway module.
- Authorization module.
- Farmer Account module.
- Cattle Profile module.
- Detection Event module.
- Fusion Orchestrator module.
- Image Evidence module.
- NLP Evidence module.
- Offline Sync module.
- Media Storage module.
- Dashboard Query module.
- Mobile Cattle Flow module.
- Mobile Offline Fusion module.
- Dashboard UI module.
- Documentation Contract module.

Deep module opportunities:

- Authorization module: encapsulates role, jurisdiction, and consent checks.
- Fusion Orchestrator module: encapsulates image/NLP score combination, conflict handling, confidence bands, and reliability policy.
- Offline Sync module: encapsulates offline result state transitions and backend reconciliation.
- Dashboard Query module: encapsulates dashboard aggregation logic.
- Cattle Profile module: encapsulates livestock profile events with stable timeline interface.

## Testing Decisions

Good tests assert external behavior and contracts, not internal implementation details.

Test modules:

- Authorization module: role, jurisdiction, and consent combinations.
- Fusion Orchestrator module: matching evidence, conflicts, missing evidence, low confidence, low-quality image.
- Offline Sync module: offline-created results sync, preserve evidence versions, transition to backend canonical state.
- Cattle Profile module: cattle creation, event timeline behavior, transfer/sale events, detection attachment.
- Detection Event module: online, offline, and synced-offline states.
- Image Evidence contract: Team 1 output conforms to fusion input.
- NLP Evidence contract: Team 2 output conforms to fusion input.
- Dashboard Query module: agency users only see permitted jurisdiction and consent-scoped data.
- Mobile cattle-first flow: cattle selection, quick scan, result attachment, offline persistence.
- Dashboard UI: displayed risk language avoids confirmed outbreak or diagnosis wording.

Prior art in repo:

- Backend tests cover contract examples, contract properties, inference, model metadata, no-retention, TFLite parity, two-stage inference contracts, and model validation.
- Mobile tests cover repository behavior, Room DAO behavior, inference routing, model metadata, quality gate, history view model, settings view model, localization, report content, and acceptance-style flows.

Testing decisions:

- Add contract tests before replacing shared API schemas.
- Keep model-specific validation in team folders.
- Keep platform behavior tests in system integration/backend/mobile areas.
- Prefer property/contract tests for fusion and authorization.
- Avoid asserting private implementation details of Go gateway, Python services, or dashboard components.

## Out of Scope

- Confirmed veterinary diagnosis.
- Official outbreak declaration.
- Government-grade epidemiological surveillance certification.
- Adding diseases beyond `healthy`, `FMD`, and `LSD` in MVP.
- Exact fusion weighting formula until validation data exists.
- Exact consent-tier wording until governance policy is finalized.
- Full file migration from old docs paths before restructure plan approval.
- Team 2 NLP model internals beyond integration contract.
- Team 1 image model retraining beyond existing image subsystem scope.
- External government SSO integration.
- Microservices-first production-scale deployment.

## Further Notes

Created supporting docs:

- system integration README
- platform scope doc
- fusion contract doc
- data model doc
- docs restructure plan
- ADR for Go gateway with Python inference services

Open decisions remain:

- MVP boundary for complete livestock profile.
- Exact consent tiers.
- Media retention policy details.
- Dashboard risk thresholds.
- Exact Team 1 image evidence schema.
- Exact Team 2 NLP evidence schema.
- Offline sync conflict resolution.
- Whether legacy image-only docs should be moved or rewritten after approval.
