# Architecture Patterns: possession-terminal v1.1 UI Overhaul

**Domain:** Terminal UI inventory manager (Textual ≥0.47.0, Python 3.9+)
**Researched:** 2026-02-24
**Confidence:** HIGH — based on direct source code analysis + Textual API knowledge at ≥0.47.0

---

## Current Architecture (v1.0 Baseline)

```
PossessionApp(App)
  └── on_mount() → push_screen(MainScreen())

MainScreen(Screen)
  ├── Breadcrumb(Static)           [top — drill-down path label]
  ├── DataTable                    [center — grows to fill space]
  ├── Input#filter-input           [hidden — live text filter]
  ├── QuickAddBar(Widget)          [docked bottom — hidden by default]
  │     ├── Input#quickadd-input
  │     └── Input#quickadd-confirm
  └── Input#delete-confirm         [hidden — yes/no confirmation]

EditItemScreen(Screen)             [pushed over MainScreen via push_screen()]
  └── Vertical
        └── [7× Input widgets]
```

**State machine in MainScreen:**
- `_view_mode`: `"rooms" | "containers" | "items"` — single DataTable reused
- `_current_room_id`, `_current_room_name`, `_current_container_id`, `_current_container_name`
- `_delete_pending_id` — tracks which item awaits confirmation

**Key pattern established in v1.0:**
- Hidden widgets toggled with CSS `.hidden` class (filter input, quickadd bar, delete confirm)
- `on_screen_resume()` on MainScreen reloads DataTable when returning from EditItemScreen
- `push_screen() / pop_screen()` for EditItemScreen — full-screen replacement
- `db_path` stored on PossessionApp instance, accessed via `self.app.db_path` in all screens/widgets

---

## Target Architecture (v1.1)

### Component Map: New vs Modified vs Unchanged

```
PossessionApp(App)                          [MODIFIED: splash push, CSS theme]
  ├── SplashScreen(Screen)                  [NEW: push on mount, any-key dismiss]
  └── MainScreen(Screen)                    [HEAVILY MODIFIED: flat list, split layout]
        ├── Header(built-in)                [NEW: replaces Breadcrumb for top bar]
        ├── StatsBar(Static)                [NEW widget: item/room/container/value counts]
        ├── Horizontal                      [NEW layout container]
        │     ├── DataTable                 [MODIFIED: always items, columns fixed]
        │     └── ItemDetailPanel(Widget)   [NEW widget: hidden until Enter]
        ├── Input#filter-input              [UNCHANGED: hidden, live text filter]
        ├── QuickAddBar(Widget)             [MODIFIED: add persistent format label]
        │     ├── Static (format hint)      [NEW: always visible label above input]
        │     ├── Input#quickadd-input
        │     └── Input#quickadd-confirm
        └── Input#delete-confirm            [UNCHANGED]

FilterPickerScreen(ModalScreen)             [NEW: overlays MainScreen, one per filter type]
EditItemScreen(Screen)                      [UNCHANGED]
```

---

## Component Specifications

### 1. SplashScreen — NEW Screen

**File:** `possession/tui/screens/splash.py`

**Pattern:** Standard `Screen` (not Modal — it occupies the full terminal). Dismissed by any keypress.

**Integration point:** `PossessionApp.on_mount()` changes from pushing `MainScreen` directly to pushing `SplashScreen`. `SplashScreen` calls `self.app.switch_screen(MainScreen())` (or `self.dismiss()` if using `push_screen_wait`) on keypress.

**Recommended approach:** Use `switch_screen` from within the splash, not `push_screen`, so the splash is not left on the stack:

```python
# In PossessionApp.on_mount():
self.push_screen(SplashScreen())

# In SplashScreen.on_key():
def on_key(self, event: events.Key) -> None:
    self.app.switch_screen(MainScreen())
```

**Why not ModalScreen:** A modal still renders the screen behind it. Splash should own the full terminal without bleed-through.

**Dependencies:** None — can be built independently. `MainScreen` does not need to change for this.

---

### 2. Top Bar — MODIFIED: use Textual built-in `Header`

**Integration:** Add `Header()` to the top of `MainScreen.compose()`. Textual's `Header` widget renders a top bar with the app title and clock by default. Title comes from `App.TITLE` class attribute.

