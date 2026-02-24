# possession-terminal

## What This Is

A terminal-based TUI application for home inventory management, built with Python + Textual and backed by a single SQLite file. Users map their home into rooms and containers, then catalog items within them — enabling both quick lookups ("where did I put the drill?") and ownership tracking for insurance or auditing purposes.

## Core Value

Users can instantly find where any item is stored and know what they own, entirely from the terminal with zero friction.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] User can add items via a quick-add bar using `/`-separated fields: `name / description / room / container / category / purchase date / cost`
- [ ] Item list displays all items with columns: Name, Description, Room/Container, Category, Cost
- [ ] User can navigate the item list with VIM-style keybindings (j/k to move, gg/G for top/bottom)
- [ ] User can search/filter the item list by pressing `/` (VIM-style live filtering)
- [ ] User can drill down into a room to see its containers, and into a container to see its items
- [ ] User can filter from the main screen by room or container
- [ ] When a new room or container is typed in quick-add that doesn't exist, user is prompted to confirm creation
- [ ] User can edit an item (VIM-style `e` binding)
- [ ] User can delete an item (VIM-style `d` binding)
- [ ] All data is stored in a single SQLite file (easy to backup/move)

### Out of Scope

- CSV/report export — deferred to v2
- OAuth or user accounts — single-user local app
- Mobile/web interface — terminal only
- Real-time sync or cloud backup — out of scope

## Context

- **Framework**: Python + Textual (rich TUI framework, fast to build, pip-installable)
- **Storage**: Single SQLite file — user can specify path or use default location
- **Data hierarchy**: House → Rooms → Containers → Items
- **Keybinding philosophy**: VIM-like throughout — `j`/`k` to move, `/` to search, `e` to edit, `d` to delete, `q` to quit/back, `Enter` to drill down
- **Quick-add format**: `item name / description / room / container / category / purchase date / cost` — fields are positional with `/` as separator; partial entries (fewer fields) should be supported

## Constraints

- **Tech Stack**: Python + Textual — chosen for rapid TUI development and ease of distribution via pip
- **Database**: SQLite single file — no server, no setup, trivially portable
- **Interface**: Terminal-only — no GUI, no web, no API

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Python + Textual over Go/Rust | Faster to build, excellent TUI primitives, easier to extend | — Pending |
| Single SQLite file | Trivially backupable, portable, no setup | — Pending |
| `/`-separated quick-add | Minimal keystrokes for common add operation | — Pending |
| Prompt on new room/container | Prevents typo-created clutter without blocking flow | — Pending |

---
*Last updated: 2026-02-24 after initialization*
