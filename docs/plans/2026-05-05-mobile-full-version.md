
# SapiSehat Mobile — Full Version Implementation Plan

> **Untuk Raditya:** Copy prompt per section dan berikan ke Pi via:
> ```
> /home/raditya/.hermes/node/bin/pi -p 'PROMPT_DI_SINI'
> ```
> Kerjakan **berurutan** (Prompt 0 dulu, baru 1, 2, dst). Jangan skip prompt.

**Goal:** Transform MVP 1-screen skeleton menjadi 8-screen full version dengan design system Tropis Bersih, iOS-style tab bar, bilingual, dan full aksesibilitas.

**Spec:** [docs/specs/mobile-full-version-spec.md](../specs/mobile-full-version-spec.md)

**Tech Stack:** Kotlin, Jetpack Compose + Material3, Hilt, Room, CameraX, Retrofit, TFLite

**Execution Order:**
1. Prompt 0 — Shared Infrastructure (theme, navigation, strings, dependencies)
2. Prompt 1 — Splash Screen
3. Prompt 2 — Onboarding Screen
4. Prompt 3 — Camera Screen
5. Prompt 4 — Result Screen
6. Prompt 5 — History Screen
7. Prompt 6 — Guide Screen
8. Prompt 7 — About Screen
9. Prompt 8 — Settings Screen

---

## Prompt 0: Shared Infrastructure

**Tujuan:** Setup design system Tropis Bersih, iOS-style bottom tab navigation, bilingual strings, dan dependency.

### Langkah-langkah (berikan sebagai prompt ke Pi):

