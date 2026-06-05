# Web Dashboard Contracts

Shared agency dashboard behavior lives here.

Use this folder for registry views, detection monitoring, disease risk signal summaries, safe wording, access-scoped dashboard reads, and Next.js TanStack dashboard contracts.


## Agency Dashboard Registry Tracer

Executable API: `GET /api/agency/registry`. Dashboard registry returns agency-scoped farmers and cattle using role, jurisdiction, and consent gates.

Prototype UI path: `apps/dashboard/app/agency/registry/page.tsx`. It uses Next.js + TanStack Table-compatible patterns:

- authenticated request header `X-Agency-User-Id`.
- permitted farmers table.
- permitted cattle table.
- shared text filter.
- no records outside agency jurisdiction or consent scope.


## Agency Detection Monitoring Tracer

Executable API: `GET /api/agency/detection-monitoring`. Dashboard detection monitoring returns agency-scoped fused detection rows with:

- disease risk signal class.
- confidence.
- reliability.
- conflict status.
- image/NLP evidence breakdown.

Prototype UI path: `apps/dashboard/app/agency/detections/page.tsx`. UI uses safe language: disease risk signals, not diagnosis or confirmed outbreak wording.


## Disease Risk Signal Summary Tracer

Human-approved placeholder rule: **2+ signals**. Flag `possible_increased_risk` when two or more non-healthy `reliable` or `needs_review` fused detections appear in the same jurisdiction within a 7-day window.

Executable API: `GET /api/agency/risk-signals`. Dashboard output is scoped by agency role, jurisdiction, and consent. Language must say possible increased disease risk signal and follow-up priority only; no confirmed outbreak or veterinary diagnosis claims.

Prototype UI path: `apps/dashboard/app/agency/risk-signals/page.tsx`.
