> **Legacy mobile note:** This spec describes the earlier image-first Android app. Current farmer mobile app must align with platform contracts in [system integration mobile](README.md). Shared platform contracts path: `docs/system-integration/mobile/README.md`.


# SapiSehat Mobile — Full Version Spec

**Status:** Draft
**Created:** 2026-05-05
**Module(s)/Domain(s):** apps/mobile

## Summary

Full version aplikasi Android SapiSehat dari MVP (1 screen skeleton) menjadi 8 screen: Splash, Onboarding, Camera, Result, History, Guide, About, Settings. Aplikasi deteksi penyakit sapi (PMK & LSD) via CNN MobileNetV2 — online-first dengan offline fallback. Target pengguna: peternak sapi (muda & tua), dosen penguji, dan orang tua — sehingga UX harus sederhana, aksesibel, dan bilingual (ID/EN).

## Constraints & Boundaries

- **In scope:** 8 screen, iOS-style tab bar navigation, warm earth-tone "Tropis Bersih" design system, full aksesibilitas (TalkBack, scalable text, color-blind safe, WCAG AA), bilingual (ID + EN)
- **Out of scope:** Dark mode (deferred), fitur sosial (share ke media sosial — hanya tombol placeholder), push notification, backend changes
- **Dependencies:** Backend FastAPI running at configurable URL, TFLite model (`cattle_disease.tflite`) in assets, Room database schema (existing)

---

## Design System — "Tropis Bersih"

### Color Palette

| Role | Name | Hex | Usage |
|---|---|---|---|
| Primary | Hijau sage | `#7DA97C` | Primary buttons, active tab icons, headers |
| Secondary | Krem gading | `#F5F0E8` | Card surfaces, secondary backgrounds |
| Accent | Oren hangat | `#E8985E` | Badges, highlights, warning indicators, FAB |
| Background | Putih susu | `#FFFAF5` | Main screen background |
| Text Primary | Cokelat tua | `#4A3728` | Headlines, body text |
| Text Secondary | Abu hangat | `#9B8E7F` | Captions, inactive icons, hints |

**Semantic Colors (for disease results):**
| Label | Color | Hex |
|---|---|---|
| SEHAT | Hijau sukses | `#5B9A5B` |
| PMK | Merah peringatan | `#D4745C` |
| LATO_LATO | Oren peringatan | `#E8985E` |

### Typography

- Font: System default (Roboto on Android — clean, modern, readable)
- Scale: Follow system font scale (dynamic type support, up to 200%)
- Base size: 16sp body, 14sp caption, 20sp title, 28sp headline

### Shape & Elevation

- Default corner radius: 16dp (cards, buttons, dialogs)
- Chip/pill radius: 24dp (fully rounded)
- Elevation: 2dp default, 4dp for cards, 8dp for FAB
- Surface: flat with subtle `elevation` — no heavy shadows

### Iconography

- Style: SF Symbols / Material Symbols rounded (iOS-like, clean lines)
- Size: 24dp for tab bar, 20dp for inline, 48dp for empty states
- ALL icons must have labels (text below or contentDescription)

---

## Navigation Structure

### iOS-Style Bottom Tab Bar (4 tabs)

```
┌──────────┬──────────┬──────────┬──────────┐
│  🐄      │  📋      │  📖      │  👤      │
│ Periksa  │ Riwayat  │ Panduan  │ Lainnya  │
└──────────┴──────────┴──────────┴──────────┘
```

| Tab | Label | Icon | Target Screen |
|---|---|---|---|
| 1 | Periksa | stetoskop/kamera | Camera → Result |
| 2 | Riwayat | jam/clock | History → Result (detail) |
| 3 | Panduan | buku/book | Guide (tab switcher) |
| 4 | Lainnya | orang/user | About + Settings |

### Screen Flow

```
App Launch
    │
    ▼
Splash (2s, check first launch)
    │
    ├── first launch ──▶ Onboarding (3 slides)
    │                        │
    └── returning ──────────┐│
                            ▼▼
                      Tab Bar (4 tabs)
                      ┌── Periksa ──▶ Camera ──▶ Result
                      │               (capture)   (detail)
                      │
                      ├── Riwayat ──▶ History ──▶ Result (detail)
                      │
                      ├── Panduan ──▶ Guide
                      │
                      └── Lainnya ──▶ About + Settings
```

---

## Screen Specifications

### 1. Splash Screen

**Purpose:** Branding saat startup, loading TFLite model

