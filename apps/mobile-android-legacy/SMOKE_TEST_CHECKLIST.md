> **Legacy mobile note:** This checklist covers the image-first Android flow. Current farmer app must follow platform mobile contracts in `docs/system-integration/mobile/README.md`.

# SapiSehat — Smoke Test Checklist

Manual smoke test flow to verify core functionality before release.

## Prerequisites

- [ ] Device or emulator with Android 8+ (API 26+)
- [ ] Backend server running (or offline mode available)
- [ ] Camera permission grantable

## 1. Fresh Install & Onboarding

- [ ] App installs without crash
- [ ] Splash screen shows loading indicator
- [ ] Onboarding screens display correctly (3 pages)
- [ ] "Skip" and "Next" buttons work
- [ ] "Get Started" navigates to main screen

## 2. Camera & Scan

- [ ] Camera permission dialog appears on first use
- [ ] Camera preview renders after granting permission
- [ ] Flash toggle cycles through Auto/On/Off
- [ ] Grid overlay toggles on/off
- [ ] Capture button takes a photo
- [ ] Gallery picker opens and selects an image
- [ ] Quality gate rejects blurry/dark images with appropriate message

## 3. Result Screen

- [ ] Result displays disease label, confidence %, and level badge
- [ ] Confidence bar renders correctly
- [ ] All class scores shown sorted by value
- [ ] Advice card shows relevant handling advice
- [ ] "Learn More" button navigates to correct guide article
- [ ] Disclaimer text is visible
- [ ] Share button opens share sheet with text + image
- [ ] Save/Edit button opens note dialog
- [ ] Export PDF generates and opens share sheet
- [ ] Retake button returns to camera

## 4. History

- [ ] Saved scan appears in history list
- [ ] Filter by class (Healthy/FMD/LSD) works
- [ ] Filter by mode (Online/Offline) works
- [ ] Tapping a history item opens result detail
- [ ] Swipe-to-delete soft-deletes the record
- [ ] Undo restores the record

## 5. Guide

- [ ] Guide tab shows article list with tabs (App Usage, FMD, LSD, Healthy)
- [ ] Search filters articles by title/summary
- [ ] Tapping an article opens detail view
- [ ] Article content renders correctly (headings, bullets)

## 6. Settings

- [ ] Language switch changes UI language (System/ID/EN)
- [ ] Text size changes apply
- [ ] Server URL can be set and cleared
- [ ] Upload consent toggle works
- [ ] Crash reporting consent toggle works
- [ ] GPS location toggle requests permission
- [ ] Manual location entry saves coordinates
- [ ] "Clear All History" shows confirmation and deletes all
- [ ] "Purge Deleted Records" removes expired soft-deleted records
- [ ] Reset onboarding shows onboarding on next launch
- [ ] App version and model version display correctly

## 7. Offline Mode

- [ ] Disable network (airplane mode)
- [ ] Scan still works using TFLite model
- [ ] Result shows "Offline" mode badge
- [ ] History saves offline results

## 8. Localization

- [ ] Switch to Indonesian: all UI strings in Indonesian
- [ ] Switch to English: all UI strings in English
- [ ] No missing string resources (no "key_name" shown raw)

## 9. Edge Cases

- [ ] Very low confidence (<60%) shows unreliable warning
- [ ] Medium confidence (60-79%) shows medium warning
- [ ] Rotating device doesn't crash
- [ ] Back navigation works from all screens
- [ ] App survives process death (check saved state)

## Sign-off

| Tester | Date | Device | Build | Pass/Fail |
|--------|------|--------|-------|-----------|
|        |      |        |       |           |