```
Project: SapiSehat Android app — full version dari MVP.
Lokasi: apps/mobile/ (Kotlin, Compose, Hilt, Room, CameraX, Retrofit, TFLite)
Package: com.sapisehat.app | Min SDK 24, Target 34, Compose BOM 2024.09.00

TASK: Setup shared infrastructure — theme, navigation, strings, dependencies.

=== 1. THEME — Tropis Bersih Design System ===

CREATE apps/mobile/app/src/main/java/com/sapisehat/app/ui/theme/Color.kt:
- Buat object TropisBersihColors:
  - Primary: #7DA97C (hijau sage), Secondary: #F5F0E8 (krem gading)
  - Accent: #E8985E (oren hangat), Background: #FFFAF5 (putih susu)
  - Surface: #F5F0E8, TextPrimary: #4A3728 (cokelat tua)
  - TextSecondary: #9B8E7F (abu hangat), Success: #5B9A5B
  - Danger: #D4745C, Warning: #E8985E
- Gunakan Color(0xFFXXXXXX)
- Buat fun lightColorScheme() menggunakan warna-warna di atas
- Export semua warna sebagai val properties

MODIFY apps/mobile/app/src/main/java/com/sapisehat/app/ui/theme/Type.kt — ganti isinya:
- Buat Typography dengan:
  - headlineLarge: 28sp Bold
  - headlineMedium: 22sp SemiBold
  - titleLarge: 20sp Medium
  - bodyLarge: 16sp Normal
  - bodyMedium: 14sp Normal
  - labelMedium: 12sp Medium

MODIFY apps/mobile/app/src/main/java/com/sapisehat/app/ui/theme/Theme.kt — ganti isinya:
- Import TropisBersihColors dari Color.kt
- LightScheme pakai TropisBersih color scheme
- Shapes: extraSmall=8dp, small=12dp, medium=16dp, large=24dp, extraLarge=32dp
- Typography pakai yang sudah dibuat di Type.kt
- SapiSehatTheme composable tetap: darkTheme selalu false
- Buat juga val MaterialTheme.colorScheme.textSecondary extension (mapping ke onSurface.copy(alpha=0.6f))

=== 2. NAVIGATION — iOS Bottom Tab Bar ===

REWRITE apps/mobile/app/src/main/java/com/sapisehat/app/ui/navigation/SapiSehatNavHost.kt:
- Hapus semua isi, tulis ulang dengan struktur:

Routes object:
- Splash = "splash", Onboarding = "onboarding", Main = "main"
- Camera = "camera", Result = "result/{label}/{confidence}/{mode}/{allScoresJson}"
- History = "history", Guide = "guide", About = "about", Settings = "settings"
- Helper fun result(label, confidence, mode, scoresJson) -> String

TabItem data class: route, icon (ImageVector), labelId, labelEn

val tabs = listOf(
  TabItem("camera", Icons.Filled.CameraAlt, "Periksa", "Check"),
  TabItem("history", Icons.Filled.History, "Riwayat", "History"),
  TabItem("guide", Icons.Filled.MenuBook, "Panduan", "Guide"),
  TabItem("more", Icons.Filled.Person, "Lainnya", "More")
)

SapiSehatNavHost composable:
- NavHost startDestination=Routes.Splash dengan 5 route:
  1. Splash → SplashRoute(onFinish)
  2. Onboarding → OnboardingRoute(onFinish)
  3. Main → MainTabScreen(rootNavController)
  4. Result → ResultRoute(label, confidence, mode, allScoresJson, onBack, onSave, onRetake)
  5. About → AboutRoute(onBack)
  6. Settings → SettingsRoute(onBack)

MainTabScreen composable:
- Scaffold dengan bottomBar NavigationBar berisi 4 tab dari 'tabs' list
- NavHost inner untuk Camera, History, Guide (tab navigation)
- Tab "more" navigasi ke About via rootNavController
- NavigationBar pakai tonalElevation 2dp, warna surface
- Selected color: primary, unselected: textSecondary

=== 3. BILINGUAL STRINGS ===

REWRITE apps/mobile/app/src/main/res/values/strings.xml — lengkap dengan semua string ID:
- app_name, tab labels, splash strings, onboarding (skip/next/start + 3 slide titles & bodies)
- camera (guidance, capture, gallery, flash modes, permission strings)
- result (loading steps, buttons, confidence labels, mode badges, disease names, advice)
- history (title, empty state, filter chips, delete confirmations)
- guide (title, 3 tab names)
- about (title, desc, team, institution, version)
- settings (title, language, text size, server URL, clear history, reset onboarding, model version)
- shared: btn_cancel, btn_delete, btn_ok

CREATE apps/mobile/app/src/main/res/values-en/strings.xml — semua string dalam English:
- Struktur sama dengan values/strings.xml
- Semua label dan teks diterjemahkan ke English

=== 4. BUILD GRADLE ===

MODIFY apps/mobile/app/build.gradle.kts — tambahkan di dependencies { }:
- implementation("io.coil-kt:coil-compose:2.6.0") — image loading
- implementation("androidx.datastore:datastore-preferences:1.0.0") — settings persistence

=== 5. ANDROID MANIFEST ===

MODIFY apps/mobile/app/src/main/AndroidManifest.xml — tambahkan:
- <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />
- <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />

=== VERIFIKASI ===
- Color.kt: TropisBersih colors + lightColorScheme()
- Type.kt: Typography kustom
- Theme.kt: pakai lightColorScheme kustom, darkTheme=false
- NavHost.kt: bottom tab bar 4 tab, Routes object, Splash/Onboarding/Main/Result/About/Settings
- strings.xml: semua string ID
- values-en/strings.xml: semua string EN
- build.gradle.kts: coil + datastore
- AndroidManifest.xml: READ_EXTERNAL_STORAGE + ACCESS_NETWORK_STATE
```

---

## Prompt 1: Splash Screen

**Tujuan:** Branding + loading TFLite model saat startup.

