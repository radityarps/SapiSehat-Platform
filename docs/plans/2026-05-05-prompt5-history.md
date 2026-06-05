# Prompt 5: History Screen — Implementation Plan

## Context

Prompts 0–4 are complete. Skeleton `HistoryRoute.kt` and `HistoryViewModel.kt` exist but are minimal (plain text rows + back button). The DAO has only `insert` and `observeAll`. Prompt 5 upgrades the History screen into a full-featured list with class/mode filter chips, swipe-to-delete or delete button, empty states, delete confirmation dialog, and tap-to-detail navigation.

### Current state of related code

| File                                     | Status   | Notes                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| ---------------------------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `data/local/dao/DetectionDao.kt`         | Minimal  | Only `insert()` and `observeAll()`. Needs 4 new queries.                                                                                                                                                                                                                                                                                                                                                                                                            |
| `data/local/entity/DetectionEntity.kt`   | Complete | Has all needed columns: `id`, `timestamp`, `predictedClass`, `displayLabel`, `confidence`, `scoreHealthy`, `scoreFmd`, `scoreLsd`, `inferenceMode`, `isReliable`, `processingMs`                                                                                                                                                                                                                                                                                    |
| `data/repository/DetectionRepository.kt` | Exists   | `saveDetection()`, `observeHistory()`, `toDomain()` works. Needs `deleteDetection()`, `deleteAll()`, `observeHistoryFiltered()`. `toDomain()` needs to include `id` and `timestamp`.                                                                                                                                                                                                                                                                                |
| `domain/model/DetectionResult.kt`        | 7 fields | Lacks `id: Long` and `timestamp: Long`. Must add both as `= 0` defaults so existing classification call sites still compile.                                                                                                                                                                                                                                                                                                                                        |
| `ui/history/HistoryRoute.kt`             | Skeleton | `onBack: () -> Unit`, `hiltViewModel()`, shows `"${item.label} - ${(item.confidence * 100).toInt()}% (${item.mode})"` in a `LazyColumn`                                                                                                                                                                                                                                                                                                                             |
| `ui/history/HistoryViewModel.kt`         | Minimal  | `uiState: StateFlow<List<HistoryItemUi>>`, `HistoryItemUi(label, confidence, mode)` — 3 fields                                                                                                                                                                                                                                                                                                                                                                      |
| `strings.xml`                            | Complete | All history strings: `history_title`, `history_delete`, `history_delete_all`, `history_empty`, `history_empty_filter`, `history_filter_all`, `history_filter_sehat`, `history_filter_pmk`, `history_filter_lato`, `history_filter_online`, `history_filter_offline`, `history_confirm_delete_title`, `history_confirm_delete_message`, `history_confirm_delete_all_title`, `history_confirm_delete_all_message`, `history_confirm_cancel`, `history_confirm_delete` |
| `Theme`                                  | Complete | `Success`, `Danger`, `Accent`, `TextSecondary`, `Primary` colours available                                                                                                                                                                                                                                                                                                                                                                                         |
| `ResultRoute` (Prompt 4)                 | Exists   | `ClassDisplayConfig`, `ModeBadge` pattern — History will reuse the same emoji/colour map and mode badge renderer                                                                                                                                                                                                                                                                                                                                                    |

## Approach

Multi-file changes across the data and UI layers:

1. **DetectionResult model** — add `id: Long = 0` and `timestamp: Long = 0L` (backward-compatible defaults)
2. **DAO** — add 4 new `@Query` methods
3. **Repository** — add delete methods, filtered observer that chooses DAO method based on which filter(s) are active
4. **HistoryViewModel** — full rewrite with `MutableStateFlow<String?>` for class/mode filters, `flatMapLatest` for reactive filtering, delete actions
5. **HistoryRoute** — full rewrite with filter chips row, card-based LazyColumn, delete confirmation dialog, empty/filter-empty states

### Key Components