```python
# In PossessionApp:
TITLE = "Possession"

# In MainScreen.compose():
yield Header()
```

**Why not custom Static:** `Header` is a built-in, handles responsive sizing, and already styled by the active theme. A custom Static bar at height=1 works too but requires manual CSS. `Header` is lower maintenance.

**Breadcrumb fate:** The v1.0 `Breadcrumb` widget is no longer needed once the drill-down state machine is removed and `Header` fills the top bar. Remove `Breadcrumb` from `MainScreen.compose()` and delete `possession/tui/widgets/breadcrumb.py` — or repurpose Breadcrumb as the filter-state indicator (shows active Room/Container/Category filters). This is the better choice: keep `Breadcrumb` but rename its role to "filter context" rather than "navigation path".

---

### 3. StatsBar — NEW widget

**File:** `possession/tui/widgets/statsbar.py`

**Base class:** `Static` — it is a non-interactive label.

**Data it displays:** item count (filtered / total), distinct room count, distinct container count, total value of filtered items.

**How it gets data:** `MainScreen` calls `stats_bar.refresh_stats(items)` after each `_load_view()` / filter application. The widget computes counts from the passed list, not by querying the DB directly. This keeps the widget stateless with respect to DB.

```python
class StatsBar(Static):
    def refresh_stats(self, items: List[dict], total_count: int) -> None:
        rooms = len({i["room_name"] for i in items if i.get("room_name")})
        containers = len({i["container_name"] for i in items if i.get("container_name")})
        total_value = sum(i["cost"] or 0 for i in items if i.get("cost"))
        self.update(
            f"Items: {len(items)}/{total_count}  Rooms: {rooms}  "
            f"Containers: {containers}  Value: ${total_value:.2f}"
        )
```

**Placement:** Yielded in `MainScreen.compose()` after `Header()`, before the `Horizontal` layout block containing DataTable.

**Dependencies:** Flat item list must exist first — `StatsBar.refresh_stats()` expects `items` to be a flat list of item dicts. Build after VIEW-01.

---

### 4. Flat Item List — MODIFIED MainScreen

**What changes in `MainScreen`:**

| Element | v1.0 | v1.1 |
|---------|------|------|
| `_view_mode` state machine | `"rooms" \| "containers" \| "items"` | Removed entirely |
| `_current_room_id`, `_current_room_name` | navigation state | Removed; replaced by `_filter_room_id` |
| `_current_container_id`, `_current_container_name` | navigation state | Removed; replaced by `_filter_container_id` |
| `on_mount` | sets `_view_mode = "rooms"` | calls `list_items()` directly |
| `_load_view()` | 3-branch switch on `_view_mode` | single branch: always `list_items()` |
| `action_go_back` / `q` binding | pops drill-down level | removed or repurposed as app exit |
| `on_data_table_row_selected` | drills into rooms/containers | opens `ItemDetailPanel` |
| `action_edit_item` guard | `if self._view_mode != "items": return` | guard removed |
| `action_delete_item` guard | same | guard removed |
| `_update_breadcrumb()` | updates Breadcrumb widget | removed (no drill-down path to show) |

**New filter state (replaces navigation state):**

```python
self._filter_room_id: Optional[int] = None
self._filter_container_id: Optional[int] = None
self._filter_category_id: Optional[int] = None
self._filter_text: str = ""
self._all_items: List[dict] = []   # full result from list_items()
```

**`_load_view()` becomes `_load_items()`:**

```python
def _load_items(self) -> None:
    self._all_items = list_items(
        self.app.db_path,
        room_id=self._filter_room_id,
        container_id=self._filter_container_id,
    )
    self._apply_filter(self._filter_text)
    self.query_one(StatsBar).refresh_stats(
        self._filtered_items, len(self._all_items)
    )
```

**Note on `list_items()` signature:** The existing `list_items(db_path, room_id=None, container_id=None)` already accepts FK filters. Category filter will need to be added to `models.py` — or filtered client-side from the full result. Client-side filtering is simpler and acceptable for typical inventory sizes (hundreds of items).

---

### 5. FilterPickerScreen — NEW ModalScreen

**File:** `possession/tui/screens/filter_picker.py`