| Aspect | Detail |
|---|---|
| Layout | Centered app logo placeholder + app name "SapiSehat" + loading indicator |
| Background | Primary hijau sage `#7DA97C` |
| Duration | 2 seconds (or until TFLite model loaded, whichever longer) |
| Behavior | After timeout → check SharedPreferences for `has_completed_onboarding` |
| First launch | → Onboarding |
| Returning user | → Main tab bar |

**States:**
- Loading: Circular progress indicator below logo
- Error (model load failure): "Gagal memuat model. Periksa instalasi aplikasi." with retry button

---

### 2. Onboarding Screen

**Purpose:** Perkenalan aplikasi untuk pengguna pertama kali

| Aspect | Detail |
|---|---|
| Slides | 3 horizontal swipeable pages |
| Navigation | Swipe left/right, dot indicators, "Lewati" button (top-right), "Lanjut" button (bottom) |
| Last slide | "Mulai" CTA button → saves `has_completed_onboarding=true` → navigates to main tab bar |

**Slide Contents (ID + EN toggle based on system locale):**

| Slide | Illustration | Title | Body |
|---|---|---|---|
| 1 | Ilustrasi sapi + kamera | "Foto Sapi, Dapatkan Diagnosis" / "Photo Your Cattle, Get Diagnosis" | "Ambil foto sapi dari jarak dekat. Aplikasi akan menganalisis kondisi kesehatannya secara instan." / "Take a close-up photo. The app will instantly analyze its health condition." |
| 2 | Ilustrasi offline/cloud | "Bekerja Tanpa Internet" / "Works Without Internet" | "Aplikasi tetap bisa digunakan di daerah tanpa sinyal. Hasil diagnosis tetap akurat dengan model offline." / "The app works even without signal. Offline diagnosis remains accurate." |
| 3 | Ilustrasi hasil + centang | "Hasil Cepat & Andal" / "Fast & Reliable Results" | "Dapatkan hasil dalam hitungan detik. Deteksi PMK dan LSD dengan teknologi AI terkini." / "Get results in seconds. Detect FMD and LSD with state-of-the-art AI technology." |

**States:**
- Active dot: Primary hijau sage, size 12dp
- Inactive dot: Abu hangat, size 8dp
- Skip button: Text "Lewati" / "Skip", style text button, top-right
- Last slide CTA: Filled primary button "Mulai" / "Get Started"

**Accessibility:**
- All illustrations have contentDescription
- Swipe gestures work with TalkBack
- Skip button clearly labeled

---

### 3. Camera Screen (Tab: Periksa)

**Purpose:** Tangkap atau pilih gambar sapi untuk dianalisis

| Aspect | Detail |
|---|---|
| Layout | Full-screen CameraX preview + overlay UI |
| Capture | Bottom-center circular shutter button (72dp, white border, primary fill) |
| Gallery | Bottom-left thumbnail button (opens system photo picker) |
| Flash | Top-right icon toggle (auto/on/off) |
| Grid | 3×3 overlay grid lines (subtle white, 20% opacity) |
| Guidance | Top-center label: "Arahkan kamera ke sapi" / "Point camera at the cattle" (auto-hide after 5s, reappear on tap) |

**Behavior:**
- CameraX lifecycle-aware, start preview on screen visible
- Capture → Tahap 1 preprocessing (EXIF, resize 800px, compress JPEG 85%, strip metadata)
- Then → navigate to Result screen with JPEG bytes
- Gallery pick → same Tahap 1 preprocessing → Result

**States:**

| State | UI |
|---|---|
| Camera ready | Live preview + full overlay |
| Permission not granted | Dark overlay + illustration + "Izinkan Kamera" / "Allow Camera" button → opens app settings |
| Permission denied permanently | Same as above but text: "Kamera tidak diizinkan. Buka Pengaturan untuk mengaktifkan." / "Camera permission denied. Open Settings to enable." + "Buka Pengaturan" / "Open Settings" button |
| Flash modes | Icon cycles: `⚡Auto` → `⚡On` → `⚡Off` |
| Grid toggle | Grid visible/hidden via tap on grid icon or long-press |

**Accessibility:**
- Shutter button: contentDescription "Ambil foto sapi untuk diperiksa" / "Take photo of cattle for examination"
- Gallery button: "Pilih foto dari galeri" / "Choose photo from gallery"
- Flash button: "Flash: Otomatis" / "Flash: Auto" (updates with mode)
- Guidance label: Live region for TalkBack

---

### 4. Result Screen

**Purpose:** Tampilkan hasil diagnosis (mengacu PRD section 7)

