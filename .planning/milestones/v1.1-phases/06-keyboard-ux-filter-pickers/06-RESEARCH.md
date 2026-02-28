# Phase 6: Keyboard UX — Filter Pickers - Research

**Researched:** 2026-02-28
**Domain:** Textual TUI — modal picker overlay, keyboard navigation, filter state management
**Confidence:** HIGH (codebase is fully readable; all patterns drawn from existing Phase 4/5 code)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Picker visual style**
- Appearance: Floating modal overlay (centered or left-aligned) with a border, rendered over the main screen. Background dims slightly — command-palette feel.
- Height: Fits content, capped at ~10 rows; scrollable for longer lists
- Type-ahead search: Yes — a text input at the top of the picker filters the visible options as the user types. `j`/`k` still navigates the filtered list.
- Confirm/dismiss: Enter confirms selection and closes picker. Escape closes picker without any change.

**Active filter indication in picker**
- When a filter is already set (e.g. Room=Kitchen) and the user presses `r` again, the active value appears with a checkmark marker (e.g. `✓ Kitchen`) and floats to the top of the list
- Pressing Enter on the marked item clears the filter (toggle behavior)
- A hint line in the picker explains: "Enter to clear" (when active item is highlighted)

**Filter state in stats bar**
- Active filters appended inline to the item count in the existing stats bar row
- Format: `42 items [Room: Kitchen]` or `42 items [Room: Kitchen] [Category: Audio]`
- Stats bar does not grow a new row — filters are part of the same line
- When no filters active: stats bar shows counts only (existing behavior)

**Zero-result and empty states**
- Zero matches: DataTable shows empty table with a centered message: `No items match the current filters`. Stats bar shows `0 items [Room: X]` — filter tag still visible.
- Empty picker (no entries): Picker still opens and shows a single disabled/dimmed row: `No [rooms/containers/categories] yet`. User presses Escape to dismiss.

### Claude's Discretion
- Exact Textual widget used for the floating modal (Screen push vs ModalScreen vs Widget overlay)
- Animation/transition for picker open/close (if any)
- Picker width (full-width vs fixed column width)
- Exact styling of the `✓` marker and hint text
- How `j`/`k` interacts with the type-ahead input focus

### Deferred Ideas (OUT OF SCOPE)
- None — discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| FILT-01 | User can filter item list by Room using a VIM-style picker (keyboard-navigable list modal) | `list_rooms()` exists in models.py; `list_items(room_id=...)` already filters at DB layer; ModalScreen pattern fits overlay requirement |
| FILT-02 | User can filter item list by Container using a VIM-style picker | `list_containers()` exists; `list_items(container_id=...)` already supported |
| FILT-03 | User can filter item list by Category using a VIM-style picker | `list_categories()` exists; `list_items(category_id=...)` already supported |
</phase_requirements>

---

## Summary

This phase adds three keyboard-triggered modal pickers (`r` → Room, `c` → Container, `t` → Category) to the existing MainScreen. The data layer is already complete: `list_items()` in `models.py` accepts `room_id`, `container_id`, and `category_id` optional parameters and applies them as SQL `WHERE` conditions. No model changes are needed.

The picker UI is a floating overlay with a type-ahead Input at the top and a scrollable ListView below. Textual's `ModalScreen` is the right mechanism — it pushes onto the screen stack, dims the background automatically, and returns a result to the caller via `dismiss()`. This matches the command-palette feel the user specified and requires no CSS layer-management hacks.

Filter state lives in `MainScreen` as three Optional[int] fields (`_filter_room_id`, `_filter_container_id`, `_filter_category_id`). When any picker confirms a selection, `MainScreen` stores the ID, re-calls `list_items()` with the active filters, and updates the stats bar item-count text to append filter tags. Escape from the picker dismisses with `None` — `MainScreen` receives `None` and makes no change.

**Primary recommendation:** Implement a single reusable `FilterPickerScreen(ModalScreen)` parameterized by title, items list, and current active ID. Use it for all three pickers. Wire `r`/`c`/`t` bindings in `MainScreen` to push the picker and handle the result via `app.push_screen(..., callback)`.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| textual | already installed | ModalScreen, ListView, ListItem, Input | Project uses Textual throughout; ModalScreen is the idiomatic overlay pattern |
| Python stdlib | 3.9+ | Filter state management, string ops | No additional deps needed |

