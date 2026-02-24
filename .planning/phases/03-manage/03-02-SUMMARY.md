---
phase: 03-manage
plan: "02"
subsystem: tui-quickadd
tags: [tui, widget, quickadd, textual, keyboard-driven]
dependency_graph:
  requires: [01-02-SUMMARY.md, 02-02-SUMMARY.md]
  provides: [QuickAddBar widget, quick-add integration in MainScreen]
  affects: [possession/tui/screens/main.py, possession/tui/widgets/quickadd.py]
tech_stack:
  added: []
  patterns: [Textual Widget with Message, deferred imports, slash-separated CLI parsing]
key_files:
  created:
    - possession/tui/widgets/quickadd.py
  modified:
    - possession/tui/screens/main.py
decisions:
  - QuickAddBar hidden by default via CSS class; open()/close() toggle visibility
  - Confirmation flow is stateful (pending_parsed + confirm_mode enum) — no subscreen needed
  - Category auto-create not triggered on missing category; silently stores NULL (only room and container prompt)
  - Escape in QuickAddBar handled by on_key, stopping event propagation so MainScreen gg logic unaffected
metrics:
  duration: "6 min"
  completed: "2026-02-24"
  tasks_completed: 2
  files_changed: 2
---

# Phase 3 Plan 02: Quick-Add Bar Summary

**One-liner:** Keyboard-driven slash-separated item creation with Y/n confirmation for unknown rooms and containers.

## What Was Built

A `QuickAddBar` Textual widget (`possession/tui/widgets/quickadd.py`) that lets users press `a` anywhere in the TUI and type `name / description / room / container / category / purchase_date / cost` to create inventory items without leaving the keyboard.

**Key behaviors:**
- `_parse_quickadd(text)` splits on `/`, strips whitespace, maps up to 7 positional fields; returns `None` if name is empty
- Missing fields default to `None` (only `name` is required)
- If the typed room name doesn't exist in the DB, a confirmation input appears: "Room 'X' not found. Create it? [y/N]"
- Same confirmation for unknown container within the resolved room
- `y` creates the entity and proceeds; any other input dismisses bar without saving
- On successful save, posts `QuickAddBar.ItemSaved` message so `MainScreen.on_quick_add_bar_item_saved` can call `_load_view()` and refresh the DataTable
- Escape closes the bar at any point without saving

**MainScreen changes** (`possession/tui/screens/main.py`):
- `("a", "open_quickadd", "Add")` added to `BINDINGS`
- `QuickAddBar(id="quickadd-bar", classes="hidden")` yielded in `compose()`
- `action_open_quickadd()` and `on_quick_add_bar_item_saved()` added

## Decisions Made

- **Hidden-by-default via CSS class:** `QuickAddBar` starts with `classes="hidden"` passed at yield site in `compose()` and cleared on `open()`. This matches the filter-input pattern already used.
- **Stateful confirmation (no subscreen):** Pending state (`_pending_parsed`, `_pending_room_id`, `_confirm_mode`) tracked as instance attributes on the widget. Avoids pushing a new Screen just for a y/n prompt.
- **Category: no auto-create prompt:** Only rooms and containers prompt before creation. Categories are resolved silently (NULL if not found). This matches plan spec ("list_categories" lookup but no confirmation required).
- **Escape handled in widget, not MainScreen:** `on_key` in `QuickAddBar` intercepts Escape and calls `close()` with `event.stop()`, preventing the MainScreen filter-bar Escape logic from firing simultaneously.

## Deviations from Plan

None - plan executed exactly as written.

## Verification Results

```
python3 -c "from possession.tui.widgets.quickadd import QuickAddBar, _parse_quickadd; ..."  → OK
python3 -c "from possession.tui.screens.main import MainScreen; ..."                        → OK
python3 -m pytest tests/ -x -q                                                              → 21 passed
```

## Self-Check: PASSED

- possession/tui/widgets/quickadd.py: FOUND
- possession/tui/screens/main.py: FOUND
- .planning/phases/03-manage/03-02-SUMMARY.md: FOUND
- Commit 7d99f9a (Task 1): FOUND
- Commit 19dabc2 (Task 2): FOUND