| Aspect | Detail |
|---|---|
| Layout | Scrollable vertical layout |
| Arrives from | Camera (after capture) OR History (tap item) |

**Content (top to bottom):**

```
┌─────────────────────────────────────┐
│  [Foto yang dianalisis]             │  ← 200dp height, rounded 16dp
│                                     │
│  🌐 Analisis Online                 │  ← badge mode (chip)
│  ─────────────────────────────────  │
│  🔴 PMK TERDETEKSI                  │  ← headline 28sp, semantic color
│  Keyakinan: 94.3%                   │  ← 16sp, text secondary
│  [████████████░░] 94.3%             │  ← segmented progress bar
│                                     │
│  Sehat       ░░░░  3.1%             │  ← class score rows
│  PMK         ████ 94.3%             │
│  Lato-Lato   ░░░░  2.6%             │
│                                     │
│  ⚠️ Saran Penanganan:               │  ← info card, accent background
│  1. Isolasi sapi segera             │
│  2. Hubungi dokter hewan            │
│  3. Lapor ke Dinas Peternakan       │
│                                     │
│  [💾 Simpan] [📤 Bagikan] [🔄 Ulangi]│  ← action buttons row
└─────────────────────────────────────┘
```

**Inference Mode Badge:**

| Mode | Icon + Label | Color |
|---|---|---|
| Online sukses | 🌐 Analisis Online / Online Analysis | Hijau |
| Offline (no internet) | 📴 Analisis Offline / Offline Analysis | Oren |
| Offline fallback | ⚠️ Offline (Server tidak merespons) / Offline (Server Unreachable) | Oren |

**Confidence Threshold Display:**

| Range | Behavior |
|---|---|
| ≥ 80% | Normal display, semantic color |
| 60-79% | Yellow/warning tint + text "Keyakinan sedang, pertimbangkan foto ulang" |
| < 60% | Red/error tint + text "Foto kurang jelas, silakan coba lagi" + auto-show retake prompt |

**Saran Penanganan (per class):**

| Class | Saran (ID) | Saran (EN) |
|---|---|---|
| SEHAT | "Sapi dalam kondisi sehat. Lanjutkan pemantauan rutin." | "Cattle is healthy. Continue routine monitoring." |
| PMK | 1. Isolasi sapi segera ⚠️ 2. Hubungi dokter hewan 3. Lapor ke Dinas Peternakan | 1. Isolate cattle immediately ⚠️ 2. Contact veterinarian 3. Report to Livestock Office |
| LATO_LATO | 1. Pisahkan dari ternak lain ⚠️ 2. Hubungi dokter hewan 3. Periksa ternak lain untuk gejala serupa | 1. Separate from other livestock ⚠️ 2. Contact veterinarian 3. Check other cattle for similar symptoms |

**Action Buttons:**
- Simpan / Save → save to Room DB, show snackbar "Tersimpan" / "Saved"
- Bagikan / Share → share intent (image + text summary) — placeholder, opens system share sheet
- Ulangi / Retake → navigate back to Camera

**States:**

| State | UI |
|---|---|
| Loading (online mode) | Progress bar + text log: "Menghubungi server..." → "Menganalisis gambar..." → "Menerima hasil..." |
| Server timeout (10s) | Auto-fallback to TFLite, show badge "⚠️ Offline (Server tidak merespons)", continue with offline result |
| Server error (5xx) | Same as timeout — auto-fallback |
| Offline mode | Direct TFLite, show badge "📴 Analisis Offline", faster loading |
| Invalid image | Error dialog: "Gambar tidak dapat diproses. Silakan ambil ulang foto sapi." / "Image cannot be processed. Please retake the photo." + "Ambil Ulang" / "Retake" button |
| Network error (no connectivity) | Direct to offline mode (no loading flicker) |

**Accessibility:**
- All scores also shown as text numbers (not just bars)
- Confidence bar has pattern fill for color-blind users
- Semantic colors paired with icons (🟢🔴🟠)
- Saran section clearly labeled as "warning" / "info" for screen readers

---

### 5. History Screen (Tab: Riwayat)

**Purpose:** Daftar riwayat deteksi tersimpan

| Aspect | Detail |
|---|---|
| Layout | LazyColumn / RecyclerView with card items |
| Sort | Newest first (by timestamp descending) |

