# PRD — SapiSehat Proposal-Based Production App

## Problem Statement

Farmers need a fast, practical way to get early indication of PMK/FMD and LSD/Lato-Lato from cattle images in field conditions where veterinary access and internet connectivity may be limited. The original proposal focuses on CNN-based cattle disease image classification for Android, but the current product direction expands that scope into a production-oriented Android app with online-first detection, on-device fallback, local scan history, bilingual UI, PDF reporting, privacy controls, and model evaluation evidence.

The system must help Farmer Users capture useful cattle images, receive an Early Detection Result, understand the confidence level, and share a Detection Report PDF with an Animal Health Advisor. It must avoid presenting results as final veterinary diagnosis.

## Solution

Build SapiSehat as a farmer-facing Android Production App for early cattle disease detection. The app will classify cattle images into three Disease Classes: `healthy`, `FMD`, and `LSD`.

The app will use Online-first Detection: it will prefer Server Inference to reduce computation on low-spec phones, then fall back to On-device Inference when upload consent is denied, no network is available, the server times out, rate limiting occurs, or server inference fails. The product will preserve privacy through Upload Consent, EXIF removal, No-retention Server Inference, local-only Scan History, optional Coarse Location, soft delete with purge, and opt-in crash reporting.

The proposal-based PRD explicitly deviates from the proposal in two places: online-first architecture replaces proposal-emphasized offline inference as the primary route, and production app scope expands beyond the proposal's prototype/conceptual field-testing boundary. These deviations are accepted because server inference protects low-spec devices, while production scope requires safety, privacy, reliability, accessibility, and validation requirements.

## User Stories

