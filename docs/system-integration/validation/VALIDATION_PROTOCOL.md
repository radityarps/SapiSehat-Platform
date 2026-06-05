# Limited Field Validation Protocol

**Project**: SapiSehat — Cattle Disease Early Detection (FMD / LSD / Healthy)
**Document type**: Limited Field Validation Protocol
**Version**: 1.0

---

## 1. Important framing

This is a **limited field validation**. Its purpose is to evaluate the
**usability, comprehension, and stability** of the SapiSehat mobile app with
representative users in a realistic setting.

It is **NOT**:

- a clinical or veterinary diagnostic validation,
- a measurement of the AI model's medical accuracy,
- a basis for any claim that the app diagnoses disease.

All materials and the final report must consistently state this limitation.

---

## 2. Objectives

1. Determine whether target users can complete core tasks (scan, interpret
   result, use the guide, review history, manage privacy settings, share a PDF)
   without assistance.
2. Measure whether users **correctly understand** that the result is an
   "Early Detection Result" / early indication and **not a final diagnosis**.
3. Identify usability problems, confusing wording, and accessibility barriers.
4. Capture stability issues (crashes, errors, long waits) on real devices.
5. Produce prioritized, actionable follow-up recommendations.
6. Decide whether any symptom-region visual should remain developer/debug-only
   or become farmer-facing after validation evidence shows it helps without
   implying confirmed lesions.

---

## 3. Scope

### In scope
- Camera capture and gallery selection
- Image quality gate behavior
- Result screen interpretation (class, confidence, mode, advice, disclaimer)
- Validation-only review of optional region wording/mockup using neutral terms:
  **model attention area** / **area to review**, never "detected lesion".
- Guide / educational content
- Scan history (view, notes, delete/undo)
- Settings & privacy controls (upload consent, location, crash reporting)
- PDF export and sharing

### Out of scope
- Model accuracy / medical correctness
- Network performance benchmarking
- Long-term retention / longitudinal study
- Farmer-facing symptom-region boxes in production unless this validation
  explicitly approves them.

---

## 4. Participants

| Attribute | Target |
|-----------|--------|
| Sample size | 5–8 participants (limited validation) |
| Primary profile | Cattle farmers |
| Secondary profile | Animal health officers / extension workers (if available) |
| Inclusion | Owns/works with cattle; uses an Android phone |
| Exclusion | Prior involvement in app development |

> Recruit farmers and/or animal health officers **when available**. If officers
> cannot be recruited, document this in the report as a limitation.

### Recruitment notes
- Aim for a mix of experience levels with smartphones.
- Record only non-identifying demographics (role, years with cattle, phone
  familiarity). Do not collect PII beyond what consent allows.

---

## 5. Environment & materials

- Validation build of the SapiSehat app installed on a test device (or the
  participant's own device, with permission).
- Backend reachable for online mode, OR offline mode demonstrated explicitly.
- Sample cattle images (printed or on a second screen) for participants without
  immediate access to live cattle, covering healthy / FMD / LSD examples.
- Printed `CONSENT_FORM.md`, `TASK_CHECKLIST.md`, `METRICS_SHEET.md`.
- Stopwatch / phone timer for completion times.
- Note-taking device.

Run `apps/mobile/SMOKE_TEST_CHECKLIST.md` before the first session.

---

## 6. Method

1. **Welcome & consent** (5 min) — Explain purpose, obtain signed consent,
   stress that we are testing the app, not the participant.
2. **Background** (3 min) — Capture role and phone familiarity.
3. **Tasks** (20–30 min) — Participant attempts tasks from `TASK_CHECKLIST.md`
   using **think-aloud**. Facilitator observes, does not coach unless the
   participant is fully blocked (then record assistance).
4. **Comprehension check** (5 min) — Ask the disclaimer-comprehension questions
   in `METRICS_SHEET.md`.
5. **Debrief** (5 min) — Open qualitative feedback.

---

## 7. Metrics

| Metric | Type | Captured in |
|--------|------|-------------|
| Task success (success / partial / fail) | Quantitative | METRICS_SHEET |
| Task completion time | Quantitative | METRICS_SHEET |
| Assistance required (yes/no per task) | Quantitative | TASK_CHECKLIST |
| Disclaimer comprehension (correct / partial / incorrect) | Quantitative | METRICS_SHEET |
| Observed crashes / errors | Quantitative | METRICS_SHEET |
| Qualitative feedback / quotes | Qualitative | METRICS_SHEET |
| System Usability Scale (SUS, optional) | Quantitative | METRICS_SHEET |
| Region visual comprehension / misleading risk | Qualitative + decision gate | METRICS_SHEET |

### Region visual validation gate

Symptom-region boxes remain disabled for farmer-facing UI by default. They may
only be exposed after validation findings show all of the following:

- Participants understand the visual as a **model attention area** or **area to
  review**, not a confirmed lesion or veterinary diagnosis.
- The visual improves next-step understanding or photo-quality correction.
- The visual does not increase overconfidence in the result.
- Wording clearly separates early detection from clinical diagnosis claims.

If evidence is mixed or negative, keep region output developer/debug-only.

---

## 8. Success indicators (limited validation)

These are **usability** targets, not medical thresholds:

- ≥80% of core tasks completed without assistance across participants.
- ≥80% of participants correctly state the result is an early indication, not a
  final diagnosis.
- No critical crashes during core flows.

Falling short of any indicator becomes a follow-up recommendation, not a pass/fail
gate on the model.

---

## 9. Ethics & privacy

- Informed consent is mandatory before any task.
- Participation is voluntary; participants may stop at any time.
- Capture only non-identifying data. No images of participants' faces.
- Cattle images and any location data stay on the device per the app's
  privacy model (local-only history, no-retention server inference).
- Store completed sheets securely; anonymize before inclusion in the report.

---

## 10. Outputs

1. Completed `METRICS_SHEET.md` per participant.
2. Aggregated `REPORT_TEMPLATE.md`.
3. Follow-up GitHub issues for each actionable finding, labeled and linked back
   to this validation.
4. Region UX decision: `disabled`, `approved_for_gated_trial`, or
   `developer_debug_only`, with supporting participant quotes.
