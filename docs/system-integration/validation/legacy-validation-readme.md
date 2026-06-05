# Limited Field Validation Package

This directory contains everything needed to run a **Limited Field Validation**
of the SapiSehat Android app with farmers and/or animal health officers.

> **This is a limited field validation, NOT a clinical or diagnostic
> validation.** It measures usability, comprehension, and stability of the app
> with representative users. It does not validate the medical accuracy of the
> AI model or establish any veterinary diagnostic capability.

## Contents

| File | Purpose | Audience |
|------|---------|----------|
| `VALIDATION_PROTOCOL.md` | Objectives, scope, participants, method, metrics | Researcher |
| `FACILITATOR_SCRIPT.md` | Step-by-step session script (what to say/do) | Facilitator |
| `TASK_CHECKLIST.md` | Per-participant task observation sheet | Facilitator |
| `CONSENT_FORM.md` | Participant informed consent (ID + EN) | Participant |
| `METRICS_SHEET.md` | Quantitative + qualitative data capture | Facilitator |
| `REPORT_TEMPLATE.md` | Findings report skeleton with follow-up section | Researcher |

## Status (HITL)

This issue is `type:HITL`. The package below is complete and ready to use. The
**actual validation sessions require human participants** and cannot be executed
autonomously. After running sessions:

1. Fill `METRICS_SHEET.md` per participant.
2. Aggregate into `REPORT_TEMPLATE.md`.
3. File follow-up GitHub issues for each actionable finding.

## Readiness check (blockers from issue #16)

All implementation prerequisites are complete:

- [x] Upload consent & privacy controls (issue #2, #10)
- [x] Image quality gate (image-quality-gate spec)
- [x] PDF export/share (issue #8)
- [x] Soft-delete/purge & complete history metadata (issue #5, #7)
- [x] Acceptance test suite (issue #15)
- [x] Diagnosis-claim wording review — "Early Detection Result" (issue #4, #9)

Run `apps/mobile/SMOKE_TEST_CHECKLIST.md` on the validation build before the
first session to confirm the device build is healthy.