```
Project: SapiSehat Android app. Prompt 0 sudah selesai.
Package: com.sapisehat.app | Pattern: Compose + Hilt

TASK: Buat SplashScreen yang menampilkan branding dan loading.

CREATE apps/mobile/app/src/main/java/com/sapisehat/app/ui/splash/SplashRoute.kt:

SplashRoute composable menerima onFinish: (hasOnboarded: Boolean) -> Unit:
- Gunakan PreferenceManager.getDefaultSharedPreferences untuk cek "has_completed_onboarding"
- LaunchedEffect: delay 2000ms, lalu panggil onFinish(hasOnboarded)
- UI: Box fillMaxSize, background primary color
  - Column center: logo placeholder (Surface 100dp, emoji 🐄 48sp)
  - Text "SapiSehat" headlineLarge bold, color onPrimary
  - CircularProgressIndicator, color onPrimary alpha 0.8
  - Text stringResource(R.string.splash_loading), bodyMedium, onPrimary alpha 0.7
- No ViewModel (simple UI), animasi fade-in opsional

VERIFIKASI: SplashRoute.kt ada, background hijau sage dengan loading indicator
```

---

## Prompt 2: Onboarding Screen

**Tujuan:** 3 slide onboarding untuk first-time users.

```
Project: SapiSehat Android app. Prompt 0-1 sudah selesai.
Package: com.sapisehat.app | Pattern: Compose

TASK: Buat Onboarding screen 3 slide dengan dots indicator.

CREATE apps/mobile/app/src/main/java/com/sapisehat/app/ui/onboarding/OnboardingRoute.kt:

Data class OnboardingSlide(emoji, titleRes, bodyRes)
val slides = listOf(
  OnboardingSlide("📸", R.string.onboarding_title_1, R.string.onboarding_body_1),
  OnboardingSlide("📴", R.string.onboarding_title_2, R.string.onboarding_body_2),
  OnboardingSlide("⚡", R.string.onboarding_title_3, R.string.onboarding_body_3)
)

OnboardingRoute(onFinish: () -> Unit):
- @OptIn(ExperimentalFoundationApi::class)
- HorizontalPager dengan pagerState
- Top: Row dengan TextButton "Lewati" di kanan atas
- Dots indicator: Row, dot aktif 12dp primary, non-aktif 8dp abu
- CTA button: "Lanjut" (slide 1-2) / "Mulai" (slide 3)
  - Klik: jika halaman terakhir → simpan "has_completed_onboarding" = true, panggil onFinish()
  - Jika bukan terakhir → animateScrollToPage +1
- SlideContent: Column center, emoji 72sp, title headlineMedium bold, body bodyLarge secondary

VERIFIKASI: 3 slide, swipe, dots, skip, CTA button
```

---

## Prompt 3: Camera Screen

**Tujuan:** CameraX preview + capture + gallery pick + flash toggle + grid + permission.

```
Project: SapiSehat Android app. Prompt 0-2 selesai. Existing: CameraRoute.kt, CameraViewModel.kt skeleton.
Package: com.sapisehat.app | Pattern: MVVM + Compose + Hilt + CameraX

TASK: Upgrade Camera ke full CameraX implementation.

=== VIEWMODEL ===
REWRITE apps/mobile/app/src/main/java/com/sapisehat/app/ui/camera/CameraViewModel.kt:
@HiltViewModel class CameraViewModel(@ApplicationContext context, classifyImageUseCase):
- CameraUiState: isLoading, error, progressText, hasCameraPermission, permissionPermanentlyDenied, flashMode(AUTO/ON/OFF), showGrid
- checkPermission() via ContextCompat.checkSelfPermission
- onPermissionResult(granted)
- classify(imageUri, onResult callback) — launch coroutine, set loading, call classifyImageUseCase
- clearError(), setFlashMode(), toggleGrid()
- enum FlashMode { AUTO, ON, OFF }

=== UI ===
REWRITE apps/mobile/app/src/main/java/com/sapisehat/app/ui/camera/CameraRoute.kt:
CameraRoute(onShowResult: (label, confidence, mode, scoresJson) -> Unit):
- permissionLauncher = rememberLauncherForActivityResult(RequestPermission)
- galleryLauncher = rememberLauncherForActivityResult(GetContent)
- LaunchedEffect: cek permission, request jika belum
- When state:
  - !hasCameraPermission → CameraPermissionScreen (permanentlyDenied? openSettings : request)
  - else → CameraActiveScreen

CameraActiveScreen:
- Box fillMaxSize:
  - AndroidView(PreviewView) dengan CameraX ProcessCameraProvider, bind Preview use-case
  - CameraGridOverlay (jika showGrid): 2 horizontal + 2 vertical lines putih alpha 0.25
  - Guidance label top-center: Surface "Arahkan kamera ke sapi"
  - Top-right controls: flash toggle (⚡A/⚡/🚫), grid toggle (⊞)
  - Bottom controls: gallery picker (🖼️), shutter button (72dp circle, border putih, inner primary 60dp)
  - Loading overlay: Box hitam semi-transparan + CircularProgressIndicator + progressText
  - Error snackbar dengan dismiss

VERIFIKASI: CameraX preview, flash toggle, grid, guidance, permission handling, capture flow
```

