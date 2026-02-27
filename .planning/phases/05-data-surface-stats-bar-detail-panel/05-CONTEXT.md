# Phase 5: Data Surface — Stats Bar + Detail Panel - Context

**Gathered:** 2026-02-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Enrich the flat list with two new surfaces: a live stats bar between the top bar and the DataTable, and a per-item detail panel that opens on Enter. Stats reflect all items (no filtering — that's Phase 6). Filters, search, and editing are out of scope.

</domain>

<decisions>
## Implementation Decisions

### Stats bar content & position
- Display four counts: items, rooms, containers, and total value
- Format: labeled columns — label on top, value below (two-row style)
  e.g.: `Items  Rooms  Containers  Value`
        `42     8      12          $1,240.00`
- Total value shows `$0.00` when no items have a cost entered (never hidden)
- Position: between the "Possession" top bar and the DataTable

### Detail panel layout
- 70/30 split — DataTable gets 70%, panel gets 30%
- Panel shows ALL fields: name, description, room, container, category, date acquired, cost
- Item name displayed as a bold panel title at the top
- Subtle vertical divider separates panel from DataTable

### Panel open/close behavior
- Enter **toggles** the panel — opens if closed, closes if already open
- When panel is open and j/k moves to a new row, the panel **updates live** to show the new item
- Escape closes the panel (only) when panel is open; Escape exits app when panel is already closed
- Panel is **closed by default** on launch — full-width DataTable until user opens it

### Empty field display
- Blank optional fields render as `FieldName: —` (dash, not hidden)
- Cost when not entered renders as `$0.00` (not dash — consistent with stats bar)
- Field labels styled in `$text-muted`, field values in default text color
- Layout: left-aligned label + colon + value on the same line
  e.g.: `Room: Kitchen`
        `Description: —`
        `Cost: $0.00`

### Claude's Discretion
- Exact CSS/Textual widget used for the stats bar columns
- Vertical divider implementation (CSS border vs dedicated widget)
- Reactive update mechanism for live stats (watch vs on_mount signal)
- Panel scroll behavior if item has very long description

</decisions>

<specifics>
## Specific Ideas

- Stats bar styled as labeled columns — label row on top, value row below — not a single inline string
- Panel content uses `Label: value` on each line with muted label styling, consistent across all fields
- No field is hidden — sparse items still show all field rows (with `—` or `$0.00`)

</specifics>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope

</deferred>

---

*Phase: 05-data-surface-stats-bar-detail-panel*
*Context gathered: 2026-02-27*
