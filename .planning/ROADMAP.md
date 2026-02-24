# Roadmap: possession-terminal

## Overview

Three phases deliver a working terminal inventory manager. Phase 1 builds the foundation: SQLite schema and all data model operations for rooms, containers, categories, and items. Phase 2 builds the browsing experience: the TUI with VIM navigation, live filtering, drill-down hierarchy, and breadcrumbs. Phase 3 completes the management loop: quick-add bar, item editing, deletion, and moving items between locations. After Phase 3, the core value is fully delivered — users can find any item instantly from the terminal.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Foundation** - SQLite database, schema, and all data model CRUD (rooms, containers, categories, items) (completed 2026-02-24)
- [x] **Phase 2: Browse** - TUI item list with VIM navigation, live filtering, drill-down hierarchy, and breadcrumbs (completed 2026-02-24)
- [ ] **Phase 3: Manage** - Quick-add bar, inline edit, delete with confirmation, and move item

## Phase Details

### Phase 1: Foundation
**Goal**: The data layer is in place — all entities can be stored, retrieved, and managed
**Depends on**: Nothing (first phase)
**Requirements**: STOR-01, STOR-02, DATA-01, DATA-02, DATA-03, DATA-04
**Success Criteria** (what must be TRUE):
  1. Running the app creates (or opens) a single `.db` SQLite file at the default path or a user-specified path via env var or CLI flag
  2. Rooms can be created, renamed, and deleted via the data layer without data loss
  3. Containers can be created, renamed, and deleted within a room
  4. Items can be created with all 7 fields (name, description, room, container, category, purchase date, cost)
  5. Categories can be added, renamed, and deleted
**Plans**: 2 plans

Plans:
- [x] 01-01-PLAN.md — Python package scaffold, SQLite schema, and DB initialization with configurable path
- [ ] 01-02-PLAN.md — CRUD operations for rooms, containers, items, and categories with pytest suite

### Phase 2: Browse
**Goal**: Users can see their full inventory and navigate it entirely from the keyboard
**Depends on**: Phase 1
**Requirements**: NAV-01, NAV-02, NAV-03, NAV-04
**Success Criteria** (what must be TRUE):
  1. The item list displays all items with Name, Description, Room/Container, Category, and Cost columns
  2. User can move through the list with `j`/`k` and jump to top/bottom with `gg`/`G`
  3. Pressing `/` opens a live filter bar — typing narrows the item list in real time, `Escape` clears it
  4. Pressing `Enter` on a room drills into its containers; pressing `Enter` on a container shows its items; pressing `q` goes back one level
  5. A breadcrumb trail at the top reflects the current drill-down location (e.g. `Garage > Tool Cabinet`)
**Plans**: 3 plans

Plans:
- [x] 02-01-PLAN.md — TUI app shell, DataTable with VIM navigation (NAV-01)
- [x] 02-02-PLAN.md — Live filter bar, drill-down hierarchy, breadcrumb widget (NAV-02, NAV-03, NAV-04)
- [ ] 02-03-PLAN.md — Human verification checkpoint for end-to-end browse experience

### Phase 3: Manage
**Goal**: Users can add, edit, delete, and move items entirely from the keyboard with minimal friction
**Depends on**: Phase 2
**Requirements**: QADD-01, QADD-02, QADD-03, ITEM-01, ITEM-02, ITEM-03
**Success Criteria** (what must be TRUE):
  1. User can type a `/`-separated string (e.g. `drill / Black & Decker / Garage / Tool Cabinet / Tools`) and have the item saved
  2. Partial quick-add entries (fewer than 7 fields) are accepted without error
  3. If a quick-add references a room or container that does not exist, the user is prompted to confirm creation before the item is saved
  4. Pressing `e` on a selected item opens an inline form pre-filled with all current field values; saving updates the item
  5. Pressing `d` on a selected item shows a confirmation prompt; confirming removes the item permanently
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation | 2/2 | Complete    | 2026-02-24 |
| 2. Browse | 2/3 | Complete    | 2026-02-24 |
| 3. Manage | 0/TBD | Not started | - |
