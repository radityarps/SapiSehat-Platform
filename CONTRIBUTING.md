# Contributing to SapiSehat Platform

SapiSehat is a cattle disease early detection platform, not an image-only Android app. Contributions must preserve the platform contracts across farmer mobile, Team 1 image evidence, Team 2 NLP evidence, backend fusion, PostgreSQL target data model, and agency dashboard.

## Code of Conduct

- Be respectful, constructive, and evidence-based.
- Keep health wording safe: early indication, risk signal, follow-up priority.
- Do not claim veterinary diagnosis, confirmed outbreak, or official certificate.

## Documentation Ownership

Start here: [docs/README.md](docs/README.md).

| Area | Source of truth |
| --- | --- |
| Shared product/API/data/privacy/dashboard contracts | [docs/system-integration](docs/../README.md) |
| Team 1 image model/evidence work | [docs/team-1-image](docs/team-1-image/README.md) |
| Team 2 NLP model/evidence work | [docs/team-2-nlp](docs/team-2-nlp/README.md) |
| Platform PRD | [docs/system-integration/product/PRD-platform-rebuild.md](docs/system-integration/product/PRD-platform-rebuild.md) |

Legacy backend/mobile/model docs may describe earlier image-first scope. Treat them as subsystem notes unless system-integration docs say otherwise.

## Contract-First Rule

Update docs before code when changing shared behavior:

- API request/response schema
- disease classes or evidence score keys
- fusion/reliability rules
- consent/privacy/media retention
- farmer/cattle data model
- dashboard language or agency visibility
- offline sync behavior

Shared contract changes belong in `docs/system-integration/**`. Team-specific model changes belong in team docs unless they affect shared contracts.

## Branching Strategy

```text
main          <- production-ready code
dev           <- integration branch
feat/xxx      <- new feature
fix/xxx       <- bug fix
docs/xxx      <- documentation change
test/xxx      <- tests only
refactor/xxx  <- behavior-preserving restructure
```

## Development Setup

```bash
pnpm install
```

Backend tracer:

```bash
pnpm backend:dev
pnpm backend:test
```

Mobile legacy/image app:

```bash
pnpm mobile:run
pnpm mobile:test
```

Agency dashboard tracer lives in `apps/dashboard`.

## Implementation Guidelines

### Backend

Current executable tracer uses FastAPI and in-memory stores. Target architecture is Go gateway + Python inference services + PostgreSQL.

- Keep route handlers thin.
- Put validation/rules in small testable modules.
- Preserve existing endpoint contracts unless docs changed first.
- Add or update tests for every route/rule.

### Team 1 Image

- Own image evidence, image model versions, image quality rules, TFLite parity.
- Use disease keys exactly as shared contract requires: `healthy`, `FMD`, `LSD`.
- Rejected image evidence must not be accepted for fusion.

### Team 2 NLP

- Own questionnaire/notes evidence, NLP model versions, offline NLP behavior.
- Evidence must avoid diagnosis wording.
- Preserve shared disease score schema.

### Dashboard

- Use safe language: disease risk signal, possible increased risk, follow-up priority.
- Do not use: confirmed outbreak, diagnosis, infected, positive case.
- Scope every agency view by role, jurisdiction, and consent.

### Privacy and Consent

- Farmer/cattle/media visibility depends on role + jurisdiction + consent.
- Stored media requires `research_and_monitoring` consent.
- Do not add precise location, personal identifiers, or media retention behavior without docs update.

## Commit Messages

```text
<type>: <short description>
```

Types:

- `feat:` feature
- `fix:` bug fix
- `docs:` documentation
- `test:` tests
- `refactor:` restructure without behavior change
- `chore:` maintenance
- `ci:` CI/CD

Examples:

```text
feat: add nlp evidence contract tracer
docs: update dashboard risk signal wording
test: cover jurisdiction consent filtering
```

## Pull Request Checklist

Before opening PR:

1. Update shared contract docs first, if needed.
2. Add/update tests.
3. Run relevant tests.
4. Verify safe health language.
5. Link issue and affected docs.

## Testing

Minimum for backend tracer changes:

```bash
python -m pytest apps/backend/tests -q
```

For focused changes, run target tests plus related contract tests.

## Issue Labels

- `ready-for-agent`: implementation ready
- `question`: human decision needed
- `bug`: defect
- `enhancement`: feature or docs improvement

## Maintainers

- Raditya Rafif Pratama Sasmita
- Noval Putra Ramadhan

Teknik Informatika, Politeknik Negeri Semarang
