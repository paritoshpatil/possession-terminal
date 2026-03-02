---
plan: quick-2
description: Fix UI border and selection colors to use $primary instead of default blue
mode: quick
date: 2026-03-02
---

## Task 1: Override focused Input border color

**Files:** `possession/tui/app.py`
**Action:** Add `Input:focus { border: tall $primary; }` to both `_CSS_DEFAULT` and `_CSS_TRANSPARENT` blocks so all focused Inputs (edit screen fields, filter bar) use the app's primary lavender color instead of Textual's default blue.

## Task 2: Override ListView highlighted item color in FilterPickerScreen

**Files:** `possession/tui/screens/filter_picker.py`
**Action:** Add `#picker-list > ListItem.--highlight { background: $primary; color: $surface; }` to `FilterPickerScreen.DEFAULT_CSS` so the selected row in room/container/category pickers uses `$primary` instead of Textual's default blue accent.
