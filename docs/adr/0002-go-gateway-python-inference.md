# ADR 0002: Go Gateway with Python Inference Services

## Status

Accepted

## Context

SapiSehat scope changed from an image-only Android early detection application into a cattle disease early detection platform for farmers and local agencies. The platform now needs:

- farmer accounts
- complete livestock profile records
- agency dashboard access
- jurisdiction-scoped authorization
- PostgreSQL-backed persistence
- image-based early detection
- NLP-based symptom screening
- backend-primary image-plus-NLP fusion
- offline result sync from mobile

The existing backend is a Python FastAPI image inference server. That shape is too narrow for the new platform because it centers inference rather than platform data, access control, dashboard APIs, and cross-team contracts.

At the same time, image and NLP inference remain easier to build, test, and evolve in Python because the model stacks and current image code are Python-based.

## Decision

Rebuild the backend as a Go gateway with Python inference services.

The Go gateway owns:

- public platform API
- authentication and authorization
- farmer, cattle, and agency data access
- PostgreSQL persistence boundaries
- agency dashboard endpoints
- shared API contracts
- routing to image and NLP inference services
- backend-primary fusion orchestration
- offline result sync endpoints

Python services own:

- image classification inference
- image preprocessing/model serving
- NLP symptom screening inference
- model-specific inference contracts
- model-specific validation support

## Alternatives Considered

### FastAPI-only platform backend

Pros:

- easiest reuse of current backend
- simple integration with image and NLP models
- one language for platform and inference

Cons:

- less aligned with planned gateway/platform split
- future platform concerns may mix with model-specific inference logic
- harder to communicate clean separation between shared platform API and team-specific model services

### Node/NestJS backend with Python inference

Pros:

- strong web/dashboard ecosystem
- common API backend patterns

Cons:

- introduces a third main backend runtime beside Python and Go-related existing migration docs
- Python inference still needs separate service
- less direct continuity with existing Go gateway migration direction

### Microservices from the start

Pros:

- clean service isolation
- scalable architecture story

Cons:

- too much operational overhead for student project scope
- requires more deployment, observability, and service coordination than needed for MVP

### Keep current image inference backend

Pros:

- lowest short-term implementation cost
- current image detection API continues working

Cons:

- cannot represent full platform backend needs
- dashboard, database, access control, and NLP integration become bolted-on
- keeps old image-only product architecture

## Consequences

Positive:

- platform API and model inference responsibilities become explicit
- Team 1 can focus on image inference integration
- Team 2 can focus on NLP inference integration
- shared backend contracts can live in `docs/system-integration`
- PostgreSQL-backed platform data model can evolve separately from model-serving code
- dashboard can consume stable Go gateway APIs

Negative:

- backend rebuild cost increases
- local development needs at least Go, Python, and PostgreSQL
- service boundaries and contracts must be documented early
- integration tests become more important

## Follow-up Work

- Define Go gateway API contract in `docs/system-integration/api-contracts/`.
- Define Python image inference contract in `docs/team-1-image/`.
- Define Python NLP inference contract in `docs/team-2-nlp/`.
- Define PostgreSQL data model in `docs/system-integration/database/`.
- Update docs migration plan after this ADR is reviewed.
