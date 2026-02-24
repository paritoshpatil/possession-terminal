# Requirements: possession-terminal

**Defined:** 2026-02-24
**Core Value:** Users can instantly find where any item is stored and know what they own, entirely from the terminal with zero friction.

## v1 Requirements

### Data Model

- [x] **DATA-01**: User can create, rename, and delete rooms
- [x] **DATA-02**: User can create, rename, and delete containers within rooms
- [x] **DATA-03**: User can create items with fields: name, description, room, container, category, purchase date, cost
- [x] **DATA-04**: User can manage a list of categories (add, rename, delete)

### Quick-Add

- [ ] **QADD-01**: User can add an item from a quick-add bar using `/`-separated fields (name / description / room / container / category / purchase date / cost)
- [ ] **QADD-02**: Quick-add supports partial entries (not all 7 fields required)
- [ ] **QADD-03**: When quick-add references a non-existent room or container, user is prompted to confirm creation before the item is saved

### Navigation

- [x] **NAV-01**: User can navigate lists with `j`/`k` (up/down) and `gg`/`G` (top/bottom) VIM-style keybindings
- [x] **NAV-02**: User can filter the item list live by pressing `/` then typing a query
- [x] **NAV-03**: User can drill down from the main item list into a room view, then into a container view (Enter to drill in, `q` to go back)
- [x] **NAV-04**: A breadcrumb trail displays the current navigation location (e.g. `Garage > Tool Cabinet`)

### Item Management

- [ ] **ITEM-01**: User can edit any item field via an inline form (triggered by `e` key)
- [ ] **ITEM-02**: User can delete an item with a confirmation prompt (triggered by `d` key)
- [ ] **ITEM-03**: User can move an item to a different room or container

### Storage

- [x] **STOR-01**: All data is stored in a single SQLite `.db` file
- [x] **STOR-02**: User can configure the database file path via environment variable or CLI flag

## v2 Requirements

### Export

- **EXPO-01**: User can export full inventory to CSV
- **EXPO-02**: User can generate a printable inventory report

### Advanced Search

- **SRCH-01**: User can filter items by multiple fields simultaneously (e.g. room AND category)
- **SRCH-02**: User can sort item list by any column

## Out of Scope

| Feature | Reason |
|---------|--------|
| CSV/report export | Deferred to v2 — TUI sufficient for v1 use cases |
| User accounts / auth | Single-user local app |
| Web or mobile interface | Terminal-only by design |
| Cloud sync / backup | Out of scope — user manages their own .db file |
| Duplicate item | Deferred to v2 — not essential for core use |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| DATA-01 | Phase 1 | Complete |
| DATA-02 | Phase 1 | Complete |
| DATA-03 | Phase 1 | Complete |
| DATA-04 | Phase 1 | Complete |
| STOR-01 | Phase 1 | Complete (01-01) |
| STOR-02 | Phase 1 | Complete (01-01) |
| NAV-01 | Phase 2 | Complete |
| NAV-02 | Phase 2 | Complete |
| NAV-03 | Phase 2 | Complete |
| NAV-04 | Phase 2 | Complete |
| QADD-01 | Phase 3 | Pending |
| QADD-02 | Phase 3 | Pending |
| QADD-03 | Phase 3 | Pending |
| ITEM-01 | Phase 3 | Pending |
| ITEM-02 | Phase 3 | Pending |
| ITEM-03 | Phase 3 | Pending |

**Coverage:**
- v1 requirements: 16 total
- Mapped to phases: 16
- Unmapped: 0

---
*Requirements defined: 2026-02-24*
*Last updated: 2026-02-24 after roadmap creation*
