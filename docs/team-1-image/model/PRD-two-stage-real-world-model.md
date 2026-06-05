## Problem Statement

SapiSehat's current three-class CNN classifier is proposal-aligned and integrated into Android, but user trials suggest real farm photos can still produce inaccurate or overconfident early detection results. Real-world photos may contain small symptoms, cluttered backgrounds, ambiguous body regions, poor lighting, non-target conditions, or out-of-scope visual evidence that a whole-image classifier can misread. The project needs a clear product and research plan for improving field reliability without changing the core claim from early detection support into clinical diagnosis.

## Solution

Create a future-work model improvement track for real-world robustness. The current MobileNetV2/TFLite classifier remains the main proposal-aligned implementation. The improvement track adds a server-first two-stage CNN-family pipeline: a small YOLO-family Symptom Region Detector proposes disease-relevant regions, then a classifier combines the original full image with the best symptom-region crops. The app/backend should also support an Insufficient Visual Evidence outcome policy so unclear, low-confidence, or ambiguous photos are not forced into FMD, LSD, or healthy.

This work is staged behind field data collection and annotation. It uses expert-reviewed field labels for validation/test, mixed label tiers for training, full symptom-region bounding boxes for disease images, hard-negative field images for threshold/error analysis, and field-only evaluation against the current single-stage baseline. Symptom-region outputs remain developer/debug information by default and become farmer-facing only after validation proves they help users without implying lesion confirmation.

## User Stories

1. As a farmer user, I want the app to avoid confidently showing a wrong disease result, so that I do not overtrust a misleading early detection result.
2. As a farmer user, I want the app to tell me when visual evidence is insufficient, so that I can retake the photo or ask an animal health advisor.
3. As a farmer user, I want the app to keep using the current Android fallback model, so that detection remains available when server inference is unavailable.
4. As a farmer user, I want early detection wording to remain non-diagnostic, so that I understand the app does not replace a veterinarian.
5. As an animal health advisor, I want unclear scans to be saved in scan history, so that failed or ambiguous attempts can be reviewed later.
6. As an animal health advisor, I want developer/debug symptom-region evidence to be available during validation, so that model behavior can be inspected without making clinical claims to farmers.
7. As a researcher, I want field images to have label tiers, so that weak labels can be distinguished from expert-reviewed labels.
8. As a researcher, I want scan history records to be excluded from training by default, so that unreviewed app scans do not poison the dataset.
9. As a researcher, I want reviewed local field images to become dataset candidates, so that retraining uses data from the target environment.
10. As a researcher, I want at least 50 expert-reviewed field images per disease class and 50 hard-negative field images before model update, so that real-world retraining has a minimum useful base.
11. As a researcher, I want hard-negative field images to be used first for threshold tuning and error analysis, so that the system reduces overconfident out-of-scope predictions before adding an unknown class.
12. As a researcher, I want disease field images to have symptom-region bounding boxes, so that the detector can learn disease-relevant visual evidence.
13. As a researcher, I want healthy field images to keep image-level healthy labels without fake symptom boxes, so that annotations remain honest.
14. As a researcher, I want a small YOLO-family detector as the first symptom-region detector candidate, so that the project gets a practical detection baseline.
15. As a researcher, I want the classifier to use both full image and symptom crop, so that context and focused symptom evidence are both preserved.
16. As a researcher, I want fusion to start with 40% full-image score and 60% symptom-crop score, so that crop evidence is emphasized while still retaining context.
17. As a researcher, I want the top three detector boxes to be evaluated, so that multiple visible lesions are not ignored.
18. As a researcher, I want crop scores aggregated by per-class maximum, so that one strong symptom crop can influence the final result.
19. As a researcher, I want conflicting symptom-region types to reduce result reliability, so that ambiguous evidence is not overpresented.
20. As a researcher, I want the first two-stage version to keep FMD, LSD, and healthy as the only disease classes, so that insufficient evidence remains a policy rather than a poorly defined fourth class.
21. As a researcher, I want field-only evaluation with expert-reviewed labels, so that real-world performance is measured honestly.
22. As a researcher, I want false confident result rate reported, so that the main real-world safety risk is visible.
23. As a researcher, I want disease recall for FMD and LSD reported, so that safer thresholds do not hide missed disease cases.
24. As a researcher, I want insufficient-evidence rate reported, so that model usefulness is measured alongside safety.
25. As a backend maintainer, I want two-stage inference introduced server-side first, so that Android model size and latency are not blocked by detector complexity.
26. As a backend maintainer, I want the current single-stage TFLite model to remain the on-device fallback, so that offline behavior remains stable until two-stage mobile viability is proven.
27. As a backend maintainer, I want optional developer-only symptom-region data in the prediction response, so that validation tooling can inspect detections without changing farmer-facing UX.
28. As a mobile maintainer, I want farmer-facing boxes hidden by default, so that the UI does not imply lesion confirmation.
29. As a mobile maintainer, I want farmer-facing boxes to be gated by field validation, so that they are only introduced if they improve understanding without overtrust.
30. As a thesis author, I want the two-stage architecture framed as future work or extension, so that the main implementation remains aligned with the original proposal.
31. As a thesis author, I want the proposal deviation documented if two-stage becomes the main implementation, so that examiners can see why the scope expanded.
32. As a thesis author, I want the work to avoid clinical validation claims, so that the system remains an early detection support tool.
33. As a future agent, I want clear acceptance criteria for the two-stage model, so that implementation does not optimize the wrong metric.
34. As a future agent, I want the current single-stage baseline preserved, so that two-stage improvement can be compared fairly.
35. As a future agent, I want an ADR documenting the YOLO detector decision, so that the mixed-framework choice is not mistaken for accidental inconsistency.

