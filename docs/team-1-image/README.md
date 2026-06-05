# Team 1 Image Documentation

Team 1 owns image-based early detection implementation across mobile and backend.

## Scope

Team 1 owns:

- image classification model behavior
- image preprocessing and quality gates
- image inference contracts and model versions
- mobile image capture/offline image model behavior
- backend image inference service behavior
- image-specific validation and evaluation
- symptom-region detector experiments when used by image subsystem

Team 1 does not own:

- NLP symptom model behavior
- shared platform data model
- shared fusion policy
- agency dashboard contracts
- shared privacy/retention/access-control policy

## Required Shared Contracts

Before changing image evidence shape or behavior, update:

- [Fusion Contract](../system-integration/api-contracts/FUSION_CONTRACT.md)
- [Data Model](../system-integration/database/DATA_MODEL.md) when stored image evidence/media changes
- [System Integration README](../system-integration/README.md) when ownership/routing changes

## Legacy Image Docs

Current image/model docs still live in `docs/model` until the restructure plan is approved. Treat those docs as Team 1 legacy material.