1. As a Farmer User, I want to open the app and understand its purpose, so that I know it provides early indication rather than veterinary diagnosis.
2. As a Farmer User, I want onboarding to explain PMK/FMD and LSD/Lato-Lato scanning, so that I know what kind of cattle images to capture.
3. As a Farmer User, I want the app to use Indonesian or English based on my Android system language, so that I can use the app in a language I understand.
4. As a Farmer User, I want Indonesian fallback when my system language is unsupported, so that app text remains understandable for the target context.
5. As a Farmer User, I want a Home action dashboard, so that I can start scanning quickly.
6. As a Farmer User, I want to see online/offline status before scanning, so that I understand whether server inference may be available.
7. As a Farmer User, I want to scan using the camera, so that I can analyze cattle directly in the field.
8. As a Farmer User, I want to scan using gallery images, so that I can analyze images captured earlier.
9. As a Farmer User, I want Guided Capture instructions, so that I take useful photos of mouth, hoof, or skin symptom areas.
10. As a Farmer User, I want a Capture Checklist with light, focus, blur, and distance reminders, so that the model receives better input.
11. As a Farmer User, I want the app to reject blurry images before inference, so that I do not receive unreliable results from poor images.
12. As a Farmer User, I want the app to reject too-dark images before inference, so that prediction quality is protected.
13. As a Farmer User, I want the app to reject too-small or invalid images before inference, so that unsupported input does not reach the model.
14. As a Farmer User, I want camera and gallery images to use the same Image Quality Gate, so that quality rules are consistent.
15. As a Farmer User, I want the app to ask before uploading cattle images, so that I control server use.
16. As a Farmer User, I want Upload Consent remembered, so that I am not asked on every scan.
17. As a Farmer User, I want to change Upload Consent in Settings, so that I can later allow or block server inference.
18. As a Farmer User, I want the app to run On-device Inference when I deny upload consent, so that I can still get an Early Detection Result.
19. As a Farmer User, I want server inference when available and allowed, so that low-spec phones do less computation.
20. As a Farmer User, I want automatic fallback when the server fails, so that scanning still works in weak connectivity.
21. As a Farmer User, I want fallback after a 10-second server timeout, so that I am not stuck waiting in the field.
22. As a Farmer User, I want an Early Detection Result with Disease Class and confidence, so that I understand the likely condition.
23. As a Farmer User, I want all class scores shown, so that I can see whether the result is clear or uncertain.
24. As a Farmer User, I want a Confidence Level, so that I know whether to trust, confirm, or retake the scan.
25. As a Farmer User, I want medium confidence to suggest retaking the photo, so that I can improve reliability.
26. As a Farmer User, I want low confidence to be marked unreliable, so that I do not overreact to weak predictions.
27. As a Farmer User, I want Handling Advice for FMD, so that I know to isolate cattle and contact an Animal Health Advisor.
28. As a Farmer User, I want Handling Advice for LSD, so that I know to isolate cattle, observe skin signs, and contact an Animal Health Advisor.
29. As a Farmer User, I want Handling Advice for healthy results, so that I know to keep observing and maintain cattle care.
30. As a Farmer User, I want the app to avoid claiming specific lesions were detected, so that I do not mistake classification for visual diagnosis.
31. As a Farmer User, I want each result to show inference mode, so that I know whether it came from Server Inference or On-device Inference.
32. As a Farmer User, I want each result to store model version, so that old and new results remain traceable.
33. As a Farmer User, I want scan results stored locally, so that I can review previous cattle checks.
34. As a Farmer User, I want Scan History to include image, timestamp, source, class, confidence, scores, mode, reliability, model version, app version, and notes, so that each result is meaningful later.
35. As a Farmer User, I want optional farmer notes, so that I can remember cattle identity or observations.
36. As a Farmer User, I want optional Coarse Location, so that I can record village or district without precise GPS tracking.
37. As a Farmer User, I want to type Coarse Location manually, so that I can avoid GPS permission if desired.
38. As a Farmer User, I want GPS to assist Coarse Location after permission, so that entry is easier.
39. As a Farmer User, I want Coarse Location to stay local by default, so that location privacy is preserved.
40. As a Farmer User, I want to delete Scan History items, so that I control stored cattle data.
41. As a Farmer User, I want deleted items hidden immediately, so that history feels deleted.
42. As a Farmer User, I want soft-deleted items purged after 30 days, so that accidental deletion can be undone while privacy is eventually enforced.
43. As a Farmer User, I want local image and PDF cache purged with deleted history, so that private files do not remain forever.
44. As a Farmer User, I want to export a Detection Report PDF, so that I can share a result with an Animal Health Advisor.
45. As an Animal Health Advisor, I want a PDF with image, timestamp, Disease Class, confidence, scores, inference mode, advice, disclaimer, app version, model version, preprocessing summary, consent status, and non-identifying device info, so that I can review context safely.
46. As an Animal Health Advisor, I want the PDF to avoid diagnosis/certificate wording, so that farmers do not treat it as official medical proof.
47. As a Farmer User, I want PDF device info to exclude IMEI, serial number, account identifiers, and precise location, so that my privacy is protected.
48. As a Farmer User, I want a Guide screen with PMK/FMD symptoms and actions, so that I can respond appropriately.
49. As a Farmer User, I want a Guide screen with LSD symptoms and actions, so that I can respond appropriately.
50. As a Farmer User, I want healthy cattle care guidance, so that I know basic preventive steps.
51. As a Farmer User, I want app usage instructions, so that I can scan without technical knowledge.
52. As a Farmer User, I want photo tips in the guide, so that future scans improve.
53. As a Farmer User, I want About and Settings screens, so that I can understand app version, model version, privacy options, and server settings.
54. As a Farmer User, I want no required account, so that I can use the app quickly in the field.
55. As a Farmer User, I want crash reporting to be opt-in, so that I control anonymous diagnostic data.
56. As a product team member, I want anonymous crash logs to exclude cattle images, location, and account identifiers, so that production metrics do not compromise privacy.
57. As a backend operator, I want No-retention Server Inference, so that uploaded cattle images are not stored by default.
58. As a backend operator, I want typed Prediction Error Codes, so that the Android app can localize errors and choose fallback behavior.
59. As a backend operator, I want basic rate limiting, so that LAN/VPS server resources are protected.
60. As a backend operator, I want HTTP LAN deployment for TA/demo and HTTPS for institutional/VPS production pilot, so that deployment matches current and future needs.
61. As a researcher, I want public images and Local Field Images, so that the dataset is both broad and locally grounded.
62. As a researcher, I want Label Validation documented, so that public labels, researcher review, and veterinarian/petugas sample approval are traceable.
63. As a researcher, I want stratified 70/15/15 train/validation/test split, so that model metrics are comparable and class balance is preserved.
64. As a researcher, I want Custom CNN, MobileNetV2, and DenseNet121 compared, so that final model selection is evidence-backed.
65. As a researcher, I want each Model Candidate to produce a Model Evaluation Report, so that accuracy, precision, recall, F1, macro F1, confusion matrix, size, and latency are visible.
66. As a product team member, I want final model selection to balance accuracy/F1 and Android viability, so that the app is both accurate and usable.
67. As a product team member, I want TFLite accuracy drop ≤ 2% and size < 10 MB, so that offline fallback remains useful on Android.
68. As a product team member, I want server and TFLite model versions visible, so that result reproducibility survives version mismatch.
69. As a tester, I want an Acceptance Test Suite covering preprocessing, quality gate, API prediction, errors, fallback, consent, history, PDF export, and real-device smoke flow, so that release readiness is not based on manual demo only.
70. As a field validator, I want Limited Field Validation with task success, completion time, comprehension, qualitative feedback, and stability, so that the app is evaluated in realistic use without claiming clinical validation.

