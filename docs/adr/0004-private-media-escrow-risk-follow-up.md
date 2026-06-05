# ADR 0004: Private Media Escrow for Risk Follow-Up

## Status
Accepted

## Context
Farmers may choose private consent, but agency follow-up may require farm-level detail and media when area disease-risk threshold is reached.

## Decision
Use Private Media Escrow for private-consent detections.

Rules:
- private media encrypted at rest
- hidden from routine agency access
- revealed only when risk-signal threshold triggers follow-up
- threshold: 2+ non-healthy detections, same disease class, same district, within 7 days
- reliability values `reliable` and `needs_review` count
- private reveal exposes full follow-up record, including escrowed media
- escrow media purged after 30 days if no threshold trigger occurs
- offline private media uses capture time; older than 30 days at sync is not escrowed
- access scoped by RBAC, jurisdiction, and consent policy
- every view/download/export logged in immutable audit events
- wording remains disease risk signal, not diagnosis or confirmed outbreak

## Consequences
Positive: agency can follow up with evidence; private consent still blocks routine browsing; retention is bounded.

Negative: private is not absolute privacy; consent copy must disclose exception; escrow adds encryption, purge, and audit complexity.

Mitigation: clear farmer consent text, jurisdiction/permission checks, audit logs, 30-day purge, safe wording.
