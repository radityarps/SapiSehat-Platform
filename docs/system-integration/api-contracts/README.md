# API Contracts

Shared API contracts used by mobile, dashboard, Go gateway, Team 1 image services, and Team 2 NLP services.

## Contracts

- [Image + NLP Fusion Contract](FUSION_CONTRACT.md)
- [Bruno OpenCollection YAML](bruno/SapiSehat%20API/opencollection.yml)

## Rule

Shared API schemas live here. Team folders may add model-specific implementation notes, but must not define competing shared schemas.


## Quick-Scan Detection Attachment Tracer

Issue #6 adds emergency quick-scan behavior. API behavior:

1. Farmer can create a detection event without `cattle_id` through quick scan.
2. Unattached quick-scan result returns `attached: false` and `cattle_id: null`.
3. Farmer can attach an unattached result only to cattle they own.
4. Farmer cannot attach a result to another farmer's cattle.
5. Agency detection visibility includes only attached detections whose cattle pass role-jurisdiction-consent authorization.

The current FastAPI in-memory detection store is a tracer for the future Go gateway and PostgreSQL implementation.


## Bruno Collection

Open this folder in Bruno:

```text
docs/system-integration/api-contracts/bruno/SapiSehat API/
```

Collection root file:

```text
opencollection.yml
```
