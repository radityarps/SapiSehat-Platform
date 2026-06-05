# Prompt 4: Result Screen — Implementation Plan

## Context

Prompt 0 (infrastructure), Prompt 1 (splash), Prompt 2 (onboarding), and Prompt 3 (camera) are complete. The existing `ResultRoute.kt` is a minimal skeleton that displays raw label, confidence, and mode with a back button. It must be rewritten into a rich diagnosis screen with mode badge, confidence bar, all-class scores, disease-specific advice, confidence warnings, and action buttons (save / share / retake).

### Current state of related code

| File                              | Status   | Notes                                                                                                                                                                                                                                                                                                           |
| --------------------------------- | -------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ui/result/ResultRoute.kt`        | Skeleton | Displays `Label: $label`, `Confidence: XX%`, `Mode: $mode`, `Button(Back)` — needs complete rewrite                                                                                                                                                                                                             |
| `domain/model/DetectionResult.kt` | Complete | Fields: `label`, `displayLabel`, `confidence`, `isReliable`, `allScores: Map<String, Float>`, `inferenceMode: InferenceMode`, `processingMs: Int?`                                                                                                                                                              |
| `domain/model/InferenceMode.kt`   | Complete | Enum: `ONLINE`, `OFFLINE`, `OFFLINE_FALLBACK`                                                                                                                                                                                                                                                                   |
| `strings.xml`                     | Complete | All result strings defined: `result_diagnosis`, `result_confidence`, `result_mode_online/offline/fallback`, `result_btn_save/share/retake`, `result_disease_*`, `result_advice_*`, `result_confidence_high/medium/low`, `result_warning_medium/low`, `result_saved`, `result_all_scores`, `result_advice_title` |
| `Theme`                           | Complete | `Success` (#5B9A5B), `Danger` (#D4745C), `Accent` (#E8985E), `Warning`, `Primary`, colours available                                                                                                                                                                                                            |

## Approach

A single-file rewrite of `ResultRoute.kt` using pure Compose (no ViewModel). The screen receives all classification data as parameters (label, confidence, mode, allScoresJson) plus callbacks for back, save, and retake. It parses the JSON scores map, maps the label to a per-class display config, computes a confidence level, and renders the full diagnosis UI.

### Key Components

1. **ClassDisplayConfig** — data object mapping disease label to display name, emoji icon, semantic colour, and multi-line advice text. Three hardcoded entries: Sehat (🟢, success green), PMK (🔴, danger red), Lato-Lato (🟠, accent orange).

2. **ConfidenceLevel** — enum with thresholds: `HIGH` (≥ 0.80), `MEDIUM` (≥ 0.60), `LOW` (< 0.60). Computed from the raw confidence float.

3. **ModeBadge** — pill-shaped `Surface` with mode text + icon. ONLINE → 🌐 (green-tinted), OFFLINE → 📴 (orange-tinted), OFFLINE_FALLBACK → ⚠️ (orange-tinted).

4. **ConfidenceBar** — a horizontal gradient bar (12 dp height, rounded 6 dp) that goes from the disease colour at alpha 0.6 to full alpha. Width is proportional to confidence.

5. **ScoreRow** — one row per class in the all-scores map. Shows a filled circle (●) for the detected class or empty (○) for others, the class label, a progress bar proportional to the score, and the percentage.

6. **AdviceCard** — a card with ⚠️ header and multi-line advice text, using `\n` splitting for per-line rendering.

7. **ConfidenceWarningCard** — shown only for MEDIUM (yellow warning) or LOW (red warning) confidence, with appropriate warning text from string resources.

### Reuse

| Source                  | What                                                                                                                                                                                                                   | Used for                                         |
| ----------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------ |
| `strings.xml`           | `result_diagnosis`, `result_confidence`, `result_mode_*`, `result_btn_*`, `result_disease_*`, `result_advice_*`, `result_confidence_*`, `result_warning_*`, `result_saved`, `result_all_scores`, `result_advice_title` | All displayed text                               |
| `Color.kt`              | `Success` (#5B9A5B), `Danger` (#D4745C), `Accent` (#E8985E), `Warning`                                                                                                                                                 | Disease and confidence colours                   |
| `Type.kt`               | `headlineMedium`, `titleLarge`, `bodyLarge`, `bodyMedium`                                                                                                                                                              | Text styling                                     |
| `DetectionResult` model | `allScores`, `inferenceMode`, `label`, `confidence`                                                                                                                                                                    | Data source (passed indirectly via route params) |

## Files to Rewrite

| #   | File                       | Action  | Purpose                                                 |
| --- | -------------------------- | ------- | ------------------------------------------------------- |
| 1   | `ui/result/ResultRoute.kt` | Rewrite | Full diagnosis display with all components listed above |

## Files Unchanged

- `domain/model/DetectionResult.kt`, `InferenceMode.kt`
- `strings.xml`, `Color.kt`, `Type.kt`, `Theme.kt`
- Navigation — `SapiSehatNavHost.kt` already passes `onSave` and `onRetake` (currently unused stubs); the new `ResultRoute` will honour them

## Steps

- [x] **1. Rewrite ResultRoute.kt**
  - Define `ClassDisplayConfig(label, displayName, icon, color, advice)` as a private data class
  - Define `classConfigs` map: `"SEHAT"/"healthy"` → Sehat, `"FMD"/"PMK"` → PMK, `"LSD"/"LATO_LATO"` → Lato-Lato; default fallback to a generic config
  - Define `ConfidenceLevel` private enum with `HIGH`, `MEDIUM`, `LOW`; companion `fun from(value: Float)` with thresholds
  - Function signature: `ResultRoute(label, confidence, mode, allScoresJson, onBack, onSave, onRetake)`
  - Parse `allScoresJson` with `org.json.JSONObject` into `Map<String, Float>`; handle malformed JSON gracefully (empty map)
  - Compute `config = classConfigs[label]`, `confidenceLevel = ConfidenceLevel.from(confidence)`, `confidencePercent = (confidence * 100).toInt()`
  - UI: `Scaffold` with top bar showing back arrow + title "Hasil Diagnosis"; body is a `Column(verticalScroll)`:
    1. **Photo placeholder** — `Surface(200.dp, rounded 16.dp, surfaceVariant)` with 📸 emoji centered
    2. **Mode badge** — `Row` pill with mode icon + text, coloured per mode
    3. `HorizontalDivider`
    4. **Diagnosis headline** — `Row`: config icon + `"${config.displayName} Terdeteksi"` in config colour, `headlineMedium` bold
    5. **Confidence** — `"Keyakinan: ${confidencePercent}%"` (`titleLarge`), plus `ConfidenceLevelLabel` (Tinggi/Sedang/Rendah) in corresponding colour
    6. **ConfidenceBar** — `ConfidenceBar(confidence, config.color)` composable
    7. **All scores** — header `"Semua Skor"` (`titleMedium`), then each entry in parsed scores map rendered as `ScoreRow(label, score, isHighlighted = label == config.label)`, sorted descending
    8. **Confidence warning** (conditional) — if MEDIUM → yellow warning card, if LOW → red warning card, with string from `result_warning_medium` or `result_warning_low`
    9. **Advice card** — header `⚠️ Saran Penanganan`, then each line from `config.advice.split("\n")` as a `Row` with bullet
    10. **Action buttons** — `Row` with `OutlinedButton("Simpan")`, `OutlinedButton("Bagikan")`, `Button("Ulangi")` calling `onSave`, share intent, `onRetake` respectively
  - `Share` functionality: build share text and launch `Intent.ACTION_SEND` with `Intent.createChooser`
  - `ConfidenceBar` composable: `Box` 12 dp height, rounded 6 dp, `Modifier.fillMaxWidth(fraction = confidence)`, background brush = horizontal gradient from `color.copy(alpha = 0.6f)` to `color`
  - `ScoreRow` composable: `Row` with circle icon (●/○) in config colour, `Text` label, `LinearProgressIndicator` weight(1f), `Text` percent
  - Include a `@Preview` with sample data

## Trade-offs & Assumptions

| Item                                               | Decision | Rationale                                                                                                                                                                                                                    |
| -------------------------------------------------- | -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| No ViewModel                                       | Accepted | Screen is purely presentational; receives all data as params; no async state changes                                                                                                                                         |
| `allScoresJson` parsing with `org.json.JSONObject` | Accepted | Built into Android; no extra dependency; handles malformed JSON via try/catch                                                                                                                                                |
| Multi-line advice split by `\n`                    | Accepted | Simple and matches the `result_advice_*` string format with explicit `\n` separators                                                                                                                                         |
| Share uses `Intent.ACTION_SEND`                    | Accepted | Standard Android sharing; no permissions required                                                                                                                                                                            |
| Class label matching (`SEHAT`/`healthy`/`Sehat`)   | Robust   | `ClassDisplayConfig` matching ignores case and handles all known label variants from the model                                                                                                                               |
| Empty `allScores` fallback                         | Accepted | If JSON parse fails, scores map is empty → `ScoreRow` list is empty → only confidence bar shown                                                                                                                              |
| `onSave` callback unused for now                   | Accepted | The stub in NavHost (`/* implemented in Prompt 4 */`) will be connected; we call it but saving logic can be filled later                                                                                                     |
| Confidence bar gradient                            | Accepted | `Brush.horizontalGradient` from Compose; no canvas needed                                                                                                                                                                    |
| ScoreRow progress bar                              | Accepted | `LinearProgressIndicator` with `progress = { score }`; colour matches disease colour                                                                                                                                         |
| Confidence level thresholds                        | Accepted | HIGH ≥ 80%, MEDIUM ≥ 60%, LOW < 60% — as specified                                                                                                                                                                           |
| Mode badge colours                                 | Accepted | ONLINE green tint, OFFLINE/OFFLINE_FALLBACK orange tint — as specified                                                                                                                                                       |
| `ResultRoute` signature change                     | Verified | NavHost passes `(label, confidence, mode, allScoresJson, onBack, onSave, onRetake)`; skeleton had only `(label, confidence, mode, onBack)` — we add params to match NavHost, keeping backward compat with existing call site |

## Risks

| Risk                                                  | Level | Mitigation                                                                                                         |
| ----------------------------------------------------- | ----- | ------------------------------------------------------------------------------------------------------------------ |
| JSON parsing failure from malformed scores            | Low   | Wrap in try/catch; return empty map; screen still renders with confidence bar and advice                           |
| Class label mismatch (model returns unexpected label) | Low   | `classConfigs.getOrDefault(label, defaultConfig)` provides fallback display                                        |
| `Uri` for photo placeholder is missing                | Low   | We show a placeholder Surface with 📸; actual image display deferred to later prompt (Coil loading from saved URI) |
| Share intent chooser not available on some devices    | Low   | `Intent.createChooser` always returns a valid intent; wraps with `try/catch`                                       |
| Scroll performance with many score rows               | Low   | Only 3 classes (Sehat, PMK, Lato-Lato); negligible                                                                 |

## Verification

1. `ResultRoute.kt` signature matches NavHost call: `(label, confidence, mode, allScoresJson, onBack, onSave, onRetake)`
2. `ClassDisplayConfig` returns correct display name, icon, colour, and advice for Sehat, PMK, and Lato-Lato
3. `ConfidenceLevel.from()` correctly maps: 0.85 → HIGH, 0.65 → MEDIUM, 0.45 → LOW (boundary 0.80 and 0.60)
4. Mode badge renders correct icon and colour for ONLINE (🌐 green), OFFLINE (📴 orange), OFFLINE_FALLBACK (⚠️ orange)
5. Confidence bar width proportional to confidence (0.75 → 75% width) with correct gradient colours
6. All scores section renders each class with icon, progress bar, and percentage; detected class highlighted
7. Confidence warning appears for MEDIUM (yellow) and LOW (red); absent for HIGH
8. Advice card renders multi-line advice text for the detected disease
9. Action buttons: Simpan calls `onSave`, Bagikan launches share intent, Ulangi calls `onRetake`
10. JSON parse failure handled gracefully — no crash, scores section empty
