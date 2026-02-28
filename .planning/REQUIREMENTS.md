# Requirements: possession-terminal v1.1

**Defined:** 2026-02-24
**Core Value:** Users can instantly find where any item is stored and know what they own, entirely from the terminal with zero friction.

## v1.1 Requirements

### Navigation

- [x] **VIEW-01**: Main screen shows a flat list of all items by default — no drill-down required to see inventory

### Filtering

- [ ] **FILT-01**: User can filter item list by Room using a VIM-style picker (keyboard-navigable list modal)
- [ ] **FILT-02**: User can filter item list by Container using a VIM-style picker
- [ ] **FILT-03**: User can filter item list by Category using a VIM-style picker

### Interface

- [x] **SPSH-01**: App shows a splash screen with ASCII art ("POSSESSION") on launch; any key dismisses it
- [x] **TOPBAR-01**: A persistent top bar displays the app name "Possession" at all times
- [x] **STAT-01**: A stats bar shows live counts — items (filtered/total), rooms, containers, and total inventory value
- [x] **PANEL-01**: Pressing Enter on an item opens a detail panel showing all item fields

### Theming

- [x] **THEME-01**: App supports terminal-native colors via `--transparent` flag (transparent background + terminal foreground); default remains Textual surface theme

### Quick-Add

- [x] **QADD-04**: Quick-add bar shows a persistent format label (field order hint) that remains visible while the user types

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Export

- **EXPO-01**: User can export full inventory to CSV file
- **EXPO-02**: User can generate a printable inventory report

### Editing

- **ITEM-04**: User can duplicate an existing item with one keypress
- **ITEM-05**: User can undo the last destructive action (delete or edit)

### Filtering (Advanced)

- **FILT-04**: User can apply multiple filters simultaneously (e.g., Room + Category)
- **FILT-05**: Filter pickers support fuzzy/substring matching on large value sets

### Miscellaneous

- **MISC-01**: App supports `--no-splash` flag to skip splash screen at launch
- **MISC-02**: Category filter uses DB-side query (not client-side) for performance at scale

## Out of Scope

| Feature | Reason |
|---------|--------|
| CSV / report export | Deferred to v2 — TUI sufficient for v1 use cases |
| User accounts / auth | Single-user local app by design |
| Web or mobile interface | Terminal-only by design |
| Cloud sync / backup | User manages their own .db file |
| Stacked multi-field filters | Complex UX; single-field pickers sufficient for typical use |

## Traceability

Phases follow on from v1.0 (Phases 1–3 complete). v1.1 adds Phases 4–6.

| Requirement | Phase | Status |
|-------------|-------|--------|
| VIEW-01 | Phase 4 | Complete (04-01) |
| TOPBAR-01 | Phase 4 | Complete (04-01) |
| THEME-01 | Phase 4 | Complete |
| QADD-04 | Phase 4 | Complete |
| SPSH-01 | Phase 4 | Complete |
| STAT-01 | Phase 5 | Complete |
| PANEL-01 | Phase 5 | Complete |
| FILT-01 | Phase 6 | Pending |
| FILT-02 | Phase 6 | Pending |
| FILT-03 | Phase 6 | Pending |

**Coverage:**
- v1.1 requirements: 10 total
- Mapped to phases: 10
- Unmapped: 0 ✓

---
*Requirements defined: 2026-02-24*
*Last updated: 2026-02-25 after 04-01 execution (VIEW-01, TOPBAR-01 complete)*