---

## Prompt 4: Result Screen

**Tujuan:** Full diagnosis display — badge mode, confidence bar, scores, advice, action buttons.

```
Project: SapiSehat Android app. Prompt 0-3 selesai. Existing: ResultRoute.kt skeleton.
Package: com.sapisehat.app | Pattern: Compose

TASK: Upgrade Result screen ke full diagnosis display.

REWRITE apps/mobile/app/src/main/java/com/sapisehat/app/ui/result/ResultRoute.kt:

ClassDisplayConfig: displayName, icon, color, advice per class
- "SEHAT"/"healthy" → "Sehat", 🟢, #5B9A5B, "Sapi sehat. Lanjutkan pemantauan rutin."
- "FMD"/"PMK" → "PMK", 🔴, #D4745C, "Isolasi sapi segera\nHubungi dokter hewan\nLapor ke Dinas Peternakan"
- "LSD"/"LATO_LATO" → "Lato-Lato", 🟠, #E8985E, "Pisahkan dari ternak lain\nHubungi dokter hewan\nPeriksa ternak lain"

ResultRoute(label, confidence, mode, allScoresJson, onBack, onSave, onRetake):
- Parse allScoresJson → Map<String, Float> (Sehat, PMK, Lato-Lato)
- ConfidenceLevel: HIGH(≥80%), MEDIUM(60-79%), LOW(<60%)
- ModeBadge: ONLINE=🌐 hijau, OFFLINE=📴 oren, fallback=⚠️ oren
- Column scrollable:
  - Photo placeholder Surface 200dp dengan 📸
  - Mode badge pill
  - HorizontalDivider
  - Diagnosis headline: "[icon] [displayName] Terdeteksi" dalam warna class
  - "Keyakinan: XX%"
  - ConfidenceBar: gradient horizontal, 12dp height, rounded 6dp
  - All class scores: ScoreRow per kelas dengan progress bar dan persentase
  - Jika confidence LOW/MEDIUM: warning card (kuning untuk medium, merah untuk low)
  - Advice card: "⚠️ Saran Penanganan" + advice text per baris
  - Action buttons: OutlinedButton Simpan, OutlinedButton Bagikan, Button Ulangi

ConfidenceBar(confidence, color): Box 12dp dengan gradient dari color(alpha 0.6) ke color
ScoreRow(label, score, isHighlighted): icon ●/○, label, progress bar, persentase

VERIFIKASI: Badge mode, confidence bar, all scores, advice text per disease, 3 action buttons
```

---

## Prompt 5: History Screen

**Tujuan:** Riwayat deteksi — list card, filter chips, delete, empty state.

