# ADR 0003: Big-Bang Production Rebuild

## Status
Accepted

## Context
SapiSehat has a FastAPI in-memory tracer proving platform behavior. Target production stack is Go gateway, PostgreSQL, internal Python image inference, internal Python NLP inference, Android integration, and Next.js/TanStack dashboard.

Options: strangler rebuild or big-bang rewrite.

## Decision
Use a big-bang production rebuild. Keep FastAPI tracer tests as Tracer Acceptance Contract. Production code must match behavior, not reuse tracer internals.

## Consequences
Positive: cleaner production boundaries, no tracer structure carried forward, explicit Go/PostgreSQL/service/dashboard/mobile architecture.

Negative: higher integration risk and more work before end-to-end value.

Mitigation: production API contract first, acceptance replay tests, do not retire tracer until production stack passes accepted scenarios.
