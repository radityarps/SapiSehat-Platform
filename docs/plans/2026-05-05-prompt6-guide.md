# Prompt 6: Guide Screen — Implementation Plan

## Context

Prompts 0–5 are complete. The `GuideRoute.kt` file does not yet exist — it needs to be created from scratch. The NavHost already calls `composable(Routes.Guide) { GuideRoute() }` with zero parameters. All guide content strings are defined in `strings.xml` (lines 92-115). This is the simplest prompt yet: a single-file, ViewModel-free, pure-Compose informational screen.

## Current State

| File                     | Status      | Notes                                                                                                                                                              |
| ------------------------ | ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `ui/guide/GuideRoute.kt` | **Missing** | Does not exist — must be created                                                                                                                                   |
| `strings.xml`            | Complete    | 24 guide strings: `guide_title`, `guide_tab_photo/fmd/lsd`, `guide_photo_title_1-4`/`body_1-4`, `guide_fmd_title_1-3`/`body_1-3`, `guide_lsd_title_1-3`/`body_1-3` |
| `Theme`                  | Complete    | `TextSecondary`, `Primary` colours available                                                                                                                       |
| `SapiSehatNavHost.kt`    | Complete    | Already calls `GuideRoute()` — no parameter changes needed                                                                                                         |

## Approach

Single-file creation (`GuideRoute.kt`) with pure Compose. No ViewModel, no data layer changes.

### Key Components

| Component         | Type       | Purpose                                                                  |
| ----------------- | ---------- | ------------------------------------------------------------------------ |
| `GuideRoute()`    | Composable | Top-level screen with `Scaffold`, top bar, and `TabRow`                  |
| `TabRow`          | Material3  | 3 tabs: "Cara Memotret" (📷), "PMK" (🔴), "Lato-Lato" (🟠)               |
| `GuideSection`    | Composable | Reusable card: icon emoji, title, body text                              |
| Photo tab content | Composable | 4 `GuideSection` cards — Jarak 📏, Pencahayaan 💡, Posisi 📐, Hindari ❌ |
| PMK tab content   | Composable | 3 `GuideSection` cards — Gejala 🩺, Penularan 🔄, Penanganan 💊          |
| LSD tab content   | Composable | 3 `GuideSection` cards — Gejala 🩺, Penularan 🔄, Penanganan 💊          |

### Design Decisions

| Decision                                                                         | Rationale                                                                        |
| -------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| `remember { mutableIntStateOf(0) }` for selected tab                             | No ViewModel needed; tab selection is transient UI state                         |
| `GuideSection` as private composable                                             | Reused across all 3 tabs; parameterized by icon emoji, title string, body string |
| Card with `elevation = 1.dp`                                                     | Light depth for section cards                                                    |
| Emoji icons                                                                      | Simple, dependency-free — no vector drawables needed                             |
| `VerticalScroll` on content Column                                               | Ensures all cards are reachable on small screens                                 |
| `headlineSmall` for icon, `titleLarge SemiBold` for title, `bodyMedium` for body | Matches spec exactly                                                             |
| `TextSecondary` colour for body text                                             | Consistent with the app's design system                                          |

## Files to Create

| #   | File                     | Action | Purpose                                    |
| --- | ------------------------ | ------ | ------------------------------------------ |
| 1   | `ui/guide/GuideRoute.kt` | Create | Full 3-tab guide screen with article cards |

## Steps

