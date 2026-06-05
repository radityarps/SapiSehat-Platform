# Team 2 NLP Documentation

Team 2 owns NLP-based symptom screening implementation across mobile and backend.

## Scope

Team 2 owns:

- symptom questionnaire design
- Indonesian farmer symptom wording
- optional symptom note handling
- NLP model behavior
- offline NLP model behavior
- backend NLP inference service behavior
- NLP evidence contract details
- NLP-specific validation and evaluation

Team 2 does not own:

- image classification behavior
- shared platform data model
- shared fusion policy
- agency dashboard contracts
- shared privacy/retention/access-control policy

## MVP Disease Scope

NLP evidence must align with MVP disease classes:

- `healthy`
- `FMD`
- `LSD`

Future diseases must be added through shared disease catalog updates.

## Required Shared Contracts

Before changing NLP evidence shape or behavior, update:

- [Fusion Contract](../system-integration/api-contracts/FUSION_CONTRACT.md)
- [Data Model](../system-integration/database/DATA_MODEL.md) when stored questionnaire/notes change
- [System Integration README](../../README.md) when ownership/routing changes


## NLP Evidence Contract Tracer

Issue #8 adds the first executable Team 2 NLP evidence contract. NLP evidence must include:

1. `source: nlp`.
2. `model_version`.
3. `inference_mode: online|offline`.
4. `questionnaire_answers` owned by Team 2.
5. `notes_present` for optional symptom notes.
6. `disease_scores` with exactly `healthy`, `FMD`, and `LSD`.
7. `top_class` matching the highest disease score.
8. `confidence` from 0.0 to 1.0.
9. `evidence_terms` extracted from questionnaire and notes.

Prototype validation endpoint: `POST /api/evidence/nlp`.