**Card Item Layout:**
```
┌─────────────────────────────────────────┐
│ ┌──────┐  🔴 PMK                         │
│ │      │  94.3% keyakinan                │
│ │thumb │  🌐 Online  12 Mei 2026, 14:30  │
│ └──────┘                          [🗑️]  │
└─────────────────────────────────────────┘
```
- Thumbnail: 56dp × 56dp, rounded 8dp
- Label: semantic color + icon
- Confidence: small text
- Badge mode: small chip
- Timestamp: formatted relative ("2 jam lalu" / "2 hours ago") + absolute
- Delete icon button: top-right (24dp)

**Filter:**

| Aspect | Detail |
|---|---|
| UI | Horizontal chip row below top bar (scrollable) |
| Options | Semua / All | Sehat / Healthy | PMK | Lato-Lato | Online | Offline |
| Default | "Semua" / "All" |
| Behavior | Single-select, animates content change |

**Swipe to delete:**
- Swipe left → red background + trash icon
- Confirmation dialog: "Hapus riwayat ini?" / "Delete this record?"

**Tap to detail:**
- Tap card → navigate to Result screen with saved DetectionResult data (no re-inference)

**States:**

| State | UI |
|---|---|
| Empty (no records) | Centered illustration (sapi sehat + clipboard) + "Belum ada pemeriksaan" / "No examinations yet" + "Mulai Periksa" / "Start Examination" CTA button → tab 1 |
| Filtered empty | "Tidak ada hasil dengan filter ini" / "No results for this filter" + "Hapus Filter" / "Clear Filter" button |
| Loading (querying DB) | Shimmer/skeleton cards (3 placeholder) |
| Database error | Error card: "Gagal memuat riwayat. Tarik untuk memuat ulang." / "Failed to load history. Pull to refresh." + pull-to-refresh support |

**Bulk actions (optional, low priority):**
- Long press → multi-select mode
- "Hapus Terpilih" / "Delete Selected" action bar

**Accessibility:**
- Delete button clearly labeled
- Swipe-to-delete works with TalkBack custom actions
- Filter chips have clear content descriptions

---

### 6. Guide Screen (Tab: Panduan)

**Purpose:** Informasi cara memotret dan penyakit sapi

| Aspect | Detail |
|---|---|
| Layout | 3-tab switcher (like Material TabRow / blog categories) |
| Tabs | 📷 Cara Memotret / How to Photo | 🦠 PMK | 🐄 LSD (Lato-Lato) |
| Default | Cara Memotret |

**Tab 1 — Cara Memotret / How to Photo:**
Scrollable page with sections:
1. **Jarak Ideal / Ideal Distance** — ilustrasi sapi + jarak 1-2 meter, hindari terlalu jauh
2. **Pencahayaan / Lighting** — outdoor terbaik, hindari backlight, jangan pakai flash di malam hari
3. **Posisi Sapi / Cattle Position** — tampak samping (side view) ideal, bisa juga depan (front view)
4. **Hindari / Avoid** — blur, terhalang objek lain, foto terlalu gelap/terang

**Tab 2 — PMK (Penyakit Mulut dan Kuku) / FMD:**
Scrollable page:
1. **Gejala Visual / Visual Symptoms** — luka/lepuh di mulut, lidah, gusi, dan kuku; air liur berlebihan; pincang
2. **Penularan / Transmission** — kontak langsung, udara, peralatan terkontaminasi
3. **Penanganan Awal / Initial Treatment** — isolasi, hubungi dokter hewan, desinfeksi kandang
4. **Kontak Dinas / Livestock Office Contact** — call-to-action dengan nomor telepon dinas (placeholder)

**Tab 3 — LSD (Lumpy Skin Disease) / Lato-Lato:**
Scrollable page:
1. **Gejala Visual / Visual Symptoms** — benjolan/nodul di kulit (2-5cm), demam, lesu, penurunan produksi susu
2. **Penularan / Transmission** — gigitan serangga (nyamuk, lalat, caplak), kontak langsung
3. **Penanganan Awal / Initial Treatment** — isolasi, hubungi dokter hewan, vaksinasi ternak sehat
4. **Kontak Dinas / Livestock Office Contact** — call-to-action (placeholder)

**States:**

| State | UI |
|---|---|
| Loading images | Skeleton placeholder for illustrations |
| Image load failed | Fallback icon placeholder + alt text visible |
| Tab switch | Crossfade or slide animation |

**Accessibility:**
- Tab content is landmark regions
- Images all have descriptive contentDescription
- Disease symptoms use list format (ordered) for screen readers
- Contact numbers are clickable tel: links

---

### 7. About Screen (Tab: Lainnya → About)

