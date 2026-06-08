# SapiSehat Context

SapiSehat is a cattle disease early detection platform for farmers and local livestock/animal-health agencies in Indonesia. It combines farmer mobile cattle records, Team 1 image evidence, Team 2 NLP evidence, FastAPI backend storage/fusion, and agency dashboard monitoring.

SapiSehat supports early indication and follow-up prioritization. It must not claim veterinary diagnosis or confirmed outbreak declaration.

## Language

**Disease Early Detection Platform**:
Canonical product identity for SapiSehat: farmer-facing mobile workflows and agency-facing monitoring for early cattle disease-risk indication.
_Avoid_: Image-only app, farmer inventory only, clinical diagnosis system

**Farmer User**:
Primary mobile user who registers an account, manages cattle records, submits detection scans, views results, and receives basic follow-up/advisory information.
_Avoid_: Agency operator, dashboard user, veterinarian-only user

**Agency User**:
Web-dashboard user from livestock or animal-health service who monitors jurisdiction-scoped farmer/cattle/detection data and records follow-up status/notes.
_Avoid_: Farmer user, cattle record owner, public self-registered user

**Farmer Account**:
Mobile account registered by farmer using email/password or Google login. Phone number is optional contact information.
_Avoid_: Phone-primary identity, anonymous-only farmer, agency-created farmer identity

**Agency Account**:
Web-dashboard identity created by administrator and signed in with email/password only.
_Avoid_: Google agency login, public agency self-registration, farmer account reuse

**Surface-Specific Account**:
Account boundary where same email may exist separately as a **Farmer Account** for mobile and an **Agency Account** for web, without automatic permission sharing.
_Avoid_: One merged account, automatic mobile access from agency account, automatic dashboard access from farmer account

**Flutter Farmer App**:
Android-first active mobile app built in Flutter for farmer login, cattle records, online-first detection, offline TFLite fallback, sync, history, archive, and area risk advisory.
_Avoid_: Native Android active app, iOS-first app, web/PWA farmer app

**Legacy Android App**:
Former native Android/Kotlin app retained as migration reference after moving from `apps/mobile` to `apps/mobile-android-legacy`.
_Avoid_: Active farmer app, deleted reference app, mixed Flutter module

**FastAPI Platform Backend**:
Single shared backend that owns authentication, PostgreSQL persistence, farmer/cattle records, stored scan images, dashboard APIs, image evidence handling, NLP evidence handling, and image-plus-NLP fusion.
_Avoid_: Go gateway rewrite, microservices-first platform, team-owned backend silos

**Platform PostgreSQL Database**:
First-release source of truth for accounts, cattle records, jurisdictions, detection events, media metadata, review items, follow-up records, and dashboard reporting.
_Avoid_: In-memory final storage, SQLite production database, team-specific separate databases

**Next.js TanStack Dashboard**:
Agency-facing web dashboard built with Next.js and TanStack libraries, consuming FastAPI APIs.
_Avoid_: Farmer dashboard, FastAPI template dashboard, Streamlit production dashboard

**Farmer-Owned Cattle Record**:
Cattle profile created and maintained by farmer in mobile app, including first-release fields such as tag/name, sex, estimated age or birth-year estimate, district/subdistrict location, status, and detection history.
_Avoid_: Agency-owned cattle CRUD, scan-only record, backend-only hidden profile

**Complete Livestock Profile**:
Longer-term cattle profile that may later include vaccination, health events, reproduction, pregnancy, feed, weight, productivity, sale, and transfer details.
_Avoid_: First-release required scope, detection-only profile, agency-only registry

**Administrative Jurisdiction**:
Indonesia area hierarchy used for agency access and reporting: province, regency/city, district/subdistrict, and optional village.
_Avoid_: Precise GPS-only scope, national-global access, arbitrary unsourced area label

**Jurisdiction-Limited Visibility**:
Rule where farmer names, cattle identities, and exact records are visible only to authorized agency users inside assigned jurisdiction.
_Avoid_: All-agencies-see-all, global farmer visibility, mask-everything-by-default

**Disease Class**:
Canonical disease category stored independently of display text. First active set is `healthy`, `FMD`, and `LSD`.
_Avoid_: Indonesian-only labels, numeric-only labels, unlimited first-release disease scope

**Extensible Disease Catalog**:
Disease taxonomy that starts with FMD and LSD risk monitoring and can add other cattle diseases later without changing core platform concepts.
_Avoid_: Fixed forever three-class taxonomy, unbounded initial scope

**Image Evidence**:
Team 1 model output from cattle scan image, including disease class scores, confidence, model version, and evidence state.
_Avoid_: Final diagnosis, unlabeled photo upload, Team 2-owned image result