**Base class:** `ModalScreen` — this is the correct Textual class for overlays that render on top of the current screen without replacing it. The underlying MainScreen remains visible behind the modal.

**How ModalScreen works in Textual ≥0.47.0:**
- `ModalScreen` renders its content in a layer above the current screen
- `self.dismiss(result)` closes the modal and passes `result` to the callback
- Caller uses `push_screen_wait()` (async, awaits result) or `push_screen(screen, callback)` (sync with callback)
- The recommended pattern for filter pickers is `push_screen(FilterPickerScreen(choices), self._on_filter_selected)`

**Widget composition inside FilterPickerScreen:**

```python
class FilterPickerScreen(ModalScreen):
    # CSS: center a dialog box, leave background visible
    DEFAULT_CSS = """
    FilterPickerScreen {
        align: center middle;
    }
    FilterPickerScreen > Vertical {
        width: 40;
        height: auto;
        max-height: 20;
        border: solid $primary;
        background: $surface;
        padding: 1;
    }
    """

    def __init__(self, title: str, choices: List[str], **kwargs):
        super().__init__(**kwargs)
        self._title = title
        self._choices = choices
        self._filtered_choices = choices[:]

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static(self._title)
            yield Input(id="picker-search", placeholder="Type to narrow...")
            yield ListView(id="picker-list")

    def on_mount(self) -> None:
        self._populate_list(self._choices)
        self.query_one("#picker-search", Input).focus()

    def _populate_list(self, choices: List[str]) -> None:
        lv = self.query_one("#picker-list", ListView)
        lv.clear()
        for choice in choices:
            lv.append(ListItem(Label(choice)))

    def on_input_changed(self, event: Input.Changed) -> None:
        q = event.value.lower()
        filtered = [c for c in self._choices if q in c.lower()]
        self._populate_list(filtered)
        self._filtered_choices = filtered

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        # Return the selected string to the caller
        idx = self.query_one("#picker-list", ListView).index
        if idx is not None and idx < len(self._filtered_choices):
            self.dismiss(self._filtered_choices[idx])

    def on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            self.dismiss(None)   # None = no selection = clear filter
        elif event.key == "enter":
            # Delegate to list selection
            self.query_one("#picker-list", ListView).action_select()
```

**Caller side in MainScreen:**

```python
BINDINGS = [
    ("r", "pick_room_filter", "Filter Room"),
    ("c", "pick_container_filter", "Filter Container"),
    ("t", "pick_category_filter", "Filter Category"),
    ...
]

def action_pick_room_filter(self) -> None:
    rooms = list_rooms(self.app.db_path)
    choices = [r["name"] for r in rooms]
    self.app.push_screen(
        FilterPickerScreen("Filter by Room", choices),
        self._on_room_filter_selected,
    )

def _on_room_filter_selected(self, result: Optional[str]) -> None:
    if result is None:
        self._filter_room_id = None
    else:
        rooms = list_rooms(self.app.db_path)
        room = next((r for r in rooms if r["name"] == result), None)
        self._filter_room_id = room["id"] if room else None
    self._load_items()
```

**Why ModalScreen not a Widget overlay:** Textual's layout model does not support dynamic z-order layering of widgets within a Screen's compose tree at runtime. `ModalScreen` is the correct primitive for "appears above the current content" — it is rendered as a separate layer by the Textual compositor. A widget approach would require `layers` CSS and manual z-index management, which is fragile.

**Dependencies:** FilterPickerScreen depends on flat item list existing (ARCHITECTURE-4 above). The picker returns a name string; MainScreen resolves it to an ID. This keeps the picker reusable across Room/Container/Category without needing to know IDs.

---

### 6. ItemDetailPanel — NEW widget

**File:** `possession/tui/widgets/detail_panel.py`

**Layout approach:** Side panel using `Horizontal` container in `MainScreen.compose()`. The DataTable takes the left side (`width: 1fr`) and `ItemDetailPanel` takes the right side (fixed width, e.g. `width: 35`). The panel is hidden by default and revealed on Enter.

**Why side panel, not modal Screen:** A modal replaces context (user loses sight of the list). A side panel keeps the list visible for spatial context ("I'm looking at the drill, here are its fields on the right"). This matches the standard file-browser / email-client split-pane interaction model.

