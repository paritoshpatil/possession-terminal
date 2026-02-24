# Feature Landscape: possession-terminal v1.1 UI Overhaul

**Domain:** Terminal UI inventory manager (Python + Textual)
**Researched:** 2026-02-24
**Scope:** New features only — v1.0 features (DataTable, VIM nav, live filter, drill-down, QuickAddBar, EditItemScreen, delete confirmation) are already shipped and excluded.

---

## Table Stakes

Features users expect from a flat-list TUI app. Missing = product feels incomplete or regressive from v1.0.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Flat item list as default view | Drill-down requires knowing the location of an item; flat list enables "find anything" from the start | Low | Models already support `list_items()` with no filters; MainScreen already has the items view mode — this is a state machine default change + query change |
| Stats bar (counts + total value) | Standard in inventory/catalog tools; users need summary at a glance without counting rows | Low-Medium | Pure computed display from existing DB data; no new DB schema needed |
| Persistent top bar with app name | Standard branding in TUI apps; orients the user at all times | Low | Textual's `Header` widget works out of the box; alternatively a `Static` docked to top |
| Item detail panel on Enter | Table rows are narrow; a detail panel is the standard pattern for exposing full field data without a modal | Medium | Requires panel layout (horizontal split or bottom panel), content rendering, dismiss behavior |
| Quick-add persistent format label | Placeholder text disappears on first keystroke; users forget the field order (`name/desc/room/container/category/date/cost`) | Low | Replace placeholder with a `Static` label above the Input, always visible |

## Differentiators

Features that elevate the UX beyond baseline expectations for a terminal inventory tool.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| VIM-style filter pickers (Room, Container, Category) | Keyboard-first filter without leaving the table; popups show only valid values (no typos, no "room not found" friction) | Medium-High | Requires a new ModalScreen subclass per picker type, or one generic picker; type-to-narrow loop inside the modal; callback to apply filter to MainScreen |
| Splash screen with ASCII art | Sets app identity on launch; standard convention in TUI tools (htop-like); zero cost after implementation | Low | Textual ModalScreen shown on first mount, dismissed on any key via `on_key`; ASCII art is static text |

## Anti-Features

Features to explicitly NOT build in v1.1.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Retain drill-down navigation as primary UX | Flat list is the new default; drill-down adds a second mental model and two different navigation modes that contradict each other | Remove or gate the drill-down: if flat list is the default, `q` going back through rooms → containers → items is no longer meaningful. Keep filter pickers as the replacement. |
| Fuzzy / substring match in filter pickers | Pickers show a small, known set of values (rooms, containers, categories); fuzzy matching adds implementation complexity for minimal gain | Use exact prefix match (type narrows the visible list, Enter selects highlighted item) |
| Multiple simultaneous filter pickers | Applying room AND category filter in a single flow increases UX complexity and state management burden | Apply one filter at a time; stacking filters can be v1.2 |
| Animated splash screen | ANSI animation in Textual is non-trivial and the value is purely aesthetic | Static ASCII art, dismiss on any key |

---

## Per-Feature UX Behavior Specifications

### Feature 1: Flat Item List as Default View (VIEW-01)

