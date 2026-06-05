# Limited Field Validation Report

**Project**: SapiSehat — Cattle Disease Early Detection
**Report type**: Limited Field Validation (usability)
**Date range of sessions**: ____ to ____
**Author**: ____
**App build / version**: ____

---

## 0. Statement of scope

> This report describes a **limited field validation** of the SapiSehat app's
> usability, comprehension, and stability with representative users. It is
> **NOT a clinical or diagnostic validation** and makes no claim about the
> medical accuracy of the AI model. Results are an early indication only.

---

## 1. Summary

- Participants: ____ (farmers: ____, animal health officers: ____, other: ____)
- Sessions conducted: ____   Mode(s): ☐ Online ☐ Offline
- Region visual probe: ☐ Not tested ☐ Tested as validation-only mockup/prototype
- Headline findings (3–5 bullets):
  - ____
  - ____
  - ____

---

## 2. Participants

| ID | Role | Years w/ cattle | Phone familiarity |
|----|------|-----------------|-------------------|
| P1 | | | |
| P2 | | | |
| … | | | |

> If animal health officers could not be recruited, state it here as a
> limitation.

---

## 3. Task success & efficiency

| Task | Success (S) | Partial (P) | Fail (F) | Median time | % unaided |
|------|:-----------:|:-----------:|:--------:|:-----------:|:---------:|
| 1 Scan | | | | | |
| 2 Interpret | | | | | |
| 3 Diagnosis comprehension | | | | | |
| 4 Guide | | | | | |
| 5 History note+delete | | | | | |
| 6 Privacy consent | | | | | |
| 7 PDF export+share | | | | | |

**Overall**: ____% of core tasks completed unaided (target ≥80%).

---

## 4. Disclaimer comprehension

| Result | Count | % |
|--------|:-----:|:-:|
| Correct | | |
| Partial | | |
| Incorrect | | |

**% correctly understanding "early indication, not a diagnosis"**: ____%
(target ≥80%).

Representative quotes:
- ____
- ____

---

## 5. Stability

- Total crashes observed: ____
- Total non-crash errors: ____
- Details:

| Participant | Action | Screen | Recovered? |
|-------------|--------|--------|:----------:|
| | | | ☐ |

---

## 6. Usability findings (prioritized)

| ID | Severity (High/Med/Low) | Finding | Evidence (tasks/quotes) | Recommendation |
|----|:----------------------:|---------|--------------------------|----------------|
| F1 | | | | |
| F2 | | | | |
| F3 | | | | |

---

## 7. Accessibility findings

- Text legibility: ____
- Color-independent meaning: ____
- Tap target / interaction: ____
- Language clarity (ID/EN): ____

---

## 8. SUS (if administered)

Mean SUS score: ____ / 100. Interpretation: ____

## 9. Region visual gate (issue #32)

Farmer-facing symptom-region visuals remain disabled unless validation evidence
supports a gated release. Use neutral wording only: **model attention area** or
**area to review**. Do not describe boxes as detected lesions.

| Decision option | Selected? | Evidence / quotes |
|-----------------|:---------:|-------------------|
| Keep disabled | ☐ | |
| Gated farmer-facing trial | ☐ | |
| Developer/debug-only | ☐ | |

Comprehension summary:
- Participants who understood marker as attention/review guidance: ____ / ____
- Participants who interpreted marker as confirmed lesion/diagnosis: ____ / ____
- Evidence of improved next-step understanding: ____
- Evidence of misleading/overconfidence risk: ____

Required decision statement:
> Based on this limited validation, farmer-facing region display is
> ☐ not approved ☐ approved only for a gated trial ☐ kept developer/debug-only.
> This does not create clinical diagnosis claims.

---

## 10. Limitations

- Limited sample size (____ participants); not statistically representative.
- Usability-only; no medical/diagnostic validation performed.
- Sample images used instead of live cattle for some tasks (if applicable).
- Other: ____

---

## 11. Follow-up actions

Each actionable finding becomes a GitHub issue. List them here with links:

| Finding | Proposed issue title | Priority | Link |
|---------|----------------------|:--------:|------|
| F1 | | | #___ |
| F2 | | | #___ |

---

## 12. Conclusion

Brief narrative: did the app meet the limited-validation usability and
comprehension indicators? What are the top changes to make before any wider
rollout? Reiterate that this remains a limited field validation, not clinical
validation.