**Why not bottom panel:** Vertical split reduces visible rows in the DataTable. A right-side panel preserves all row visibility while using otherwise-empty terminal width.

**Compose structure:**

```python
# In MainScreen.compose():
yield Header()
yield StatsBar(id="stats-bar")
with Horizontal(id="main-body"):
    yield DataTable(cursor_type="row", show_header=True)
    yield ItemDetailPanel(id="detail-panel", classes="hidden")
yield Input(placeholder="Filter...", id="filter-input", classes="hidden")
yield QuickAddBar(id="quickadd-bar", classes="hidden")
yield Input(placeholder="Delete item? [y/N]", id="delete-confirm", classes="hidden")
```

**ItemDetailPanel widget:**

```python
class ItemDetailPanel(Widget):
    DEFAULT_CSS = """
    ItemDetailPanel {
        width: 35;
        border-left: solid $primary;
        padding: 1;
        overflow-y: auto;
    }
    ItemDetailPanel.hidden {
        display: none;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static("", id="detail-content")

    def show_item(self, item: dict) -> None:
        self.remove_class("hidden")
        content = self._format_item(item)
        self.query_one("#detail-content", Static).update(content)

    def hide(self) -> None:
        self.add_class("hidden")

    def _format_item(self, item: dict) -> str:
        lines = [
            f"[bold]{item['name']}[/bold]",
            "",
            f"Description: {item.get('description') or '—'}",
            f"Room:        {item.get('room_name') or '—'}",
            f"Container:   {item.get('container_name') or '—'}",
            f"Category:    {item.get('category_name') or '—'}",
            f"Purchased:   {item.get('purchase_date') or '—'}",
            f"Cost:        {_fmt_cost(item.get('cost')) or '—'}",
        ]
        return "\n".join(lines)
```

**Trigger:** `on_data_table_row_selected` in MainScreen (which previously drilled into rooms) now calls `detail_panel.show_item(item)` instead. A second Enter (or Escape) hides the panel.

**Key binding change:** The `Enter` key on DataTable triggers `on_data_table_row_selected`. This previously navigated the drill-down. In v1.1 it opens the detail panel. The `e` binding opens `EditItemScreen`. These are distinct — no conflict.

**Dependencies:** Flat item list (ARCHITECTURE-4) must be in place first. `ItemDetailPanel.show_item()` receives the same item dict that `_items` already contains.

---

### 7. QuickAddBar Persistent Format Label — MODIFIED widget

**File:** `possession/tui/widgets/quickadd.py` (existing, modified)

**Change:** Add a `Static` label above the `#quickadd-input` Input in `QuickAddBar.compose()`. This replaces the long placeholder text (which disappears as soon as the user types).

```python
def compose(self) -> ComposeResult:
    yield Static(
        "name / description / room / container / category / purchase_date / cost",
        id="quickadd-label",
    )
    yield Input(
        placeholder="",   # placeholder now empty — label carries the hint
        id="quickadd-input",
    )
    yield Input(
        placeholder="Room not found. Create it? [y/N]",
        id="quickadd-confirm",
        classes="hidden",
    )
```

**No structural changes** to the QuickAddBar state machine, open/close logic, or event handlers. This is a pure compose-level addition.

**CSS addition:**

```css
QuickAddBar #quickadd-label {
    color: $text-muted;
    height: 1;
    padding: 0 1;
}
```

---

### 8. Theme and Colors — MODIFIED App CSS

**File:** `possession/tui/app.py`

**Current CSS:**
```css
Screen {
    background: $surface;
}
```

**Target:** Transparent background (terminal shows through), terminal foreground color.

**Textual CSS for transparent background:**

```css
Screen {
    background: transparent;
}
```

Setting `background: transparent` on `Screen` tells Textual not to paint a background — the terminal's own background shows through. This is supported in Textual ≥0.38.0.

**Terminal foreground color:**

```css
Screen {
    background: transparent;
    color: $foreground;
}
```

`$foreground` is the Textual design token that resolves to the terminal's foreground color (white in dark terminals, black in light terminals). Combined with `background: transparent`, this achieves the "terminal theme" look where the app looks native to the terminal rather than imposing its own color scheme.

