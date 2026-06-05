# Prompt 1: Splash Screen — Implementation Plan

## Context

Prompt 0 (Shared Infrastructure) is complete. Theme, navigation, bilingual strings, and dependencies are all set up. The Splash Screen is the root screen in the navigation graph defined in Prompt 0 — it handles the Splash → Onboarding or Splash → Main transition. This UI component is fully self-contained: no ViewModel or complex dependencies needed.

### Current state of related code

- `SapiSehatNavHost.kt` already imports and calls `SplashRoute(onFinish)` from `com.sapisehat.app.ui.splash.SplashRoute`
- `strings.xml` already defines `splash_loading` and `splash_subtitle`
- `TropisBersihColors.Primary` (#7DA97C) and `OnPrimary` (#FFFFFF) are defined in `Color.kt`
- `SapiSehatTypography.headlineLarge` (28sp Bold) and `bodyMedium` (14sp) are available

## Approach

Create a single new Composable function `SplashRoute` that:

1. Reads `has_completed_onboarding` from `PreferenceManager.getDefaultSharedPreferences`
2. Waits 2000ms via `LaunchedEffect`
3. Calls `onFinish(hasOnboarded)` to navigate to the appropriate screen
4. Renders branding UI (logo placeholder, app name, subtitle, loading indicator)

No existing files are modified. Theme and strings from Prompt 0 are reused.

## Files to Create (1 new)

| #   | File                                                                       | Purpose                          |
| --- | -------------------------------------------------------------------------- | -------------------------------- |
| 1   | `apps/mobile/app/src/main/java/com/sapisehat/app/ui/splash/SplashRoute.kt` | Branding + loading splash screen |

## Files to Modify (none)

No existing files need changes.

## Reuse

- `Color.kt` — `TropisBersihColors.Primary` for background, `OnPrimary` for text and indicator colors
- `Type.kt` — `headlineLarge` (28sp Bold) for "SapiSehat" title, `bodyMedium` (14sp) for loading text
- `strings.xml` — `splash_loading` and `splash_subtitle` string resources
- Navigation — `SplashRoute(onFinish: (Boolean) -> Unit)` signature already matches the NavHost call site; creating this file resolves the existing import error

## Steps

- [x] **1. Create SplashRoute.kt**
  - Package: `com.sapisehat.app.ui.splash`
  - Signature: `@Composable fun SplashRoute(onFinish: (hasOnboarded: Boolean) -> Unit)`
  - Read `has_completed_onboarding` from `PreferenceManager.getDefaultSharedPreferences` (default `false`)
  - `LaunchedEffect(Unit)`: 2000ms delay → `onFinish(hasOnboarded)`
  - UI layout:
    - `Box(fillMaxSize, background = TropisBersihColors.Primary)`
    - `Column(center)`:
      - Logo placeholder: `Surface(100.dp, CircleShape)` with `Text("🐄", 48.sp)`
      - `Text("SapiSehat", style = headlineLarge, fontWeight = Bold, color = OnPrimary)`
      - `Spacer(16.dp)`
      - `Text(splash_subtitle, style = bodyLarge, color = OnPrimary.copy(alpha = 0.8f))`
      - `Spacer(32.dp)`
      - `CircularProgressIndicator(color = OnPrimary.copy(alpha = 0.8f))`
      - `Spacer(16.dp)`
      - `Text(splash_loading, style = bodyMedium, color = OnPrimary.copy(alpha = 0.7f))`
  - Optional: `AnimatedVisibility` fade-in for the entire column
  - Include a `@Preview` composable for design-time preview

## Trade-offs & Assumptions

| Item                         | Decision | Rationale                                                                     |
| ---------------------------- | -------- | ----------------------------------------------------------------------------- |
| No ViewModel                 | Accepted | Simple one-shot UI with no state management needed                            |
| 2000ms fixed delay           | Accepted | Placeholder until TFLite model loading is integrated in a later prompt        |
| `PreferenceManager` directly | Accepted | Minimal dependency; will migrate to DataStore in Prompt 8                     |
| Emoji logo placeholder       | Accepted | Replaceable with real image assets later with zero code changes               |
| Fade-in animation            | Optional | Low implementation cost, improves UX; `AnimatedVisibility` is straightforward |
| Works offline                | Assumed  | No network access required — always displayable                               |

## Risks

- **Low risk**: Directory `ui/splash/` does not exist yet — the `write` tool auto-creates parent directories
- **Low risk**: `PreferenceManager` requires an Android `Context` — available via `LocalContext.current` in Compose
- **Compile fix**: Creating this file resolves the existing `SplashRoute` import error in `SapiSehatNavHost.kt`

## Verification

1. `SplashRoute.kt` exists at `com.sapisehat.app.ui.splash.SplashRoute`
2. Signature matches `SplashRoute(onFinish: (Boolean) -> Unit)` — compatible with NavHost call site
3. Background is Primary sage green (#7DA97C)
4. `CircularProgressIndicator` and `splash_loading` text are visible
5. `has_completed_onboarding` is read from SharedPreferences with default `false`
6. `onFinish` is called after a 2-second delay