**NLP Evidence**:
Team 2 model output from symptom input, used as separate evidence for fusion once real Team 2 integration is available.
_Avoid_: Team 1-owned NLP behavior, fake symptom score, free-form undocumented output

**Image-Only Evidence Result**:
Early detection result produced from Team 1 image evidence before Team 2 NLP evidence is available, clearly labeled image-only and not presented as fused evidence.
_Avoid_: Fake fusion result, mock NLP result, unlabeled partial evidence

**NLP Placeholder**:
Temporary backend contract response stating NLP is unavailable, without producing scores or affecting risk, fusion, review items, or alerts.
_Avoid_: Fake neutral NLP, mock symptom score, placeholder-driven alert

**Weighted Evidence Fusion**:
Backend process that combines image evidence and real NLP evidence into one early detection result using defined weights and reliability handling.
_Avoid_: Image-always-wins, NLP-always-wins, two separate farmer-facing results

**Equal-Weight Fusion**:
Initial real fusion setting where image evidence and NLP evidence each contribute 50% before validation-based tuning.
_Avoid_: Image-heavy default, NLP-heavy default, no-weight fusion

**Early Detection Result**:
Farmer-facing scan outcome containing evidence state, likely class, confidence band, handling advice, and non-diagnostic wording.
_Avoid_: Diagnosis, clinical verdict, outbreak confirmation

**Confidence Level**:
Interpretation band: high at 80% or above, medium at 60–79%, low below 60%.
_Avoid_: Binary certainty, uncalibrated certainty

**Insufficient Visual Evidence**:
Result state when image quality, confidence, or visible symptom evidence is not enough to support a disease-class result.
_Avoid_: Unknown disease diagnosis, forced healthy result, silent model failure

**Stored Scan Image**:
Detection scan image retained by backend after inference as part of detection record and agency follow-up data.
_Avoid_: Temporary inference-only upload, unstored scan image, non-detection camera photo

**Scan Image Storage Notice**:
Blocking first-scan acknowledgement that every detection scan image is stored by backend for monitoring and follow-up.
_Avoid_: Hidden storage, silent upload, optional storage consent

**Farmer Archive Action**:
Farmer action that hides a detection record from mobile view without deleting backend record, stored scan image, or agency follow-up copy.
_Avoid_: Backend delete, agency record deletion, permanent purge

**Agency Monitoring Dashboard**:
Web view combining jurisdiction summary cards, review-item table, cluster risk signals, and map or area summary for agency follow-up.
_Avoid_: Farmer cattle-management screen, map-only dashboard, analytics-only dashboard

**Agency Review Item**:
Single risky early detection submission visible to authorized agency users for review and possible follow-up.
_Avoid_: Outbreak alert, confirmed case, automatic diagnosis

**Agency Follow-Up Status**:
Agency workflow state for review item: New, In Review, Followed Up, or Closed.
_Avoid_: Farmer record status, diagnosis status, unlimited custom workflow

**Farmer Follow-Up Status**:
Farmer-visible simplified lifecycle for submitted detection: Submitted, Under Review, Followed Up, or Closed.
_Avoid_: Agency internal notes, diagnosis status, hidden-only state

**Cluster Risk Signal**:
Area-level dashboard signal created when multiple related risky submissions indicate possible infectious-disease spread within jurisdiction and time window.
_Avoid_: Single-case alert, confirmed outbreak, diagnosis cluster

**Hybrid Alert Threshold**:
Policy where one risky submission becomes an **Agency Review Item**, while a jurisdiction/time cluster becomes a **Cluster Risk Signal**.
_Avoid_: Single-case public alert, cluster-only review, manual-only alerting

**Cluster Trigger Rule**:
First-release rule where 3 risky results for same disease in same district within 7 days escalate to **Cluster Risk Signal**.
_Avoid_: 1-case area alert, cross-district mixing, open-ended threshold

**Farmer Area Risk Advisory**:
Generic farmer-facing notice shown only when **Cluster Risk Signal** exists in farmer district, with safe prevention wording and no other farmer/cattle details.
_Avoid_: Nearby farmer details, outbreak warning, confirmed spread claim

**Online-First Detection**:
Mobile detection flow where Flutter calls FastAPI first, then uses on-device TFLite image inference only as offline fallback and syncs later.
_Avoid_: Offline-first, server-only no fallback, local-only final storage

**On-Device TFLite Fallback**:
Offline image inference path in Flutter using bundled TFLite model when network/backend is unavailable.
_Avoid_: Primary inference path, remote model push, NLP fallback ownership by Team 1

**Full E2E Release Gate**:
Final release validation across FastAPI, PostgreSQL, Flutter, dashboard, image model, real NLP model, equal-weight fusion, scan image storage, review items, cluster alerts, farmer advisories, follow-up status, and archive behavior.
_Avoid_: Backend-only test, manual demo only, release without real NLP

