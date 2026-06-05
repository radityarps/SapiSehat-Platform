# SapiSehat Platform Scope

## Product Identity

SapiSehat is a cattle disease early detection platform for farmers and local agencies in Indonesia.

It is not an image-only Android app. It is also not a clinical diagnosis system.

The platform supports early disease-risk indication through:

- image classification
- NLP symptom screening
- farmer cattle records
- agency monitoring
- follow-up prioritization

## Primary and Secondary Users

### Farmer User

Primary mobile user.

Farmers use the app to:

- create a phone-number account
- register cattle
- maintain cattle records
- submit image evidence
- answer symptom questionnaire
- add optional symptom notes
- receive early detection results
- sync offline results when connectivity returns

### Agency User

Secondary dashboard user.

Agency users use the dashboard to:

- monitor disease risk signals
- view farmer and cattle records within permitted scope
- review early detection trends
- prioritize follow-up
- monitor jurisdiction-level risk

Agency access is controlled by role, administrative jurisdiction, and farmer consent tier.

## Target System with MVP Phases

Documentation describes the complete intended platform while separating first-deliverable MVP scope from later expansion phases.

### Target System

Target system includes:

- complete livestock profile
- farmer mobile app
- agency dashboard
- Go gateway platform API
- Python image inference service
- Python NLP inference service
- PostgreSQL database
- backend-primary fusion
- offline mobile fusion and sync
- role-jurisdiction-consent access control

### MVP Direction

MVP should prioritize:

- farmer account
- cattle registration
- cattle-first detection flow with quick-scan escape
- image classification integration
- NLP questionnaire integration
- backend fusion
- detection result storage
- jurisdiction-scoped agency dashboard
- disease risk signal monitoring

## Complete Livestock Profile

A cattle profile may include:

- cattle identity
- ownership
- age or birth estimate
- sex
- breed
- location
- photos
- health events
- early detection history
- vaccination
- reproduction
- weight
- feed
- pregnancy
- productivity
- sale
- transfer

## Disease Scope

MVP disease classes remain:

- `healthy`
- `FMD`
- `LSD`

The disease catalog should be extensible for future cattle diseases.

## Dashboard Scope

The agency dashboard focuses on outbreak surveillance as disease-risk monitoring, not official outbreak declaration.

Dashboard language must use terms like:

- disease risk signal
- possible increased risk
- follow-up needed
- suspected risk cluster

Dashboard must avoid:

- confirmed outbreak
- official epidemiological finding
- veterinary diagnosis