| Component                                      | Type              | Purpose                                                                                                                     |
| ---------------------------------------------- | ----------------- | --------------------------------------------------------------------------------------------------------------------------- |
| `DetectionResult.id`, `.timestamp`             | Data class fields | Carry DB id and timestamp through the repository layer into UI                                                              |
| `DetectionDao.deleteById()`                    | DAO method        | Delete one record                                                                                                           |
| `DetectionDao.deleteAll()`                     | DAO method        | Delete all records                                                                                                          |
| `DetectionDao.observeByClass()`                | DAO method        | Filter by `predictedClass` column                                                                                           |
| `DetectionDao.observeByMode()`                 | DAO method        | Filter by `inferenceMode` column                                                                                            |
| `DetectionRepository.observeHistoryFiltered()` | Repository method | Returns `Flow<List<DetectionResult>>`, chooses DAO query by active filter(s), falls back to `observeAll()` for null filters |
| `HistoryViewModel`                             | ViewModel         | `_filterClass`, `_filterMode` state flows; `filteredRows` via `combine`; `deleteItem()`, `deleteAll()`, `clearError()`      |
| `HistoryItemUi`                                | Data class        | `id: Long, label: String, displayLabel: String, confidence: Float, mode: String, timestamp: Long, allScoresJson: String`    |
| `FilterChipRow`                                | Composable        | `ScrollableTabRow` with 6 chips: Semua, Sehat, PMK, Lato-Lato, Online, Offline                                              |
| `HistoryCard`                                  | Composable        | Card: thumbnail placeholder 📸 56dp, emoji+label, confidence %, mode badge pill, timestamp, delete IconButton               |
| `formatTimestamp`                              | Util function     | `SimpleDateFormat("dd MMM yyyy, HH:mm", Locale("id", "ID"))`                                                                |
| `EmptyState`                                   | Composable        | 🐄 + "Belum ada pemeriksaan"                                                                                                |
| `FilterEmptyState`                             | Composable        | "Tidak ada hasil dengan filter ini" + clear filter Button                                                                   |

### Data Flow

```
HistoryRoute (UI)
  ├── reads filteredRows: StateFlow<List<HistoryItemUi>>
  │     └── HistoryViewModel
  │           ├── _filterClass: MutableStateFlow<String?>
  │           ├── _filterMode: MutableStateFlow<String?>
  │           └── combine(_filterClass, _filterMode).flatMapLatest { ... }
  │                 └── repository.observeHistoryFiltered(class, mode)
  │                       └── detectionDao.observeAll() / observeByClass() / observeByMode()
  ├── setClassFilter(chip) ──▶ ViewModel._filterClass.value = chip or null
  ├── setModeFilter(chip) ──▶ ViewModel._filterMode.value = chip or null
  ├── onDeleteItem(id) ──▶ ViewModel.deleteItem(id) ──▶ repository.deleteDetection(id)
  ├── onDeleteAll() ──▶ show dialog ──▶ ViewModel.deleteAll() ──▶ repository.deleteAll()
  └── onTapCard(item) ──▶ onOpenDetail(label, confidence, mode, scoresJson)
```

## Files to Modify / Rewrite

| #   | File                                     | Action  | Purpose                                                                           |
| --- | ---------------------------------------- | ------- | --------------------------------------------------------------------------------- |
| 1   | `domain/model/DetectionResult.kt`        | Edit    | Add `id: Long = 0` and `timestamp: Long = 0L`                                     |
| 2   | `data/local/dao/DetectionDao.kt`         | Edit    | Add `deleteById`, `deleteAll`, `observeByClass`, `observeByMode`                  |
| 3   | `data/repository/DetectionRepository.kt` | Edit    | Add `deleteDetection`, `deleteAll`, `observeHistoryFiltered`; update `toDomain()` |
| 4   | `ui/history/HistoryViewModel.kt`         | Rewrite | Full reactive filtering, delete actions, HistoryItemUi with all fields            |
| 5   | `ui/history/HistoryRoute.kt`             | Rewrite | Full UI: top bar, filter chips, card list, empty states, dialogs                  |

## Steps

- [x] **1. Add `id` and `timestamp` to `DetectionResult`**
  - `val id: Long = 0` (default so existing camera → repository flow still works)
  - `val timestamp: Long = 0L` (default for classification results without DB id)

- [x] **2. Add new DAO queries**
  - `deleteById(id: Long)` — `@Query("DELETE FROM detection_records WHERE id = :id")`
  - `deleteAll()` — `@Query("DELETE FROM detection_records")`
  - `observeByClass(classFilter: String)` — `@Query("SELECT * FROM detection_records WHERE predictedClass = :classFilter ORDER BY timestamp DESC")`
  - `observeByMode(modeFilter: String)` — `@Query("SELECT * FROM detection_records WHERE inferenceMode = :modeFilter ORDER BY timestamp DESC")`

