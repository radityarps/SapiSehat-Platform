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
Mobile account registered by farmer using email/password. Phone number is optional contact information. Google login was removed as overkill for tugas akhir scope.
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

**Backend Test Entry Point**:
Repository-root `tests/test_backend_suite.py` wrapper that runs backend suite from `apps/backend/tests` so `python -m pytest tests -q` works from repo root.
_Avoid_: Repo-root test folder with duplicated backend cases, backend-only command that fails from root

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

**Active Detection Class**:
Canonical outcome that a currently deployed model may produce as an accepted cattle result. The active set is `healthy` and `FMD`; `LSD` is historical-only and `non_cattle` is an input rejection, not a disease result.
_Avoid_: Disease Class, model output class, Indonesian-only label, treating `non_cattle` as disease

**Historical Detection Class**:
Canonical outcome retained only to preserve records produced by retired model versions. `LSD` records remain auditable through admin/export surfaces but cannot be created by active inference or shown in farmer-facing product flows.
_Avoid_: Active LSD support, relabeling historical records, deleting retired-model evidence

**Non-Cattle Rejection**:
Outcome indicating that the submitted image is outside the cattle-image domain. It stops before image evidence fusion and is never stored or counted as a disease result.
_Avoid_: Disease class, healthy result, low-confidence diagnosis

**Extensible Disease Catalog**:
Disease taxonomy that actively monitors FMD while preserving retired classes such as LSD for auditability and allowing validated disease classes to be added later.
_Avoid_: Fixed forever classifier taxonomy, deleting historical classes, unbounded initial scope

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

**Private Object Storage**:
S3-compatible storage for detection image bytes, using local MinIO in development and production S3-compatible buckets later, while metadata stays in PostgreSQL.
_Avoid_: Public bucket images, database blob storage, local filesystem-only production storage

**Signed Media URL**:
Short-lived backend-issued URL that lets authorized agency users preview or download private stored scan images without making bucket objects public.
_Avoid_: Public image URL, permanent shared link, direct bucket credential exposure

**Agency Audit Log Read API**:
Admin-only endpoint for recent backend audit events such as predictions, media uploads, signed media URL issuance, and follow-up creation.
_Avoid_: Public audit feed, farmer-visible internal notes, normal agency review queue

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
- **Farmer Account** supports email/password only; Google login is out of scope for tugas akhir.
- Farmer email/password registration does not require email verification in first release.
- **Agency Account** supports email/password only and is admin-seeded.
- Agency password reset is manual/admin reset only in first release.
- **Surface-Specific Account** allows same email on mobile and web only as separate records; permissions do not merge.
- **Flutter Farmer App** uses **FastAPI Platform Backend** online-first.
- **On-Device TFLite Fallback** produces offline image-only result and syncs later.
- **Legacy Android App** remains reference only after repo move.
- **FastAPI Platform Backend** uses **Platform PostgreSQL Database** for final first-release storage.
- Root repo `tests/test_backend_suite.py` delegates to backend suite under `apps/backend/tests` so root pytest command stays usable.
- **Stored Scan Image** is created for every detection scan after **Scan Image Storage Notice** acknowledgement.
- **Private Object Storage** stores scan image bytes; **Platform PostgreSQL Database** stores media metadata and object keys.
- **Signed Media URL** is issued by backend only after agency authorization checks.
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
- **Non-Cattle Rejection** stops before image/NLP fusion, persistence as disease evidence, review-item creation, and cluster-risk calculation.
- New image and NLP evidence use only `FMD` and `healthy` scores; `LSD` evidence is accepted only from explicitly retired model versions during historical offline synchronization.
- Historical `LSD` records remain unchanged and are accessible only through admin/export paths, not active farmer or agency product views.
- Low-confidence or conflicting fusion lowers reliability and may mark result needs review.
- One risky **Early Detection Result** creates **Agency Review Item**.
- Multiple related review items matching **Cluster Trigger Rule** create **Cluster Risk Signal**.
- **Agency User** may update **Agency Follow-Up Status** and notes only.
- **Agency Audit Log Read API** is admin-only and exposes recent audit events for debugging and ops review.
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
- "farmer login" means **Farmer Account** with email/password; phone is optional contact.
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

**Foundation-Complete Farmer App**:
Milestone 2 target for Flutter mobile: onboarding, terms/privacy/storage acknowledgement, login/register, farmer home shell, cattle CRUD/status/archive, camera/gallery scan upload, offline fallback with sync queue, detection history, profile, settings, configurable backend URL, and safe wording. It excludes real Team 2 NLP, cluster risk advisory, agency follow-up workflow, and final E2E release gate.
_Avoid_: Tracer-only shell, final release app, dashboard scope, real NLP fusion scope

**Terms & Privacy Checklist**:
Mobile farmer app checklist shown from registration and settings so farmer can review terms, privacy, non-diagnostic product boundaries, and scan-image storage expectations. It does not replace the blocking first-scan **Scan Image Storage Notice** acknowledgement.
_Avoid_: Hidden legal copy, scan consent replacement, diagnosis disclaimer buried only in settings