### No New Packages Required

All needed Textual widgets (`ModalScreen`, `ListView`, `ListItem`, `Input`, `Static`, `Label`) are part of the existing `textual` install. `list_rooms()`, `list_containers()`, `list_categories()`, `list_items()` are all already implemented in `possession/models.py`.

**Installation:** None — no new packages.

---

## Architecture Patterns

### Recommended Project Structure

```
possession/tui/
├── screens/
│   ├── main.py          # Add r/c/t bindings + filter state + callback handlers
│   ├── filter_picker.py # NEW: FilterPickerScreen(ModalScreen)
│   ├── edit.py          # unchanged
│   └── splash.py        # unchanged
├── widgets/
│   ├── statsbar.py      # Modify refresh_stats() to accept filter_tags string
│   └── ...              # unchanged
```

### Pattern 1: ModalScreen with dismiss() callback

**What:** Push a ModalScreen onto the Textual screen stack. When the user confirms or cancels, call `self.dismiss(result)`. The caller receives `result` in a callback.

**When to use:** Any overlay that blocks interaction with the screen behind it and needs to return a value. Exactly matches the picker requirement.

**Example:**
```python
# filter_picker.py
from textual.screen import ModalScreen
from textual.app import ComposeResult
from textual.widgets import Input, ListView, ListItem, Label, Static
from textual import events
from typing import Optional, List, Dict

class FilterPickerScreen(ModalScreen):
    """Reusable VIM-style picker modal. Returns selected item dict or None."""

    DEFAULT_CSS = """
    FilterPickerScreen {
        align: center middle;
    }
    #picker-container {
        width: 50;
        max-height: 14;
        border: solid $primary;
        background: $surface;
        padding: 0 1;
    }
    #picker-search {
        width: 1fr;
        height: 1;
        border: none;
        background: $surface-darken-1;
        margin-bottom: 1;
    }
    #picker-list {
        width: 1fr;
        height: auto;
        max-height: 10;
    }
    #picker-hint {
        height: 1;
        color: $text-muted;
        text-align: center;
    }
    """

    def __init__(self, title: str, items: List[Dict], active_id: Optional[int] = None):
        super().__init__()
        self._title = title        # e.g. "Room"
        self._items = items        # list of dicts with 'id' and 'name'
        self._active_id = active_id
        self._filtered: List[Dict] = []

    def compose(self) -> ComposeResult:
        from textual.containers import Vertical
        with Vertical(id="picker-container"):
            yield Static(self._title, id="picker-title")
            yield Input(placeholder="Type to filter...", id="picker-search")
            yield ListView(id="picker-list")
            yield Static("", id="picker-hint")

    def on_mount(self) -> None:
        self._rebuild_list("")
        self.query_one("#picker-search", Input).focus()

    def _rebuild_list(self, query: str) -> None:
        lv = self.query_one("#picker-list", ListView)
        lv.clear()
        q = query.lower().strip()

        # Active item floats to top with checkmark
        active_item = None
        other_items = []
        for item in self._items:
            if item["id"] == self._active_id:
                active_item = item
            else:
                other_items.append(item)

        ordered = ([active_item] if active_item else []) + other_items

        self._filtered = []
        for item in ordered:
            if q and q not in item["name"].lower():
                continue
            self._filtered.append(item)
            marker = "✓ " if item["id"] == self._active_id else "  "
            lv.append(ListItem(Label(f"{marker}{item['name']}"), id=f"item-{item['id']}"))

        if not self._items:
            lv.append(ListItem(Label(f"  No {self._title.lower()}s yet"), disabled=True))
        elif not self._filtered:
            lv.append(ListItem(Label("  (no matches)"), disabled=True))

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "picker-search":
            self._rebuild_list(event.value)

    def on_key(self, event: events.Key) -> None:
        lv = self.query_one("#picker-list", ListView)
        if event.key == "escape":
            self.dismiss(None)
        elif event.key == "j":
            lv.action_cursor_down()
            event.prevent_default()
        elif event.key == "k":
            lv.action_cursor_up()
            event.prevent_default()
        elif event.key == "enter":
            # Confirm highlighted item
            idx = lv.index
            if idx is not None and idx < len(self._filtered):
                self.dismiss(self._filtered[idx])
            event.prevent_default()

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        hint = self.query_one("#picker-hint", Static)
        if event.item is not None:
            item_id_str = event.item.id  # "item-{id}"
            try:
                item_id = int(item_id_str.split("-", 1)[1])
                if item_id == self._active_id:
                    hint.update("Enter to clear filter")
                    return
            except (ValueError, AttributeError, IndexError):
                pass
        hint.update("")
```

