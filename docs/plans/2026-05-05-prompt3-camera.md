# Prompt 3: Camera Screen — Implementation Plan

## Context

Prompt 0 (infrastructure), Prompt 1 (splash), and Prompt 2 (onboarding) are complete. The existing `CameraRoute.kt` and `CameraViewModel.kt` are placeholder skeletons — they need to be rewritten into a full CameraX-powered capture screen with permission handling, flash toggle, grid overlay, and gallery picker. The `ClassifyImageUseCase` already exists and will be reused as-is.

### Current state of related files

| File                                     | Status   | Notes                                                                                                                                                                |
| ---------------------------------------- | -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ui/camera/CameraRoute.kt`               | Skeleton | Placeholder UI with fake URI classification; needs complete rewrite                                                                                                  |
| `ui/camera/CameraViewModel.kt`           | Skeleton | Basic `classify(imageUri, onResult)` using `ClassifyImageUseCase`; lacks permission, flash, grid, progress                                                           |
| `domain/usecase/ClassifyImageUseCase.kt` | Complete | `suspend operator fun invoke(imageUri: Uri)` → saves via `DetectionRepository`; no changes needed                                                                    |
| `strings.xml`                            | Complete | Camera strings already defined: `camera_guidance`, `camera_capture`, `camera_gallery`, `camera_flash_*`, `camera_grid_*`, `camera_permission_*`, `camera_processing` |
| `Theme` / `Color` / `Type`               | Complete | All colors and typography available for overlay elements                                                                                                             |

## Approach

A two-file rewrite following MVVM + Hilt + CameraX:

1. **CameraViewModel** — Expand the existing HiltViewModel with full camera state management:
   - `CameraUiState` data class extended with `hasCameraPermission`, `permissionPermanentlyDenied`, `flashMode`, `showGrid`, `progressText`
   - `FlashMode` enum (AUTO, ON, OFF)
   - `checkPermission()` using `ContextCompat.checkSelfPermission`
   - `onPermissionResult(granted: Boolean)` to update state
   - Enhanced `classify(imageUri, onResult)` with progress text stages
   - `setFlashMode()`, `toggleGrid()`, `clearError()`

2. **CameraRoute** — Full Compose UI with CameraX integration:
   - Permission flow via `rememberLauncherForActivityResult(RequestPermission)` and `ActivityResultContracts.GetContent()` for gallery
   - Conditional rendering: permission denied → `CameraPermissionScreen`; granted → `CameraActiveScreen`
   - `CameraActiveScreen`: `AndroidView(PreviewView)` bound to CameraX `ProcessCameraProvider`, grid overlay, guidance label, flash/grid toggles, shutter button, gallery button, loading overlay, error snackbar

No new files; two existing files rewritten. No other files modified.

## Files to Rewrite (2 existing)

| #   | File                           | Action  | Purpose                                                           |
| --- | ------------------------------ | ------- | ----------------------------------------------------------------- |
| 1   | `ui/camera/CameraViewModel.kt` | Rewrite | Full camera state, permission, flash, grid, classify coordination |
| 2   | `ui/camera/CameraRoute.kt`     | Rewrite | CameraX preview, controls, overlays, permission UI                |

## Files Unchanged

- `domain/usecase/ClassifyImageUseCase.kt` — used as-is
- `domain/model/DetectionResult.kt` — used as-is
- All theme, string, and navigation files

## Steps

- [x] **1. Rewrite CameraViewModel.kt**
  - `enum class FlashMode { AUTO, ON, OFF }`
  - `data class CameraUiState` with fields: `isLoading`, `error`, `progressText`, `hasCameraPermission`, `permissionPermanentlyDenied`, `flashMode` (default `AUTO`), `showGrid` (default `false`)
  - Constructor: `@Inject constructor(@ApplicationContext private val appContext: Context, private val classifyImageUseCase: ClassifyImageUseCase)`
  - `fun checkPermission()` — calls `ContextCompat.checkSelfPermission(appContext, CAMERA)` → updates `hasCameraPermission` and `permissionPermanentlyDenied`
  - `fun onPermissionResult(granted: Boolean)` — updates `hasCameraPermission`; if previously denied and now denied again, sets `permissionPermanentlyDenied = true`
  - `fun classify(imageUri: Uri, onResult: (DetectionResult) -> Unit)` — launches coroutine, sets `isLoading = true`, `progressText = R.string.camera_processing`, calls `classifyImageUseCase(imageUri)`, on success clears loading and calls `onResult`, on failure sets `error`
  - `fun setFlashMode(mode: FlashMode)` — cycles or sets directly
  - `fun toggleGrid()` — flips `showGrid`
  - `fun clearError()` — sets `error = null`

- [x] **2. Rewrite CameraRoute.kt**
  - `CameraRoute(onShowResult: (label: String, confidence: Float, mode: String, scoresJson: String) -> Unit, onOpenHistory: () -> Unit, viewModel: CameraViewModel = hiltViewModel())`
  - Permission launcher: `rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { granted -> viewModel.onPermissionResult(granted) }`
  - Gallery launcher: `rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri -> uri?.let { viewModel.classify(it) { result -> onShowResult(result.label, result.confidence, result.inferenceMode.name, result.allScoresJson) } } }`
  - `LaunchedEffect`: call `viewModel.checkPermission()`; if not granted and not permanently denied, launch permission request
  - Conditional rendering:
    - `!hasCameraPermission` → `CameraPermissionScreen(permanentlyDenied, onRequestPermission, onOpenSettings)`
    - `hasCameraPermission` → `CameraActiveScreen`
  - **CameraActiveScreen** layout:
    - `Box(fillMaxSize)`:
      - `AndroidView(factory = { PreviewView(it).apply { ... } }, modifier = Modifier.fillMaxSize())` — CameraX setup with `ProcessCameraProvider`, bind Preview + flash-aware ImageCapture
      - `CameraGridOverlay(visible = showGrid)` — 2 horizontal + 2 vertical semi-transparent white lines
      - **Guidance label** — top-center `Surface` with `camera_guidance` text
      - **Top-right toggles** — `Column`:
        - Flash button (icon varies by mode: ⚡A / ⚡ / 🚫), cycles `FlashMode`
        - Grid button (⊞), toggles grid
      - **Bottom bar** — `Row(center)`:
        - Gallery button (🖼️ icon) → launches gallery picker
        - Shutter button — `Box(72.dp, CircleShape, border = white 3.dp)`, inner `Box(60.dp, Primary)` → onClick triggers image capture via `ImageCapture.takePicture()`
      - **Loading overlay** — `Box(black 0.6f, fillMaxSize)` with `CircularProgressIndicator` + `progressText`
      - **Error snackbar** — `Snackbar` with dismiss action
  - CameraX lifecycle: `AndroidView` update block binds/unbinds use cases on lifecycle changes; respect `LifecycleEvent.ON_DESTROY`
  - `@Preview` composable stubs (camera preview not available at design time — show placeholder)

## Trade-offs & Assumptions

| Item                                              | Decision     | Rationale                                                                                                            |
| ------------------------------------------------- | ------------ | -------------------------------------------------------------------------------------------------------------------- |
| CameraX ProcessCameraProvider                     | Accepted     | Official Jetpack library; already in dependencies (camera-core, camera-camera2, camera-lifecycle, camera-view 1.3.4) |
| Flash managed via CameraX ImageCapture.flashMode  | Accepted     | Direct CameraX API; no need for Camera2 manual flash control                                                         |
| Grid overlay as Compose lines                     | Accepted     | Simple canvas-drawn lines over PreviewView; avoids platform camera grid APIs                                         |
| Gallery via `GetContent` contract                 | Accepted     | Works on all Android versions; no need for legacy `READ_EXTERNAL_STORAGE` permission on Android 13+                  |
| Permission launcher in Composable (not ViewModel) | Accepted     | `rememberLauncherForActivityResult` must be called in Composition; ViewModel receives result via callback            |
| `@ApplicationContext` for permission check        | Accepted     | `ContextCompat.checkSelfPermission` needs a Context; `@ApplicationContext` avoids Activity leak                      |
| Guidance label as Surface overlay                 | Accepted     | Semitransparent surface floating over preview; matches spec                                                          |
| Shutter uses CameraX ImageCapture.takePicture()   | Accepted     | Saves to app cache, returns Uri for classification pipeline                                                          |
| No video support                                  | Out of scope | Prompt 3 spec only mentions capture + gallery; video deferred or excluded                                            |
| Loading overlay shows progress text               | Accepted     | Spec requires `progressText` (string resource) during classification                                                 |
| `ImageCapture` needs `@Composable remember`       | Accepted     | Must survive recomposition; stored in `remember {}` block alongside `ProcessCameraProvider`                          |

## Risks

| Risk                                            | Level  | Mitigation                                                                                                |
| ----------------------------------------------- | ------ | --------------------------------------------------------------------------------------------------------- |
| CameraX lifecycle binding errors                | Medium | Follow official pattern: observe `LifecycleEvent` in `AndroidView` update block; unbind on `ON_DESTROY`   |
| Permission flow edge cases                      | Low    | Handle: never-asked, denied-once, permanently-denied; use `shouldShowRequestPermissionRationale`          |
| Gallery Uri may be content:// with no file path | Low    | `ClassifyImageUseCase` already handles `Uri` directly — no file path assumption                           |
| `ProcessCameraProvider` async availability      | Low    | Use `ProcessCameraProvider.getInstance(context)` with `ListenableFuture` — await in coroutine or callback |
| `ImageCapture.takePicture()` output file race   | Low    | Use `File.createTempFile` in `context.cacheDir` with unique name                                          |
| Preview rotation on device orientation          | Low    | CameraX handles orientation automatically via `Preview.SurfaceProvider`                                   |
| Compose recomposition resetting CameraX         | Low    | Store `ProcessCameraProvider` and `ImageCapture` in `remember {}`; bind only once                         |
| `@Preview` cannot render camera                 | Low    | Provide a `@Preview` with placeholder content; annotate camera-specific parts with `@VisibleForTesting`   |

## Verification

1. `CameraViewModel.kt` has `FlashMode` enum, extended `CameraUiState`, permission methods, `classify()` with progress
2. `CameraRoute.kt` requests camera permission on launch
3. Permission denied → `CameraPermissionScreen` with rationale and settings button
4. Permission granted → CameraX preview fills screen
5. Flash toggle cycles: AUTO → ON → OFF → AUTO; icon changes
6. Grid toggle shows/hides 2×2 overlay lines
7. Guidance label visible at top-center over preview
8. Gallery button opens system file picker; selected image triggers classification
9. Shutter button captures photo; image is classified via `ClassifyImageUseCase`
10. Loading overlay appears with progress text during classification
11. Error snackbar appears on classification failure with dismiss action
12. Successful classification calls `onShowResult` with label, confidence, mode, and scores JSON