**Farmer Mobile Registration**:
Flutter farmer app email/password account creation flow with name, email, password, optional phone, jurisdiction fields, and visible **Terms & Privacy Checklist** before submit. Email verification is not required for first release. Native Google sign-in may be deferred behind a clear unavailable state until the mobile SDK path is wired.
_Avoid_: Agency registration, email-verification blocker, hidden terms, fake Google success

**Jurisdiction Autofill from GPS**:
Registration/profile helper that proposes a district/subdistrict jurisdiction and full address from device location via Nominatim reverse geocoding, letting the farmer confirm or edit it. It is a convenience input aid, not a precise geofence truth source. Requires `ACCESS_FINE_LOCATION` and `ACCESS_COARSE_LOCATION` Android permissions, requested at runtime with an explain-first dialog.
_Avoid_: Silent auto-override, hard GPS lock, exact coordinate storage as profile identity

**Farmer Address Field**:
Optional free-text address on farmer account, populated via GPS auto-fill or manual entry. Stored in `AccountModel.address` and returned in auth responses. Used by agency dashboard registry to show farmer location.
_Avoid_: Required registration field, precise GPS coordinate storage, address-as-identity

**Agency Dashboard RBAC**:
Role-based access control for agency dashboard with 5 roles: admin, province_officer, district_officer, village_officer, viewer. Each role determines which nav items, pages, and data are visible, scoped by jurisdiction assignment.
_Avoid_: Single admin-only dashboard, no-role all-access, farmer RBAC

**Agency Notification**:
In-app notification for agency dashboard users, stored in `NotificationModel` and delivered via `GET /api/notifications`. Emitted by backend on follow-up status changes. Read/unread state tracked per account. Bell icon with unread badge in dashboard topbar opens a right-drawer sheet.
_Avoid_: Email/SMS notification, push notification, farmer-facing agency notification

**Dashboard Settings Page**:
Agency dashboard page at `/agency/settings` with three sections: profile (edit display name), password change (auto-logout on success), and logout. All destructive actions guarded by AlertDialog confirmation.
_Avoid_: Agency registration, admin-only settings, farmer settings page

**Debug Mode Pre-fill**:
Flutter `kDebugMode` flag that pre-fills login/register fields with seeded dev credentials (`farmer@example.com` / `strong-password`) in debug builds only. Empty in release builds.
_Avoid_: Hardcoded production credentials, env-file credentials for mobile, release-time pre-fill

**Farmer Account Archive**:
Backend-supported soft delete for farmer account that disables future login while preserving existing records, scan images, and follow-up history. It is reversible only by admin policy, not by farmer self-service in first release.
_Avoid_: Permanent deletion, cascade purge, hidden local-only logout

**Feature Tour Onboarding**:
First-launch farmer mobile onboarding with two or three Indonesian-language feature screens for cattle management, scan risk signals, and offline sync. Privacy and storage acknowledgement are handled through registration/settings and the first-scan notice, not as onboarding screens.
_Avoid_: Legal-only onboarding, alarmist disease promises, diagnosis claims

**Offline TFLite Model Asset**:
Legacy Android asset `cattle_disease.tflite` under `apps/mobile-android-legacy/app/src/main/assets/` is the current offline image inference model source for Flutter migration.
_Avoid_: Missing-model assumption, hardcoded fake offline scores

**Complete Livestock Profile Fields**:
Cattle profiles now store optional physical, reproductive, health, economic, and notes data: `name`, `color`, `weight_kg`, `reproductive_status`, `is_pregnant`, `last_calving_date`, `last_vaccination_date`, `last_deworming_date`, `health_notes`, `purchase_date`, `purchase_price_idr`, and `notes`. Timeline events remain separate for dated operational history, while profile fields store latest-known summary values. Development seeding includes realistic Indonesian cattle data for these fields.
_Avoid_: diagnosis claims, required completion before scanning, replacing timeline events with summary-only data

**Guide Article**:
Admin-curated, multilingual educational content shown in the Flutter Farmer App, such as cattle-profile guidance, app usage, biosecurity, and FMD information. Bahasa Indonesia is required for publication; other translations are optional.
_Avoid_: Blog Post, news feed, Farmer-Owned Cattle Record, user-generated content

**Guide Category**:
Admin-managed grouping for Guide Articles. The system-owned `Umum` category is the permanent fallback when another category is archived.
_Avoid_: hard-coded mobile filter, disease taxonomy, article tag

**Published Guide Snapshot**:
One integrity-checked version of every published Guide Article, Guide Category, translation, and required media file that the mobile app can activate atomically for offline reading.
_Avoid_: partially downloaded catalog, per-screen live content, mixed content versions

**Bundled Guide Catalog**:
The install-time Published Guide Snapshot packaged with the Flutter Farmer App so guidance exists before the first successful online synchronization. Its stable article and category IDs match the seeded CMS catalog.
_Avoid_: permanent parallel content source, demo-only fixture, empty first-install cache

**Guide Editorial Audit Event**:
An immutable record of an admin creating, editing, publishing, unpublishing, archiving, or moving Guide content. It records action metadata but does not preserve a restorable copy of every article revision.
_Avoid_: full revision history, reader analytics, mutable activity note
