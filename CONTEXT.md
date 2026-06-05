# SapiSehat Context

SapiSehat is an Android-based cattle disease image classification system for early detection of PMK/FMD and LSD/Lato-Lato in cattle.

## Language

**Online-first Detection**:
A detection flow where Android sends cattle image to server as primary path to reduce computation on low-spec phones, then uses on-device inference when server, connection, consent, or timeout prevents online result.
_Avoid_: Offline-first, server-only diagnosis

**On-device Inference**:
Model inference executed inside Android device using TensorFlow Lite bundled with the APK and updated only through app release.
_Avoid_: Offline mode, local AI, remote model push

**Server Inference**:
Model inference executed by backend API after Android uploads preprocessed image.
_Avoid_: Cloud diagnosis, online AI

**Prediction Response**:
Backend response containing status, disease class, display-label key, confidence, all class scores, reliability flag, model version, processing time, and optional developer-only symptom-region data when server inference uses a validated two-stage model.
_Avoid_: Localized server text, label-only response

**Prediction Error Code**:
Stable backend error identifier for client handling and localization, including `INVALID_IMAGE`, `MODEL_NOT_READY`, `INFERENCE_FAILED`, `TIMEOUT`, and `RATE_LIMITED`.
_Avoid_: Free-text-only error, silent failure

**Disease Class**:
Canonical classification category stored as `healthy`, `FMD`, or `LSD` independent of display language.
_Avoid_: Indonesian-only labels, numeric-only labels

**Localized Display Label**:
User-facing disease class name rendered from Android system language when supported, with Indonesian fallback.
_Avoid_: Canonical label, database label

**Farmer User**:
Primary non-technical app user who needs simple early detection support for cattle in farm conditions.
_Avoid_: Researcher user, admin user

**Animal Health Advisor**:
Secondary user such as animal health officer or veterinarian who reviews early detection results and advises farmer without requiring separate app role.
_Avoid_: Admin dashboard user, separate role account

**Detection Report PDF**:
Shareable report containing image, timestamp, disease class, confidence, class scores, inference mode, handling advice, disclaimer, app version, model version, preprocessing summary, consent status, and non-identifying device info.
_Avoid_: PDF diagnosis, medical certificate

**Guided Capture**:
Photo-taking flow that instructs user to capture relevant visible symptoms such as mouth or hoof lesions for FMD and skin nodules for LSD.
_Avoid_: Free capture, unrestricted photo input

**Image Source**:
Origin of submitted cattle image, either live camera capture or gallery selection.
_Avoid_: Unknown source

**Coarse Location**:
Optional non-precise farm area such as village or district entered manually or filled with GPS assistance after permission, then stored locally.
_Avoid_: GPS coordinate, precise location, silent location capture

**Local Field Image**:
Cattle image collected directly from local farms for project validation and dataset grounding.
_Avoid_: Public dataset image, synthetic image

**Hard-Negative Field Image**:
Field image that should not support a confident FMD, LSD, or healthy result because it shows poor evidence, non-target conditions, or out-of-scope content.
_Avoid_: Unknown disease label, confirmed healthy image, ignored failure case

**Symptom Region Annotation**:
Bounding-box label around visible disease-relevant image evidence such as FMD mouth or hoof lesions and LSD skin nodules.
_Avoid_: Whole-cow-only box, segmentation mask, background cue

**False Confident Result**:
Wrong disease-class early detection result shown with confidence at or above 70% and top-class margin at or above 15 percentage points.
_Avoid_: Any wrong result, insufficient-evidence outcome

**Label Validation**:
Dataset labeling process where labels are assigned a review tier, public labels are retained with review notes, researchers filter unusable images, and veterinarian or animal health officer review is preferred for final disease labels.
_Avoid_: Unchecked labels, model-generated labels

**Model Candidate**:
CNN architecture trained and evaluated as alternative classifier before selecting production model.
_Avoid_: Assumed final model

**Symptom Region Detector**:
Small object-detection model that proposes disease-relevant symptom regions before disease classification in the two-stage server pipeline.
_Avoid_: Clinical lesion detector, whole-cow classifier, final diagnosis engine

**Model Evaluation Report**:
Evidence artifact containing accuracy, per-class precision, per-class recall, per-class F1-score, macro F1-score, confusion matrix, and field-only performance when field data is available.
_Avoid_: Accuracy-only report, informal result