### Pattern 2: Filter state in MainScreen

**What:** Store three Optional[int] filter fields on MainScreen. Pass them to `list_items()`. On any change, reload items and update stats bar.

```python
# In MainScreen.__init__
self._filter_room_id: Optional[int] = None
self._filter_container_id: Optional[int] = None
self._filter_category_id: Optional[int] = None

# In MainScreen._load_items()
self._items = list_items(
    self.app.db_path,
    room_id=self._filter_room_id,
    container_id=self._filter_container_id,
    category_id=self._filter_category_id,
)

# New bindings in BINDINGS list
("r", "open_room_picker", "Room Filter"),
("c", "open_container_picker", "Container Filter"),
("t", "open_category_picker", "Category Filter"),
```

### Pattern 3: Push picker and handle result

```python
def action_open_room_picker(self) -> None:
    from possession.models import list_rooms
    rooms = list_rooms(self.app.db_path)
    self.app.push_screen(
        FilterPickerScreen("Room", rooms, self._filter_room_id),
        self._on_room_picked,
    )

def _on_room_picked(self, result: Optional[dict]) -> None:
    if result is None:
        return  # Escape — no change
    if result["id"] == self._filter_room_id:
        self._filter_room_id = None  # Toggle off
    else:
        self._filter_room_id = result["id"]
    self._load_items()
```

### Pattern 4: Stats bar filter tags

**What:** Modify `StatsBar.refresh_stats()` to accept an optional `filter_tags` string appended to the item count.

```python
# In StatsBar.refresh_stats():
def refresh_stats(self, db_path, filter_tags: str = "") -> None:
    from possession.models import get_stats
    stats = get_stats(db_path)
    item_text = str(stats["item_count"])
    if filter_tags:
        item_text = f"{item_text} {filter_tags}"
    self.query_one("#stat-val-items", Static).update(item_text)
    # ... rest unchanged

# In MainScreen._refresh_stats():
def _refresh_stats(self) -> None:
    tags = self._build_filter_tags()
    self.query_one(StatsBar).refresh_stats(self.app.db_path, filter_tags=tags)

def _build_filter_tags(self) -> str:
    parts = []
    if self._filter_room_id is not None:
        # Look up name from self._items (or cache separately)
        name = self._get_filter_name("room_name")
        parts.append(f"[Room: {name}]")
    if self._filter_container_id is not None:
        name = self._get_filter_name("container_name")
        parts.append(f"[Container: {name}]")
    if self._filter_category_id is not None:
        name = self._get_filter_name("category_name")
        parts.append(f"[Category: {name}]")
    return " ".join(parts)
```

### Pattern 5: Zero-match empty state

**What:** When `self._items` is empty after a filtered `list_items()` call, show a centered message row in the DataTable.

**Approach:** After `_apply_filter()` if `table.row_count == 0` and any filter is active, add a single spanning informational row:

```python
# In _apply_filter(), after the loop:
if table.row_count == 0 and self._any_filter_active():
    table.add_row(
        "No items match the current filters", "", "", "", "",
        key="__empty__",
    )
```

### Anti-Patterns to Avoid

