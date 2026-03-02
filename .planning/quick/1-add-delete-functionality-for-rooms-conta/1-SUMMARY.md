---
phase: quick
plan: 1
subsystem: tui-picker
tags: [delete, filter-picker, models, ux]
dependency_graph:
  requires: []
  provides: [room-delete-in-picker, container-delete-in-picker, category-delete-in-picker]
  affects: [possession/models.py, possession/tui/screens/filter_picker.py, possession/tui/screens/main.py]
tech_stack:
  added: []
  patterns: [inline-delete-confirmation, dismiss-with-result-type]
key_files:
  created: []
  modified:
    - possession/models.py
    - possession/tui/screens/filter_picker.py
    - possession/tui/screens/main.py
decisions:
  - "Delete confirmation is inline in picker modal (not a separate screen) — consistent with existing QuickAddBar and delete-confirm patterns"
  - "Dismiss result uses deleted=True sentinel key to distinguish deletion from normal selection"
  - "Navigation fully blocked while in delete confirm mode — only y/n/escape accepted"
  - "Hint line shows 'd to delete' for all non-active items so users discover the shortcut"
metrics:
  duration: "~5 min"
  completed_date: "2026-03-02"
  tasks_completed: 2
  files_changed: 3
---

# Quick Task 1: Add Delete Functionality for Rooms, Containers, Categories - Summary

**One-liner:** Inline 'd' delete flow in FilterPickerScreen with impact confirmation, using new count_room_contents and count_container_items model helpers.

## What Was Built

Users can now press 'd' on any highlighted entry in the Room, Container, or Category picker to delete it directly from within the picker modal, without leaving the TUI.

### Task 1: count_room_contents and count_container_items (cbffed1)

Two new query helpers added to `possession/models.py`:

- `count_room_contents(db_path, room_id) -> {"containers": int, "items": int}` — counts containers directly in the room and items assigned to the room
- `count_container_items(db_path, container_id) -> {"items": int}` — counts items in the container

Both use the project's standard per-call connection pattern with sqlite3.Row factory.

### Task 2: FilterPickerScreen delete flow + MainScreen wiring (eaf5002)

**FilterPickerScreen changes (`possession/tui/screens/filter_picker.py`):**
- Constructor now accepts `db_path: Optional[Path]` and `kind: str` ("room"/"container"/"category")
- New state: `_delete_mode` (bool) and `_delete_candidate` (Optional[Dict])
- New `_get_impact_line(item)` method builds context-specific impact message:
  - Room: "This will also delete N container(s) and M item(s) will lose their room."
  - Container: "This will remove N item(s) from this container."
  - Category: "Items with this category will have their category cleared (not deleted)."
- `on_key` updated with delete mode guard at top — blocks all navigation, only responds to y/n/escape
- Pressing 'd' in normal mode sets `_delete_mode = True`, shows `#picker-delete-confirm` Static widget
- Pressing 'y' dispatches to delete_room/delete_container/delete_category (ValueError caught if already gone), then dismisses with `{"deleted": True, "id": ..., "name": ...}`
- Pressing 'n' or Escape resets delete mode and hides confirmation widget
- Hint line now shows `[dim]d to delete[/dim]` for non-active items (previously empty string)
- New `#picker-delete-confirm` Static widget in compose() with appropriate CSS

**MainScreen changes (`possession/tui/screens/main.py`):**
- All three picker call-sites updated to pass `db_path=self.app.db_path` and `kind="room"/"container"/"category"`
- `_on_room_picked`, `_on_container_picked`, `_on_category_picked` each gain a `result.get("deleted")` guard before existing toggle logic — clears filter if the deleted entity was the active filter, then reloads
- `_FOOTER_TEXT` updated to "add: a | edit: e | delete item: d | rooms: r | containers: c | categories: t | details: enter | close: esc | quit: q"

## Deviations from Plan

None - plan executed exactly as written.

## Self-Check

Files created/modified:
- FOUND: possession/models.py (count_room_contents, count_container_items added)
- FOUND: possession/tui/screens/filter_picker.py (delete flow added)
- FOUND: possession/tui/screens/main.py (call-sites and callbacks updated)

Commits:
- cbffed1: feat(quick-1): add count_room_contents and count_container_items model helpers
- eaf5002: feat(quick-1): add delete flow to FilterPickerScreen and update MainScreen call-sites

## Self-Check: PASSED