## Implementation Decisions

- Use the project's domain vocabulary: Farmer User, Animal Health Advisor, Disease Class, Localized Display Label, Early Detection Result, Online-first Detection, Server Inference, On-device Inference, Scan History, Detection Report PDF, Upload Consent, No-retention Server Inference, Coarse Location, Model Candidate, Model Evaluation Report, Image Quality Gate, and Limited Field Validation.
- Product direction is proposal-based but explicitly expands beyond proposal scope into Production App requirements.
- Online-first Detection is chosen over offline-first as primary path because server inference reduces computation burden on low-spec phones. On-device Inference remains mandatory fallback for weak connectivity and consent denial.
- App uses no account system. Scan History remains local to device.
- App supports Indonesian and English display using Android system language, with Indonesian fallback. Canonical Disease Class values remain `healthy`, `FMD`, and `LSD` regardless of language.
- Core Android screens are Splash, Onboarding, Home, Camera, Result, History, Guide, About, and Settings.
- Home is an action dashboard with primary scan action, recent result, connection status, and guide entry.
- Camera and gallery input are both supported. Each Early Detection Result records Image Source.
- Guided Capture includes a Capture Checklist for symptom-area examples, enough light, close-up framing, blur avoidance, and retake prompt.
- Image Quality Gate is a deep module candidate. It exposes a simple decision interface for camera/gallery images and encapsulates blur, darkness, and minimum-size checks before inference.
- Inference routing is a deep module candidate. It decides Server Inference vs On-device Inference based on network, Upload Consent, server timeout, errors, and rate limits, while exposing one Early Detection Result interface to the app.
- Server Inference uses a 10-second total timeout before fallback.
- On-device Inference uses TFLite bundled with APK. Offline model updates only through app release.
- Backend Deployment Phase starts with HTTP LAN backend for TA/demo, then scales to HTTPS institutional or VPS server for production pilot.
- Server upload requires Upload Consent. First online scan asks for consent, remembers choice, and allows changing it in Settings.
- If Upload Consent is denied or disabled, Online-first Detection skips Server Inference and uses On-device Inference.
- Server Inference is No-retention Server Inference: uploaded images are processed in memory, not persisted, not added to dataset by default, then discarded after response.
- Backend returns Prediction Response with status, Disease Class, display-label key, confidence, all class scores, reliability flag, model version, and processing time. Backend does not localize user-facing text.
- Backend returns stable Prediction Error Codes: `INVALID_IMAGE`, `MODEL_NOT_READY`, `INFERENCE_FAILED`, `TIMEOUT`, and `RATE_LIMITED`.
- Backend applies basic per-device or per-IP rate limiting.
- Early Detection Result includes Disease Class, confidence, class scores, Confidence Level, inference mode, reliability, model version, app version, Handling Advice, Image Source, and optional Coarse Location/farmer notes.
- Confidence Level bands are high at ≥80%, medium at 60–79%, and low below 60%.
- Medium confidence suggests retake. Low confidence marks result unreliable and recommends retake.
- Handling Advice is generated from Disease Class and Confidence Level. It must not claim actual lesion localization or final diagnosis.
- Scan History stores local result data including id, timestamp, image path, Image Source, Coarse Location, Disease Class, confidence, all class scores, inference mode, reliability, model version, app version, optional farmer notes, and soft-delete state.
- Deleted Scan History records are hidden immediately, retained as soft-deleted for 30 days, then purged with local image/PDF cache.
- Coarse Location is optional, local-only by default, manually entered or GPS-assisted after permission. Precise coordinates are not stored by default and are not uploaded by default.
- Detection Report PDF includes image, timestamp, Disease Class, Localized Display Label, confidence, all class scores, inference mode, Handling Advice, disclaimer, app version, model version, preprocessing summary, consent status, non-identifying device info, optional Coarse Location, and optional farmer notes.
- Detection Report PDF excludes IMEI, serial number, account identifiers, precise location, and diagnosis/certificate claims.
- Guide Content covers PMK/FMD symptoms/actions, LSD symptoms/actions, healthy cattle care, photo capture tips, and app usage. It must not become a treatment protocol or veterinary encyclopedia.
- Basic Accessibility is required: large touch targets, readable text, high contrast, content descriptions, and farmer-friendly wording.
- Dataset combines public cattle disease images and Local Field Images. Target for Local Field Images is 20–50 images per Disease Class when available.
- Label Validation documents public dataset labels, researcher symptom review, and veterinarian or animal health officer sample review/approval.
- Dataset split is stratified 70/15/15 across `healthy`, `FMD`, and `LSD`.
- Model Candidates are Custom CNN baseline, MobileNetV2, and DenseNet121.
- Final model selection prioritizes accuracy and F1-score while enforcing Android viability through latency and model-size constraints.
- Target metrics are test accuracy ≥88%, per-class F1-score ≥85%, TFLite accuracy drop ≤2%, TFLite size <10 MB, offline inference <1 second.
- Training Augmentation is separate from Inference Preprocessing. Random transformations run during training only, never during user prediction.
- Crash Reporting Consent is opt-in. Crash logs must be anonymous and exclude cattle images, location, and account identifiers.
- Production readiness targets online inference <3 seconds, offline inference <1 second, crash-free sessions ≥99%, fallback success ≥95%, APK size <50 MB.
- Limited Field Validation measures task success, completion time, user comprehension that results are not diagnosis, qualitative feedback, and stability. It does not claim lab-confirmed clinical accuracy.