**Purpose:** Informasi aplikasi, tim, dan credit

| Aspect | Detail |
|---|---|
| Layout | Scrollable card-based |

**Content:**
- **App Logo + Nama** — SapiSehat (placeholder logo)
- **Versi** — 1.0.0
- **Deskripsi Singkat** — "Aplikasi deteksi penyakit sapi berbasis AI" / "AI-based cattle disease detection app"
- **Tim Pengembang / Development Team:**
  - Raditya Rafif Pratama Sasmita
  - Noval Putra Ramadhan
- **Institusi** — Teknik Informatika, Politeknik Negeri Semarang
- **Dosen Pembimbing** — (placeholder — tanyakan user)
- **Sumber Dataset / Dataset Sources:**
  - Kaggle — Lumpy Skin Disease dataset
  - Roboflow Universe — FMD cattle dataset
  - Data lapangan peternakan lokal
- **Teknologi / Technology:**
  - MobileNetV2 (CNN)
  - TensorFlow Lite
  - FastAPI + Python
- **Copyright** — © 2026 SapiSehat Team
- **Link ke Repository** — (placeholder GitHub URL)

**States:** Static content, no loading state needed.

---

### 8. Settings Screen (Tab: Lainnya → Settings)

**Purpose:** Konfigurasi aplikasi

| Aspect | Detail |
|---|---|
| Layout | Preference-style list |

**Settings Items:**

| Item | Type | Detail |
|---|---|---|
| Bahasa / Language | Dropdown/selector | Indonesia / English (default: system locale) |
| Ukuran Teks / Text Size | Slider or follow system | "Ikuti Sistem" / "Follow System" toggle (default: ON), or 3 preset sizes |
| Server URL | EditText preference | Default: `http://10.0.2.2:8000` (emulator localhost). Dialog edit dengan validasi URL |
| Hapus Semua Riwayat / Clear All History | Button (destructive) | Red text, confirmation dialog: "Semua riwayat pemeriksaan akan dihapus. Tindakan ini tidak dapat dibatalkan." / "All examination history will be deleted. This cannot be undone." + "Hapus" / "Delete" + "Batal" / "Cancel" |
| Reset Onboarding / Reset Onboarding | Button | Reset `has_completed_onboarding` flag. Next launch will show onboarding again |
| Versi Aplikasi / App Version | Info text (read-only) | "1.0.0" |
| Versi Model / Model Version | Info text (read-only) | "1.0.0" |

**States:**
- Clear history: show confirmation dialog → snackbar "Riwayat dihapus" / "History cleared"
- Language change: show restart prompt "Ubah bahasa? Aplikasi akan dimuat ulang." / "Change language? App will restart."

**Accessibility:**
- Destructive action clearly labeled as "Hapus" with warning role
- All preferences have clear labels

---

## Data Model (Existing — from PRD)

### Room: `detection_records`

```sql
CREATE TABLE detection_records (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp        INTEGER NOT NULL,
    image_path       TEXT NOT NULL,
    predicted_class  TEXT NOT NULL,     -- 'SEHAT' | 'PMK' | 'LATO_LATO'
    confidence       REAL NOT NULL,
    score_sehat      REAL NOT NULL,
    score_pmk        REAL NOT NULL,
    score_lato_lato  REAL NOT NULL,
    inference_mode   TEXT NOT NULL,     -- 'ONLINE' | 'OFFLINE' | 'OFFLINE_FALLBACK'
    is_reliable      INTEGER NOT NULL,
    processing_ms    INTEGER,
    notes            TEXT
);
```

**No new tables needed for full version.**

### SharedPreferences Keys

| Key | Type | Default | Description |
|---|---|---|---|
| `has_completed_onboarding` | Boolean | false | First launch flag |
| `app_language` | String | "system" | "id", "en", or "system" |
| `server_url` | String | "http://10.0.2.2:8000" | Backend endpoint |
| `text_size_mode` | String | "system" | "system", "small", "medium", "large" |

---

## Business Logic

### Inference Flow

```
1. User captures/selects image
2. ClientPreprocessor (Tahap 1): EXIF correction → resize max 800px → JPEG compress 85% → strip metadata
3. InferenceRouter decides:
   ┌─ Online (has internet)
   │   ├─ Upload JPEG bytes to server → Tahap 2 done server-side
   │   ├─ Success → return Result with ONLINE badge
   │   └─ Timeout/Error (10s) → fallback to Offline → return Result with OFFLINE_FALLBACK badge
   └─ Offline (no internet)
       └─ ModelPreprocessor (Tahap 2) → TFLite inference → return Result with OFFLINE badge
4. Display Result
5. User optional: Save to Room DB
```

