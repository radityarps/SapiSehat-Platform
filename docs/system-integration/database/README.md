# Database Contracts

Shared PostgreSQL data model contracts for farmer accounts, cattle records, administrative jurisdictions, consent, detection events, media, and dashboard reporting.

## Contracts

- [Data Model](DATA_MODEL.md)


## Phone-Number Farmer Account Tracer

Issue #3 adds the first farmer identity tracer. Farmer account behavior:

1. Phone number is canonical farmer identity and normalizes Indonesian numbers to `+62` format.
2. Duplicate phone numbers sign in to the existing farmer account instead of creating a second identity.
3. New farmer accounts include name, phone number, administrative jurisdiction, and initial consent state.
4. Initial consent state is `private` until farmer opts into agency monitoring.
5. Stable farmer id is available for downstream cattle and detection records.

The current FastAPI in-memory store is a tracer for the future Go gateway and PostgreSQL implementation.


## Cattle-First Profile Tracer

Issue #4 adds the first cattle-first profile path. Cattle profile behavior:

1. Cattle profile must link to an existing farmer account.
2. Profile stores tag/identity, sex, breed or `unknown`, age in months or birth year estimate, status, and location jurisdiction.
3. Farmer-owned cattle can be listed and selected before starting early detection.
4. Farmer cannot select another farmer's cattle.
5. Agency cattle reads must use the same role-jurisdiction-consent access rule as farmer reads.

The current FastAPI in-memory store is a tracer for the future Go gateway and PostgreSQL implementation.


## Livestock Profile Timeline Tracer

Issue #5 adds the first livestock profile timeline path. Timeline behavior:

1. Cattle profile supports operational timeline events.
2. Supported event type in tracer: `vaccination`.
3. Event stores date, title, description, structured payload, and creator id.
4. Farmer-owned cattle detail includes timeline events ordered newest first.
5. Agency cattle detail includes timeline only when role-jurisdiction-consent authorization allows the cattle read.

The current FastAPI in-memory event store is a tracer for the future Go gateway and PostgreSQL implementation.


## Stored Media Metadata Tracer

Media metadata table shape for tracer:

- `id`.
- `farmer_id`.
- `cattle_id` nullable.
- `detection_id` nullable.
- `checksum`.
- `consent_scope`.
- `storage_reference`.

First retention policy stores media only under `research_and_monitoring` consent.