**What changes:**
- App opens directly to the items view showing ALL items (no drill-down entry screen).
- Columns: Name | Location (`Room > Container`) | Category | Cost. Description is secondary — consider truncation or omitting from the main table (it's visible in the detail panel).
- The `_view_mode` state machine in `MainScreen` should default to `"items"` with `_current_room_id=None` and `_current_container_id=None`, which already triggers the full-item query in `_load_view()`.

**Filter behavior in flat mode:**
- The live text filter (`/`) still works — it already searches across all item fields in the `"items"` view mode.
- VIM-style field pickers (Feature 2) apply an additional SQL-level filter to `list_items()`.
- These two filter mechanisms stack: active picker filter narrows the DB query; live text filter narrows the rendered rows further.

**Existing code touch points:**
- `MainScreen.__init__`: change `self._view_mode = "rooms"` to `"items"`.
- `MainScreen.on_mount`: change `self._view_mode = "rooms"` to `"items"` (same line, ~line 83).
- `on_data_table_row_selected`: the `"rooms"` and `"containers"` drill-down branches become dead code — remove or gate them.
- `action_go_back`: the back-navigation state machine becomes irrelevant in flat mode; `q` can exit the app directly.
- `_update_breadcrumb`: simplify or replace with stats bar / filter indicator instead.

**Complexity:** Low. The data model and query already support this. It is a state machine default change and UI reorganization.

---

### Feature 2: VIM-Style Filter Pickers (FILT-01, FILT-02, FILT-03)

**Concept:**
A keyboard-triggered popup (Textual `ModalScreen`) showing a vertical list of filter values. The user types to narrow the list (prefix/substring match on the displayed names), moves with `j`/`k`, and presses Enter to apply. Escape clears/dismisses without changing the filter.

**Trigger keys (recommended):**
- `r` → Room picker
- `c` → Container picker
- `t` → Category picker (avoids `c` collision if both are needed; or use `R`, `C`, `T`)
- Escape inside picker → dismiss, no filter change
- Enter inside picker → apply selected value as filter, reload table

**Picker modal layout:**
```
+---------------------------+
| Filter by Room            |
| > [type to narrow...]     |
|---------------------------|
| Garage                    |
| Kitchen          (cursor) |
| Living Room               |
| Office                    |
+---------------------------+
```

- Title line: "Filter by Room / Container / Category"
- Input at top of modal (auto-focused on open): typed characters narrow the list below
- List below: rendered as a `ListView` or `DataTable`; j/k or arrow keys navigate
- Selected item highlighted
- Enter: dismiss modal, post a message to MainScreen with the selected ID
- Escape: dismiss modal, no change
- "All" row at top of list: clears the active filter for that field

**MainScreen state to add:**
```python
self._filter_room_id: Optional[int] = None
self._filter_container_id: Optional[int] = None
self._filter_category_id: Optional[int] = None
```
These IDs are passed as kwargs to `list_items()` which already accepts them.

**Active filter indicator:**
When a filter is active, display it in the stats bar or a status line, e.g., `[Room: Garage]  [Category: Electronics]`. This replaces the breadcrumb trail from the drill-down era.

**Textual implementation pattern:**
```python
class FilterPickerModal(ModalScreen):
    def __init__(self, title: str, items: list[dict], **kwargs): ...
    # compose: Static(title) + Input(id="picker-search") + ListView/DataTable
    # on_input_changed: filter the list
    # on_key("enter"): dismiss(selected_item_id)
    # on_key("escape"): dismiss(None)
```
`ModalScreen.dismiss(value)` passes the value back to the caller's callback. This is the standard Textual pattern since v0.20+. Confirmed available in Textual >=0.47.0.

**Complexity:** Medium-High.
- One reusable `FilterPickerModal` widget (not three separate classes)
- Three key bindings on MainScreen (`r`, `c`, `t`)
- State management for three active filters
- Filter indicator display
- `list_items()` already accepts `room_id`, `container_id`, `category_id` — no DB changes needed

**Dependency:** VIEW-01 (flat list must be the default for pickers to make sense as the primary filter UX)

---

### Feature 3: Item Detail Panel (PANEL-01)

**Concept:**
Pressing Enter on a highlighted row in the DataTable opens a detail view showing all fields for that item. The user presses Escape (or Enter again, or `q`) to dismiss.

**Panel positioning — two options:**

**Option A: Right-side panel (horizontal split)**
```
+-------------------+---------------------------+
| Name     Location | Name: Power Drill         |
| Drill    Garage   | Description: 18V cordless |
| Hammer   Kitchen  | Room: Garage              |
| ...               | Container: Tool Cabinet   |
|                   | Category: Tools           |
|                   | Purchased: 2023-06-12     |
|                   | Cost: $89.99              |
+-------------------+---------------------------+
```
- Always visible once an item is selected; updates as cursor moves.
- More screen real estate used at all times.
- Common pattern in file managers (e.g., Ranger, nnn with preview).

**Option B: Bottom panel (vertical split)**
```
+-------------------------------------------+
| Name        Location      Category  Cost  |
| Power Drill Garage > TC   Tools    $89.99 |
| Hammer      Kitchen       —         —     |
+-------------------------------------------+
| Name: Power Drill   Description: 18V cord.|
| Room: Garage        Container: Tool Cab.  |
| Category: Tools     Purchased: 2023-06-12 |
| Cost: $89.99                              |
+-------------------------------------------+
```
- Only visible when Enter is pressed; table shrinks.
- Less disruptive to the default layout.
- Requires show/hide toggling and layout height management.

**Recommendation: Option B (bottom panel)**
- More consistent with the existing layout (everything stacks vertically: header → table → panel → quickadd/filter).
- Simpler implementation: toggle a `Static` widget docked to bottom, update its content on Enter, collapse on Escape.
- The panel does not need to be a new Screen — it is a widget within MainScreen.

**Content to show in detail panel:**
```
Name: [value]          Description: [value or "—"]
Room: [value or "—"]   Container: [value or "—"]
Category: [value or "—"]  Cost: [value or "—"]
Purchased: [value or "—"]
```
Use two-column label/value layout with Rich markup for label coloring.

**Dismiss behavior:**
- Escape: collapse panel, return focus to DataTable.
- Enter on same row (toggle): re-pressing Enter collapses (debatable; Escape is cleaner).
- `e` key: if panel is open, open EditItemScreen for that item (natural next action).

**Existing code touch points:**
- `on_data_table_row_selected`: currently a no-op for items view; this is where panel-open logic goes.
- New widget: `ItemDetailPanel(Static)` or `ItemDetailPanel(Widget)` with `show(item: dict)` and `hide()` methods.
- CSS: panel height (5-7 lines), hidden by default.
- Conflict to resolve: currently `on_data_table_row_selected` drills into rooms/containers — since drill-down is removed in VIEW-01, the event handler is free for the detail panel.

**Complexity:** Medium.
- New widget (ItemDetailPanel), toggle logic, focus management.
- No new DB queries needed; item data is already in `self._items`.

**Dependency:** VIEW-01 (flat list default; Enter is currently consumed by drill-down)

---

### Feature 4: Stats Bar (STAT-01)

**Concept:**
A persistent single-line bar showing aggregate inventory data. Updates whenever the data or filters change.

**Content:**
```
Items: 47 (12 filtered)   Rooms: 5   Containers: 18   Total Value: $2,341.50
```

- "Items: N (M filtered)" — total items in DB vs. items currently visible after filter.
- "Rooms: N" — count of rooms in DB (not filtered).
- "Containers: N" — count of containers in DB.
- "Total Value: $N" — sum of `cost` for all visible items (respects active filters), or all items if no filter. Items with `NULL` cost are excluded from the sum.

**Positioning:**
Docked below the persistent top bar, above the DataTable. Alternatively, docked below the DataTable above the QuickAddBar. Below the table is more natural for summary data (summary comes after content).

Recommended layout stack (top to bottom):
```
[Top bar / Header — app name]
[DataTable — main content]
[Stats bar — summary]
[Detail panel — hidden by default, appears above stats bar on Enter]
[QuickAddBar — hidden by default]
[Filter input — hidden by default]
```

**Update trigger:**
Refresh stats bar on every `_load_view()` call. Stats bar reads from `self._items` (already loaded) for visible count and sum, and makes two cheap `COUNT(*)` queries for total rooms and containers.

**Textual implementation:**
```python
class StatsBar(Static):
    DEFAULT_CSS = """
    StatsBar { height: 1; padding: 0 1; }
    """
    def update_stats(self, visible_items, total_items, rooms, containers, total_value): ...
```

**Complexity:** Low-Medium.
- New `StatsBar` widget (simple `Static` subclass).
- Two extra queries (`COUNT(*)` on rooms and containers) per load cycle.
- Value sum computed from already-loaded `self._items`.

**Dependency:** VIEW-01 (needs flat list to compute meaningful "filtered" count). No dependency on Feature 2 or 3.

---

### Feature 5: Splash Screen (SPSH-01)

**Concept:**
On app launch, before MainScreen is visible, show a full-screen ASCII art display of the app name. Press any key to dismiss and proceed to the main interface.

**Textual implementation pattern:**
- `SplashScreen(ModalScreen)` — shown as the first screen via `self.push_screen(SplashScreen())` before `MainScreen`, or shown on top of `MainScreen` immediately after mount.
- Compose: single `Static` widget with centered ASCII art and a "Press any key to continue" footer.
- Dismiss: `on_key` handler calls `self.dismiss()` or `self.app.pop_screen()`.
- The `ModalScreen` approach overlays on top of whatever is beneath — using it before pushing MainScreen means MainScreen loads in background (data may already be ready when splash dismisses).

**ASCII art for "POSSESSION":**
The app name is the natural content. A blocky font rendered in plain ASCII (no Unicode box-drawing) is the most portable:
```
 ____   ____  _____ _____ _____ _____ _____ _____  ____  _   _
|  _ \ / __ \/ ___// ____/ ____/ ____|_   _/ ____|/ __ \| \ | |
| |_) | |  | \__ \| (___| (___ | |___  | || |  _ | |  | |  \| |
|  __/| |  | |___) \___  \___  \  ___| | || | |_ || |  | | . ` |
| |   | |__| |___/ /___) |___) | |___ _| || |__| || |__| | |\  |
|_|    \____/_____/_____/_____/|_____|_____\_____| \____/|_| \_|
```
Or a simpler word-mark. The exact art is a design decision, not a behavior constraint.

**Dismiss behavior:**
- Any key (including Enter, Space, Escape, letter keys) dismisses.
- Mouse click can also dismiss (optional).
- Splash should NOT show if app is invoked with `--no-splash` flag (out of scope for v1.1 but worth noting as a future escape hatch).

**UX conventions from TUI ecosystem:**
- htop shows a splash/header on first run (dismissed immediately).
- Neovim has a startup screen (`:intro`) that clears on first input.
- Standard pattern: splash is a transient `ModalScreen` or custom `Screen` displayed for a fixed duration OR until keypress. Keypress is preferred (respects slow terminal startup).

**Complexity:** Low.
- New `SplashScreen` class (~20-30 lines).
- `PossessionApp.on_mount` pushes SplashScreen before or instead of MainScreen.
- ASCII art string is a module-level constant.

**Dependency:** None. Fully independent of all other features.

---

### Feature 6: Persistent Top Bar (TOPBAR-01)

**Concept:**
An always-visible single-line bar at the top of the screen displaying the app name "Possession". Never scrolls away. Acts as branding and orientation anchor.

**Textual options:**

**Option A: Textual built-in `Header` widget**
- Usage: `yield Header()` in `PossessionApp.compose()` (app level, not screen level).
- Automatically displays the app's `TITLE` attribute.
- Shows clock on the right by default (`show_clock=True`); set `show_clock=False` for clean look.
- Clicking the header opens the command palette by default — may need to disable.
- Fixed height: 1 line (or 3 lines in some versions).
- CSS: `Header { background: $primary; }` for theming.

**Option B: Custom `Static` widget docked to top**
- Usage: `yield Static("POSSESSION", id="topbar")` with `CSS: #topbar { dock: top; height: 1; }`.
- Full control over content, styling, and no unwanted behaviors (no command palette, no clock).
- Can add key hint summary on the right side: `POSSESSION                    [/] filter  [a] add  [r] room  [?] help`.
- This is the approach used by tools like `lazygit` header bars.