**Training Augmentation**:
Image variation applied only during model training, such as rotation and brightness changes, to improve robustness.
_Avoid_: Runtime augmentation

**Inference Preprocessing**:
Deterministic image preparation before prediction, limited to orientation correction, resizing, compression, and pixel rescaling according to model input.
_Avoid_: Training augmentation, random transform

**Handling Advice**:
General recommended action based on predicted disease class and confidence level, such as isolation, retake photo, or contacting veterinarian.
_Avoid_: Detected symptom claim, treatment prescription

**Confidence Level**:
Interpretation band for model confidence: high at 80% or above, medium at 60–79%, and low below 60%.
_Avoid_: Uncalibrated certainty, binary certainty

**Scan History**:
Local record of previous early detection results stored on device for follow-up and review, including id, timestamp, image path, image source, coarse location, disease class, confidence, class scores, inference mode, reliability, model version, app version, optional farmer notes, and soft-delete state.
_Avoid_: Cloud history, server medical record

**Upload Consent**:
User permission given before cattle image is sent to server for inference, requested on first online scan and changeable in settings.
_Avoid_: Silent upload, blanket consent

**Crash Reporting Consent**:
User permission for anonymous crash log collection without cattle images, location, or account identifiers.
_Avoid_: Always-on analytics, image upload in logs

**No-retention Server Inference**:
Server inference policy where uploaded images are processed in memory and discarded after response.
_Avoid_: Dataset collection by default, stored upload

**Backend Deployment Phase**:
Planned server availability stage, starting from LAN backend for TA/demo and scaling to institutional or VPS server for production pilot.
_Avoid_: Undefined deployment, cloud-scale assumption

**Limited Field Validation**:
Real-device field test with farmers or animal health officers measuring task success, completion time, and qualitative feedback without claiming clinical validation.
_Avoid_: Clinical validation, lab-confirmed trial

**Acceptance Test Suite**:
Minimum verification set covering preprocessing, API prediction, online-to-offline fallback, local history storage, and Android real-device smoke flow.
_Avoid_: Manual demo only, unit-only testing

**Early Detection Result**:
Scan outcome containing either a disease-class prediction with confidence and handling advice or an insufficient-visual-evidence outcome, used only as early indication rather than veterinary diagnosis.
_Avoid_: Diagnosis, verdict

**Core Screen Set**:
Production navigation set containing Splash, Onboarding, Home, Camera, Result, History, Guide, About, and Settings screens.
_Avoid_: Role-based navigation, scan-only app

**Guide Content**:
In-app educational content covering PMK symptoms and actions, LSD symptoms and actions, healthy cattle care, photo capture tips, and app usage.
_Avoid_: Veterinary encyclopedia, treatment protocol

**Capture Checklist**:
Pre-capture guidance with symptom-area examples, enough-light reminder, close-up instruction, blur avoidance, and retake prompt.
_Avoid_: Unguided camera, text-only warning

**Image Quality Gate**:
Basic pre-inference check that rejects images that are too blurry, too dark, or too small and asks user to retake.
_Avoid_: Advanced quality classifier, post-inference-only warning

**Insufficient Visual Evidence**:
Early detection outcome used when image quality, model confidence, or visible symptoms are not enough to support a disease-class result.
_Avoid_: Unknown disease, negative diagnosis, model failure

**Basic Accessibility**:
Farmer-facing usability baseline with large touch targets, readable text, high contrast, and content descriptions.
_Avoid_: Visual-only controls, tiny text, low contrast

**Production App**:
Released Android system with full reliability, security, crash-rate monitoring, and broad device validation.
_Avoid_: Prototype, demo app

## Relationships

