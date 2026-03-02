---
plan: quick-2
status: complete
commit: 3bdb091
date: 2026-03-02
---

## Summary

Fixed three blue-accent UI overrides to use `$primary` (#cba6f7 lavender) consistently.

### Changes

**`possession/tui/app.py`**
- Added `Input:focus { border: tall $primary; }` to both `_CSS_DEFAULT` and `_CSS_TRANSPARENT`
- Covers: edit screen inputs, main screen filter input (`/`), delete-confirm input

**`possession/tui/screens/filter_picker.py`**
- Added `#picker-list > ListItem.--highlight { background: $primary; color: $surface; }` to `FilterPickerScreen.DEFAULT_CSS`
- Covers: highlighted row in room, container, and category picker modals
