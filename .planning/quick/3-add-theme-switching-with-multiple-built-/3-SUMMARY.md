---
phase: quick-3
plan: "01"
subsystem: tui/settings
tags: [themes, settings, persistence, sqlite, css]
dependency_graph:
  requires: []
  provides: [theme-switching, settings-persistence, transparent-toggle]
  affects: [possession/tui/app.py, possession/tui/screens/main.py]
tech_stack:
  added: []
  patterns: [per-call-sqlite-connection, textual-modal-screen, css-variable-theming]
key_files:
  created:
    - possession/settings.py
    - possession/tui/screens/theme_picker.py
  modified:
    - possession/schema.sql
    - possession/tui/app.py
    - possession/tui/screens/main.py
decisions:
  - Safe fallback to catppuccin-mocha in build_css() for unknown theme names — no crash on bad DB data
  - CLI --transparent flag overrides DB for session only; not persisted — respects one-time override intent
  - apply_theme() persists to DB before calling refresh_css() — ensures restart consistency
  - ListView._nodes._clear() used for in-place rebuild without await — synchronous on_mount compatible
  - t key also works from ThemePickerScreen to toggle transparent live (mirrors the plan's t binding intent)
metrics:
  duration: "2 min"
  completed_date: "2026-03-02"
  tasks_completed: 2
  tasks_total: 2
  files_created: 2
  files_modified: 3
---

# Quick Task 3: Add theme switching with multiple built-in themes — Summary

**One-liner:** Multi-theme CSS switching (5 palettes) with SQLite persistence and transparent toggle via X key in MainScreen.

## What Was Built

### Task 1: Settings persistence module + schema migration

- **`possession/schema.sql`** — Added `settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)` table. Uses `CREATE TABLE IF NOT EXISTS` so existing DBs are safe on startup.
- **`possession/settings.py`** — New module providing:
  - `THEMES` dict: 5 named palettes (catppuccin-mocha, dracula, nord, tokyo-night, gruvbox), each with 6 color keys.
  - `build_css(theme_name, transparent)` — generates full Textual CSS string including all variable declarations ($primary, $panel, $border, $block-cursor-*, $scrollbar-*) plus Screen, DataTable, and cursor rules. Transparent flag controls Screen background. Safe fallback to catppuccin-mocha for unknown names.
  - `get_setting(db_path, key, default)` — per-call SQLite read.
  - `set_setting(db_path, key, value)` — per-call SQLite INSERT OR REPLACE.

### Task 2: ThemePickerScreen modal + app wiring

- **`possession/tui/screens/theme_picker.py`** — `ThemePickerScreen(ModalScreen)`:
  - Takes `db_path`, `current_theme`, `transparent` at init.
  - Renders a 48-wide bordered ListView with `* name` for active theme, `  name` for others.
  - Transparent toggle row at bottom: `[transparent: ON/OFF]`.
  - `j`/`k` navigate the list; `enter` selects a theme and dismisses with `{"theme": name, "transparent": bool}`; `t` toggles transparent live (persists immediately, calls `app.apply_theme()`); `escape` dismisses with None.

- **`possession/tui/app.py`** — Refactored `PossessionApp`:
  - Removed `_CSS_DEFAULT` and `_CSS_TRANSPARENT` class attributes.
  - `__init__` now calls `get_setting()` to load saved theme + transparent from DB, applies CLI `--transparent` as one-time override, assigns `self.CSS = build_css(...)`.
  - New `apply_theme(theme, transparent)` method: persists both settings to DB, rebuilds CSS, calls `self.refresh_css()`.

- **`possession/tui/screens/main.py`** — Updated `MainScreen`:
  - Added `("X", "action_open_theme_picker", "Theme")` to BINDINGS.
  - `action_open_theme_picker()` guarded by `_any_input_active()`, pushes `ThemePickerScreen` with `_on_theme_picked` callback.
  - `_on_theme_picked(result)` calls `self.app.apply_theme(...)` on non-None result.
  - `_FOOTER_TEXT` updated to include `| theme: X`.

## Decisions Made

| Decision | Rationale |
|----------|-----------|
| Safe fallback to catppuccin-mocha in `build_css()` | Prevents crash if DB has corrupted/old theme name |
| CLI `--transparent` not persisted | One-time session override — user intent is explicit per-run flag |
| `apply_theme()` persists before `refresh_css()` | Ensures DB is consistent if refresh_css() were to fail |
| `t` key available in ThemePickerScreen too | Matches plan spec; also natural UX while browsing themes |
| X (capital) for theme binding | Avoids conflict with all existing lowercase bindings |

## Deviations from Plan

None — plan executed exactly as written.

## Self-Check: PASSED

- FOUND: possession/settings.py
- FOUND: possession/tui/screens/theme_picker.py
- FOUND: commit 16dd641 (Task 1)
- FOUND: commit 99a8d10 (Task 2)
