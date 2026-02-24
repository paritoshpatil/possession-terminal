---
phase: 03-manage
plan: "01"
subsystem: models
tags: [crud, sqlite, items, update, delete]
dependency_graph:
  requires: []
  provides: [update_item, delete_item]
  affects: [possession/tui/screens/main.py]
tech_stack:
  added: []
  patterns: [sentinel-object, dynamic-sql-builder, per-call-connection]
key_files:
  created: []
  modified:
    - possession/models.py
    - tests/test_models.py
decisions:
  - "_UNSET sentinel used for room_id/container_id/category_id to distinguish 'do not change' from 'set to NULL' — None alone is ambiguous for nullable FK fields"
  - "Dynamic SET clause built from (column, value) pairs — only passed fields included in UPDATE"
metrics:
  duration: "4 min"
  completed: "2026-02-24"
  tasks_completed: 2
  files_modified: 2
---

# Phase 03 Plan 01: update_item and delete_item Model Functions Summary

**One-liner:** Partial-update and delete CRUD functions for items using _UNSET sentinel to handle nullable FK fields correctly.

## What Was Built

Two new functions added to `possession/models.py`:

- `update_item(db_path, item_id, name, description, room_id, container_id, category_id, purchase_date, cost)` — builds a dynamic UPDATE statement from only the fields the caller explicitly passes. Uses `_UNSET` sentinel (module-level `object()`) for the three nullable FK fields so that passing `None` means "set to NULL" while omitting the argument means "don't touch this field".
- `delete_item(db_path, item_id)` — issues `DELETE FROM items WHERE id=?`, raises `ValueError` if rowcount is 0 (item not found).

Both follow the established per-call connection pattern (open / execute / commit / close in finally).

## Tasks Completed

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1 | Add update_item and delete_item to models.py | 0f84700 | possession/models.py |
| 2 | Add pytest coverage for update_item and delete_item | f5cb3c5 | tests/test_models.py |

## Tests

21 total tests pass (15 pre-existing + 6 new):

- `test_update_item_name` — name field updated
- `test_update_item_partial` — other fields untouched when only description passed
- `test_update_item_clear_room` — passing `room_id=None` correctly NULLs the column
- `test_update_item_not_found` — `ValueError` on nonexistent id
- `test_delete_item` — item removed from DB
- `test_delete_item_not_found` — `ValueError` on nonexistent id

## Decisions Made

1. `_UNSET = object()` sentinel at module level for room_id/container_id/category_id — `None` is a valid value meaning "clear this FK" so a separate sentinel is needed to mean "caller did not pass this argument"
2. Dynamic SET clause built from `(column, value)` pairs list — only columns with non-UNSET values are included in the SQL UPDATE

## Deviations from Plan

None — plan executed exactly as written.

## Self-Check

- [x] possession/models.py modified with update_item and delete_item
- [x] tests/test_models.py updated with 6 new test cases
- [x] Commit 0f84700 exists (feat: add update_item and delete_item)
- [x] Commit f5cb3c5 exists (test: add pytest coverage)
- [x] All 21 tests pass
