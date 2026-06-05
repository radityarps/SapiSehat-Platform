# Privacy and Security Contracts

Shared consent, retention, authorization, and data-access rules live here.

Use this folder for role-jurisdiction-consent access, media retention policy, farmer consent tiers, and agency visibility rules.


## Role-Jurisdiction-Consent Authorization Tracer

Issue #2 adds the first executable authorization tracer. Agency visibility is allowed only when all gates pass:

1. Agency user has a recognized role.
2. Farmer record is inside the agency user's assigned administrative jurisdiction or descendant jurisdiction.
3. Farmer consent tier allows agency monitoring.

The current FastAPI endpoint is a prototype for this rule until the Go gateway and PostgreSQL implementation replaces it. Shared access behavior must stay compatible with this contract.
