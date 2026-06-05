# Privacy and Security Contracts

Shared consent, retention, authorization, and data-access rules live here.

Use this folder for role-jurisdiction-consent access, media retention policy, farmer consent tiers, and agency visibility rules.


## Role-Jurisdiction-Consent Authorization Tracer

Issue #2 adds the first executable authorization tracer. Agency visibility is allowed only when all gates pass:

1. Agency user has a recognized role.
2. Farmer record is inside the agency user's assigned administrative jurisdiction or descendant jurisdiction.
3. Farmer consent tier allows agency monitoring.

The current FastAPI endpoint is a prototype for this rule until the Go gateway and PostgreSQL implementation replaces it. Shared access behavior must stay compatible with this contract.


## Stored Media Governance Tracer

Human-approved first retention rule: **Consent opt-in**. Store media metadata and storage reference only when farmer consent is `research_and_monitoring`.

Stored metadata includes:

- owner `farmer_id`.
- optional `cattle_id`.
- optional `detection_id`.
- `checksum`.
- `consent_scope`.
- `storage_reference`.

Agency media access must pass role, jurisdiction, and consent authorization before metadata is visible.
