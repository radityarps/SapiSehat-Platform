# Prompt 7: About Screen — Implementation Plan

## Context

Prompts 0–6 are complete. The `AboutRoute.kt` file does not yet exist — it must be created from scratch. The NavHost already calls `composable(Routes.About) { AboutRoute(onBack = { rootNavController.popBackStack() }) }`. All about strings are defined in `strings.xml` (lines 118-138). This is a single-file, ViewModel-free informational screen — similar in complexity to Prompt 6 (Guide).

## Current State

| File                     | Status      | Notes                                                                                                                                                                                                                                                                                                        |
| ------------------------ | ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `ui/about/AboutRoute.kt` | **Missing** | Does not exist — must be created                                                                                                                                                                                                                                                                             |
| `strings.xml`            | Complete    | 21 about strings: `about_title`, `about_desc`, `about_team_title`, `about_team_member_1/2`, `about_institution_title`, `about_institution`, `about_supervisor_title`, `about_supervisor`, `about_tech_title`, `about_tech_1-5`, `about_source_title`, `about_source_1-3`, `about_version`, `about_copyright` |
| `Theme`                  | Complete    | `Primary`, `TextSecondary` colours; `headlineLarge`, `titleMedium`, `bodyLarge`, `bodyMedium` styles                                                                                                                                                                                                         |
| `SapiSehatNavHost.kt`    | Complete    | Already calls `AboutRoute(onBack = { rootNavController.popBackStack() })`                                                                                                                                                                                                                                    |

## Approach

Single-file creation (`AboutRoute.kt`) with pure Compose. No ViewModel, no data layer changes. About 80% of the code is declarative content layout; the only logic is the back navigation callback.

### Key Components

| Component                        | Type              | Purpose                                                                   |
| -------------------------------- | ----------------- | ------------------------------------------------------------------------- |
| `AboutRoute(onBack: () -> Unit)` | Composable        | Top-level screen with Scaffold, top bar + back button, scrollable content |
| `AboutSection`                   | Composable        | Reusable section: Card with title + bulleted item list                    |
| Logo placeholder                 | Surface           | 100dp rounded Surface with 🐄 emoji centered                              |
| Version                          | Text              | `BuildConfig.VERSION_NAME` from Gradle                                    |
| Divider                          | HorizontalDivider | Separates header block from sections                                      |
| Copyright                        | Text              | Centered, small, secondary colour                                         |

### Layout Structure

```
AboutRoute(onBack: () -> Unit)
├── Scaffold
│   ├── TopAppBar("Tentang") + navigationIcon = back arrow
│   └── Column(verticalScroll, centerHorizontally)
│       ├── Spacer(24.dp)
│       ├── Logo placeholder — Surface 100dp rounded + 🐄 (48.sp)
│       ├── Spacer(16.dp)
│       ├── "SapiSehat" — headlineLarge, Bold, primary
│       ├── Spacer(8.dp)
│       ├── Description — bodyLarge, secondary, center text alignment
│       ├── Spacer(8.dp)
│       ├── "Versi: ${BuildConfig.VERSION_NAME}" — labelMedium, secondary
│       ├── Spacer(24.dp)
│       ├── HorizontalDivider
│       ├── Spacer(24.dp)
│       ├── AboutSection("Tim Pengembang", [member1, member2])
│       ├── AboutSection("Institusi", [institution])
│       ├── AboutSection("Dosen Pembimbing", [supervisor TBD])
│       ├── AboutSection("Teknologi", [tech1..tech5])
│       ├── AboutSection("Sumber Dataset", [source1..source3])
│       ├── Spacer(24.dp)
│       ├── Copyright text — centered, small, secondary
│       └── Spacer(24.dp)
│
│   AboutSection(@StringRes titleRes, items: List<String>)
│   ├── Card(elevation = 1.dp, rounded 12.dp)
│   │   └── Column(padding = 16.dp)
│   │       ├── titleRes text — titleMedium, SemiBold, primary colour
│   │       ├── Spacer(8.dp)
│   │       └── items.forEach:
│   │           └── Row: "•  " + item — bodyMedium, secondary
```

## Files to Create

| #   | File                     | Action | Purpose                                                                |
| --- | ------------------------ | ------ | ---------------------------------------------------------------------- |
| 1   | `ui/about/AboutRoute.kt` | Create | Full about screen with logo, description, version, and 5 card sections |

## Steps