- **Online-first Detection** uses exactly one primary **Server Inference** attempt before fallback, with 10-second total timeout.
- **Server Inference** returns **Prediction Response** without localizing user-facing text.
- Failed **Server Inference** returns **Prediction Error Code** for app localization and fallback decisions.
- Backend applies basic per-device or per-IP rate limiting and returns `RATE_LIMITED` when exceeded.
- **On-device Inference** acts as fallback when **Server Inference** fails or network unavailable.
- **Farmer User** is primary user for UX wording, navigation, and capture flow.
- **Animal Health Advisor** is secondary user who may review shared **Early Detection Result** without separate role-based interface.
- **Detection Report PDF** is exportable from **Early Detection Result** for review by **Animal Health Advisor**.
- **Detection Report PDF** device info excludes IMEI, serial number, account identifier, and precise location.
- **Coarse Location** may appear in **Scan History** and **Detection Report PDF** only after explicit location permission, and is not uploaded by default.
- **Guided Capture** produces image input for **Online-first Detection**.
- Each **Early Detection Result** records one **Image Source**.
- Training dataset combines public images with at least 20–50 **Local Field Image** entries per **Disease Class** when available.
- Real-world retraining targets at least 50 expert-reviewed **Local Field Image** entries for each **Disease Class** plus 50 **Hard-Negative Field Image** entries before model update.
- Two-stage model improvement uses full **Symptom Region Annotation** for field disease images instead of whole-cow-only boxes; healthy field images keep image-level healthy labels without fake symptom boxes.
- When a two-stage model finds no symptom region, it must not automatically produce healthy; it may show healthy only when an image-level classifier confidently supports healthy, otherwise it returns **Insufficient Visual Evidence**.
- Two-stage inference is introduced on **Server Inference** first; **On-device Inference** remains current single-stage TFLite fallback until two-stage mobile size, latency, and parity are proven.
- The first **Symptom Region Detector** candidate is a small YOLO-family detector, even though the single-stage classifier pipeline remains TensorFlow/Keras.
- Stage-two disease classification in the two-stage pipeline uses both the original full image and the best symptom-region crop rather than relying on crop-only classification.
- Two-stage score fusion starts as a weighted ensemble with 40% full-image score and 60% symptom-crop score, then is tuned on validation data.
- When multiple symptom regions are detected, stage-two classification uses the top three detector boxes after suppression and aggregates crop scores by per-class maximum before fusion.
- When detected symptom-region types conflict, the classifier/fusion result decides the **Disease Class**, but the **Early Detection Result** is marked lower reliability or needs review.
- Two-stage symptom-region outputs are developer/debug information by default and may become farmer-facing only after field validation proves they help users without implying lesion confirmation.
- **Scan History** records are not training data by default; only reviewed **Local Field Image** entries may become training dataset candidates.
- Each training dataset release must document **Label Validation** method.
- For the initial public-dataset training run, **Label Validation** retains source labels, performs researcher review to remove corrupt/irrelevant/obviously mislabeled images, and requests veterinarian or animal-health-officer sample audit (minimum 10 images per class or 10% per class if smaller); missing expert audit must be documented as a limitation, never fabricated.
- For field data, **Label Validation** uses mixed label tiers: expert-reviewed labels are primary, researcher-reviewed labels may filter image usability and obvious mismatch, and farmer-provided labels are weak labels unless confirmed by an expert.
- Weak field labels may be used for training only when their tier is recorded; validation and test sets for field performance must use expert-reviewed labels.
- Dataset split uses stratified 70/15/15 train/validation/test proportions across `healthy`, `FMD`, and `LSD` classes.
- Training handles class imbalance with train-split class weights and per-class support reporting; validation/test splits are not oversampled, and weak minority-class performance must drive data or augmentation follow-up rather than be hidden by accuracy.
- Training dataset preparation removes exact duplicates by file hash, detects near-duplicates by perceptual hash, and keeps duplicate/near-duplicate groups in the same split or removes extras to prevent train/test leakage.
- Model training must create its own fixed-seed stratified 70/15/15 split from the available public dataset images instead of relying on a vendor-export split, unless a documented exception is approved.
- Final model is selected by comparing at least three **Model Candidate** architectures on same test protocol: Custom CNN baseline, MobileNetV2, and DenseNet121.
- Transfer-learning **Model Candidate** training uses two phases: train classification head with pretrained base frozen, then optionally fine-tune top layers with low learning rate when validation metrics improve.
- Model training and export use fixed class index order: `0 = FMD`, `1 = LSD`, `2 = healthy`; Indonesian PMK/Lato-Lato wording remains display text only.
- The first two-stage model version keeps the same three **Disease Class** outputs and handles **Insufficient Visual Evidence** as a decision policy rather than a fourth model class.
- Final model selection uses macro F1 as the primary metric, rejects candidates with any per-class F1 below 85% unless a documented exception is approved, then tie-breaks by test accuracy, TFLite size, and offline latency.
- Each **Model Candidate** must produce a **Model Evaluation Report**.
- Model training project is done only when dataset split report, label validation report, three-candidate evaluation, final model selection rationale, Keras/TFLite exports, TFLite parity report, backend metadata update, Android TFLite asset update, offline-inference smoke test, and early-detection wording check are complete.
- Each full training run must produce dataset, label, evaluation, and deployment artifacts: `DATASET_SPLIT_REPORT.md`, `LABEL_VALIDATION.md`, `MODEL_EVALUATION_REPORT.md`, `TFLITE_PARITY_REPORT.md`, metrics JSON, confusion matrix images, `class_indices.json`, `split_manifest.csv`, server model, TFLite model, backend metadata, Android asset, and one shared model version string.
- Model version pattern is `cattle-disease-{architecture}-vYYYYMMDD-s{seed}`; artifact filenames mirror architecture, date, seed, and conversion type, e.g. `mobilenetv2_v20260601_s42.keras` and `mobilenetv2_v20260601_s42_dynamic_range.tflite`.
- Full model training runs on Kaggle GPU as primary environment, with Google Colab free tier as fallback; training artifacts must record runtime platform, TensorFlow version, random seed, dataset version, and training date.
- Kaggle or Colab notebooks are wrappers only; `docs/model/evaluate_candidates.py` is the source-of-truth training/evaluation script and must produce a versioned `model_training_artifacts_<version>.zip` output without secret-only notebook logic.
- Model training uses TensorFlow/Keras end-to-end for single-stage classifier candidates, server classifier export, and TensorFlow Lite conversion.
- Initial model training protocol uses maximum 50 epochs, early stopping with patience 8 and best-weight restore, learning-rate reduction on plateau with patience 4 and factor 0.2, seed 42, batch size 32 by default, and batch size 16 for DenseNet121 if GPU memory requires it.
- Candidate evaluation trains all **Model Candidates** once with seed 42, then reruns the winning candidate with two additional seeds if time permits; single-seed results are acceptable only when documented as a limitation.
- Model training input uses RGB images resized to 224 × 224 × 3 with pixel rescaling to 1/255 for all candidates and exported inference models.
- Each model export must include `preprocessing.json` documenting deterministic inference preprocessing: EXIF orientation correction before resize where available, RGB decode, 224 × 224 resize, and pixel rescale to 1/255; backend and mobile preprocessing must be checked against this artifact.
- Final model target is test accuracy at least 88% and per-class F1-score at least 85%.
- Real-world model updates must include a field-only evaluation using expert-reviewed labels and reporting macro F1, per-class recall, disease recall for FMD and LSD, confusion matrix, insufficient-evidence rate, and **False Confident Result** rate.
- Two-stage model success requires lower **False Confident Result** rate than the current single-stage baseline, field macro F1 equal or better, FMD/LSD recall not worse by more than 5 percentage points, and field **Insufficient Visual Evidence** rate at or below 35%.
- If no **Model Candidate** reaches model targets, the best candidate may be used only as an experimental/demo model with a documented exception, follow-up issue recommendations, and no clinical/production-validity claim.
- TFLite model target is accuracy drop at most 2% compared with server model and file size under 10 MB.
- TFLite conversion ladder exports Float32 TFLite first for parity baseline, then dynamic-range quantized TFLite for app candidate, and only attempts full int8 quantization with representative data if size or latency targets fail.
- TFLite parity passes only when Keras server model and TFLite model are evaluated on the same test split with accuracy drop ≤2 percentage points, macro F1 drop ≤2 percentage points, per-class F1 drop ≤3 percentage points, no class-index mismatch, confusion matrices recorded, probability drift summarized, model size recorded, and offline latency measured or explicitly marked as an unmeasured limitation.
- **Training Augmentation** is separate from **Inference Preprocessing**; random transformations never run during user prediction.
- Allowed **Training Augmentation** for the initial model run is mild and lesion-preserving: rotation up to ±15°, mild brightness/contrast changes, zoom up to ±10%, and horizontal flip; vertical flip, heavy blur, aggressive crop, and extreme color shift are avoided.
- **Early Detection Result** contains either exactly one predicted **Disease Class** or **Insufficient Visual Evidence**.
- **Early Detection Result** includes **Handling Advice** based on predicted **Disease Class** and **Confidence Level**, or retake/advisor guidance for **Insufficient Visual Evidence**, not claimed lesion localization.
- Thesis, app, and report wording should frame outputs as image classification, early detection, prediction results, confidence, and initial handling advice; they must avoid claiming final diagnosis, veterinarian replacement, or clinical disease determination.
- Medium **Confidence Level** suggests retaking photo; low **Confidence Level** marks result unreliable and requires retaking photo.
- **Insufficient Visual Evidence** avoids forcing an **Early Detection Result** into FMD, LSD, or healthy when confidence is below 70%, top-class margin is below 15 percentage points, or image quality is not enough.
- Real-world tuning prioritizes reducing **False Confident Result** cases over maximizing disease-class coverage.
- **Hard-Negative Field Image** entries are used first for threshold tuning and error analysis; they become an explicit unknown/other training class only after enough reviewed examples exist.
- **Disease Class** has one **Localized Display Label** per supported app language.
- **Early Detection Result** may come from **Server Inference** or **On-device Inference** with same domain fields for history, result UI, and PDF export.
- **Early Detection Result** stores model version so backend and APK model version mismatch remains visible in result, history, and PDF.
- Backend deploys the selected Keras/SavedModel server artifact and Android deploys the matching selected TFLite artifact; both must share class index order, preprocessing, model version, and evaluation report, and release is blocked if parity thresholds fail.
- **Scan History** stores **Early Detection Result** data locally, including **Insufficient Visual Evidence** outcomes, timestamp, image source, confidence, and inference mode.
- Deleted **Scan History** items are hidden as soft-deleted records and automatically purged with local image/PDF cache after 30 days.
- Server upload requires **Upload Consent**, EXIF metadata removal, local-only **Scan History**, user-controlled record deletion, and **No-retention Server Inference**.
- Crash-free metric uses **Crash Reporting Consent** or limited field-test logs when consent is unavailable.
- If **Upload Consent** is denied or disabled, **Online-first Detection** skips **Server Inference** and uses **On-device Inference**.
- Production readiness includes **Limited Field Validation** but not lab-confirmed clinical validation.
- Production readiness requires **Acceptance Test Suite** before release candidate.
- Production app targets online inference under 3 seconds, offline inference under 1 second, crash-free sessions at least 99%, fallback success at least 95%, and APK size under 50 MB.
- App does not require user account because **Scan History** remains local to device.
- **Backend Deployment Phase** starts with HTTP LAN backend for current TA/demo, then scales to HTTPS institutional or VPS server for production pilot.
- Proposal-based PRD is written in English and includes explicit deviation section for online-first architecture and production-scope expansion.
- **Production App** includes **Core Screen Set** and **Basic Accessibility** for complete farmer-facing workflow.
- Home screen acts as action dashboard with primary scan action, recent result, connection status, and quick guide entry.
- Guide screen provides **Guide Content** for farmer decision support without replacing veterinarian advice.
- Camera screen presents **Capture Checklist** before or during image capture.
- **Image Quality Gate** runs before **Online-first Detection** for both camera and gallery images to avoid unreliable input.

