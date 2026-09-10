# SapiSehat Mobile Design System

## Product stance
- Farmer-first Android field app for cattle health risk-signal workflows.
- Copy must say risk signal, review, follow-up, and sync status.
- Copy must not claim diagnosis, confirmed outbreak, or veterinary certainty.

## Visual direction
Calm field operations: deep leaf green, warm ivory surfaces, soil neutrals, clear cards, large tap targets, and restrained status chips.

## Tokens
- Leaf: `#2E6B4F`
- Soft leaf: `#E6F2EA`
- Warm ivory: `#FFFBF1`
- Border: `#E0DED2`
- Muted text: `#5B645B`
- Warning soil: `#9A3412`

## Typography
- Screen headers: bold, large, direct.
- Body text: plain operational copy.
- Safety phrase: `Sinyal risiko, bukan diagnosis` visible on onboarding and login.

## Layout
- Android-first single-column flow.
- Zero-height AppBar (`toolbarHeight: 0`) on main scaffold — status bar safe area only.
- Bottom navigation: `Sapi`, `Scan`, `Riwayat`, `Setelan` (4 tabs).
- Cards use rounded corners, low/no elevation, soft border.
- Primary CTA on scan screen has strong leaf panel.

## Core screens

### Onboarding
- Brand: `SapiSehat` (text only, no icon).
- 3 slides with SVG illustrations.
- Dot page indicator + Lanjut / Mulai pakai SapiSehat CTA.
- Skip button top-right.

### Login / Register
- Toggle between Masuk and Daftar via SegmentedButton.
- Email, password fields with placeholder text.
- Password visibility toggle (eye icon, end of field).
- Register: name, district, address fields + GPS auto-fill button.
- GPS fills address and district via Nominatim reverse geocode.
- Permission dialogs before OS prompt; settings shortcut for denied-forever.
- Input validation: primary CTA disabled until requirements met.
- Terms & privacy checklist required for register.
- In debug mode (`kDebugMode`): fields pre-filled with dev credentials.

### Cattle
- Header: `Kandang Sapi`.
- Tag entry card.
- Cattle cards show tag and status chip.

### Scan
- Header: `Scan Kamera`.
- Primary online scan CTA.
- Secondary offline fallback CTA.
- Results displayed as `Risk signal: {label}` with inference and sync state.

### History
- Header: `Riwayat Deteksi`.
- Shows local pending and remote risk signals.
- Preserves original capture time for local/offline results.

### Settings
- Profile card at top: avatar initial, name, email, address, jurisdiction.
- "Edit profil" button → navigates to `ProfileScreen`.
- Device permission info cards (camera, gallery, location).
- Logout button.
- Account archive with password confirmation.

### Edit Profile (pushed from Settings)
- AppBar with back button.
- Name, email (read-only), district, address fields.
- GPS button fills address + district from Nominatim.
- Save → snackbar confirmation → pop.

## Accessibility
- Large touch targets.
- High contrast leaf on ivory/white.
- Avoid color-only state; include text labels for sync/status.
