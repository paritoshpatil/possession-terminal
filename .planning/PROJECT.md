# possession-terminal

## What This Is

A terminal-based TUI application for home inventory management, built with Python + Textual and backed by a single SQLite file. Users map their home into rooms and containers, then catalog items within them — enabling instant lookups ("where did I put the drill?") and ownership tracking for insurance or auditing purposes.

v1.1 ships a flat item list as the primary view (no drill-down), enriched with a live stats bar, per-item detail panel, VIM-style filter pickers for Room/Container/Category, a splash screen, persistent top bar, and terminal-native color theme via `--transparent` flag.

## Core Value

Users can instantly find where any item is stored and know what they own, entirely from the terminal with zero friction.

## Requirements

### Validated

- ✓ User can create, rename, and delete rooms — v1.0 (DATA-01)
- ✓ User can create, rename, and delete containers within rooms — v1.0 (DATA-02)
- ✓ User can create items with fields: name, description, room, container, category, purchase date, cost — v1.0 (DATA-03)
- ✓ User can manage a list of categories (add, rename, delete) — v1.0 (DATA-04)
- ✓ All data stored in a single SQLite `.db` file — v1.0 (STOR-01)
- ✓ DB path configurable via --db CLI flag or POSSESSION_DB env var — v1.0 (STOR-02)
- ✓ VIM-style navigation (j/k up/down, gg/G top/bottom) — v1.0 (NAV-01)
- ✓ Live filter bar (/ to open, Escape to clear) — v1.0 (NAV-02)
- ✓ Drill-down from rooms → containers → items, q to go back — v1.0 (NAV-03, superseded by v1.1 flat list)
- ✓ Breadcrumb trail showing current navigation location — v1.0 (NAV-04, superseded by v1.1 stats bar)
- ✓ Quick-add bar (`a`) with slash-separated fields, partial entries supported — v1.0 (QADD-01, QADD-02)
- ✓ Confirmation prompt when quick-add references unknown room or container — v1.0 (QADD-03)
- ✓ Inline edit form (`e`) pre-filled with all current field values, Ctrl+S saves — v1.0 (ITEM-01)
- ✓ Delete with confirmation (`d`) — v1.0 (ITEM-02)
- ✓ Moving item by changing room/container in edit form — v1.0 (ITEM-03)
- ✓ Main screen shows flat list of all items by default (no drill-down) — v1.1 (VIEW-01)
- ✓ VIM-style filter pickers for Room, Container, Category — v1.1 (FILT-01, FILT-02, FILT-03)
- ✓ Splash screen with ASCII art on launch, dismiss with any key — v1.1 (SPSH-01)
- ✓ Persistent top bar with "Possession" app name — v1.1 (TOPBAR-01)
- ✓ Stats bar: item count (filtered/total), rooms, containers, total value — v1.1 (STAT-01)
- ✓ Item detail panel on Enter key — v1.1 (PANEL-01)
- ✓ Terminal theme colors — transparent background, terminal foreground — v1.1 (THEME-01)
- ✓ Quick-add persistent format label always visible while typing — v1.1 (QADD-04)

### Active

(None — planning next milestone)

### Out of Scope

| Feature | Reason |
|---------|--------|
| CSV/report export | Deferred to v2 — TUI sufficient for current use cases |
| User accounts / auth | Single-user local app |
| Web or mobile interface | Terminal-only by design |
| Cloud sync / backup | User manages their own .db file |
| Multi-field simultaneous filters | Complex UX; single-field pickers sufficient for typical use (FILT-04) |
| Fuzzy matching in filter pickers | Not needed until filter list grows large (FILT-05) |

## Context

**Shipped v1.1 with 1,979 LOC Python.**
Tech stack: Python 3.9+, Textual ≥0.47.0, SQLite (stdlib), pytest.

- DB init is idempotent (CREATE TABLE IF NOT EXISTS) — re-running never destroys data
- Item FKs use ON DELETE CASCADE for containers (room deleted → container deleted) and ON DELETE SET NULL for items (room/container/category deleted → item preserved with NULL FK)
- `_UNSET` sentinel in models.py distinguishes "don't touch this field" from "set to NULL" for nullable FKs in update_item
- VIM multi-key `gg` tracked with `_last_key` state in on_key handler
- Flat list as primary view — all items visible immediately, no drill-down state machine
- `_load_items()` → `_apply_filter()` is the sole data-loading path; filter IDs passed directly to SQL
- FilterPickerScreen is data-agnostic (receives items list as parameter, never imports models)
- `breadcrumb.py` is dead code — preserved but unused, safe to delete in a future cleanup

## Constraints

- **Tech Stack**: Python + Textual — chosen for rapid TUI development and ease of distribution via pip
- **Database**: SQLite single file — no server, no setup, trivially portable
- **Interface**: Terminal-only — no GUI, no web, no API
- **Python version**: ≥3.9 (3.11+ syntax avoided for compatibility)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Python + Textual over Go/Rust | Faster to build, excellent TUI primitives, easier to extend | ✓ Good — shipped full MVP in one session |
| Single SQLite file | Trivially backupable, portable, no setup | ✓ Good — zero friction for users |
| `/`-separated quick-add | Minimal keystrokes for common add operation | ✓ Good — partial entries work cleanly |
| Prompt on new room/container | Prevents typo-created clutter without blocking flow | ✓ Good — verified by user in UAT |
| requires-python ≥3.9 (not 3.11) | Only Python 3.9 available in dev environment | ✓ Good — Optional[str] used throughout |
| per-call connection pattern in models | Simpler for CLI tool, no concurrent access | ✓ Good — no issues encountered |
| _UNSET sentinel for nullable FKs | None alone is ambiguous for update_item | ✓ Good — clean API for callers |
| Flat list replaces drill-down (v1.1) | Simpler mental model; hierarchy still in data, not nav | ✓ Good — drill-down removed cleanly |
| switch_screen in SplashScreen (v1.1) | Prevents DataTable rendering behind transparent splash | ✓ Good — clean screen transition |
| self.CSS instance override for theme (v1.1) | Simpler than CSS class toggling for two-state theme | ✓ Good — works cleanly |
| FilterPickerScreen data-agnostic (v1.1) | Avoids circular imports, maximizes modal reusability | ✓ Good — one class serves Room/Container/Category |
| SQL-level filtering via list_items() (v1.1) | Cleaner and performant vs client-side filter | ✓ Good — filter IDs passed directly to SQL |
| await lv.clear() in _rebuild_list (v1.1) | Prevents DuplicateIds error on fast type-ahead | ✓ Good — fixed intermittent bug |

---
*Last updated: 2026-02-28 after v1.1 UI Overhaul milestone*