```
Project: SapiSehat Android app. Prompt 0-4 selesai. Existing: HistoryRoute, HistoryViewModel, DetectionDao, DetectionRepository.
Package: com.sapisehat.app | Pattern: MVVM + Compose + Hilt + Room + Coil

TASK: Upgrade History ke full list dengan filter, delete, empty state.

=== DAO ===
MODIFY apps/mobile/app/src/main/java/com/sapisehat/app/data/local/dao/DetectionDao.kt — tambahkan:
- @Query("DELETE FROM detection_records WHERE id = :id") suspend fun deleteById(id: Long)
- @Query("DELETE FROM detection_records") suspend fun deleteAll()
- @Query("SELECT * FROM detection_records WHERE predictedClass = :classFilter ORDER BY timestamp DESC") fun observeByClass(classFilter: String): Flow<List<DetectionEntity>>
- @Query("SELECT * FROM detection_records WHERE inferenceMode = :modeFilter ORDER BY timestamp DESC") fun observeByMode(modeFilter: String): Flow<List<DetectionEntity>>

=== REPOSITORY ===
MODIFY apps/mobile/app/src/main/java/com/sapisehat/app/data/repository/DetectionRepository.kt — tambahkan:
- suspend fun deleteDetection(id: Long)
- suspend fun deleteAll()
- fun observeHistoryFiltered(classFilter: String?, modeFilter: String?): Flow<List<DetectionResult>>
- Update toDomain() untuk include id dan timestamp

=== VIEWMODEL ===
REWRITE apps/mobile/app/src/main/java/com/sapisehat/app/ui/history/HistoryViewModel.kt:
- _filterClass: MutableStateFlow<String?>
- _filterMode: MutableStateFlow<String?>
- filteredRows: StateFlow<List<HistoryItemUi>> — flatMapLatest dari observeHistoryFiltered
- HistoryItemUi: id, label, displayLabel, confidence, mode, timestamp, allScores
- setClassFilter(), setModeFilter(), deleteItem(id), deleteAll(), clearError()

=== UI ===
REWRITE apps/mobile/app/src/main/java/com/sapisehat/app/ui/history/HistoryRoute.kt:
HistoryRoute(onOpenDetail: (label, confidence, mode, scoresJson)):
- Top bar: judul "Riwayat Deteksi" + delete all button
- Filter chips ScrollableTabRow: "Semua", "Sehat", "PMK", "Lato-Lato", "Online", "Offline"
- LazyColumn card items:
  - HistoryCard: thumbnail placeholder 📸 56dp, label dengan emoji + warna, confidence %, ModeBadge, timestamp, delete button
- Empty state: emoji 🐄, teks "Belum ada pemeriksaan"
- Filter empty state: "Tidak ada hasil dengan filter ini" + clear filter button
- Delete confirmation AlertDialog
- Tap card → onOpenDetail via JSONObject(allScores).toString()
- formatTimestamp: SimpleDateFormat("dd MMM yyyy, HH:mm", Locale("id"))

VERIFIKASI: Filter chips, delete, empty states, tap ke detail
```

---

## Prompt 6: Guide Screen

**Tujuan:** Panduan 3 tab: Cara Memotret, PMK, LSD.

```
Project: SapiSehat Android app. Prompt 0-5 selesai.
Package: com.sapisehat.app | Pattern: Compose (no ViewModel)

TASK: Buat Guide screen 3-tab switcher dengan konten artikel.

CREATE apps/mobile/app/src/main/java/com/sapisehat/app/ui/guide/GuideRoute.kt:

GuideRoute():
- var selectedTab (0..2)
- tabs: "Cara Memotret", "PMK", "Lato-Lato"
- Column:
  - Top bar: Text "Panduan" headlineMedium bold
  - TabRow 3 tab, contentColor primary
  - Content berdasarkan selectedTab:
    0 → PhotoGuideContent: 4 GuideSection cards (Jarak, Pencahayaan, Posisi, Hindari)
    1 → FmdContent: 3 GuideSection cards (Gejala, Penularan, Penanganan)
    2 → LsdContent: 3 GuideSection cards (Gejala, Penularan, Penanganan)

GuideSection(icon, title, body):
- Card dengan elevation 1dp
- Row: icon emoji headlineSmall + title titleLarge SemiBold
- body text bodyMedium secondary

VERIFIKASI: 3 tab, konten artikel per tab, card sections
```

---

## Prompt 7: About Screen

**Tujuan:** Info aplikasi — logo, tim, institusi, versi, teknologi.

