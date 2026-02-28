# Phase 6: Keyboard UX — Filter Pickers - Context

**Gathered:** 2026-02-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Three keyboard-triggered modal pickers (`r`/`c`/`t`) that narrow the flat list by Room, Container, or Category. Filters stack independently. Active filters display in the stats bar. Re-selecting an active value clears it. Fuzzy search across multiple fields, multi-filter persistence, and advanced picker UX are out of scope.

</domain>

<decisions>
## Implementation Decisions

### Picker visual style
- **Appearance:** Floating modal overlay (centered or left-aligned) with a border, rendered over the main screen. Background dims slightly — command-palette feel.
- **Height:** Fits content, capped at ~10 rows; scrollable for longer lists
- **Type-ahead search:** Yes — a text input at the top of the picker filters the visible options as the user types. `j`/`k` still navigates the filtered list.
- **Confirm/dismiss:** Enter confirms selection and closes picker. Escape closes picker without any change.

### Active filter indication in picker
- When a filter is already set (e.g. Room=Kitchen) and the user presses `r` again, the active value appears with a checkmark marker (e.g. `✓ Kitchen`) and floats to the top of the list
- Pressing Enter on the marked item **clears** the filter (toggle behavior)
- A hint line in the picker explains: "Enter to clear" (when active item is highlighted)

### Filter state in stats bar
- Active filters appended inline to the item count in the existing stats bar row
- Format: `42 items [Room: Kitchen]` or `42 items [Room: Kitchen] [Category: Audio]`
- Stats bar does not grow a new row — filters are part of the same line
- When no filters active: stats bar shows counts only (existing behavior)

### Zero-result and empty states
- **Zero matches:** DataTable shows empty table with a centered message: `No items match the current filters`. Stats bar shows `0 items [Room: X]` — filter tag still visible.
- **Empty picker (no entries):** Picker still opens and shows a single disabled/dimmed row: `No [rooms/containers/categories] yet`. User presses Escape to dismiss.

### Claude's Discretion
- Exact Textual widget used for the floating modal (Screen push vs ModalScreen vs Widget overlay)
- Animation/transition for picker open/close (if any)
- Picker width (full-width vs fixed column width)
- Exact styling of the `✓` marker and hint text
- How `j`/`k` interacts with the type-ahead input focus

</decisions>

<specifics>
## Specific Ideas

- Picker should feel like a command palette — fast to open, type to narrow, Enter to confirm
- The `✓` marker on the active value makes toggle behavior self-evident without needing docs
- Filter tags in the stats bar stay compact — `[Room: Kitchen]` not `Filter: Room = Kitchen`

</specifics>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope

</deferred>

---

*Phase: 06-keyboard-ux-filter-pickers*
*Context gathered: 2026-02-28*
