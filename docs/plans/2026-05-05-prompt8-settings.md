# Prompt 8: Settings Screen — Implementation Plan

## Context

Prompts 0–7 are complete. Prompt 8 adds a full Settings screen with DataStore-backed preferences, Hilt DI, and a ViewModel + UI combo in a single file.

## Files Created / Modified

| #   | File                              | Action | Purpose                                |
| --- | --------------------------------- | ------ | -------------------------------------- |
| 1   | `data/local/SettingsDataStore.kt` | Create | DataStore preferences wrapper          |
| 2   | `di/AppModule.kt`                 | Edit   | Add `provideSettingsDataStore` binding |
| 3   | `ui/settings/SettingsRoute.kt`    | Create | ViewModel + full settings UI           |

## Steps

- [x] **1. Create `SettingsDataStore.kt`** — DataStore with language/textSize/serverUrl keys
- [x] **2. Add `@Provides @Singleton` method to `AppModule.kt`**
- [x] **3. Create `SettingsRoute.kt`** — ViewModel + preference list UI with dialogs and snackbar

## Verification

1. ✅ DataStore keys: `KEY_LANGUAGE`, `KEY_TEXT_SIZE`, `KEY_SERVER_URL`
2. ✅ Flow properties: `language`, `textSize`, `serverUrl`
3. ✅ Suspend setters: `setLanguage`, `setTextSize`, `setServerUrl`
4. ✅ AppModule provides `SettingsDataStore` as singleton
5. ✅ ViewModel observes DataStore flows as StateFlow
6. ✅ Language dialog with radio buttons (System / Indonesia / English)
7. ✅ Text size dialog with radio buttons (System / Small / Medium / Large)
8. ✅ Server URL dialog with OutlinedTextField + OK/Cancel
9. ✅ Clear all history with red text + confirmation dialog + snackbar
10. ✅ Reset onboarding with confirmation dialog + snackbar
11. ✅ App version (BuildConfig.VERSION_NAME) and Model version (1.0.0) shown as read-only
12. ✅ Top bar with "Pengaturan" title + back button
13. ✅ SettingsRoute(onBack) signature matches NavHost