- [x] **1. Create `GuideRoute.kt`**
  - `@Composable fun GuideRoute()` — no parameters
  - `var selectedTab by remember { mutableIntStateOf(0) }`
  - Tab definitions: list of `Pair<String, @StringRes Int>` — `("📷", R.string.guide_tab_photo)`, `("🔴", R.string.guide_tab_fmd)`, `("🟠", R.string.guide_tab_lsd)`
  - `Scaffold` with `TopAppBar` — title `stringResource(R.string.guide_title)`
  - `TabRow(selectedTabIndex = selectedTab)` with 3 `Tab` items — each with emoji icon + text
  - Tab `onClick = { selectedTab = index }`
  - Content area: `when (selectedTab)` switching between 3 content composables
  - Tab 0 → `PhotoGuideContent()`: 4 `GuideSection` cards
    - 📏 `guide_photo_title_1` / `guide_photo_body_1` — Jarak
    - 💡 `guide_photo_title_2` / `guide_photo_body_2` — Pencahayaan
    - 📐 `guide_photo_title_3` / `guide_photo_body_3` — Posisi
    - ❌ `guide_photo_title_4` / `guide_photo_body_4` — Hindari
  - Tab 1 → `FmdContent()`: 3 `GuideSection` cards
    - 🩺 `guide_fmd_title_1` / `guide_fmd_body_1` — Gejala
    - 🔄 `guide_fmd_title_2` / `guide_fmd_body_2` — Penularan
    - 💊 `guide_fmd_title_3` / `guide_fmd_body_3` — Penanganan
  - Tab 2 → `LsdContent()`: 3 `GuideSection` cards
    - 🩺 `guide_lsd_title_1` / `guide_lsd_body_1` — Gejala
    - 🔄 `guide_lsd_title_2` / `guide_lsd_body_2` — Penularan
    - 💊 `guide_lsd_title_3` / `guide_lsd_body_3` — Penanganan
  - Each content section wrapped in `Column(Modifier.verticalScroll(rememberScrollState()).padding(16.dp))` with `Arrangement.spacedBy(12.dp)`
  - `GuideSection(icon: String, @StringRes titleRes: Int, @StringRes bodyRes: Int)`:
    - `Card(elevation = CardDefaults.cardElevation(defaultElevation = 1.dp), shape = RoundedCornerShape(12.dp))`
    - `Column(Modifier.padding(16.dp))`:
      - `Row`: `Text(icon, fontSize = 28.sp)` + `Spacer(12.dp)` + `Text(stringResource(titleRes), style = titleLarge, fontWeight = SemiBold)`
      - `Spacer(8.dp)`
      - `Text(stringResource(bodyRes), style = bodyMedium, color = TextSecondary)`

## Trade-offs & Assumptions

| Item                                        | Decision      | Rationale                                                            |
| ------------------------------------------- | ------------- | -------------------------------------------------------------------- |
| No ViewModel                                | Accepted      | Pure informational content; tab selection is ephemeral UI state      |
| Emoji icons instead of vector drawables     | Accepted      | No need for icon dependencies; emojis render consistently on Android |
| Hardcoded icon strings in composable        | Accepted      | Only 3 tabs; simpler than a separate data model                      |
| Tab content not extracted to separate files | Accepted      | Content is small (4+3+3 sections); single file keeps it co-located   |
| `mutableIntStateOf` (Compose 1.5+)          | Available     | Project uses Compose BOM 2024+ which includes this API               |
| No animation on tab switch                  | Accepted      | Spec doesn't mention transitions; simple `when` block is sufficient  |
| Scrollable content per tab                  | Accepted      | Each tab's Column uses `verticalScroll` independently                |
| `CardDefaults.cardElevation(1.dp)`          | Material3 API | Consistent with other cards in the app (Onboarding, History)         |
| Tab content uses `@StringRes` annotations   | Best practice | Type-safe string resource references                                 |

## Risks

| Risk                                               | Level | Mitigation                                                                                                                                      |
| -------------------------------------------------- | ----- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| `mutableIntStateOf` not available in older Compose | Low   | Project uses BOM 2024.02+ which bundles Compose 1.6+; `mutableIntStateOf` is stable since 1.5. If unavailable, fall back to `mutableStateOf(0)` |
| Long body text overflows on small screens          | Low   | `verticalScroll` ensures all content is reachable; text uses default wrapping                                                                   |
| Tab labels too long for `TabRow`                   | Low   | Labels are short: "Cara Memotret" (13 chars), "PMK" (3 chars), "Lato-Lato" (8 chars) — fit easily                                               |
| GuideRoute file path doesn't exist                 | Low   | `write` tool auto-creates parent directories                                                                                                    |

## Verification

1. `GuideRoute()` renders with "Panduan" top bar title
2. 3 tabs visible: "Cara Memotret" 📷, "PMK" 🔴, "Lato-Lato" 🟠
3. Tab 0 selected by default → shows 4 photo guide cards
4. Switching to tab 1 → shows 3 PMK cards
5. Switching to tab 2 → shows 3 Lato-Lato cards
6. Each `GuideSection` card: icon emoji, title (SemiBold), body (secondary)
7. Content scrolls independently per tab
8. All string resources resolve correctly (no missing IDs)
9. No compilation errors — NavHost call `GuideRoute()` matches zero-parameter signature
10. Preview renders correctly with sample content