- **Using a custom Widget overlay instead of ModalScreen:** Without ModalScreen, the picker won't dim the background and keyboard events will leak to MainScreen. Use ModalScreen — it handles both automatically.
- **Re-fetching rooms/containers/categories from DB on every keypress in type-ahead:** Fetch once on picker open, filter the in-memory list. The list is small (typical: < 100 entries).
- **Storing filter names separately from filter IDs:** Look up display names from `self._items` rows (which already have `room_name`, `container_name`, `category_name` from the LEFT JOIN). No extra DB query needed for the stats bar tag text.
- **Putting `r`/`c`/`t` bindings outside the DataTable focus context:** These keys should only fire when the DataTable is focused (not when filter-input, delete-confirm, or quickadd-bar are open). The existing `on_key` escape-priority ladder pattern (already in MainScreen) handles this — pickers should not be openable while other inputs are active.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Background dimming on picker open | CSS layer + z-index hack | `ModalScreen` | Textual handles compositor stacking automatically |
| Returning a value from overlay to caller | Custom message/event bus | `self.dismiss(result)` + callback in `push_screen()` | Built-in ModalScreen contract; clean, type-safe |
| Scrollable list with keyboard navigation | Custom DataTable or manual scroll | `ListView` + `ListItem` | Textual ListView has built-in cursor, scroll, and highlighted event |

**Key insight:** Textual's `ModalScreen` + `ListView` + `dismiss()` pattern is purpose-built for exactly this use case. Any custom approach adds complexity without benefit.

---

## Common Pitfalls

### Pitfall 1: `j`/`k` conflicting with ListView's own keyboard handling
**What goes wrong:** ListView has its own `up`/`down` arrow key handling, but `j`/`k` won't work by default inside it. If focus is on ListView, `j` types "j" into nothing. If focus is on the Input, `j`/`k` types into the search field.
**Why it happens:** Focus is either on Input (type-ahead) or ListView (navigation), not both simultaneously.
**How to avoid:** Keep focus on the Input always. Handle `j`/`k` in `FilterPickerScreen.on_key()` and call `lv.action_cursor_down()` / `lv.action_cursor_up()` programmatically. Call `event.prevent_default()` so the key doesn't propagate to Input.
**Warning signs:** `j` appearing in the search field when user expects cursor to move.

### Pitfall 2: ModalScreen receiving `r`/`c`/`t` key events from parent
**What goes wrong:** While picker is open, pressing `r` again might try to open a second picker.
**Why it happens:** Textual event bubbling — key events propagate up the DOM. ModalScreen blocks pointer events but not all key routing.
**How to avoid:** ModalScreen intercepts key events at the screen level. No extra guard needed — Textual's screen stack means the picker screen receives keys first and they don't reach MainScreen while the modal is on top.

### Pitfall 3: Stats bar item count shows unfiltered total
**What goes wrong:** `get_stats()` returns global `item_count` (all items), but stats bar should show filtered count.
**Why it happens:** `get_stats()` has no filter parameters.
**How to avoid:** Set the item-count stat to `len(self._items)` (the filtered list) rather than `stats["item_count"]` from `get_stats()`. Pass `len(self._items)` into `refresh_stats()` or compute it there from `self._items`.

### Pitfall 4: Filter tag name lookup fails when list is empty
**What goes wrong:** `_build_filter_tags()` tries to find `room_name` from `self._items`, but if zero items match, `self._items` is empty — no row to look up the name from.
**Why it happens:** We use items rows to get filter display names, but filtered items are empty.
**How to avoid:** Cache filter display names at the time the picker selection is made (`_on_room_picked` etc.), not at stats-refresh time. Store `self._filter_room_name: Optional[str] = None` alongside `self._filter_room_id`.

### Pitfall 5: Existing `/` text-filter and new picker filters conflicting
**What goes wrong:** `_apply_filter(self._filter_text)` runs against `self._items`, which is now the DB-filtered set. Text filter still works correctly (it filters the already-filtered list), but clearing a picker filter via toggle reloads items — any active text filter in `#filter-input` should still apply.
**Why it happens:** `_load_items()` calls `_apply_filter(self._filter_text)` — so existing text filter is re-applied automatically on every load. This is correct behavior; no special handling needed.
**Warning signs:** Text filter disappearing after picker selection. (Should not happen given current code structure.)

---

## Code Examples

### Opening a picker from MainScreen

```python
# Source: Textual ModalScreen pattern — textual.screen.ModalScreen.dismiss()
def action_open_room_picker(self) -> None:
    from possession.models import list_rooms
    from possession.tui.screens.filter_picker import FilterPickerScreen
    rooms = list_rooms(self.app.db_path)
    self.app.push_screen(
        FilterPickerScreen("Room", rooms, self._filter_room_id),
        self._on_room_picked,
    )

def _on_room_picked(self, result: Optional[dict]) -> None:
    if result is None:
        return
    if result["id"] == self._filter_room_id:
        self._filter_room_id = None
        self._filter_room_name = None
    else:
        self._filter_room_id = result["id"]
        self._filter_room_name = result["name"]
    self._load_items()
```