- [x] **3. Add repository methods + update `toDomain()`**
  - `suspend fun deleteDetection(id: Long)` — delegates to `detectionDao.deleteById(id)`
  - `suspend fun deleteAll()` — delegates to `detectionDao.deleteAll()`
  - `fun observeHistoryFiltered(classFilter: String?, modeFilter: String?): Flow<List<DetectionResult>>`
    - Both null → `detectionDao.observeAll()`
    - Only classFilter not null → `detectionDao.observeByClass(classFilter)`
    - Only modeFilter not null → `detectionDao.observeByMode(modeFilter)`
    - Both not null → `detectionDao.observeAll().map { rows -> rows.filter { it.predictedClass == classFilter && it.inferenceMode == modeFilter } }` (filter in-memory since Room doesn't easily do dynamic multi-column WHERE)
  - `toDomain()` — add `id = id` and `timestamp = timestamp` to the `DetectionResult` constructor

- [x] **4. Rewrite `HistoryViewModel`**
  - Inject `DetectionRepository`
  - `_filterClass: MutableStateFlow<String?> = MutableStateFlow(null)`
  - `_filterMode: MutableStateFlow<String?> = MutableStateFlow(null)`
  - `filteredRows: StateFlow<List<HistoryItemUi>>` — using `combine(_filterClass, _filterMode) { classFilter, modeFilter -> ... }.flatMapLatest { repository.observeHistoryFiltered(classFilter, modeFilter) }.map { rows -> rows.map { it.toHistoryItemUi() } }.stateIn(...)`
  - `HistoryItemUi(id, label, displayLabel, confidence, mode, timestamp, allScoresJson)`
  - `setClassFilter(label: String?)` — sets `_filterClass.value = label`
  - `setModeFilter(label: String?)` — sets `_filterMode.value = label`
  - `deleteItem(id: Long)` — `viewModelScope.launch { repository.deleteDetection(id) }`
  - `deleteAll()` — `viewModelScope.launch { repository.deleteAll() }`
  - `toHistoryItemUi()` extension — maps `DetectionResult` → `HistoryItemUi`, serializes `allScores` to JSON string via `JSONObject`

- [x] **5. Rewrite `HistoryRoute`**
  - Signature: `HistoryRoute(onOpenDetail: (label: String, confidence: Float, mode: String, scoresJson: String) -> Unit)`
  - Remove `onBack` — History is a bottom nav tab, no back needed (NavHost already handles)
  - Top bar: `TopAppBar` with title `stringResource(R.string.history_title)` + delete all `IconButton` (🗑️)
  - Filter chips: `ScrollableTabRow` with 6 chips — Semua, Sehat, PMK, Lato-Lato, Online, Offline
    - Class chip selected → `setClassFilter(label)` + clear mode filter
    - Mode chip selected → `setModeFilter(label)` + clear class filter
    - "Semua" → clear both filters
  - Content area:
    - **Empty state** (history is totally empty): 🐄 emoji + `R.string.history_empty`
    - **Filter empty state** (history exists but filter yields nothing): `R.string.history_empty_filter` + clear filter Button
    - **List**: `LazyColumn` with `HistoryCard` items
  - `HistoryCard` composable:
    - `Card` with `Row`: 📸 56dp `Surface` placeholder, `Column` (emoji+displayLabel, confidence %, mode badge pill, formatted timestamp), delete `IconButton` (🗑️)
    - `Modifier.clickable` → `onOpenDetail(item.label, item.confidence, item.mode, item.allScoresJson)`
  - Delete confirmation: `AlertDialog` with title/message/cancel/confirm from string resources
    - Single delete: `history_confirm_delete_title` / `history_confirm_delete_message`
    - Delete all: `history_confirm_delete_all_title` / `history_confirm_delete_all_message`
  - `formatTimestamp(millis: Long): String` — `SimpleDateFormat("dd MMM yyyy, HH:mm", Locale("id", "ID"))`
  - Disease emoji+colour mapping — reuse the same map from ResultRoute (🟢 Sehat, 🔴 PMK, 🟠 Lato-Lato). Define as a shared object or duplicate.

- [x] **6. Update NavHost** — removed `onBack` from `HistoryRoute` call in `MainTabScreen`, kept `onOpenDetail` lambda unchanged.

## Trade-offs & Assumptions

| Item                                               | Decision                                                                  | Rationale                                                                                                                      |
| -------------------------------------------------- | ------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| `DetectionResult` gains nullable-like id/timestamp | Add `id: Long = 0, timestamp: Long = 0L`                                  | Classification flow creates results without DB id; defaults keep existing call sites compiling                                 |
| Class + mode filters are mutually exclusive in UI  | Selecting a class chip clears mode chip, and vice versa                   | Spec's chip list implies single-axis filtering; simpler UX than grid of multi-axis                                             |
| In-memory fallback for combined class+mode filter  | When both filters active, fall back to `observeAll()` + Kotlin `filter`   | Room doesn't support dynamic multi-column `WHERE` without raw query or `@RawQuery`; history size is small enough for in-memory |
| Delete confirmation dialog                         | Single dialog state in Composable (`showDeleteDialog`, `deleteTargetId`)  | No need for ViewModel — pure UI concern                                                                                        |
| Timestamp formatting                               | `SimpleDateFormat` with Indonesian locale                                 | Strings are bilingual; `Locale("id", "ID")` yields `05 Mei 2026, 14:30`                                                        |
| HistoryItemUi carries `allScoresJson: String`      | Serialize `Map<String, Float>` to JSON in ViewModel's `toHistoryItemUi()` | ResultRoute already expects `allScoresJson: String` in `onOpenDetail`                                                          |
| Photo placeholder (📸) in HistoryCard              | Surface 56dp with camera emoji                                            | Same pattern as ResultRoute; actual images deferred to later prompt (photo URI saving)                                         |
| No swipe-to-dismiss                                | Delete via IconButton only                                                | Simpler than `SwipeToDismissBox`; matches spec which only mentions delete button                                               |
| Filter chips use `ScrollableTabRow`                | Needed because 6 chips may not fit on small screens                       | Material3 API; horizontal scroll                                                                                               |
| Mode filter handles "ONLINE"/"OFFLINE" strings     | Match against `InferenceMode` enum values (uppercase)                     | DAO stores mode as enum `.name`; UI chip label uses string resources                                                           |

## Risks

| Risk                                                           | Level  | Mitigation                                                                                                                                                                                                                                |
| -------------------------------------------------------------- | ------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `DetectionResult` field additions break existing code          | Low    | Default values (`= 0`, `= 0L`) make new fields backward-compatible; existing camera flow creates results without DB id — still works                                                                                                      |
| Filter state desynchronization                                 | Low    | Class and mode filters are stored in ViewModel state flows; UI updates them via clear setter methods                                                                                                                                      |
| `observeHistoryFiltered` with both filters hits O(n) in-memory | Low    | Typical history size is < 1000 records; in-memory filter is milliseconds                                                                                                                                                                  |
| `JSONObject` serialization of allScores may fail               | Low    | `Map<String, Float>` → `JSONObject` is trivial; try/catch → empty `{}` on failure                                                                                                                                                         |
| Delete all confirmation dialog state lost on rotation          | Medium | Dialog state in Composable, not ViewModel — lost on process death but acceptable for simple confirmation; can use `rememberSaveable` to persist                                                                                           |
| `HistoryRoute` signature change breaks NavHost                 | Low    | NavHost currently doesn't pass `onOpenDetail` to `HistoryRoute` — will need to be updated. However spec says "Prompt 0-4 selesai" and the skeleton is minimal; we add `onOpenDetail` as new param, NavHost update is part of this prompt. |
| NavHost already has History tab wired                          | Medium | Need to verify NavHost call site — skeleton currently takes `onBack`; new signature drops `onBack`, adds `onOpenDetail`. Must read NavHost before implementing.                                                                           |

## Verification

1. `DetectionResult` has `id: Long = 0` and `timestamp: Long = 0L` — existing camera flow still compiles
2. DAO: `deleteById` deletes one record by id; `deleteAll` clears table; `observeByClass`/`observeByMode` return filtered flows
3. Repository: `observeHistoryFiltered(null, null)` ≡ `observeHistory()`; filtered queries return correct subsets
4. ViewModel: `filteredRows` emits updated list when filters change; `deleteItem`/`deleteAll` remove records
5. UI: filter chips highlight correctly, selecting "Semua" clears both filters, selecting a class chip clears mode and vice versa
6. Empty state: 🐄 + message when history is empty
7. Filter empty state: message + clear filter button when filter yields nothing
8. HistoryCard: shows emoji, label, confidence %, mode badge, timestamp, delete button
9. Delete confirmation: AlertDialog appears, cancel dismisses, confirm calls delete
10. Tap card → `onOpenDetail` with correct parameters
11. `formatTimestamp` produces Indonesian-formatted date/time (e.g., "05 Mei 2026, 14:30")
12. Delete all: confirmation dialog → clears all records → shows empty state