- [x] **1. Create `AboutRoute.kt`**
  - Signature: `@Composable fun AboutRoute(onBack: () -> Unit)`
  - `Scaffold` with `TopAppBar`:
    - Title: `stringResource(R.string.about_title)`
    - Navigation icon: `IconButton(onClick = onBack)` with `Icons.AutoMirrored.Filled.ArrowBack`
  - Body: `Column(Modifier.fillMaxSize().verticalScroll().padding(24.dp), horizontalAlignment = CenterHorizontally)`
  - Logo: `Surface(100.dp, CircleShape/RoundedCornerShape 16.dp, surfaceVariant)` with `Text("🐄", 48.sp)` centered
  - App name: `Text("SapiSehat", headlineLarge, Bold, Primary)`
  - Description: `Text(stringResource(R.string.about_desc), bodyLarge, TextSecondary, textAlign = Center)`
  - Version: `Text("${stringResource(R.string.about_version)}: ${BuildConfig.VERSION_NAME}", labelMedium, TextSecondary)`
  - `HorizontalDivider`
  - 5 `AboutSection` cards:
    1. `R.string.about_team_title` → items from `R.string.about_team_member_1`, `R.string.about_team_member_2`
    2. `R.string.about_institution_title` → item from `R.string.about_institution`
    3. `R.string.about_supervisor_title` → item from `R.string.about_supervisor`
    4. `R.string.about_tech_title` → items from `R.string.about_tech_1` through `R.string.about_tech_5`
    5. `R.string.about_source_title` → items from `R.string.about_source_1` through `R.string.about_source_3`
  - Copyright: `Text(stringResource(R.string.about_copyright), labelSmall, TextSecondary, textAlign = Center)`
  - `AboutSection` composable:
    - `@StringRes titleRes: Int, @StringRes vararg itemRes: Int` or `titleRes: Int, itemResList: List<Int>`
    - Or: `title: String, items: List<String>` — caller resolves strings
    - Simpler approach (avoids composable context issues): resolve strings in parent and pass as `String` and `List<String>`
    - `Card(elevation = 1.dp, shape = RoundedCornerShape(12.dp), modifier = Modifier.fillMaxWidth())`
    - `Column(Modifier.padding(16.dp))`:
      - `Text(title, titleMedium, SemiBold, Primary)`
      - `Spacer(8.dp)`
      - `items.forEach { Text("•  $it", bodyMedium, TextSecondary) }` with `Spacer(4.dp)` between

## Trade-offs & Assumptions

| Item                                                           | Decision  | Rationale                                                                                                                                                       |
| -------------------------------------------------------------- | --------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| No ViewModel                                                   | Accepted  | Purely informational screen; no reactive state beyond back navigation                                                                                           |
| `BuildConfig.VERSION_NAME`                                     | Accepted  | Gradle generates `BuildConfig`; import from app package                                                                                                         |
| `AboutSection` takes `String`/`List<String>`, not `@StringRes` | Accepted  | Resolving strings in the parent avoids passing `@StringRes` into a private composable that may not have `@Composable`-safe lifecycle; simpler and zero overhead |
| Logo as Surface + emoji                                        | Accepted  | No image assets yet; emoji is consistent with Guide and History placeholders                                                                                    |
| Scrollable entire body                                         | Accepted  | All content in one scrollable Column; simpler than nested scrolling                                                                                             |
| `Icons.AutoMirrored.Filled.ArrowBack`                          | Available | `material-icons-extended` is in dependencies (from Prompt 0)                                                                                                    |
| `textAlign = Center` for description/copyright                 | Accepted  | Centered text for branding elements looks polished                                                                                                              |
| HorizontalDivider separator                                    | Accepted  | Visual break between header and sections                                                                                                                        |
| Card spacing via `Arrangement.spacedBy`                        | Accepted  | Consistent 12dp gap between sections                                                                                                                            |

## Risks

| Risk                                                    | Level | Mitigation                                                                                                                                                      |
| ------------------------------------------------------- | ----- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `BuildConfig.VERSION_NAME` import path wrong            | Low   | Gradle generates `BuildConfig` in the app module package; may be `com.sapisehat.app.BuildConfig` or `com.sapisehat.app.BuildConfig` — check with grep if needed |
| `BuildConfig` not generated in debug build              | Low   | Standard Android behavior; always generated                                                                                                                     |
| About screen not reachable via nav                      | Low   | NavHost already wired — `composable(Routes.About) { AboutRoute(onBack = ...) }` in Turn 34                                                                      |
| Long institution text wraps poorly                      | Low   | `bodyMedium` handles wrapping naturally                                                                                                                         |
| Supervisor text `[Dosen Pembimbing — TBD]` may look odd | Low   | User can update the string later; explicitly marked as TBD                                                                                                      |

## Verification

1. `AboutRoute(onBack = ...)` renders with "Tentang" top bar and back arrow
2. Logo: 100dp Surface with 🐄 centered
3. "SapiSehat" headlineLarge Bold in Primary colour
4. Description text bodyLarge secondary centered
5. Version: "Versi: X.Y.Z" from BuildConfig
6. HorizontalDivider between header and sections
7. 5 AboutSection cards: Tim Pengembang (2 members), Institusi (1), Dosen Pembimbing (1 TBD), Teknologi (5), Sumber Dataset (3)
8. Each card: titleMedium SemiBold Primary + bulleted items bodyMedium TextSecondary
9. Copyright: "© 2026 SapiSehat Team | Politeknik Negeri Semarang" centered small secondary
10. Back arrow navigates back (via rootNavController.popBackStack)
11. Entire screen scrolls if content exceeds viewport
12. Preview renders correctly