## Example dialogue

> **Dev:** "If cattle image is captured in village with unstable signal, does app still produce Detection Result?"
> **Domain expert:** "Yes — Online-first Detection tries Server Inference first, then falls back to On-device Inference when server cannot respond."

## Flagged ambiguities

- Final TA report title and Bab I follow the approved proposal framing; online-first architecture and production-scope additions are documented as implementation realization and discussion in later chapters, not as replacements for the proposal premise.
- Final TA report Bab I may revise proposal limitations to reflect the implemented Android system, model evaluation, functional testing, and limited field validation, while still excluding clinical/veterinary diagnostic validation.
- Final TA report Bab III uses a staged rancang-bangun method; the machine-learning pipeline is presented as one implementation activity within system development rather than as the only research method.
- Final TA report Bab IV analyzes implemented Android/backend behavior, model evaluation, TFLite parity, functional testing, limited field validation, and explicit non-clinical limitations.
- Final TA report Bab II uses the proposal references as an audited base, then maps them into related cattle-disease image-classification studies and project technologies such as CNN, transfer learning, MobileNetV2, TensorFlow/Keras, TensorFlow Lite, Android, backend API, and validation methods.
- Proposal language implies offline Android as primary path, while chosen PRD direction is **Online-first Detection**. PRD must explicitly justify this deviation from proposal.
- Proposal limits Android work to prototype/conceptual field testing, while chosen PRD direction is **Production App**. PRD must explicitly state scope expansion and add production-grade requirements.
- App language must support Indonesian and English display without changing canonical **Disease Class** values.
- App language follows Android system language when Indonesian or English is available, otherwise falls back to Indonesian.
- App must guide image capture toward visible symptom areas instead of accepting unrestricted cattle photos as equally valid.