```
Project: SapiSehat Android app. Prompt 0-6 selesai.
Package: com.sapisehat.app | Pattern: Compose

TASK: Buat About screen.

CREATE apps/mobile/app/src/main/java/com/sapisehat/app/ui/about/AboutRoute.kt:

AboutRoute(onBack: () -> Unit):
- TopAppBar "Tentang" + back button "←"
- Column scrollable center:
  - Logo placeholder Surface 100dp + 🐄
  - "SapiSehat" headlineLarge bold
  - Deskripsi aplikasi bodyLarge secondary
  - Versi: BuildConfig.VERSION_NAME
  - Divider
  - AboutSection "Tim Pengembang": ["Raditya Rafif Pratama Sasmita", "Noval Putra Ramadhan"]
  - AboutSection "Institusi": ["Teknik Informatika, Politeknik Negeri Semarang"]
  - AboutSection "Dosen Pembimbing": ["[Dosen Pembimbing — TBD]"]
  - AboutSection "Teknologi": ["MobileNetV2 (CNN)", "TensorFlow Lite", "FastAPI + Python", "Jetpack Compose + Kotlin", "CameraX + Room + Hilt"]
  - AboutSection "Sumber Dataset": ["Kaggle", "Roboflow Universe", "Data lapangan"]
  - © 2026 SapiSehat Team | Politeknik Negeri Semarang

AboutSection(title, items):
- Card elevation 1dp
- title titleMedium SemiBold primary
- items: "• [item]" bodyMedium

VERIFIKASI: Logo, tim, institusi, versi, teknologi, dataset sources
```

---

## Prompt 8: Settings Screen

**Tujuan:** Pengaturan — bahasa, ukuran teks, server URL, hapus riwayat, reset onboarding.

```
Project: SapiSehat Android app. Prompt 0-7 selesai.
Package: com.sapisehat.app | Pattern: MVVM + Compose + Hilt + DataStore

TASK: Buat Settings dengan preference list.

=== DATASTORE ===
CREATE apps/mobile/app/src/main/java/com/sapisehat/app/data/local/SettingsDataStore.kt:
- Context.dataStore extension via preferencesDataStore(name = "settings")
- Keys: KEY_LANGUAGE (stringPreferencesKey), KEY_TEXT_SIZE, KEY_SERVER_URL
- Flow properties: language, textSize, serverUrl
- Suspend fun: setLanguage(), setTextSize(), setServerUrl()

=== DI MODULE ===
MODIFY apps/mobile/app/src/main/java/com/sapisehat/app/di/AppModule.kt — tambahkan:
- @Provides @Singleton fun provideSettingsDataStore(@ApplicationContext context): SettingsDataStore

=== VIEWMODEL + UI (single file) ===
CREATE apps/mobile/app/src/main/java/com/sapisehat/app/ui/settings/SettingsRoute.kt:

SettingsViewModel @HiltViewModel:
- Observe language, textSize, serverUrl dari SettingsDataStore
- setLanguage(), setTextSize(), setServerUrl()
- clearAllHistory() via DetectionRepository.deleteAll()
- resetOnboarding(context) — set "has_completed_onboarding" = false

SettingsRoute(onBack):
- Scaffold TopAppBar "Pengaturan" + back
- Column scrollable:
  - Language dropdown: "Ikuti Sistem" / "Indonesia" / "English"
  - Text size dropdown: "Ikuti Sistem" / "Kecil" / "Sedang" / "Besar"
  - Server URL: clickable → AlertDialog dengan OutlinedTextField + OK/Cancel
  - Divider
  - Clear all history (warna error) → AlertDialog confirmation
  - Reset onboarding
  - Divider
  - App version: BuildConfig.VERSION_NAME (read-only)
  - Model version: "1.0.0" (read-only)
- Snackbar untuk feedback (history cleared, onboarding reset)

VERIFIKASI: Language, text size, server URL, clear history, reset onboarding, info versi
```

---

## Final Verification

Setelah semua 9 prompt selesai:
1. `cd apps/mobile && ./gradlew assembleDebug` — harus sukses
2. File harus ada di package masing-masing
3. Splash → Onboarding → Camera → Result → History → Guide → About → Settings
4. String bilingual lengkap di values/ dan values-en/
5. Tab bar 4 item berfungsi

*Copy setiap prompt (dalam triple backtick) ke Pi. Mulai dari Prompt 0.*
