---
phase: 05-data-surface-stats-bar-detail-panel
plan: "01"
subsystem: ui
tags: [textual, sqlite, tui, widgets, stats, detail-panel]

# Dependency graph
requires:
  - phase: 01-foundation
    provides: possession/models.py with list_items(), get_connection() per-call pattern, items schema
  - phase: 04-flat-list-visual-chrome
    provides: MainScreen with flat item DataTable — Plan 02 will wire StatsBar/DetailPanel here
provides:
  - get_stats() aggregate query returning item_count, room_count, container_count, total_value
  - StatsBar widget with 4-column label/value layout and refresh_stats() method
  - DetailPanel widget with show_item() populating 7 fields with correct fallbacks
affects: [05-02, any future phase using inventory stats or item detail display]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Lazy import of get_stats inside refresh_stats() method avoids circular import risk"
    - "StatsBar uses height:2, not docked — MainScreen yields in normal compose flow to avoid topbar overlap"
    - "DetailPanel uses VerticalScroll for field list — supports future expansion beyond 6 fields"
    - "FIELDS class attribute as list of (field_key, label) tuples — single source of truth for compose and show_item"

key-files:
  created:
    - possession/tui/widgets/statsbar.py
    - possession/tui/widgets/detailpanel.py
  modified:
    - possession/models.py

key-decisions:
  - "StatsBar is not docked — must appear in normal MainScreen compose() flow between topbar and main body (docking causes overlap with topbar)"
  - "get_stats imported lazily inside refresh_stats() to avoid module-level circular import risk"
  - "DetailPanel FIELDS defined as class attribute list of tuples for single source of truth between compose() and show_item()"
  - "COALESCE(SUM(cost), 0.0) handles NULL cost gracefully — no special-casing needed in Python"
  - "COUNT(DISTINCT room_id) excludes NULL room_id — unassigned items don't inflate room count (correct behavior)"

patterns-established:
  - "Lazy import pattern: from possession.models import get_stats inside method body, not module top"
  - "Widget FIELDS class attribute: [(field_key, label)] drives both compose() and show_item() iteration"
  - "Fallback pattern in show_item(): — for missing strings, $0.00 for missing cost"

requirements-completed: [STAT-01, PANEL-01]

# Metrics
duration: 1min
completed: 2026-02-28
---

# Phase 5 Plan 01: Stats Bar + Detail Panel Summary

**SQLite aggregate query (get_stats) and two standalone Textual widgets (StatsBar with 4-column layout, DetailPanel with 7-field show_item) ready for Plan 02 MainScreen wiring**

## Performance

- **Duration:** 1 min
- **Started:** 2026-02-28T06:56:01Z
- **Completed:** 2026-02-28T06:57:13Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments
- Added `get_stats()` to models.py — single SQL query returning item_count, room_count, container_count, total_value with correct NULL handling
- Created StatsBar widget with 4 labeled columns (Items/Rooms/Containers/Value), 2-row label/value layout, and `refresh_stats(db_path)` method
- Created DetailPanel widget with bold title, 6-field VerticalScroll body, and `show_item(item_dict)` with — / $0.00 fallbacks

## Task Commits

Each task was committed atomically:

1. **Task 1: Add get_stats() aggregate query to models.py** - `0cb56b4` (feat)
2. **Task 2: Create StatsBar widget (statsbar.py)** - `9e4152d` (feat)
3. **Task 3: Create DetailPanel widget (detailpanel.py)** - `5acd738` (feat)

**Plan metadata:** (docs commit below)

## Files Created/Modified
- `possession/models.py` - Added get_stats() aggregate query function after list_items()
- `possession/tui/widgets/statsbar.py` - New StatsBar widget with 4-column layout and refresh_stats()
- `possession/tui/widgets/detailpanel.py` - New DetailPanel widget with show_item() for 7 item fields

## Decisions Made
- StatsBar not docked (height: 2 in normal flow) — avoids double-dock overlap with topbar; Plan 02 places it between topbar Static and main Horizontal body
- get_stats imported lazily inside refresh_stats() — prevents circular import if models.py ever imports from widgets
- FIELDS class attribute drives both compose() and show_item() — single source of truth, no duplication
- COALESCE in SQL handles empty DB gracefully — total_value is 0.0 not NULL on empty items table

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None — no external service configuration required.

## Next Phase Readiness
- Plan 02 (05-02) can now import StatsBar and DetailPanel directly and wire them into MainScreen
- StatsBar goes between topbar and main Horizontal in compose() — no docking needed
- DetailPanel goes alongside the DataTable in a Horizontal container
- refresh_stats(self.app.db_path) called on mount and after QuickAdd; show_item(row_dict) called on DataTable row selection

---
*Phase: 05-data-surface-stats-bar-detail-panel*
*Completed: 2026-02-28*
