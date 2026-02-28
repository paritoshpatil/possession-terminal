---
phase: 05-data-surface-stats-bar-detail-panel
plan: "02"
subsystem: ui
tags: [textual, tui, main-screen, stats-bar, detail-panel, horizontal-layout]

# Dependency graph
requires:
  - phase: 05-01
    provides: StatsBar widget with refresh_stats(), DetailPanel widget with show_item(), get_stats() aggregate query
  - phase: 04-flat-list-visual-chrome
    provides: MainScreen with flat DataTable, topbar Static, filter input, QuickAddBar, delete-confirm pattern
provides:
  - MainScreen with StatsBar in normal compose flow (below topbar, above Horizontal body)
  - Horizontal(id="main-body") container with DataTable (7fr) + DetailPanel (3fr) split
  - _refresh_stats() called at end of every _load_items() — live stats on every mutation
  - on_data_table_row_selected() toggling DetailPanel display open/closed
  - on_data_table_row_highlighted() updating DetailPanel live as cursor moves
  - Escape hierarchy: panel > delete-confirm > filter > app exit
affects: [any future phase modifying MainScreen, Phase 6 pickers/filters]

# Tech tracking
tech-stack:
  added: [textual.containers.Horizontal]
  patterns:
    - "Horizontal container for 70/30 fractional split: DataTable(7fr) + DetailPanel(3fr)"
    - "panel.display = not panel.display for toggle — works with existing .hidden CSS (display: none)"
    - "on_data_table_row_highlighted guarded by if not panel.display: return — no-op when panel closed"
    - "Escape hierarchy via on_key: panel first, then delete-confirm, then filter, then fall through to binding"

key-files:
  created: []
  modified:
    - possession/tui/screens/main.py

key-decisions:
  - "DetailPanel toggle uses panel.display = not panel.display — simpler than add/remove_class for binary visible/hidden"
  - "on_data_table_row_highlighted always fires; guard with if not panel.display prevents wasted show_item() calls when panel closed"
  - "Escape chain prepends panel check before existing delete-confirm and filter checks — no refactor of existing logic needed"
  - "self.query_one(DataTable).focus() called after hiding panel to restore keyboard navigation"
  - "QuickAdd confirm prompt hidden-behind-main-input bug fixed inline (db47eb5) — visible confirm input was obscured by main input"

patterns-established:
  - "Display toggle pattern: panel.display = not panel.display (no class manipulation needed for single widget)"
  - "Row-key lookup: next((i for i in self._items if str(i['id']) == row_key_str), None) — safe, no KeyError"
  - "Escape hierarchy: ordered if-chain in on_key, each branch calls event.prevent_default() and returns"

requirements-completed: [STAT-01, PANEL-01]

# Metrics
duration: ~15min
completed: 2026-02-28
---

# Phase 5 Plan 02: MainScreen Wiring Summary

**StatsBar + DetailPanel wired into MainScreen: 70/30 Horizontal split, live stats on every _load_items(), Enter toggles panel, j/k updates live, Escape hierarchy closes panel before exiting app**

## Performance

- **Duration:** ~15 min (including human verify checkpoint)
- **Started:** 2026-02-28
- **Completed:** 2026-02-28
- **Tasks:** 2 (1 auto + 1 checkpoint:human-verify)
- **Files modified:** 1 (main.py) + 1 bug fix (main.py)

## Accomplishments
- Updated `compose()` to yield StatsBar in normal flow and wrap DataTable + DetailPanel in `Horizontal(id="main-body")` for 70/30 fractional split
- Added `_refresh_stats()` method called at end of every `_load_items()` — stats update automatically after every add/edit/delete
- Implemented `on_data_table_row_selected()` to toggle panel open/closed; `on_data_table_row_highlighted()` to update panel live as cursor moves
- Extended `on_key()` Escape chain to check panel first, preserving existing delete-confirm and filter dismiss behavior
- Fixed QuickAdd confirm-prompt visibility bug (main input was hiding confirm input) — caught during checkpoint verify

## Task Commits

Each task was committed atomically:

1. **Task 1: Wire StatsBar + DetailPanel into MainScreen** - `e612113` (feat)
2. **Bug fix: hide main input when showing confirm prompt** - `db47eb5` (fix)

**Plan metadata:** (docs commit below)

## Files Created/Modified
- `possession/tui/screens/main.py` - Updated compose() layout, added _refresh_stats(), on_data_table_row_selected() toggle, on_data_table_row_highlighted() live update, extended on_key() Escape hierarchy

## Decisions Made
- `panel.display = not panel.display` for toggle — direct attribute assignment, no class manipulation needed
- `on_data_table_row_highlighted` guarded with `if not panel.display: return` — prevents unnecessary show_item() calls when panel is closed
- Escape chain implemented as ordered if-chain in on_key(), each branch calls `event.prevent_default()` and returns — no refactor of existing logic required
- `self.query_one(DataTable).focus()` called after every panel hide to restore keyboard navigation

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] QuickAdd confirm prompt hidden by main input widget**
- **Found during:** Task 2 (human-verify checkpoint — user-reported during testing)
- **Issue:** When QuickAdd enters confirm mode, the confirm Input widget was obscured because the main QuickAddBar input was still visible on top of it
- **Fix:** Added logic to hide the main input when the confirm prompt is shown, and restore it when confirm is dismissed
- **Files modified:** `possession/tui/screens/main.py`
- **Verification:** QuickAdd confirm flow tested end-to-end — confirm prompt now visible and functional
- **Committed in:** `db47eb5` (fix(quickadd): hide main input when showing confirm prompt)

---

**Total deviations:** 1 auto-fixed (Rule 1 - bug fix)
**Impact on plan:** Bug fix was necessary for QuickAdd usability. No scope creep — existing feature corrected.

## Issues Encountered
- QuickAdd confirm prompt was not visible due to main input overlap — discovered during human-verify checkpoint, fixed inline as deviation Rule 1 bug fix.

## User Setup Required
None — no external service configuration required.

## Next Phase Readiness
- Phase 5 complete: stats bar and detail panel fully wired and verified working end-to-end
- All Phase 5 requirements met: STAT-01 (stats bar with live counts), PANEL-01 (detail panel with j/k live update)
- MainScreen is stable for Phase 6 (pickers/filters) — Horizontal layout and panel display pattern are established

---
*Phase: 05-data-surface-stats-bar-detail-panel*
*Completed: 2026-02-28*