## Implementation Decisions

- Keep the current MobileNetV2/TFLite classifier as the main proposal-aligned implementation and Android fallback.
- Treat the two-stage architecture as a future model-improvement track unless explicitly approved as a main implementation scope expansion.
- Introduce Insufficient Visual Evidence as an early detection outcome when confidence, margin, image quality, or visible symptoms are not enough to support a disease-class result.
- Start the insufficient-evidence decision policy with confidence below 70%, top-class margin below 15 percentage points, or image-quality failure.
- Save insufficient-evidence outcomes in scan history as non-disease early detection outcomes.
- Do not use scan history as training data by default.
- Use mixed label tiers for field data: expert-reviewed labels are primary; researcher-reviewed labels may filter usability and obvious mismatch; farmer labels are weak unless expert-confirmed.
- Allow weak field labels in training only when tier is recorded; require expert-reviewed labels for field validation/test sets.
- Target at least 50 expert-reviewed local field images per disease class plus 50 hard-negative field images before model update.
- Use hard-negative field images first for threshold tuning and error analysis; do not add an explicit unknown/other class in the first two-stage version.
- Use full symptom-region bounding-box annotation for field disease images; do not use whole-cow-only boxes as the main detector target.
- Keep healthy field images image-level healthy with no fake symptom boxes.
- Introduce two-stage inference on server inference first.
- Keep on-device inference as the current single-stage TFLite fallback until two-stage mobile size, latency, and parity are proven.
- Use a small YOLO-family model as the first symptom-region detector candidate, even though the single-stage classifier pipeline remains TensorFlow/Keras.
- Use both the original full image and symptom-region crop for stage-two disease classification.
- Start fusion as a 40% full-image score and 60% symptom-crop score weighted ensemble, then tune on validation data.
- When multiple symptom regions are detected, use the top three boxes after suppression.
- Aggregate crop scores by per-class maximum before fusion.
- When detected symptom-region types conflict, allow classifier/fusion to decide the disease class but lower result reliability or mark as needing review.
- Keep model disease outputs as FMD, LSD, and healthy; keep insufficient evidence as decision policy, not a fourth model class.
- Keep symptom-region outputs developer/debug-only by default.
- Allow farmer-facing symptom boxes only after field validation proves they help without implying lesion confirmation.
- Success requires lower false confident result rate than current single-stage baseline, field macro F1 equal or better, FMD/LSD recall not worse by more than 5 percentage points, and field insufficient-evidence rate at or below 35%.
- Record the mixed-framework YOLO detector decision in an ADR because it deliberately deviates from the previous TensorFlow/Keras-only assumption.

## Testing Decisions

- Tests should focus on external behavior: whether the system returns the correct outcome, reliability state, saved history data, and report/debug data under observable scenarios.
- Do not test internal detector implementation details beyond stable interfaces and output contracts.
- Establish a field-only evaluation set using expert-reviewed labels before claiming real-world improvement.
- Compare every two-stage candidate against the current single-stage baseline on the same field-only evaluation set.
- Measure macro F1, per-class recall, FMD recall, LSD recall, confusion matrix, insufficient-evidence rate, and false confident result rate.
- Add evaluation tests for threshold policy: confidence below 70%, top-class margin below 15 percentage points, and image-quality failure should produce insufficient evidence.
- Add fusion tests with fixed synthetic model scores to verify 40/60 weighting, top-three crop aggregation, and conflict reliability behavior.
- Add response-contract tests to ensure developer-only symptom-region data does not become farmer-facing by default.
- Add scan-history behavior tests to ensure insufficient-evidence outcomes are saved but not treated as disease-class results.
- Add regression tests to ensure on-device fallback remains single-stage until two-stage mobile viability is explicitly proven.
- Use existing backend contract/property tests and mobile history/result tests as prior art for behavioral coverage.

## Out of Scope

- Full clinical validation or lab-confirmed diagnostic claims.
- Replacing the current proposal-aligned MobileNetV2/TFLite implementation as the thesis main result without explicit scope-deviation approval.
- Farmer-facing symptom boxes before validation.
- Automatic use of scan history as training data.
- Explicit unknown/other model class in the first two-stage version.
- Android two-stage TFLite deployment before server-first evaluation proves value and mobile viability is measured.
- Segmentation masks.
- Whole-cow-only detector as the main symptom-region target.
- New GitHub implementation issues unless separately requested.

## Further Notes

The two-stage model plan remains conceptually aligned with image-based CNN early detection because YOLO-family detectors are CNN-based and the project proposal already references object detection work for PMK imagery. However, it expands the original single-stage classifier method. For thesis safety, the current three-class CNN classifier integrated with Android should remain the main proposal-aligned implementation, while the two-stage pipeline should be framed as future work or an extension motivated by field accuracy limitations.

Related ADR: `docs/adr/0001-yolo-symptom-region-detector.md`.