### Validation Rules
- Image must be JPEG, PNG, or WebP
- Image must not be empty/corrupt
- Server URL must be valid HTTP/HTTPS URL

### Confidence Rules
- ≥ 80%: Normal display
- 60-79%: Warning + "Keyakinan sedang" message
- < 60%: Error + "Foto kurang jelas" + auto retake prompt

---

## Error Handling

| Error Case | User Sees | Log Level |
|---|---|---|
| Camera permission denied | Overlay with "Buka Pengaturan" button | warn |
| Image decode failure | Dialog: "Gambar tidak dapat diproses" + retake | error |
| Server timeout (10s) | Auto-fallback to offline, badge shows "Offline (Server tidak merespons)" | warn |
| Server 5xx | Same as timeout — auto-fallback | error |
| Server 422 (invalid image) | Dialog: "Format gambar tidak didukung" | warn |
| Server 503 (model not ready) | Auto-fallback to offline | error |
| No internet | Direct offline mode (no loading flicker) | info |
| TFLite model missing/corrupt | Splash screen error: "Gagal memuat model. Periksa instalasi." | error |
| Room DB write failure | Snackbar: "Gagal menyimpan. Coba lagi." | error |
| Room DB read failure | Pull-to-refresh + "Gagal memuat. Tarik untuk memuat ulang." | error |

---

## Security

- **Roles:** No authentication required (offline-first app)
- **Sensitive data:** Image files stored in app-private internal storage (not external)
- **Server URL:** Stored in SharedPreferences, validated before use
- **No PII collected** except images (user-initiated)
- EXIF metadata stripped in Tahap 1 preprocessing (GPS, device info removed)

---

## Performance

| Metric | Target |
|---|---|
| App cold start | < 2s (including TFLite load) |
| Camera preview start | < 500ms |
| TFLite inference | < 1s |
| Online inference (4G) | < 3s end-to-end |
| APK size | < 20 MB |
| Memory usage | < 150 MB peak |
| Crash rate | < 1% sessions |

---

## Accessibility Checklist

- [ ] All images have contentDescription
- [ ] All icon buttons have contentDescription
- [ ] Touch targets ≥ 48dp
- [ ] WCAG AA contrast (4.5:1 for normal text, 3:1 for large text)
- [ ] Color not the sole differentiator (icons + patterns + labels)
- [ ] Dynamic text scaling (system font scale)
- [ ] TalkBack navigation order matches visual layout
- [ ] Swipe gestures work with TalkBack
- [ ] Live regions for dynamic content (result loading, camera guidance)
- [ ] Bilingual: Indonesian + English (toggle via Settings)
- [ ] All strings externalized in `strings.xml` + `strings-en.xml`

---

## Tech Stack

- **Language:** Kotlin
- **UI:** Jetpack Compose (Material 3)
- **Navigation:** Compose Navigation + Bottom Navigation Bar
- **DI:** Hilt
- **Database:** Room
- **Network:** Retrofit + OkHttp
- **Camera:** CameraX
- **Image Loading:** Coil (thumbnails in History)
- **TFLite:** TensorFlow Lite Android
- **Architecture:** MVVM (ViewModel + StateFlow)
- **Min SDK:** API 24 (Android 7.0)
- **Target SDK:** API 34 (Android 14)

---

## Testing Plan

- **Unit tests:** ViewModels, UseCases, ClientPreprocessor, ModelPreprocessor, InferenceRouter
- **Integration tests:** Room DAO queries, Retrofit API calls, TFLite inference
- **UI tests:** Compose testing for each screen's states (loading, empty, error, success)
- **Accessibility tests:** TalkBack walkthrough, contrast check, touch target check
- **Existing test framework:** JUnit + Compose Test + Hilt Testing

---

## Open Questions

- Dosen Pembimbing name — needed for About screen
- GitHub repository URL — needed for About screen
- Logo design — placeholder needed, final TBD
- Disease handling advice text — review by veterinarian for accuracy
- Contact numbers for Livestock Office — placeholder or real data?

---

## Changelog

| Date | Version | Changes |
|---|---|---|
| 2026-05-05 | 0.1.0 | Initial draft from grill-me session |

---

*Spec ini adalah destination document untuk AI consumption — prioritaskan kelengkapan dan presisi. Semua keputusan diambil dari sesi grill-me Raditya, 5 Mei 2026.*
