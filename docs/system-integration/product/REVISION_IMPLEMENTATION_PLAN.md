# SapiSehat Revision Implementation Plan

This plan replaces the deleted production-rebuild direction. It captures the current revision goal: continue SapiSehat as a FastAPI-backed cattle early-detection platform with a new Flutter farmer app, an agency web dashboard, Team 1 image evidence, Team 2 NLP evidence, and jurisdiction-scoped infectious-disease risk monitoring.

SapiSehat remains an early detection and monitoring platform. It must not claim veterinary diagnosis or confirmed outbreak declaration.

## Resolved Product Direction

### Users and Surfaces

- Farmer users use the mobile app.
- Agency users use the web dashboard.
- There is no farmer web dashboard in the first release.
- A farmer owns day-to-day cattle record creation and maintenance.
- An agency user views jurisdiction-scoped farmer/cattle records and updates follow-up status/notes only.

### Accounts and Auth

- Farmer accounts support email/password and Google login.
- Farmer email/password registration does not require email verification in the first release.
- Agency accounts are admin-seeded and use email/password only.
- Agency password reset is manual/admin-reset only in the first release.
- The same email may be registered separately as a farmer account and an agency account.
- Agency account access does not automatically allow mobile farmer access; the user must register separately as a farmer.
- Farmer account access does not automatically allow web dashboard access.
- Google login is farmer/mobile only, not agency dashboard login.

### Backend Architecture

- Use the existing FastAPI direction, not a Go gateway rewrite.
- FastAPI owns platform APIs, authentication, PostgreSQL persistence, image detection records, dashboard data, and image+NLP fusion.
- First release uses a single deployable FastAPI backend with internal image/NLP modules or local adapters.
- PostgreSQL is the first-release database; in-memory storage is not acceptable for final revision behavior.

### Mobile Architecture

- Rewrite the active farmer app in Flutter.
- Target Android first.
- Move the current native Android/Kotlin app from `apps/mobile` to `apps/mobile-android-legacy` as reference.
- Create the new Flutter farmer app at `apps/mobile`.
- Flutter uses FastAPI online-first.
- Flutter keeps TFLite image inference as offline fallback and syncs fallback results later.

### Dashboard Architecture

- Keep Next.js + TanStack for the web dashboard.
- Dashboard consumes FastAPI platform APIs.
- First dashboard view is mixed: summary cards, review-item table, cluster risk signals, and map or area summary.
- Dashboard users have one agency role in first release; permissions are jurisdiction-scoped.

## Data and Privacy Rules

### Jurisdiction

- Dashboard geography uses Indonesian administrative hierarchy through district/subdistrict level.
- Province and regency/city are parent areas.
- Village is optional.
- Farmer names and cattle identities are visible only to authorized agency users inside their assigned jurisdiction.

### Stored Scan Images

- Every detection scan image is stored by the backend after a blocking first-scan acknowledgement.
- Storage is not optional consent in this revision.
- The app must clearly acknowledge before first scan that scan images are stored for monitoring and follow-up.
- Detection images are stored; non-detection camera/gallery photos are not in scope.
- EXIF metadata should be removed before storage.

### Archive Behavior

- Farmer “delete” in first release means archive/hide from mobile view.
- Archive does not delete backend record, stored scan image, or agency follow-up copy.
- Local mobile cache may be purged after 30 days.
- No true backend deletion is provided in first release.

## Cattle Management Scope

### First Release

Farmer mobile app supports:

- cattle profile create/read/update
- required first-release cattle fields:
  - tag/name
  - sex
  - estimated age or birth-year estimate
  - district/subdistrict location
- detection history per cattle
- active/sold/transferred status

### Later Scope

Full livestock record can later include:

- vaccination
- health notes
- reproduction
- pregnancy
- feed
- weight
- productivity
- sale details
- transfer details

## Evidence and Fusion

### Team 1 Image Evidence

- Team 1 image model can run before Team 2 NLP is ready.
- Image-only results must be clearly labeled as image-only evidence.
- Image-only results may create review items and risk signals, but must not be presented as fused evidence.

### Team 2 NLP Evidence

- A temporary NLP placeholder endpoint may exist.
- Placeholder returns NLP unavailable.
- Placeholder must not produce fake scores.
- Placeholder must not affect risk, fusion, dashboard alerts, or review item creation.
- Real Team 2 NLP integration is required before final release completion.

### Fusion Policy

