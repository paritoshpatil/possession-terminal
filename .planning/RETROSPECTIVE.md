# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

---

## Milestone: v1.1 — UI Overhaul

**Shipped:** 2026-02-28
**Phases:** 3 (4–6) | **Plans:** 6 | **Commits:** ~32

### What Was Built

- Flat-list MainScreen replacing three-mode drill-down state machine — all items visible immediately (VIEW-01, TOPBAR-01)
- SplashScreen with ASCII art + `--transparent` CLI flag for terminal-native theme (SPSH-01, THEME-01)
- QuickAddBar persistent format label always visible while typing (QADD-04)
- StatsBar widget with 4-column live aggregate stats (items, rooms, containers, value) + `get_stats()` SQL query (STAT-01)
- DetailPanel widget with `show_item()` for all 7 item fields; Enter-to-toggle side-by-side layout (PANEL-01)
- Reusable `FilterPickerScreen(ModalScreen)` — VIM-style modal with type-ahead, active-item float-to-top
- r/c/t filter bindings in MainScreen with SQL-level filtering, StatsBar tags, toggle-to-clear behavior (FILT-01–03)

### What Worked

- **Phase atomicity**: Each phase built cleanly on the previous — flat list was stable foundation before adding stats bar, which was stable before adding filters. No cross-phase rework needed.
- **Data-agnostic modal**: Designing FilterPickerScreen to receive an items list (not import models) paid off immediately — one class handled Room, Container, and Category pickers without modification.
- **SQL-level filtering**: Passing filter IDs to `list_items()` rather than filtering client-side was the right call — no array iteration, no mismatch between SQL data and displayed data.
- **Plans were well-scoped**: All 6 plans completed without scope deviation. Each plan had clear provides/requires contracts that were honored.

### What Was Inefficient

- **ROADMAP.md checkbox staleness**: Phase 5 checkboxes remained unchecked in ROADMAP.md even after summaries existed on disk, creating a false "in progress" signal. Checkbox tracking and disk tracking diverged.
- **No audit before completing milestone**: Skipped `/gsd:audit-milestone` — all requirements happened to be shipped, but the discipline of verifying cross-phase integration was skipped.
- **breadcrumb.py left as dead code**: The breadcrumb import was removed from compose() but the file was not deleted. Should be cleaned up.

### Patterns Established

- **`_load_items()` as sole data path**: Single method clears columns, fetches `list_items()` with filter IDs, applies text filter — no branching, no view modes. Extending with new filters means adding a parameter, not a branch.
- **ModalScreen with dismiss(result)**: FilterPickerScreen dismisses with `(id, name)` tuple or `None` for cancel — clean async callback pattern for all picker modals.
- **`switch_screen()` not `pop_screen()` for splash**: When the underlying screen should not render while the overlay is visible (especially with transparent theme), `switch_screen` is the right call.
- **`self.CSS` instance override for two-state theme**: Set in `__init__` after `super().__init__()` based on constructor arg — avoids class-level mutation, works cleanly with Textual's CSS resolution.
- **`await lv.clear()` before repopulating ListView**: Essential when rebuilding a list quickly (e.g., on type-ahead input) — prevents DuplicateIds from stale keys.

### Key Lessons

1. **Flat-list architecture is dramatically simpler than drill-down** — the five-variable state machine was replaced by zero state variables. When designing navigation, flat with filters beats hierarchical drill-down for inventory-style data.
2. **Keep modals data-agnostic** — the picker screen doesn't need to know what it's picking; it just needs a list. This made reuse trivial across three filter types.
3. **SQL filtering > client filtering** — always push filtering to the query layer when the data source supports it. The `list_items(room_id, container_id, category_id)` signature was the right API surface.
4. **Textual ListView requires explicit clear before repopulate** — `await lv.clear()` is not automatic; skipping it causes DuplicateIds on fast user input.

### Cost Observations

- Model mix: ~100% sonnet (balanced profile, no opus/haiku used)
- Sessions: ~4 (one per phase, plus milestone completion)
- Notable: All 6 plans executed without scope deviation — planning quality was high relative to execution overhead

---

## Milestone: v1.0 — MVP

**Shipped:** 2026-02-24
**Phases:** 3 (1–3) | **Plans:** 9 | **Sessions:** ~1 (single session)

### What Was Built

- pip-installable `possession-terminal` package with SQLite schema (rooms/categories/containers/items), WAL mode, configurable DB path
- 14 CRUD functions with LEFT JOIN item queries and 21-test pytest suite
- Full-screen Textual DataTable, VIM navigation (j/k/G/gg), three-level drill-down with Breadcrumb
- Quick-add bar (`a`) with slash-separated field parsing and Y/n confirmation
- EditItemScreen (`e`) with pre-filled form, Ctrl+S saves, inline delete confirmation (`d`)

### What Worked

- Single-session MVP delivery — full scope shipped in one focused session
- Test suite caught FK cascade behavior cleanly before shipping
- VIM key navigation pattern established (j/k/gg/G) — consistent across all views

### What Was Inefficient

- Drill-down state machine was complex from the start — five variables to track location became technical debt immediately (removed in v1.1)
- Breadcrumb widget added then superseded — only lived one milestone

### Patterns Established

- `_UNSET` sentinel for nullable FK updates — distinguishes "don't change" from "set to NULL"
- `per-call connection` pattern — open/close SQLite connection per function call (appropriate for CLI tool)
- `_last_key` state for multi-key VIM sequences (gg)

### Key Lessons

1. **Drill-down hierarchy adds complexity without proportional UX benefit** for inventory data — flat + filter is the better model (confirmed by v1.1 refactor).
2. **Single SQLite file is the right choice** — zero setup, trivially backupable, no issues encountered.

### Cost Observations

- Model mix: ~100% sonnet
- Sessions: ~1
- Notable: Full MVP in single session — Textual's component model enabled rapid assembly

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Sessions | Phases | Plans | Key Change |
|-----------|----------|--------|-------|------------|
| v1.0 | ~1 | 3 | 9 | Initial project — rapid single-session delivery |
| v1.1 | ~4 | 3 | 6 | Multi-session; GSD workflow with per-phase planning |

### Cumulative Quality

| Milestone | Tests | LOC Python | New Screens/Widgets |
|-----------|-------|------------|---------------------|
| v1.0 | 21 | 1,481 | DataTable, EditItemScreen, QuickAddBar, Breadcrumb |
| v1.1 | 21 (unchanged) | 1,979 | SplashScreen, StatsBar, DetailPanel, FilterPickerScreen |
