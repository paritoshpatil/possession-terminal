# possession-terminal

## What This Is

A terminal-based TUI application for home inventory management, built with Python + Textual and backed by a single SQLite file. Users map their home into rooms and containers, then catalog items within them — enabling instant lookups ("where did I put the drill?") and ownership tracking for insurance or auditing purposes. v1.0 shipped with full CRUD, VIM-style navigation, live filtering, drill-down hierarchy, quick-add bar, and inline edit/delete.

## Core Value

Users can instantly find where any item is stored and know what they own, entirely from the terminal with zero friction.

## Current Milestone: v1.1 UI Overhaul

**Goal:** Rebuild the main screen as a flat item list with filters, add a splash screen, persistent top bar, stats bar, terminal theme colors, item detail panel, and improve the quick-add UX.

**Target features:**
- Flat item list as default view (all items, no drill-down required)
- VIM-style filter pickers for Room, Container, Category
- Terminal theme colors (transparent background, terminal foreground)
- Stats bar showing item count, rooms, containers, total value
- Splash screen with ASCII art on launch (dismiss with any key)
- Persistent top bar with app name
- Item detail panel on Enter
- Quick-add persistent format label (always visible, replaces placeholder)

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
- ✓ Drill-down from rooms → containers → items, q to go back — v1.0 (NAV-03)
- ✓ Breadcrumb trail showing current navigation location — v1.0 (NAV-04)
- ✓ Quick-add bar (`a`) with slash-separated fields, partial entries supported — v1.0 (QADD-01, QADD-02)
- ✓ Confirmation prompt when quick-add references unknown room or container — v1.0 (QADD-03)
- ✓ Inline edit form (`e`) pre-filled with all current field values, Ctrl+S saves — v1.0 (ITEM-01)
- ✓ Delete with confirmation (`d`) — v1.0 (ITEM-02)
- ✓ Moving item by changing room/container in edit form — v1.0 (ITEM-03)

### Active

- [ ] Main screen shows flat list of all items by default (VIEW-01)
- [ ] VIM-style filter pickers for Room, Container, Category (FILT-01, FILT-02, FILT-03)
- [ ] Splash screen with ASCII art on launch, dismiss with any key (SPSH-01)
- [ ] Persistent top bar with "Possession" app name (TOPBAR-01)
- [ ] Stats bar: item count (filtered/total), rooms, containers, total value (STAT-01)
- [ ] Item detail panel on Enter key (PANEL-01)
- [ ] Terminal theme colors — transparent background, terminal foreground (THEME-01)
- [ ] Quick-add persistent format label always visible while typing (QADD-04)
- [ ] Export full inventory to CSV (EXPO-01)
- [ ] Generate printable inventory report (EXPO-02)
- [ ] Duplicate item shortcut
- [ ] Undo last action

### Out of Scope

| Feature | Reason |
|---------|--------|
| CSV/report export | Deferred to v2 — TUI sufficient for v1 use cases |
| User accounts / auth | Single-user local app |
| Web or mobile interface | Terminal-only by design |
| Cloud sync / backup | User manages their own .db file |

## Context

**Shipped v1.0 with 1,481 LOC Python.**
Tech stack: Python 3.9+, Textual ≥0.47.0, SQLite (stdlib), pytest.

- DB init is idempotent (CREATE TABLE IF NOT EXISTS) — re-running never destroys data
- Item FKs use ON DELETE CASCADE for containers (room deleted → container deleted) and ON DELETE SET NULL for items (room/container/category deleted → item preserved with NULL FK)
- `_UNSET` sentinel in models.py distinguishes "don't touch this field" from "set to NULL" for nullable FKs in update_item
- VIM multi-key `gg` tracked with `_last_key` state in on_key handler
- Initial TUI view is rooms (not flat item dump) — spatial hierarchy visible immediately
- Live filter works across all three view modes (rooms, containers, items)

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
| Initial view: rooms (not flat list) | Reflects mental model of physical spaces | ⚠️ Revisit — v1.1 moving to flat list |

---
*Last updated: 2026-02-24 after v1.1 milestone started*
