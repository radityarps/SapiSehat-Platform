# SapiSehat System Integration Docs

SapiSehat is a cattle disease early detection platform for farmers and local agencies in Indonesia.

The platform combines:

- farmer mobile app
- complete livestock profile management
- image-based early detection from Team 1
- NLP-based symptom screening from Team 2
- backend-primary image-plus-NLP fusion
- PostgreSQL platform database
- agency dashboard for disease risk monitoring
- offline mobile detection and later sync

## Documentation Split

```text
docs/
├── team-1-image/        # Image classification subsystem
├── team-2-nlp/          # NLP symptom screening subsystem
└── system-integration/  # Shared platform contracts and architecture
```

## System Integration Owns

- product scope and MVP phases
- farmer mobile flow
- complete livestock profile data model
- backend and database architecture
- shared API contracts
- image + NLP fusion contract
- agency dashboard behavior
- privacy, retention, consent, and access rules
- cross-team implementation contracts

## Team Ownership Summary

Team 1 focuses on implementing the image classification model across mobile and backend.

Team 2 focuses on implementing the NLP symptom model across mobile and backend.

Both teams may contribute to shared backend, mobile, and dashboard features, but model-specific features remain owned by the responsible model team.

Shared backend, mobile, dashboard, API, data model, or fusion-flow changes must update the relevant `docs/system-integration` contract before implementation or release.

## Key Docs

- [Docs Restructure Plan](DOCS_RESTRUCTURE_PLAN.md)
- [Platform Scope](product/PLATFORM_SCOPE.md)
- [Platform Rebuild PRD](product/PRD-platform-rebuild.md)
- [Fusion Contract](api-contracts/FUSION_CONTRACT.md)
- [Data Model](database/DATA_MODEL.md)
- [Architecture Contracts](architecture/README.md)
- [Backend Contracts](backend/README.md)
- [Mobile Flow Contracts](mobile/README.md)
- [Web Dashboard Contracts](web-dashboard/README.md)
- [Privacy and Security Contracts](privacy-security/README.md)
- [Deployment Contracts](deployment/README.md)
- [Cross-Team Validation](validation/README.md)
- [ADR 0002: Go Gateway with Python Inference](../adr/0002-go-gateway-python-inference.md)

## Contract Routing

| Shared decision or artifact | Contract location |
| --- | --- |
| Product scope, MVP phases, roles | `product/` |
| Platform architecture | `architecture/` |
| Go gateway/backend API behavior | `backend/` and `api-contracts/` |
| PostgreSQL entities and relationships | `database/` |
| Farmer mobile app flow | `mobile/` |
| Agency dashboard behavior | `web-dashboard/` |
| Consent, retention, access control | `privacy-security/` |
| Deployment topology | `deployment/` |
| Cross-team validation | `validation/` |
| Image-specific implementation | `../team-1-image/` |
| NLP-specific implementation | `../team-2-nlp/` |

## Shared Contract Approval Rule

Before implementing or releasing any shared backend, mobile, dashboard, API, data model, privacy, deployment, or fusion-flow change:

1. Update the relevant `docs/system-integration` contract.
2. Link impacted Team 1 and Team 2 docs when model-specific behavior changes.
3. Add or update an ADR when the decision is hard to reverse, surprising without context, and based on a real trade-off.
4. Keep implementation aligned with the approved contract.

Do not duplicate shared schemas in team folders. Team folders may reference shared contracts and add model-specific details only.
