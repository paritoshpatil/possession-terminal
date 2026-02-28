# Milestones

## v1.1 UI Overhaul (Shipped: 2026-02-28)

**Phases completed:** 3 phases (4–6), 6 plans
**Files changed:** 26 files, +3,791 / -226 lines
**Lines of code:** 1,979 Python
**Timeline:** 2026-02-25 → 2026-02-28 (4 days)
**Git range:** `9b1a2a3` → `03933e3`

**Key accomplishments:**
- Replaced drill-down state machine with flat-list MainScreen — all items visible immediately in a single DataTable with no `_view_mode` branching (VIEW-01, TOPBAR-01)
- Added SplashScreen with ASCII art on launch + `--transparent` CLI flag for terminal-native background colors (SPSH-01, THEME-01)
- QuickAddBar shows persistent format label `name / description / room / container / category / date / cost` above the input at all times (QADD-04)
- Created StatsBar (4-column live aggregate: items, rooms, containers, total value) and DetailPanel widgets with new `get_stats()` SQL query (STAT-01, PANEL-01)
- Wired StatsBar + DetailPanel into MainScreen with Enter-to-toggle side-by-side layout and live updates on every mutation
- Built reusable `FilterPickerScreen(ModalScreen)` — VIM-style modal with type-ahead input, active-item float-to-top, dismiss(result) pattern
- Wired r/c/t filter bindings into MainScreen with SQL-level filtering, StatsBar filter tags, and toggle-to-clear behavior (FILT-01–03)

**Requirements:** 10/10 v1.1 requirements shipped (VIEW-01, FILT-01–03, SPSH-01, TOPBAR-01, STAT-01, PANEL-01, THEME-01, QADD-04)

---

## v1.0 MVP (Shipped: 2026-02-24)

**Phases completed:** 3 phases, 9 plans
**Files changed:** 22 files, 2,212 insertions
**Lines of code:** 1,481 Python
**Timeline:** 2026-02-24 (single session)
**Git range:** `feat(01-foundation-01)` → `feat(03-03)`

**Key accomplishments:**
- pip-installable `possession-terminal` package with SQLite schema (rooms/categories/containers/items), WAL mode, and configurable DB path (--db flag, POSSESSION_DB env var, default ~/.possession)
- 14 CRUD functions across all 4 entities with LEFT JOIN item queries and 21-test pytest suite
- Textual TUI shell with full-screen DataTable, VIM navigation (j/k/G/gg), and updated CLI entry point
- Live filter bar (/), three-level drill-down (rooms→containers→items), and Breadcrumb widget — all bugs caught and fixed during verification
- Quick-add bar (`a`) with slash-separated field parsing and Y/n confirmation when room/container doesn't exist
- EditItemScreen (`e`) with pre-filled form (Ctrl+S saves, Escape cancels) and inline delete confirmation (`d`) — all 6 manage requirements verified on first pass

**Requirements:** 16/16 v1 requirements shipped (DATA-01–04, STOR-01–02, NAV-01–04, QADD-01–03, ITEM-01–03)

---

