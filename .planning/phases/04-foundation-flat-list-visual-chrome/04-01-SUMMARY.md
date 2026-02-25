---
phase: 04-foundation-flat-list-visual-chrome
plan: "01"
subsystem: ui
tags: [textual, tui, datatable, flat-list, topbar]

# Dependency graph
requires:
  - phase: 03-manage
    provides: list_items(), delete_item(), EditItemScreen — all used by the new flat MainScreen
provides:
  - Flat-list MainScreen (no drill-down) as load-bearing foundation for Phases 5 and 6
  - Persistent "Possession" top bar (Static widget with topbar CSS)
  - VIEW-01 and TOPBAR-01 requirements satisfied
affects:
  - 04-02 (splash screen plan reads MainScreen structure)
  - 05-data-surface (stats bar and detail panel build on flat-list compose order)
  - 06-keyboard-ux (filter pickers extend _apply_filter items-only branch)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Flat-list pattern: _load_items() → _apply_filter() — single data path, no _view_mode branching"
    - "Dock: top Static widget for persistent header — zero layout impact on DataTable height"
    - "on_screen_resume() reloads flat list on return from any pushed screen (edit, detail, etc.)"

key-files:
  created: []
  modified:
    - possession/tui/screens/main.py

key-decisions:
  - "Removed _view_mode, _current_room_id, _current_room_name, _current_container_id, _current_container_name from MainScreen.__init__() — flat list needs no location state"
  - "Static('Possession', id='topbar') docked at top with height=1 — always visible regardless of DataTable scroll"
  - "on_data_table_row_selected() replaced with single-line return — Enter is a no-op in Phase 4; Phase 5 will wire detail panel"
  - "action_go_back() reduced to self.app.exit() — no drill-down stack to pop"
  - "_apply_filter() now items-only (no three-way rooms/containers/items branch) — Phase 6 pickers will add filter parameters, not branches"

patterns-established:
  - "_load_items() is the sole data-loading method: clear columns, add columns, fetch list_items(), apply filter"
  - "Filter is always active on the flat list — _filter_text preserved across reloads"
  - "Action methods (edit, delete) check row key and look up from self._items directly — no _view_mode guard needed"

requirements-completed: [VIEW-01, TOPBAR-01]

# Metrics
duration: ~5min
completed: 2026-02-25
---

# Phase 4 Plan 01: Foundation — Flat List + Top Bar Summary

**Flat-list MainScreen replacing three-mode drill-down state machine, with persistent "Possession" top bar docked at top using Textual Static widget**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-02-25T00:00:00Z
- **Completed:** 2026-02-25T00:05:00Z
- **Tasks:** 1 implementation task + 1 checkpoint (human-verify)
- **Files modified:** 1

## Accomplishments

- Removed the five-variable drill-down state machine (`_view_mode`, `_current_room_id`, `_current_room_name`, `_current_container_id`, `_current_container_name`) from MainScreen
- Replaced `_load_view()` (three-way branch) with `_load_items()` — single flat load path that always shows all items
- Added `Static("Possession", id="topbar")` as the first composed widget, docked at top — visible at all times
- `action_edit_item()` and `action_delete_item()` now work unconditionally on any selected row (no `_view_mode` guard)
- `_apply_filter()` simplified to items-only filtering — ready for Phase 6 picker parameters
- Breadcrumb import and widget removed from compose(); breadcrumb.py preserved as dead code but not used

## Task Commits

Each task was committed atomically:

1. **Task 1: Remove drill-down state machine — migrate MainScreen to flat list (VIEW-01 + TOPBAR-01)** - `9b1a2a3` (feat)
2. **Task 2: Checkpoint: Verify flat list and top bar work end-to-end** - human-verify, no files modified, approved by user

**Plan metadata:** (see final commit in this plan's docs)

## Files Created/Modified

- `possession/tui/screens/main.py` — Full replacement of drill-down state machine with flat-list architecture; Static topbar added; _load_items(), _apply_filter() (items-only), action_go_back() (exit), on_data_table_row_selected() (no-op) all updated

## Decisions Made

- `_view_mode` and all associated room/container cursor variables removed — the flat list has no concept of "current drill-down location"
- Static `id="topbar"` docked with `height: 1` and `background: $primary-darken-2` — matches app color scheme, zero layout disruption
- `on_data_table_row_selected()` is a no-op in Phase 4; comment documents Phase 5 will wire the detail panel
- `action_go_back()` calls `self.app.exit()` directly — with no drill-down stack there is nothing to pop
- `_apply_filter()` operates on `self._items` (items-only) — Phase 6 filter pickers will pass filter parameters into this method rather than adding branches back

## Deviations from Plan

None — plan executed exactly as written. All ten migration steps completed in a single coordinated edit as specified. Verification checklist (zero occurrences of `_view_mode`, `_current_room`, `Breadcrumb`, `_load_view`, `_update_breadcrumb`) confirmed before commit.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- VIEW-01 and TOPBAR-01 are confirmed working (human-verified)
- Phase 4 Plan 02 (04-02-PLAN.md) can now proceed: splash screen, transparent flag, QuickAddBar format label
- Phase 5 stats bar and detail panel have a stable flat-list compose order to build on
- Phase 6 filter pickers have a clean `_apply_filter()` signature to extend

---
*Phase: 04-foundation-flat-list-visual-chrome*
*Completed: 2026-02-25*
