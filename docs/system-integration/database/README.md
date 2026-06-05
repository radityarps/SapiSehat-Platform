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
