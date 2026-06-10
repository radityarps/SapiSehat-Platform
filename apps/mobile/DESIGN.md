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
- Safety phrase: `Risk signal, not diagnosis` visible in app shell.

## Layout
- Android-first single-column flow.
- Bottom navigation: `Sapi`, `Scan`, `Riwayat`.
- Cards use rounded corners, low/no elevation, soft border.
- Primary CTA on scan screen has strong leaf panel.

## Core screens
### Login
- Brand: `SapiSehat`.
- Safe-language subtitle.
- Email/password fields.
- Primary `Masuk` CTA.

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

## Accessibility
- Large touch targets.
- High contrast leaf on ivory/white.
- Avoid color-only state; include text labels for sync/status.
