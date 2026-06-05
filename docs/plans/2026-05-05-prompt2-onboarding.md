# Prompt 2: Onboarding Screen — Implementation Plan

## Context

Prompt 0 (Shared Infrastructure) and Prompt 1 (Splash Screen) are complete. Navigation routes, bilingual strings, theme, and splash-to-onboarding flow are in place. The Onboarding screen is the first destination for new users — it presents 3 informational slides before granting access to the main app. This UI component is fully self-contained with no ViewModel or complex dependencies.

### Current state of related code

- `SapiSehatNavHost.kt` already imports and calls `OnboardingRoute(onFinish)` from `com.sapisehat.app.ui.onboarding.OnboardingRoute`
- `strings.xml` already defines `onboarding_title_1` through `onboarding_title_3` and `onboarding_body_1` through `onboarding_body_3`, plus `button_skip` (Lewati), `button_next` (Lanjut), and `button_start` (Mulai)
- `TropisBersihColors.Primary` (#7DA97C), `OnPrimary` (#FFFFFF), and other colors are available in `Color.kt`
- `SapiSehatTypography.headlineMedium` (22sp SemiBold) and `bodyLarge` (16sp) are available
- `SplashRoute.kt` reads `has_completed_onboarding` from `PreferenceManager.getDefaultSharedPreferences` — this Onboarding screen will write the same key

## Approach

Create a single new Composable file `OnboardingRoute.kt` containing:

1. A data class `OnboardingSlide` to model each slide
2. A `slides` list of 3 hardcoded slides referencing string resources
3. The `OnboardingRoute` composable with:
   - `HorizontalPager` for swipeable slides (Material3 foundation, `@OptIn(ExperimentalFoundationApi::class)`)
   - A skip button ("Lewati") in the top-right corner
   - A dots page indicator below the pager
   - A CTA button: "Lanjut" (slides 1-2) or "Mulai" (slide 3)
   - On "Mulai" click: write `has_completed_onboarding = true` to `PreferenceManager`, then call `onFinish()`
   - Slide content: centered emoji at 72sp, title in `headlineMedium` bold, body in `bodyLarge` colored `textSecondary`

No existing files are modified. All reused resources were created in Prompt 0.

## Files to Create (1 new)

| #   | File                                                                               | Purpose                                                |
| --- | ---------------------------------------------------------------------------------- | ------------------------------------------------------ |
| 1   | `apps/mobile/app/src/main/java/com/sapisehat/app/ui/onboarding/OnboardingRoute.kt` | 3-slide onboarding with dots, skip, and CTA navigation |

## Files to Modify (none)

No existing files need changes.

## Reuse

| Source           | What                                                                   | Used for                                                    |
| ---------------- | ---------------------------------------------------------------------- | ----------------------------------------------------------- |
| `strings.xml`    | `onboarding_title_1`–`3`, `onboarding_body_1`–`3`                      | Slide titles and body text                                  |
| `strings.xml`    | `button_skip` (Lewati), `button_next` (Lanjut), `button_start` (Mulai) | Skip button and CTA button labels                           |
| `Color.kt`       | `TropisBersihColors.Primary` (#7DA97C)                                 | Active dot color, CTA button background                     |
| `Color.kt`       | `TropisBersihColors.OnPrimary` (#FFFFFF)                               | CTA button text color                                       |
| `Color.kt`       | `TropisBersihColors.OnSurface.copy(alpha = 0.3f)`                      | Inactive dot color                                          |
| `Type.kt`        | `headlineMedium` (22sp SemiBold)                                       | Slide title text style                                      |
| `Type.kt`        | `bodyLarge` (16sp)                                                     | Slide body text style                                       |
| `SplashRoute.kt` | `PreferenceManager.getDefaultSharedPreferences` pattern                | Consistent SharedPreferences key `has_completed_onboarding` |
| Navigation       | `OnboardingRoute(onFinish: () -> Unit)` signature                      | Already imported and called in `SapiSehatNavHost.kt`        |

## Steps

- [x] **1. Create OnboardingRoute.kt**
  - Package: `com.sapisehat.app.ui.onboarding`
  - Data class:
    ```kotlin
    data class OnboardingSlide(
        val emoji: String,
        @StringRes val titleRes: Int,
        @StringRes val bodyRes: Int,
    )
    ```
  - Slides list:
    ```kotlin
    val slides = listOf(
        OnboardingSlide("📸", R.string.onboarding_title_1, R.string.onboarding_body_1),
        OnboardingSlide("📴", R.string.onboarding_title_2, R.string.onboarding_body_2),
        OnboardingSlide("⚡", R.string.onboarding_title_3, R.string.onboarding_body_3),
    )
    ```
  - `OnboardingRoute(onFinish: () -> Unit)`:
    - `@OptIn(ExperimentalFoundationApi::class)`
    - `val pagerState = rememberPagerState(pageCount = { slides.size })`
    - `val context = LocalContext.current`
    - Layout structure (top to bottom):
      - **Top bar**: `Row` with `Spacer(weight(1f))` + `TextButton("Lewati")` → `onFinish()`
      - **HorizontalPager**: `state = pagerState`, `modifier = Modifier.fillMaxSize().weight(1f)`, each page renders `SlideContent(slide)`
      - **Dots indicator**: `Row(center)` with 3 dots — active dot `12.dp`, `Primary`; inactive dot `8.dp`, `OnSurface.copy(alpha = 0.3f)`; `animateColorAsState` for smooth transitions
      - **CTA button**: `Button` or `FilledTonalButton` spanning full width with padding
        - Text: `if (currentPage == slides.lastIndex) R.string.button_start else R.string.button_next`
        - OnClick:
          ```kotlin
          if (currentPage == slides.lastIndex) {
              PreferenceManager.getDefaultSharedPreferences(context)
                  .edit()
                  .putBoolean("has_completed_onboarding", true)
                  .apply()
              onFinish()
          } else {
              coroutineScope.launch { pagerState.animateScrollToPage(currentPage + 1) }
          }
          ```
  - `SlideContent(slide: OnboardingSlide)`:
    - `Column(center, horizontalPadding = 32.dp)`
    - `Text(slide.emoji, fontSize = 72.sp)`
    - `Spacer(32.dp)`
    - `Text(slide.titleRes, style = headlineMedium, fontWeight = Bold, textAlign = Center)`
    - `Spacer(16.dp)`
    - `Text(slide.bodyRes, style = bodyLarge, color = MaterialTheme.colorScheme.textSecondary, textAlign = Center)`
  - Include a `@Preview` composable for design-time preview

## Trade-offs & Assumptions

| Item                                   | Decision | Rationale                                                                                                                                                         |
| -------------------------------------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| No ViewModel                           | Accepted | UI-only screens with simple page index state; no async ops or business logic                                                                                      |
| `PreferenceManager` directly           | Accepted | Consistent with SplashScreen (Prompt 1); DataStore migration deferred to Prompt 8                                                                                 |
| Skip does NOT save onboarding complete | Accepted | Skip only navigates to Main without setting `has_completed_onboarding = true`; user will see onboarding again on next launch unless they explicitly press "Mulai" |
| `HorizontalPager` (Experimental)       | Accepted | Stable API in Material3 1.2+; `@OptIn` suppresses compiler warning; widely used in production                                                                     |
| Emoji slides instead of images         | Accepted | Zero-code change to swap in images later; keep implementation simple                                                                                              |
| `rememberCoroutineScope` for scroll    | Accepted | Standard Compose pattern for launching scroll animations from click handlers                                                                                      |
| Works offline                          | Assumed  | No network access needed; all content is local strings and emoji                                                                                                  |

## Risks

- **Low risk**: `ExperimentalFoundationApi` is marked experimental but has been stable across multiple Compose versions; Material3 1.2+ is already in the project dependencies
- **Low risk**: Directory `ui/onboarding/` does not exist — `write` tool auto-creates parent directories
- **Low risk**: `PreferenceManager.getDefaultSharedPreferences(context)` requires Android `Context` — available via `LocalContext.current`
- **Low risk**: NavHost already imports `OnboardingRoute(onFinish)` — creating this file resolves the existing import error, same pattern as Prompt 1
- **Medium-low risk**: `animateScrollToPage` requires a coroutine scope — use `rememberCoroutineScope()` to launch from click handler

## Verification

1. `OnboardingRoute.kt` exists at `com.sapisehat.app.ui.onboarding.OnboardingRoute`
2. 3 slides defined with emoji (📸📴⚡), title, and body from string resources
3. `HorizontalPager` allows swipe between slides
4. Dots indicator shows active (12dp Primary) and inactive (8dp gray) states, updates on page change
5. Skip button ("Lewati") in top-right navigates to Main via `onFinish()`
6. CTA button shows "Lanjut" on slides 1-2 and "Mulai" on slide 3
7. "Mulai" click writes `has_completed_onboarding = true` to SharedPreferences and calls `onFinish()`
8. "Lanjut" click animates to next page via `animateScrollToPage(currentPage + 1)`
9. Slide content: emoji (72sp), title (headlineMedium bold, centered), body (bodyLarge secondary, centered)