**Widget-level overrides:** Individual widgets that have explicit `background` set (like `Breadcrumb`'s `background: $primary-darken-2`) will keep their own backgrounds. Only widgets that rely on the Screen's background for their own background will benefit from the transparent rule. This is intentional — the DataTable, StatsBar, and detail panel can use `background: transparent` in their own CSS to continue the effect.

**DataTable transparency:**

```css
DataTable {
    background: transparent;
    height: 1fr;
}
```

**Confidence:** MEDIUM on exact CSS token names for transparent — `background: transparent` is documented Textual behavior but behavior of individual widget backgrounds requires testing.

---

## Data Flow: Filter State

```
User presses 'r'
  → action_pick_room_filter()
  → push_screen(FilterPickerScreen("Filter by Room", room_names), callback)
  → [FilterPickerScreen renders as modal overlay]
  → User types to narrow, presses Enter
  → FilterPickerScreen.dismiss("Kitchen")
  → callback: _on_room_filter_selected("Kitchen")
  → resolve "Kitchen" → room_id=3
  → self._filter_room_id = 3
  → self._load_items()
    → list_items(db_path, room_id=3)
    → self._all_items = [... items in Kitchen ...]
    → self._apply_filter(self._filter_text)   # applies text filter too
    → StatsBar.refresh_stats(filtered_items, total_count)
  → DataTable repopulated
  → Breadcrumb/StatsBar shows "Room: Kitchen" context

User presses 'r' again
  → FilterPickerScreen opens
  → User presses Escape
  → FilterPickerScreen.dismiss(None)
  → callback: _on_room_filter_selected(None)
  → self._filter_room_id = None
  → self._load_items() → shows all items
```

**Filter composability:** Room filter + container filter + category filter + text filter all stack. `_load_items()` passes `room_id` and `container_id` to `list_items()` (DB-side filtering). Category and text filter are applied client-side in `_apply_filter()` for simplicity. This avoids requiring `models.list_items()` to support category FK filtering (though adding it is straightforward if performance demands it).

---

## Component Boundaries

| Component | Owns | Calls | Does NOT own |
|-----------|------|-------|--------------|
| `PossessionApp` | `db_path`, app-level CSS, screen stack | `push_screen()`, `switch_screen()` | Data, widget state |
| `SplashScreen` | ASCII art display | `self.app.switch_screen()` | Nothing from DB |
| `MainScreen` | All filter state (`_filter_*`), `_all_items`, `_filtered_items` | `list_items()`, `list_rooms()`, `list_containers()`, `list_categories()` | Widget internals |
| `StatsBar` | Display-only rendering | Called by MainScreen | DB access |
| `FilterPickerScreen` | Choice list, text narrowing, selection | `self.dismiss()` | Filter state (returned to caller) |
| `ItemDetailPanel` | Item field display | Called by MainScreen | DB access, item selection logic |
| `QuickAddBar` | Input state, confirmation flow | `create_item()`, `create_room()`, `create_container()` | MainScreen state |
| `EditItemScreen` | Edit form state | `update_item()`, resolution helpers | MainScreen state |

---

## Build Order

Dependencies determine order. Each step must be complete before the next starts.

### Step 1: Flat Item List (VIEW-01) — Foundation

**Why first:** All other features depend on items being a flat list. The detail panel, stats bar, and filter pickers all consume the flat item list. The drill-down state machine removal is the single biggest structural change.

**Changes:**
- Remove `_view_mode`, `_current_room_id`, `_current_room_name`, `_current_container_id`, `_current_container_name` from `MainScreen.__init__()`
- Add `_filter_room_id`, `_filter_container_id`, `_filter_category_id`, `_filter_text`, `_all_items`, `_filtered_items`
- Rewrite `_load_view()` to `_load_items()` — single DB call always
- Remove `action_go_back()` and `q` binding (or rebind `q` to app exit directly)
- Remove `on_data_table_row_selected` drill-down logic (repurpose for detail panel later)
- Remove `_update_breadcrumb()` and `Breadcrumb` from compose
- Remove `Breadcrumb` import

**Risk:** This is a destructive change to MainScreen. Do not attempt alongside any other step.

### Step 2: Theme + Top Bar (THEME-01, TOPBAR-01) — Low Risk, High Visibility

**Why second:** Isolated CSS changes. No widget dependencies. Quick win that makes every subsequent step visually validate against the final look.

**Changes:**
- Add `TITLE = "Possession"` to `PossessionApp`
- Add `Header()` to `MainScreen.compose()` top
- Change App-level CSS from `background: $surface` to `background: transparent`
- Add `DataTable { background: transparent }` to MainScreen CSS

### Step 3: StatsBar (STAT-01)

**Why third:** Depends on Step 1 (flat items list exists). Simple new widget with no dependencies of its own.

**Changes:**
- Create `possession/tui/widgets/statsbar.py`
- Add `StatsBar` to `MainScreen.compose()` after `Header`
- Call `StatsBar.refresh_stats()` from `_load_items()` and `_apply_filter()`

### Step 4: ItemDetailPanel (PANEL-01)

**Why fourth:** Depends on Step 1 (flat item list exists and `on_data_table_row_selected` is now free to use for detail panel). Depends on Step 3 being done so the compose layout is stable before adding the Horizontal split.

**Changes:**
- Create `possession/tui/widgets/detail_panel.py`
- Wrap DataTable in `Horizontal` container in `MainScreen.compose()`
- Yield `ItemDetailPanel` inside the `Horizontal` (hidden by default)
- `on_data_table_row_selected` → `detail_panel.show_item(item)` instead of drill-down
- Add Escape handler to hide detail panel

**Layout risk:** Adding `Horizontal` wrapper around DataTable changes the layout model. Test that DataTable still fills available height (`height: 1fr` on DataTable inside Horizontal needs `height: 1fr` on Horizontal too).

### Step 5: Filter Pickers (FILT-01, FILT-02, FILT-03)

**Why fifth:** Depends on Step 1 (filter state exists). Can be done independently of detail panel (Steps 4 and 5 have no dependency on each other — could be parallel phases).

**Changes:**
- Create `possession/tui/screens/filter_picker.py` with `FilterPickerScreen(ModalScreen)`
- Add `r`, `c`, `t` (or chosen keys) bindings to `MainScreen`
- Add `action_pick_room_filter()`, `action_pick_container_filter()`, `action_pick_category_filter()` to `MainScreen`
- Add `_on_room_filter_selected()`, `_on_container_filter_selected()`, `_on_category_filter_selected()` callbacks
- Update `_apply_filter()` to handle `_filter_category_id` client-side

### Step 6: Splash Screen (SPSH-01)

**Why sixth:** Completely isolated from all other steps. No shared state. Can be done at any point after Step 2 (theme) but placed last because it is pure UX polish with zero data dependencies.

**Changes:**
- Create `possession/tui/screens/splash.py`
- Modify `PossessionApp.on_mount()` to push `SplashScreen` instead of `MainScreen`
- `SplashScreen.on_key()` calls `self.app.switch_screen(MainScreen())`

### Step 7: QuickAddBar Format Label (QADD-04)

**Why last for QuickAddBar:** It is the smallest change. The bar already works. This is additive-only within the widget — no integration changes needed beyond the widget file itself.

**Changes:**
- Add `Static(format_hint, id="quickadd-label")` to `QuickAddBar.compose()`
- Clear the `Input` placeholder
- Add CSS for the label

---

## Textual API Notes (Confidence: HIGH for ≥0.47.0)

| API | Usage | Notes |
|-----|-------|-------|
| `ModalScreen` | `FilterPickerScreen` base class | Renders as overlay layer; `dismiss(result)` returns value |
| `push_screen(screen, callback)` | Open filter pickers | Callback receives the `dismiss()` argument |
| `switch_screen(screen)` | Splash → Main transition | Replaces top of stack, does not accumulate |
| `Header()` | Top bar widget | Uses `App.TITLE`; add `show_clock=False` to hide clock |
| `Horizontal` container | DataTable + detail panel split | Both children get CSS width; outer needs `height: 1fr` |
| `ListView` + `ListItem` | Filter picker choice list | Built-in, keyboard navigable |
| `background: transparent` | Theme CSS | Supported; individual widget backgrounds may override |
| `on_screen_resume()` | Reload on return from edit | Already used in v1.0; unchanged |
| `Static.update(content)` | StatsBar, detail panel updates | Supports Rich markup |

**`ListView` import:** `from textual.widgets import ListView, ListItem, Label` — all available in ≥0.47.0.

**`ModalScreen` import:** `from textual.screen import ModalScreen` — available since ≥0.18.0.

---

## Files: New vs Modified vs Deleted

| File | Action | Why |
|------|--------|-----|
| `possession/tui/app.py` | Modified | Add TITLE, change CSS to transparent, change on_mount for splash |
| `possession/tui/screens/main.py` | Heavily modified | Remove drill-down, add flat list, add Horizontal layout |
| `possession/tui/screens/splash.py` | New | SplashScreen implementation |
| `possession/tui/screens/filter_picker.py` | New | FilterPickerScreen(ModalScreen) |
| `possession/tui/screens/edit.py` | Unchanged | No changes needed |
| `possession/tui/widgets/breadcrumb.py` | Deleted (or repurposed) | Drill-down is gone; Header replaces it |
| `possession/tui/widgets/quickadd.py` | Modified | Add persistent label in compose() |
| `possession/tui/widgets/statsbar.py` | New | StatsBar widget |
| `possession/tui/widgets/detail_panel.py` | New | ItemDetailPanel widget |
| `possession/models.py` | Possibly modified | May need category_id filter on list_items() — assess per phase |

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Widget-level Overlay Simulation
**What it is:** Implementing the filter picker as a Widget with absolute positioning and CSS `z-index` layered inside MainScreen's compose tree.
**Why bad:** Textual's layout engine does not honor `z-index` reliably across arbitrary widget trees. Clicks and focus handling don't respect simulated z-order. `ModalScreen` is the framework's intended primitive.
**Instead:** Use `ModalScreen` and `push_screen()`.

### Anti-Pattern 2: Rebuilding `compose()` Dynamically
**What it is:** Calling `remove()` + `mount()` on the DataTable or detail panel to swap them in/out.
**Why bad:** `compose()` runs once at mount. Dynamic `mount()` works but creates lifecycle complexity and flickers. For show/hide, the `.hidden` CSS class pattern (already used in v1.0 for filter input, quickadd, delete confirm) is simpler, faster, and already established in the codebase.
**Instead:** Toggle `.hidden` class on `ItemDetailPanel`, `QuickAddBar`, etc.

### Anti-Pattern 3: DB Queries in Widget Methods
**What it is:** Having `StatsBar` or `ItemDetailPanel` call `list_items()` directly.
**Why bad:** Violates the established pattern where MainScreen owns all DB interaction and passes data to widgets. Creates hidden coupling, makes testing harder, and introduces duplicate queries.
**Instead:** MainScreen calls model functions and passes results to widget update methods.

### Anti-Pattern 4: Keeping the Drill-Down State Machine and Adding Flat View on Top
**What it is:** Adding a new `_view_mode = "flat"` branch while keeping "rooms"/"containers"/"items" branches.
**Why bad:** Doubles the complexity of `_load_view()`, `_apply_filter()`, `on_data_table_row_selected`, and `action_go_back`. The v1.1 goal is to remove the drill-down, not extend it.
**Instead:** Do a clean removal of all drill-down branches in Step 1, then build upward.

### Anti-Pattern 5: Using `push_screen` for Splash
**What it is:** Pushing SplashScreen and then pushing MainScreen on top of it (two screens on stack).
**Why bad:** When MainScreen calls `self.app.pop_screen()`, it would return to SplashScreen. The splash should not be reachable after dismissal.
**Instead:** Use `switch_screen(MainScreen())` from within SplashScreen, or push MainScreen first and overlay SplashScreen as a Modal (either works — the `switch_screen` approach is cleaner).

---

## Sources

- Direct source code analysis: `possession/tui/screens/main.py`, `app.py`, `screens/edit.py`, `widgets/breadcrumb.py`, `widgets/quickadd.py` (2026-02-24)
- Textual API knowledge: ModalScreen, Header, ListView, Horizontal containers — based on Textual ≥0.47.0 (training data, HIGH confidence for APIs that have been stable since ≥0.18.0 for ModalScreen, ≥0.33.0 for Header)
- `background: transparent` in Textual CSS — MEDIUM confidence (documented behavior, recommend smoke-test in Step 2 before committing to it across all widgets)
- `ListView`/`ListItem` in ≥0.47.0 — HIGH confidence (part of core widgets since ≥0.15.0)