### Updated _load_items() with filter parameters

```python
def _load_items(self) -> None:
    table = self.query_one(DataTable)
    try:
        table.clear(columns=True)
    except TypeError:
        table.clear()
    table.add_columns("Name", "Description", "Location", "Category", "Cost")
    self._items = list_items(
        self.app.db_path,
        room_id=self._filter_room_id,
        container_id=self._filter_container_id,
        category_id=self._filter_category_id,
    )
    self._apply_filter(self._filter_text)
    self._refresh_stats()
```

### Escape priority ladder — add picker guard

```python
# In MainScreen.on_key, before existing escape checks:
# (No change needed — ModalScreen captures escape before MainScreen sees it)
```

### Bindings additions

```python
BINDINGS = [
    ("j", "cursor_down", "Down"),
    ("k", "cursor_up", "Up"),
    ("G", "cursor_bottom", "Bottom"),
    ("g", "cursor_top_gg", "Top"),
    ("/", "open_filter", "Filter"),
    ("r", "open_room_picker", "Room"),
    ("c", "open_container_picker", "Container"),
    ("t", "open_category_picker", "Category"),
    ("a", "open_quickadd", "Add"),
    ("e", "edit_item", "Edit"),
    ("d", "delete_item", "Delete"),
    ("q", "go_back", "Back"),
]
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Custom overlay widgets with CSS z-index | `ModalScreen` in Textual | Textual 0.20+ | No manual compositor management |
| Passing data between screens via globals | `dismiss(result)` + `push_screen(callback)` | Textual 0.30+ | Type-safe, stack-clean result passing |

---

## Open Questions

1. **Should `c` (Container) be blocked if no Room filter is active?**
   - What we know: CONTEXT.md says filters stack independently. Container picker should show ALL containers regardless of room filter.
   - What's unclear: Is it confusing to show containers from all rooms when a room filter is active?
   - Recommendation: Show all containers unconditionally for simplicity — matches "filters stack independently" and keeps the picker uniform. This is in-scope.

2. **Stats bar item count: `len(self._items)` vs `get_stats()["item_count"]`**
   - What we know: `get_stats()` always returns the global unfiltered count. The stats bar currently shows that value.
   - Recommendation: When filters are active, replace item count with `len(self._items)` (filtered count). When no filters active, use `stats["item_count"]` as before (identical value, consistent source). Pass `item_count_override: Optional[int]` into `refresh_stats()`.

---

## Sources

### Primary (HIGH confidence)
- Codebase direct read: `possession/tui/screens/main.py` — existing MainScreen architecture, escape priority ladder, `_apply_filter` pattern, `_load_items` pattern
- Codebase direct read: `possession/models.py` line 328 — `list_items()` already accepts `room_id`, `container_id`, `category_id` optional filter parameters
- Codebase direct read: `possession/tui/widgets/statsbar.py` — current `refresh_stats()` signature and widget structure
- Codebase direct read: `possession/models.py` — `list_rooms()`, `list_containers()`, `list_categories()` exist and return `List[Dict]`
- Textual documentation (training knowledge, Textual 0.40+): `ModalScreen`, `ListView`, `ListItem`, `dismiss()`, `push_screen(screen, callback)` — these are stable Textual APIs

### Secondary (MEDIUM confidence)
- STATE.md accumulated decisions — confirms `ModalScreen` hasn't been used yet, `push_screen` used for EditItemScreen (same pattern applies)
- CONTEXT.md — all picker UX decisions are locked and directly inform implementation

### Tertiary (LOW confidence)
- None

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new packages; all APIs from existing codebase and stable Textual
- Architecture: HIGH — directly derived from existing MainScreen patterns (escape ladder, `_apply_filter`, `push_screen` for EditItemScreen)
- Pitfalls: HIGH — derived from reading actual code; focus/event pitfall is a known Textual pattern issue

**Research date:** 2026-02-28
**Valid until:** 2026-03-30 (Textual APIs are stable; codebase patterns won't change mid-phase)
