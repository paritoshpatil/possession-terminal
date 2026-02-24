# Roadmap: possession-terminal

## Milestones

- ✅ **v1.0 MVP** — Phases 1-3 (shipped 2026-02-24)
- 🚧 **v1.1 UI Overhaul** — Phases 4-6 (in progress)

## Phases

<details>
<summary>✅ v1.0 MVP (Phases 1-3) — SHIPPED 2026-02-24</summary>

- [x] Phase 1: Foundation (2/2 plans) — completed 2026-02-24
- [x] Phase 2: Browse (3/3 plans) — completed 2026-02-24
- [x] Phase 3: Manage (4/4 plans) — completed 2026-02-24

Full details: `.planning/milestones/v1.0-ROADMAP.md`

</details>

<details open>
<summary>🚧 v1.1 UI Overhaul (Phases 4-6) — IN PROGRESS</summary>

- [ ] **Phase 4: Foundation — Flat List + Visual Chrome** - Remove drill-down, add flat list, top bar, splash screen, transparent theme, and corrected quick-add label
- [ ] **Phase 5: Data Surface — Stats Bar + Detail Panel** - Enrich the flat list with live aggregate stats and a per-item detail panel
- [ ] **Phase 6: Keyboard UX — Filter Pickers** - VIM-style modal pickers to narrow the flat list by Room, Container, or Category

### Phase 4: Foundation — Flat List + Visual Chrome

**Goal**: The drill-down state machine is gone; users see all items in a flat list immediately, with top bar, splash screen, and corrected quick-add label.
**Depends on**: Phase 3
**Requirements**: VIEW-01, TOPBAR-01, THEME-01, QADD-04, SPSH-01
**Success Criteria** (what must be TRUE):
  1. Running `python -m possession` shows a splash screen; any key proceeds to main screen
  2. Main screen shows all items in a single flat DataTable (no drill-down rooms/containers view)
  3. Pressing `e` on a selected item opens EditItemScreen; pressing `d` shows delete confirmation; pressing `a` opens QuickAddBar — all work without any `_view_mode` guard
  4. A persistent top bar reading "Possession" is visible at all times
  5. Quick-add bar shows field-order label (e.g. `name / description / room / container / category / date / cost`) that remains visible while typing
  6. Running with `--transparent` flag renders the app with transparent background; default launch uses Textual surface theme
**Plans**: TBD

### Phase 5: Data Surface — Stats Bar + Detail Panel

**Goal**: The flat list is enriched with live stats and per-item detail view.
**Depends on**: Phase 4
**Requirements**: STAT-01, PANEL-01
**Success Criteria** (what must be TRUE):
  1. A stats bar below the top bar shows item count, room count, container count, and total value — updates live when items are added, edited, or deleted
  2. Pressing Enter on a row opens a detail panel showing all fields for that item
  3. The DataTable and detail panel coexist in a side-by-side layout; `j`/`k` navigation continues to work with panel visible
  4. Closing the detail panel (Escape) returns focus to DataTable without cursor reset
**Plans**: TBD

### Phase 6: Keyboard UX — Filter Pickers

**Goal**: Users can narrow the flat list by Room, Container, or Category using VIM-style keyboard-driven modal pickers.
**Depends on**: Phase 5
**Requirements**: FILT-01, FILT-02, FILT-03
**Success Criteria** (what must be TRUE):
  1. Pressing `r` opens a Room filter picker (modal list); selecting a room narrows the item list to that room; pressing Escape cancels without change
  2. Pressing `c` opens a Container filter picker; pressing `t` opens a Category filter picker — same behavior
  3. Active filters are visible in the stats bar (e.g. `[Room: Kitchen]`)
  4. Multiple individual filters stack: e.g. filtering by Room=Kitchen then Category=Tools shows only Tools in Kitchen
  5. Pressing `r`/`c`/`t` when a filter is active re-opens the picker; selecting the already-active value clears the filter
**Plans**: TBD

</details>

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Foundation | v1.0 | 2/2 | Complete | 2026-02-24 |
| 2. Browse | v1.0 | 3/3 | Complete | 2026-02-24 |
| 3. Manage | v1.0 | 4/4 | Complete | 2026-02-24 |
| 4. Foundation — Flat List + Visual Chrome | v1.1 | 0/2 | Not started | - |
| 5. Data Surface — Stats Bar + Detail Panel | v1.1 | 0/2 | Not started | - |
| 6. Keyboard UX — Filter Pickers | v1.1 | 0/2 | Not started | - |