**Recommendation: Option B (custom Static)**
The built-in `Header` has opinionated defaults (command palette on click, clock) that would require fighting. A custom `Static` is 5 lines of CSS and gives full layout control. The breadcrumb widget already demonstrates this pattern (it's a `Static` subclass with `dock` CSS).

**Textual implementation:**
```python
class TopBar(Static):
    DEFAULT_CSS = """
    TopBar {
        dock: top;
        height: 1;
        background: $primary;
        color: $text;
        padding: 0 1;
        text-align: left;
    }
    """
```
Content: `"POSSESSION"` left-aligned; optionally right-aligned key hints.

**Existing code touch points:**
- `PossessionApp.compose()` does not currently compose any widgets (it uses `on_mount` to push MainScreen). Textual apps can yield permanent widgets in `App.compose()` alongside the screen stack — or TopBar can be the first widget in `MainScreen.compose()`.
- The breadcrumb (`Breadcrumb` widget) currently serves as the top-of-screen label. With a proper TopBar added, the breadcrumb becomes redundant in flat-list mode (no hierarchy to show). The breadcrumb can be replaced by the active filter indicator (Feature 2).

**Complexity:** Low.
- New `TopBar` widget (~10 lines including CSS).
- Composed in `MainScreen.compose()` or `PossessionApp.compose()`.
- Remove or repurpose the existing `Breadcrumb` widget.

**Dependency:** None. But its removal of the breadcrumb role interacts with Feature 2's filter indicator.

---

### Feature 7: Quick-Add Persistent Format Label (QADD-04)

**Concept:**
The existing QuickAddBar uses a single `Input` widget whose `placeholder` text describes the field format: `"name / description / room / container / category / purchase_date / cost"`. Placeholder text disappears the moment the user starts typing. After typing `Drill /`, the format hint is gone, and users lose track of which position they are in.

**Solution:**
Replace the placeholder-as-hint with a persistent `Static` label that always displays the format string above (or beside) the input field. The label never disappears.

**Recommended layout:**
```
name / description / room / container / category / date / cost
> [                                                           ]
```
The label line is a `Static` widget inside `QuickAddBar.compose()`, above the `Input`. The `Input`'s placeholder becomes an empty string or just `">"`.

**Enhancement: live position indicator**
As the user types, count `/` characters to determine the current field position, and highlight/bold that field name in the label. For example, after typing `Drill / 18V /`, the user is at position 3 (room), so the label shows:
```
name / description / ROOM / container / category / date / cost
```
This is a differentiator, not table stakes. Start with a static label; add position highlighting if time permits.

**Existing code touch points:**
- `QuickAddBar.compose()`: add `Static(FORMAT_HINT_TEXT, id="quickadd-label")` before the `Input`.
- `QuickAddBar.DEFAULT_CSS`: add styling for the label (height: 1, color: dim).
- `QuickAddBar.open()`: no changes needed — label is always visible when widget is shown.
- The `Input` placeholder text can be simplified to an empty string or `">"` since the label carries the format info.

**Complexity:** Low.
- 2-3 lines of compose change, ~3 lines of CSS.
- Optional position highlighting adds ~15 lines of `on_input_changed` logic.

**Dependency:** None. Fully self-contained within `QuickAddBar`.

---

## Feature Dependencies

```
SPSH-01 (splash screen)      → independent
TOPBAR-01 (top bar)          → independent; removes breadcrumb role
STAT-01 (stats bar)          → VIEW-01 (needs flat list for "filtered" count)
QADD-04 (persistent label)   → independent; self-contained in QuickAddBar

VIEW-01 (flat list default)  → prerequisite for FILT-01/02/03 and PANEL-01
FILT-01/02/03 (pickers)      → VIEW-01
PANEL-01 (detail panel)      → VIEW-01
```

Dependency graph:
```
SPSH-01    TOPBAR-01    QADD-04
    \           |           /
     \          |          /
      [no shared dependency]

VIEW-01
   |
   +-------> STAT-01
   |
   +-------> FILT-01, FILT-02, FILT-03
   |
   +-------> PANEL-01
```

---

## MVP Recommendation for v1.1

**Build first (foundations, unblock other work):**
1. VIEW-01 — flat list default (prerequisite for pickers and panel; trivial LOC)
2. TOPBAR-01 — persistent top bar (visual anchor, 1-2 hours)
3. QADD-04 — persistent label (zero-risk, contained change)
4. SPSH-01 — splash screen (independent, low effort, high visual impact)

**Build second (meat of the milestone):**
5. STAT-01 — stats bar (depends on VIEW-01; medium effort)
6. PANEL-01 — detail panel (depends on VIEW-01; medium effort)

**Build last (most complex, depends on all of the above):**
7. FILT-01 + FILT-02 + FILT-03 — filter pickers (VIM-style modal; most complex; depends on VIEW-01 and STAT-01 for filter indicator)

**Defer:**
- Position-highlighting in QuickAddBar label (nice-to-have, not table stakes)
- `--no-splash` flag
- Stacked multi-field filters (room AND category simultaneously)

---

## Complexity Summary

| Feature | Requirement ID | Category | Complexity | LOC Estimate | Dependencies |
|---------|----------------|----------|------------|--------------|--------------|
| Flat item list default | VIEW-01 | Table Stakes | Low | ~10 LOC change | None |
| Persistent top bar | TOPBAR-01 | Table Stakes | Low | ~20 LOC new | None |
| Stats bar | STAT-01 | Table Stakes | Low-Med | ~40 LOC new | VIEW-01 |
| Quick-add label | QADD-04 | Table Stakes | Low | ~10 LOC change | None |
| Item detail panel | PANEL-01 | Table Stakes | Medium | ~60 LOC new | VIEW-01 |
| Splash screen | SPSH-01 | Differentiator | Low | ~30 LOC new | None |
| Filter pickers (3) | FILT-01/02/03 | Differentiator | Medium-High | ~100 LOC new | VIEW-01 |

Total estimated new code: ~270 LOC for all seven features.

---

## VIM-Style Conventions (for Filter Pickers)

These conventions must be respected to maintain consistency with v1.0 VIM navigation:

| Convention | v1.0 Behavior | v1.1 Picker Behavior |
|------------|---------------|----------------------|
| `j` / `k` | Move cursor down/up in DataTable | Move cursor down/up in picker list |
| `gg` / `G` | Jump to top/bottom | Jump to top/bottom in picker list |
| Escape | Close filter input, dismiss modals | Close picker modal, no filter change |
| Enter | Drill-down (v1.0) / detail panel (v1.1) | Apply selected filter, dismiss picker |
| `/` | Open text filter | Text filter still active (separate from pickers) |
| `q` | Go back one level | Exit app (no levels in flat mode) |

---

## Sources

- Textual >=0.47.0 documentation and API: knowledge from training data (August 2025 cutoff); `ModalScreen.dismiss(value)` pattern is stable since Textual v0.20 (confirmed via codebase that already uses `Screen.push_screen`/`pop_screen`).
- Existing codebase analysis: `MainScreen`, `QuickAddBar`, `EditItemScreen`, `Breadcrumb` (read directly from source).
- TUI UX conventions: htop, lazygit, ranger, neovim splash/picker patterns from training knowledge. Confidence: MEDIUM (training data, well-established conventions unlikely to change).
- `list_items()` filter parameters: directly verified from `models.py` source — `room_id`, `container_id`, `category_id` all accepted. Confidence: HIGH.
- Textual `ModalScreen.dismiss()` callback pattern: used in the same project via `app.push_screen`/`pop_screen`; `ModalScreen` dismiss with return value is the standard post-v0.20 pattern. Confidence: HIGH for Textual >=0.47.0.