## Relationships

- **Farmer User** uses **Flutter Farmer App** only; there is no farmer web dashboard in first release.
- **Agency User** uses **Next.js TanStack Dashboard** only.
- **Farmer Account** supports email/password and Google login.
- Farmer email/password registration does not require email verification in first release.
- **Agency Account** supports email/password only and is admin-seeded.
- Agency password reset is manual/admin reset only in first release.
- **Surface-Specific Account** allows same email on mobile and web only as separate records; permissions do not merge.
- **Flutter Farmer App** uses **FastAPI Platform Backend** online-first.
- **On-Device TFLite Fallback** produces offline image-only result and syncs later.
- **Legacy Android App** remains reference only after repo move.
- **FastAPI Platform Backend** uses **Platform PostgreSQL Database** for final first-release storage.
- **Stored Scan Image** is created for every detection scan after **Scan Image Storage Notice** acknowledgement.
- EXIF metadata should be removed before storing detection images.
- Non-detection camera/gallery photos are not part of **Stored Scan Image** scope.
- **Farmer Archive Action** hides records in mobile view but preserves backend data and agency follow-up copy.
- **Farmer-Owned Cattle Record** is created/maintained by farmer; agency users do not edit farmer-owned cattle fields.
- **Jurisdiction-Limited Visibility** controls exact farmer/cattle identity visibility on dashboard.
- **Image-Only Evidence Result** may create image-only **Agency Review Item** and image-only risk signal during early development.
- **NLP Placeholder** has no effect on **Weighted Evidence Fusion**, **Agency Review Item**, or **Cluster Risk Signal**.
- Real **NLP Evidence** integration is required before release completion.
- **Weighted Evidence Fusion** is owned by **FastAPI Platform Backend**.
- **Equal-Weight Fusion** is initial setting when real image and NLP evidence are both available.
- Healthy results do not create **Agency Review Item**; they may appear in aggregate statistics.
- Low-confidence or conflicting fusion lowers reliability and may mark result needs review.
- One risky **Early Detection Result** creates **Agency Review Item**.
- Multiple related review items matching **Cluster Trigger Rule** create **Cluster Risk Signal**.
- **Agency User** may update **Agency Follow-Up Status** and notes only.
- **Farmer User** sees **Farmer Follow-Up Status** only, not agency internal notes.
- **Farmer Area Risk Advisory** appears only when **Cluster Risk Signal** exists in farmer district.
- Advisory wording must avoid outbreak declaration and identity leakage.

## Milestone Language

1. **Backend Foundation**: FastAPI auth, PostgreSQL, farmer/agency accounts, cattle records, stored scan images, image-only detection records, dashboard-ready APIs.
2. **Mobile Migration and Flutter Foundation**: move Android legacy app, create Flutter app, implement farmer auth, cattle records, scan upload, history, offline TFLite fallback, sync.
3. **NLP Placeholder and Agency Dashboard**: add unavailable NLP contract, build Next.js dashboard with jurisdiction-scoped review flow and image-only labels.
4. **PostgreSQL Hardening**: constraints, indexes, agency seeds, migration discipline, backup/export basics.
5. **Alerting and Farmer Advisory**: cluster trigger, dashboard cluster risk signals, farmer area advisory.
6. **Real Team 2 NLP Fusion Before Release**: replace placeholder with real NLP, generate real fusion, keep historical image-only records unchanged.
7. **Full E2E Release Gate**: validate all core backend, mobile, dashboard, fusion, alert, follow-up, archive, and storage flows.

## Flagged Ambiguities Resolved

- "mobile stack" means **Flutter Farmer App** for Android first release; native Android/Kotlin becomes **Legacy Android App**.
- "backend architecture" means **FastAPI Platform Backend**, not Go gateway.
- "farmer login" means **Farmer Account** with email/password and Google login; phone is optional contact.
- "same email on mobile and dashboard" means **Surface-Specific Account**; no automatic cross-surface access.
- "combine Team 1 and Team 2 models" means **Weighted Evidence Fusion** with real **NLP Evidence** before release.
- "Team 2 NLP not ready" means **Image-Only Evidence Result** plus **NLP Placeholder** temporarily; no fake NLP scores.
- "scan image storage" means every detection scan image is stored after blocking notice; storage is not optional consent.
- "delete detection record" means **Farmer Archive Action**, not backend deletion.
- "dashboard alert" means single case = **Agency Review Item**, cluster = **Cluster Risk Signal**.
- "cluster rule" means 3 risky results for same disease in same district within 7 days.
- "farmer area alert" means **Farmer Area Risk Advisory**, not outbreak warning or nearby-case detail.
- "agency dashboard edits" means agency follow-up status/notes only, not farmer cattle CRUD.
- "farmer follow-up visibility" means simplified status only, no internal agency notes.
