# Prompt 0: Shared Infrastructure — Implementation Plan

## Context

The SapiSehat Android app currently has only MVP-level scaffolding:

- Empty `Theme.kt` (placeholder lightColorScheme/darkColorScheme)
- Empty `Type.kt` (placeholder Typography())
- Basic `SapiSehatNavHost.kt` (3 routes: Camera, Result, History only)
- Minimal `strings.xml` (just `app_name`)
- No `values-en/strings.xml`
- No Coil, DataStore, or material-icons-extended dependencies
- Only INTERNET + CAMERA permissions

This plan implements **Prompt 0: Shared Infrastructure** from the [mobile full version plan](./2026-05-05-mobile-full-version.md), establishing the design system, navigation structure, bilingual strings, and dependencies needed by all subsequent screens (Prompts 1–8).

## Approach

All changes are additive or rewrites that other screens (Prompts 1–8) will build upon. No existing behavior is broken — the current MVP screens will be replaced in later prompts.

### Files to Create (4 new files)

| #   | File                                                                | Purpose                                           |
| --- | ------------------------------------------------------------------- | ------------------------------------------------- |
| 1   | `apps/mobile/app/src/main/java/com/sapisehat/app/ui/theme/Color.kt` | TropisBersih design tokens + `lightColorScheme()` |
| 2   | `apps/mobile/app/src/main/res/values-en/strings.xml`                | English translations for all string IDs           |

### Files to Rewrite (4 existing files)

| #   | File                                                                                | What Changes                                                                                  |
| --- | ----------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| 3   | `apps/mobile/app/src/main/java/com/sapisehat/app/ui/theme/Type.kt`                  | Replace empty `Typography()` with custom font scales                                          |
| 4   | `apps/mobile/app/src/main/java/com/sapisehat/app/ui/theme/Theme.kt`                 | Wire TropisBersih colors, shapes, typography; add `textSecondary` extension                   |
| 5   | `apps/mobile/app/src/main/java/com/sapisehat/app/ui/navigation/SapiSehatNavHost.kt` | Full rewrite: 6 routes (Splash, Onboarding, Main, Result, About, Settings) + 4-tab bottom bar |
| 6   | `apps/mobile/app/src/main/res/values/strings.xml`                                   | Expand from 1 string to ~100 bilingual-ready string IDs                                       |

### Files to Modify (2 existing files)

| #   | File                                           | What Changes                                                           |
| --- | ---------------------------------------------- | ---------------------------------------------------------------------- |
| 7   | `apps/mobile/app/build.gradle.kts`             | Add `coil-compose`, `datastore-preferences`, `material-icons-extended` |
| 8   | `apps/mobile/app/src/main/AndroidManifest.xml` | Add `READ_EXTERNAL_STORAGE`, `ACCESS_NETWORK_STATE` permissions        |

## Reuse

- `apps/mobile/app/src/main/java/com/sapisehat/app/di/AppModule.kt` — already provides `ConnectivityManager`; will be extended in Prompt 8 for `SettingsDataStore`
- `apps/mobile/app/src/main/java/com/sapisehat/app/MainActivity.kt` — wraps `SapiSehatTheme` and `SapiSehatNavHost`; no changes needed yet
- `apps/mobile/app/build.gradle.kts` — already has Compose BOM 2024.09.00, Hilt, Room, Retrofit, TFLite, CameraX

## Steps

- [x] **1. Create Color.kt** — `TropisBersihColors` object with all colors per spec (#7DA97C primary, #F5F0E8 secondary, #E8985E accent, #FFFAF5 background, etc.) + `TropisBersihLightColorScheme` via `lightColorScheme()`
- [x] **2. Rewrite Type.kt** — Custom `Typography` with headlineLarge (28sp Bold), headlineMedium (22sp SemiBold), titleLarge (20sp Medium), bodyLarge (16sp), bodyMedium (14sp), labelMedium (12sp Medium)
- [x] **3. Rewrite Theme.kt** — `SapiSehatTheme` using `TropisBersihLightColorScheme`, `SapiSehatTypography`, shapes (8/12/16/24/32dp), `ColorScheme.textSecondary` extension
- [x] **4. Rewrite SapiSehatNavHost.kt** — `Routes` object with Splash/Onboarding/Main/Camera/Result/History/Guide/About/Settings + `TabItem` data class + 4-tab `NavigationBar` + `MainTabScreen` inner NavHost
- [x] **5. Rewrite strings.xml** — ~100 string IDs: tabs, splash, onboarding (3 slides), camera (guidance/capture/gallery/flash/grid/permission), result (loading/diagnosis/confidence/mode/buttons/disease/advice), history (title/empty/filter/delete), guide (3 tabs × 3-4 sections), about (team/tech/source), settings (language/text/server/clear/reset)
- [x] **6. Create values-en/strings.xml** — All strings translated to English with identical structure
- [x] **7. Edit build.gradle.kts** — Add `coil-compose:2.6.0`, `datastore-preferences:1.0.0`, `material-icons-extended` (via BOM)
- [x] **8. Edit AndroidManifest.xml** — Add `READ_EXTERNAL_STORAGE` and `ACCESS_NETWORK_STATE` permissions

## Verification

1. `Color.kt` compiles — all `Color(0xFFXXXXXX)` values parse correctly
2. `Type.kt` compiles — `SapiSehatTypography` is a valid `Typography` instance
3. `Theme.kt` compiles — `textSecondary` extension resolves from `ColorScheme`
4. `SapiSehatNavHost.kt` compiles — all route references resolve (screen files may not exist yet, but will be created in Prompts 1–8)
5. `strings.xml` is valid XML — no duplicate IDs, all `\n` and `&amp;` properly escaped
6. `values-en/strings.xml` has identical structure to `values/strings.xml`
7. `build.gradle.kts` dependencies resolve — `io.coil-kt:coil-compose`, `androidx.datastore:datastore-preferences`, `material-icons-extended`
8. `AndroidManifest.xml` has all 4 permissions