- Real fusion combines Team 1 image evidence and Team 2 NLP evidence into one early detection result.
- Initial fusion uses equal weights: 50% image evidence and 50% NLP evidence.
- Conflicting or low-confidence evidence lowers reliability and marks the result as needs review.
- Existing confidence bands apply:
  - high: >= 80%
  - medium: 60–79%
  - low: < 60%
- Low-confidence fusion still shows likely class but marked needs review.
- Healthy results do not create review items; they may appear only in aggregate statistics.
- Insufficient visual evidence appears as aggregate/quality metric unless NLP evidence is risky.

## Agency Review and Alerting

### Review Items

- A single risky detection creates an agency review item.
- Agency users may update follow-up status and notes.
- Agency users may not edit farmer-owned cattle/farmer profile fields.
- Agency follow-up statuses:
  - New
  - In Review
  - Followed Up
  - Closed

### Farmer Follow-Up Status

Farmers see basic status only:

- Submitted
- Under Review
- Followed Up
- Closed

Farmers do not see agency internal notes.

### Cluster Risk Signals

- One risky detection is a review item, not an area alert.
- Cluster risk signal rule for first release: 3 risky results for the same disease in the same district within 7 days.
- First active disease set is FMD and LSD.
- The disease catalog can be extended later.

### Farmer Area Risk Advisory

- Farmer sees a generic area advisory only when a cluster risk signal exists in the farmer's district.
- Advisory wording must be safe, e.g. “Increased disease-risk reports in your district. Monitor cattle, improve biosecurity, and contact animal health officers if symptoms appear.”
- Do not expose other farmer names, cattle identities, exact scan details, or outbreak claims.

## Milestones

### Milestone 1 — Backend Foundation

Build FastAPI foundation first:

- PostgreSQL connection and migrations
- farmer account auth
- Google token verification for farmer login
- agency account auth with admin-seeded accounts
- cattle profile records
- cattle status values
- stored scan image handling
- image-only detection records
- dashboard-ready data APIs

### Milestone 2 — Mobile Migration and Flutter Foundation

- Move current Android app to `apps/mobile-android-legacy`.
- Create Flutter app at `apps/mobile`.
- Implement farmer login.
- Implement cattle list/create/edit/status.
- Implement camera scan upload to FastAPI.
- Implement detection history.
- Implement offline TFLite fallback path and later sync.

### Milestone 3 — NLP Placeholder and Agency Dashboard

- Add NLP placeholder endpoint returning NLP unavailable.
- Ensure placeholder has no risk/fusion/alert effect.
- Build Next.js + TanStack agency dashboard:
  - login through web surface
  - jurisdiction-scoped records
  - summary cards
  - review item table
  - image-only evidence labels
  - follow-up status/notes

### Milestone 4 — PostgreSQL Hardening

- Add DB constraints for accounts, cattle, detections, images, follow-up records, and jurisdictions.
- Add indexes for dashboard queries and cluster detection.
- Add seed flow for agency accounts.
- Add migration discipline.
- Add basic backup/export approach.

### Milestone 5 — Alerting and Farmer Advisory

- Implement hybrid alert threshold.
- Implement cluster trigger rule: 3 risky results for the same disease in the same district within 7 days.
- Show cluster risk signals on dashboard.
- Show generic farmer area risk advisory in Flutter app.
- Enforce safe non-diagnostic wording.

### Milestone 6 — Real Team 2 NLP Fusion Before Release

- Replace NLP placeholder with real Team 2 evidence contract/model integration.
- Generate real weighted fusion results.
- Preserve image-only historical records as image-only; do not automatically reprocess old records.
- New detections after NLP availability use real fusion.
- Final release is blocked until real Team 2 NLP evidence participates in fusion.

### Milestone 7 — Full End-to-End Release Gate

Validate complete flow:

- FastAPI backend
- PostgreSQL persistence
- Flutter farmer app
- Next.js dashboard
- farmer auth
- agency auth
- cattle records
- stored scan images
- image model result
- real NLP model result
- equal-weight fusion
- agency review item
- cluster risk signal
- farmer area advisory
- agency follow-up status
- farmer follow-up status
- farmer archive behavior

## Non-Goals for First Release

- No Go gateway rewrite.
- No microservices-first architecture.
- No farmer web dashboard.
- No agency editing of farmer-owned cattle records.
- No public agency self-registration.
- No Google login for agency dashboard.
- No true backend deletion by farmer.
- No confirmed outbreak declaration.
- No veterinary diagnosis claim.
- No fake/mock NLP scores.
- No iOS target in first release.