## Testing Decisions

- Good tests verify external behavior and domain outcomes, not implementation details. Tests should assert decisions such as “bad image is rejected,” “server timeout falls back to offline,” and “PDF excludes identifying device data,” rather than private helper calls.
- Image Quality Gate should be tested as a deep module with representative image inputs for blurry, dark, too-small, invalid, and acceptable images.
- Inference routing should be tested as a deep module with fake network, fake consent, fake server, and fake offline engine. Scenarios should cover online success, consent denial, no network, timeout, model-not-ready, rate limit, and fallback success.
- Prediction response mapping should be tested so both Server Inference and On-device Inference produce the same Early Detection Result domain fields.
- Upload Consent behavior should be tested for first-scan prompt, remembered choice, Settings update, and denied-consent offline path.
- Scan History should be tested for saving required fields, farmer notes, Coarse Location, model/app version, soft delete, and 30-day purge behavior.
- Detection Report PDF should be tested for required content and excluded fields. External behavior is the rendered/exported report metadata/content, not PDF implementation internals.
- Localization should be tested for Indonesian, English, and unsupported-locale fallback to Indonesian.
- Backend API should be tested using existing backend prediction and inference test patterns in the repo. Coverage should include valid image, invalid image, model-not-ready, prediction shape, model version, and error code response.
- Android real-device smoke flow should be tested with camera/gallery scan, fallback path, history save, PDF export, and Settings consent change.
- Model evaluation testing should produce Model Evaluation Reports for Custom CNN, MobileNetV2, and DenseNet121 using the same stratified test set.
- TFLite validation should compare server model and TFLite model predictions on the test set and assert accuracy drop ≤2% unless a documented exception is approved.
- Limited Field Validation should use a checklist, not clinical claims: task success, time to complete scan, comprehension of disclaimer, qualitative feedback, and observed crashes/errors.

## Out of Scope

- Final veterinary diagnosis.
- Treatment prescription.
- Lab-confirmed clinical validation.
- Object localization, lesion detection, Grad-CAM, or heatmap explanation.
- Claiming specific symptoms were detected by the model.
- Cloud account system.
- Cloud scan history.
- Admin dashboard for animal health officers.
- Remote TFLite model download or server-pushed offline model updates.
- Full outbreak analytics or epidemiological surveillance.
- Required precise GPS location.
- Storing uploaded images on the server by default.
- Always-on analytics without consent.
- Full cloud-scale backend autoscaling.
- Broad multi-device production certification beyond the stated production readiness metrics.

## Further Notes

- This PRD was regenerated using the `to-prd` template from the current conversation context, project documents, and observed codebase structure.
- The original proposal emphasizes offline Android usage; this PRD intentionally chooses Online-first Detection with mandatory On-device Inference fallback.
- The original proposal limits Android implementation and field testing toward prototype/conceptual scope; this PRD intentionally expands to Production App scope and therefore adds privacy, quality, accessibility, reliability, and deployment requirements.
- `CONTEXT.md` contains the current project glossary and flagged ambiguities. Future PRD edits should preserve that vocabulary.
- Current repo already contains major pieces for backend prediction, Android app, TFLite inference, history, settings, guide, and result flows, but the regenerated PRD adds missing or expanded requirements such as Image Quality Gate, PDF report content, soft-delete purge, explicit consent behavior, model comparison reports, TFLite validation, and limited field validation evidence.
- Issue tracker publishing and `ready-for-agent` labeling were not performed because no issue tracker tool or triage vocabulary is available in this session.
