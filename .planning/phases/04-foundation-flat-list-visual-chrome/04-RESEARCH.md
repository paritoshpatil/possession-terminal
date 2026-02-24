# Phase 4: Foundation — Flat List + Visual Chrome - Research

**Researched:** 2026-02-24
**Domain:** Python + Textual 8.0.0 TUI — removing drill-down state machine, adding flat list, splash screen, top bar, transparent theme, and QuickAddBar format label
**Confidence:** HIGH

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| VIEW-01 | Main screen shows a flat list of all items by default — no drill-down required to see inventory | Remove `_view_mode` state machine from `MainScreen`; replace `_load_view()` with single-branch `_load_items()` that always calls `list_items()` |
| TOPBAR-01 | A persistent top bar displays the app name "Possession" at all times | Add `Header()` or custom `Static(dock=top)` widget to `MainScreen.compose()`; remove `Breadcrumb` widget |
| THEME-01 | App supports terminal-native colors via `--transparent` flag (transparent background + terminal foreground); default remains Textual surface theme | Add `--transparent` CLI flag to `__main__.py`; conditionally override `Screen { background: transparent }` in `PossessionApp`; keep `$surface` as default |
| QADD-04 | Quick-add bar shows a persistent format label (field order hint) that remains visible while the user types | Add `Static` format hint label to `QuickAddBar.compose()` above the `Input`; set explicit `height: 2` on `QuickAddBar` |
| SPSH-01 | App shows a splash screen with ASCII art ("POSSESSION") on launch; any key dismisses it | Create `SplashScreen(Screen)` in `screens/splash.py`; modify `PossessionApp.on_mount()` to push `MainScreen` first then `SplashScreen` on top |
</phase_requirements>

---

## Summary

Phase 4 is a focused surgical refactor of the existing Textual 8.0.0 app. No new dependencies are required. The work divides into one high-risk structural change (VIEW-01: removing the drill-down state machine) and four low-risk additive changes (TOPBAR-01, THEME-01, SPSH-01, QADD-04). The structural change must land first and completely, because six locations in `main.py` silently no-op on `e`, `d`, and Enter if any `_view_mode` guard remains.

The existing codebase has been read directly. `MainScreen` currently has `_view_mode: str = "rooms"` initialized in `__init__` and `on_mount`, with three-way branches in `_load_view()`, `_apply_filter()`, `on_data_table_row_selected()`, `action_edit_item()`, `action_delete_item()`, and `action_go_back()`. All six must be replaced in a single coordinated commit. The `Breadcrumb` widget must be removed from `compose()` in the same commit.

The four additive changes are isolated and low-risk: TOPBAR-01 adds a persistent top bar (replacing Breadcrumb's visual role), THEME-01 adds a `--transparent` CLI flag that conditionally overrides the CSS background, SPSH-01 creates a new `SplashScreen` screen (~25 LOC), and QADD-04 adds a `Static` label to `QuickAddBar.compose()`. The transparent background must be opt-in (not default) because it renders as opaque black in tmux and multiplexers — the environment most TUI power users live in.

**Primary recommendation:** Implement VIEW-01 first in isolation (remove entire drill-down state machine, replace with flat list), verify `e`/`d`/Enter all work, then implement the four additive changes in any order.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| textual | 8.0.0 (installed) | TUI framework — screens, widgets, CSS, events | Already in use; all needed APIs stable since ≥0.20 |
| Python stdlib `os` | 3.9+ | Reading `COLORFGBG` env var for dark/light detection | No external dependencies; established convention |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| textual.screen.Screen | 8.0.0 | Base class for `SplashScreen` | Full-screen replacement (not modal) so splash owns the entire terminal |
| textual.widgets.Static | 8.0.0 | Top bar widget, QuickAddBar label, splash art display | Non-interactive display; `update()` for dynamic content |
| textual.widgets.Header | 8.0.0 | Built-in top bar alternative | Lower maintenance than custom Static; uses `App.TITLE` automatically |
| argparse (stdlib) | 3.9+ | `--transparent` CLI flag parsing in `__main__.py` | Already used in `__main__.py` for `--db` flag |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Custom `Static` top bar | Textual built-in `Header()` | `Header` adds clock and command-palette-on-click by default; `Header(show_clock=False)` removes clock but command palette behavior varies in 8.0.0 — custom `Static` with `dock: top` is simpler and fully controlled |
| `--transparent` CLI flag | Always-on transparent background | Always-on transparent renders black in tmux/screen/SSH; opt-in flag is the safe default |
| `SplashScreen(Screen)` | `SplashScreen(ModalScreen)` | Modal renders the background screen behind it; splash should own the full terminal without bleed-through |

**Installation:** No new packages needed. All in existing install.

```bash
# Already installed:
# textual==8.0.0
# Python 3.9+ stdlib: os, argparse, typing
```

---

## Architecture Patterns

### Recommended Project Structure

The changes to Phase 4 touch:

```
possession/
├── __main__.py              # MODIFIED: add --transparent flag
├── tui/
│   ├── app.py               # MODIFIED: TITLE constant, CSS conditional on transparent flag
│   ├── screens/
│   │   ├── main.py          # HEAVILY MODIFIED: remove drill-down state machine
│   │   ├── splash.py        # NEW: SplashScreen
│   │   └── edit.py          # UNCHANGED
│   └── widgets/
│       ├── breadcrumb.py    # DELETED (or kept for reference — remove from compose)
│       └── quickadd.py      # MODIFIED: add format label Static in compose()
```

### Pattern 1: VIEW-01 — Flat List Migration (The Critical Change)

**What:** Replace the three-mode state machine (`_view_mode: "rooms"|"containers"|"items"`) with a flat-list-only screen that always shows all items. The `_view_mode`, `_current_room_id`, `_current_room_name`, `_current_container_id`, `_current_container_name` state variables are removed entirely. New state: `_filter_text: str = ""` and `_items: List[dict] = []` (already exists but now always holds items, not conditional).

**When to use:** The foundational change for the entire v1.1 milestone. Must land before any other Phase 4 change.

**Six locations that must all change in the same commit:**

```python
# 1. action_edit_item — remove guard
def action_edit_item(self) -> None:
    # REMOVE: if self._view_mode != "items": return
    row_key_str = self._get_current_row_key_str()
    if row_key_str is None:
        return
    item = next((i for i in self._items if str(i["id"]) == row_key_str), None)
    if item is not None:
        from possession.tui.screens.edit import EditItemScreen
        self.app.push_screen(EditItemScreen(item, self.app.db_path))

# 2. action_delete_item — remove guard
def action_delete_item(self) -> None:
    # REMOVE: if self._view_mode != "items": return
    row_key_str = self._get_current_row_key_str()
    ...

# 3. _load_view() → renamed to _load_items(), single branch only
def _load_items(self) -> None:
    table = self.query_one(DataTable)
    try:
        table.clear(columns=True)
    except TypeError:
        table.clear()
    table.add_columns("Name", "Description", "Location", "Category", "Cost")
    self._items = list_items(self.app.db_path)   # no room_id/container_id filters yet
    self._apply_filter(self._filter_text)

# 4. _apply_filter() — single items-only branch
def _apply_filter(self, query: str) -> None:
    table = self.query_one(DataTable)
    table.clear()
    q = query.lower().strip()
    # REMOVE: rooms and containers branches
    for item in self._items:
        if q and not any(
            q in (item.get(f) or "").lower()
            for f in ("name", "description", "room_name", "container_name", "category_name")
        ):
            continue
        table.add_row(
            item["name"],
            item.get("description") or "",
            _fmt_location(item),
            item.get("category_name") or "",
            _fmt_cost(item.get("cost")),
            key=str(item["id"]),
        )

# 5. on_data_table_row_selected — remove drill-down logic entirely
def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
    # In flat-list mode, Enter on a row opens detail (Phase 5 concern).
    # For Phase 4, this can be a no-op (Enter no longer drills into rooms).
    return

# 6. action_go_back → rebind 'q' to exit app directly
def action_go_back(self) -> None:
    self.app.exit()   # No drill-down levels; q exits app
    # REMOVE: all if/elif branches for view_mode
```

**Also in the same commit:**
- Remove `Breadcrumb` from `compose()` and delete its import
- Remove `_update_breadcrumb()` method and all call sites
- Remove `_view_mode`, `_current_room_id`, `_current_room_name`, `_current_container_id`, `_current_container_name` from `__init__()`
- Update `on_mount()`: remove `self._view_mode = "rooms"`; call `self._load_items()` directly
- Remove unused imports: `list_rooms`, `list_containers` (unless kept for Phase 6 filter pickers)
- Add `self._filter_text: str = ""` to `__init__()` (used by `_apply_filter`)

### Pattern 2: SPSH-01 — Splash Screen Push Order

**What:** `PossessionApp.on_mount()` pushes `MainScreen` first (bottom of stack), then pushes `SplashScreen` on top. When `SplashScreen` receives any keypress, it calls `self.app.pop_screen()` to reveal `MainScreen` below.

**Why this order:** Pushing `MainScreen` first lets it mount and run `_load_items()` in the background while the splash is visible. When the splash is dismissed, `MainScreen.on_screen_resume()` fires (harmlessly reloads — already fast). The splash is not left on the stack because it is popped, not replaced.

**Example:**

```python
# Source: ARCHITECTURE.md + PITFALLS.md (Pitfall 7)

# possession/tui/app.py
class PossessionApp(App):
    TITLE = "Possession"

    def on_mount(self) -> None:
        self.push_screen(MainScreen())        # pushed first — bottom of stack
        self.push_screen(SplashScreen())      # pushed second — shown on top

# possession/tui/screens/splash.py
from textual.app import ComposeResult
from textual import events
from textual.screen import Screen
from textual.widgets import Static


SPLASH_ART = """\
 ____  ___  ____  ____  ____  ____  ____  ____  ___  _  _
(  _ \\/ __)(  __)/ ___)(  __)/ ___)/ ___)(  __)/   \\( \\/ )
 ) __/\\__ \\ ) _) \\___ \\ ) _) \\___ \\\\___ \\ ) _)(  O ) )  /
(__)  (___/(____)(____/(____)(____/(____/(____) \\__/(_/\\_/

             Press any key to continue...
"""


class SplashScreen(Screen):
    DEFAULT_CSS = """
    SplashScreen {
        align: center middle;
        background: $surface;
    }
    #splash-art {
        color: $primary;
        text-align: center;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static(SPLASH_ART, id="splash-art")

    def on_key(self, event: events.Key) -> None:
        self.app.pop_screen()
```

### Pattern 3: TOPBAR-01 — Persistent Top Bar

**What:** Replace the `Breadcrumb` widget (which showed drill-down path) with a persistent top bar displaying "Possession".

**Two implementation options** — planner should choose based on Phase 4 plan:

**Option A: Textual built-in `Header`** (lower maintenance)
```python
# Source: STACK.md §4.2 + ARCHITECTURE.md §2

# In PossessionApp (app.py):
TITLE = "Possession"

# In MainScreen.compose() — first widget yielded:
from textual.widgets import Header
yield Header(show_clock=False)
```

**Option B: Custom Static** (full control, matches Breadcrumb pattern)
```python
# In MainScreen.compose():
yield Static("Possession", id="topbar")

# In MainScreen.CSS:
"""
#topbar {
    dock: top;
    height: 1;
    background: $primary-darken-2;
    color: $text;
    padding: 0 1;
    text-style: bold;
}
"""
```

**Recommendation:** Use Option B (custom Static) for Phase 4. It directly replaces the `Breadcrumb` pattern (same base class, same CSS approach) and avoids any `Header` widget behavior surprises in Textual 8.0.0. `Header` command-palette-on-click behavior is not verified for 8.0.0 — custom Static is safe.

### Pattern 4: THEME-01 — Transparent Background via CLI Flag

**What:** Add `--transparent` flag to CLI. When flag is present, override `PossessionApp.CSS` to use `background: transparent` instead of `$surface`.

**Example:**

```python
# possession/__main__.py
parser.add_argument(
    "--transparent",
    action="store_true",
    default=False,
    help="Use terminal native background (transparent mode)",
)
# ...
PossessionApp(db_path=resolved_path, transparent=args.transparent).run()

# possession/tui/app.py
class PossessionApp(App):
    TITLE = "Possession"

    _CSS_DEFAULT = """
    Screen {
        background: $surface;
    }
    """
    _CSS_TRANSPARENT = """
    Screen {
        background: transparent;
    }
    DataTable {
        background: transparent;
    }
    """

    def __init__(self, db_path: Path, transparent: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.db_path = db_path
        # Set CSS before run() is called — Textual reads CSS at compose time
        self.CSS = self._CSS_TRANSPARENT if transparent else self._CSS_DEFAULT
```

**Note on CSS assignment at init time:** Setting `self.CSS` in `__init__` before `run()` is called should work because Textual reads the CSS class attribute at compose time. If this proves unreliable, an alternative is to use `self.app.set_class("transparent-mode")` and have both CSS rules in DEFAULT_CSS gated by the class.

### Pattern 5: QADD-04 — Persistent Format Label

**What:** Add a `Static` format hint label above the `Input` in `QuickAddBar.compose()`. Set explicit `height: 2` on the widget to prevent clipping when docked at bottom.

**Example:**

```python
# Source: ARCHITECTURE.md §7, PITFALLS.md Pitfall 9

# possession/tui/widgets/quickadd.py — modified compose():
QUICKADD_FORMAT_HINT = "name / description / room / container / category / date / cost"

def compose(self) -> ComposeResult:
    yield Static(QUICKADD_FORMAT_HINT, id="quickadd-label")
    yield Input(
        placeholder="",   # hint now lives in the Static label above
        id="quickadd-input",
    )
    yield Input(
        placeholder="Room not found. Create it? [y/N]",
        id="quickadd-confirm",
        classes="hidden",
    )

# Updated DEFAULT_CSS — explicit height: 2 to avoid dock clipping
DEFAULT_CSS = """
QuickAddBar {
    height: 2;
    dock: bottom;
}
QuickAddBar.hidden {
    display: none;
}
#quickadd-label {
    height: 1;
    color: $text-muted;
    padding: 0 1;
}
"""
```

**No other changes to QuickAddBar.** All state machine logic, `open()`/`close()`, event handlers, and confirmation flow remain identical. This is a pure `compose()` + CSS change.

### Anti-Patterns to Avoid

- **Partial VIEW-01 migration:** Setting `_view_mode = "items"` on mount without removing the guards in `action_edit_item`, `action_delete_item`, `_apply_filter`, `on_data_table_row_selected`, and `action_go_back` causes silent failures where `e`, `d`, and Enter do nothing.
- **Keeping Breadcrumb in compose():** After drill-down is removed, `Breadcrumb` occupies one row of vertical space with no meaningful content. Remove from `compose()` in the same commit as VIEW-01.
- **Pushing SplashScreen before MainScreen:** If `SplashScreen` is pushed first and `MainScreen` pushed on top, then `MainScreen.on_screen_resume()` fires when splash is popped. The correct order is: push `MainScreen` first, push `SplashScreen` second (so splash renders on top).
- **Always-on transparent background:** `background: transparent` renders as opaque black in tmux/screen/multiplexers. Must be opt-in via `--transparent` flag.
- **`height: auto` on QuickAddBar with two children:** The existing `height: auto` with one child works. Adding a second child (the format label) can clip under the DataTable. Set explicit `height: 2`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Top bar with app name | Custom positioning/z-index widget | `Static` with `dock: top` in CSS (already proven by `Breadcrumb`) | The `Breadcrumb` widget already demonstrates this exact pattern; reuse it |
| Any-key dismiss for splash | Timer-based auto-dismiss, specific key binding | `on_key(event)` on `Screen` — fires for any key | `Screen.on_key` receives all key events before bindings; simplest possible implementation |
| Dark/light terminal detection | OSC 10/11 color query sequences | `os.environ.get("COLORFGBG")` | OSC queries conflict with Textual's terminal ownership; `COLORFGBG` is the established convention and requires no terminal raw mode |
| Conditional CSS at runtime | `inject_css()` or dynamic stylesheet mutation | Set `self.CSS` on the App instance in `__init__` before `run()` | App-level `CSS` is read at compose time; setting it before `run()` is the supported pattern |

**Key insight:** Every mechanism needed for Phase 4 is either already in the codebase (Breadcrumb's dock pattern, QuickAddBar's hidden/shown pattern, push_screen/pop_screen for navigation) or is a trivial use of stable Textual built-ins. Nothing in this phase requires novel patterns.

---

## Common Pitfalls

### Pitfall 1: Dead `_view_mode` Guards After Partial Migration

**What goes wrong:** VIEW-01 is implemented by changing `_load_view()` to call `list_items()` but forgetting to remove the `if self._view_mode != "items": return` guards in `action_edit_item` and `action_delete_item`. The app appears to work (items are displayed in the table) but pressing `e`, `d`, or Enter does nothing — no error, no visual feedback.

**Why it happens:** Six separate locations in `main.py` reference `_view_mode`. Changing one without changing all others creates a working-looking but broken state.

**How to avoid:** Treat VIEW-01 as a single coordinated commit. Create a checklist of all six locations before writing code. Do not commit until all six have been updated and manually tested.

**Warning signs:** After migration, `e` key does nothing on a selected item row. `d` key does nothing. Press Enter on a row — nothing happens.

**The six locations (with current line numbers from direct source read):**
1. `action_edit_item()` line 120: `if self._view_mode != "items": return`
2. `action_delete_item()` line 131: `if self._view_mode != "items": return`
3. `_apply_filter()` lines 173–206: three-way branch on `_view_mode`
4. `_load_view()` lines 220–248: three-way branch
5. `on_data_table_row_selected()` lines 253–277: three-way branch
6. `action_go_back()` lines 281–303: full drill-down state machine
7. `_update_breadcrumb()` lines 312–323: breadcrumb path update (must also be removed)
8. `on_mount()` line 83: `self._view_mode = "rooms"` (must be removed)
9. `__init__()` lines 57–61: four drill-down state variables (must be removed)

### Pitfall 2: Breadcrumb Left in `compose()` After Drill-Down Removed

**What goes wrong:** `Breadcrumb` is yielded in `compose()` unconditionally. After removing the drill-down state machine, `_update_breadcrumb()` is removed but the widget itself remains mounted. It occupies one row of vertical space at the top of the screen with either no text or stale text.

**How to avoid:** Remove `Breadcrumb` from `compose()` and delete its import in the same commit as VIEW-01. The top bar (TOPBAR-01) fills the visual role of the breadcrumb — implement TOPBAR-01 in the same commit to avoid an in-between state with no header text.

**Warning signs:** A colored horizontal bar with no text appears at the top of the screen.

### Pitfall 3: Splash Push Order Causes Double `on_screen_resume`

**What goes wrong:** If `SplashScreen` is pushed first in `on_mount()`, then `MainScreen` is pushed second, then when the splash is dismissed via `pop_screen()`, `MainScreen.on_screen_resume()` fires and calls `_load_items()` again. This is harmless functionally but is an extra DB query on every launch.

**Correct order:** Push `MainScreen` first, push `SplashScreen` second. When `SplashScreen` calls `self.app.pop_screen()`, `MainScreen` is revealed and `on_screen_resume` fires once (expected — same as returning from edit screen). This is acceptable behavior.

**How to avoid:** Push order: `self.push_screen(MainScreen())` then `self.push_screen(SplashScreen())`.

### Pitfall 4: Transparent Background Breaks in tmux

**What goes wrong:** `Screen { background: transparent }` renders as opaque black in tmux, screen, and most SSH sessions. This is the environment most TUI power users operate in.

**How to avoid:** Ship transparent as opt-in (`--transparent` flag). Default `PossessionApp.CSS` keeps `background: $surface`. Document in README that `--transparent` is for native terminal emulators without multiplexers.

**Verification step:** Before marking THEME-01 done, test inside `tmux` — confirm black background is acceptable (it is for typical use) and native emulator without tmux shows the terminal background correctly.

### Pitfall 5: QuickAddBar Label Clips at `height: auto`

**What goes wrong:** Adding a `Static` label above the `Input` in `QuickAddBar.compose()` increases the widget's total height to 2 cells. With `height: auto; dock: bottom`, Textual may compute the docked height incorrectly, causing the label to render behind the DataTable or the Input to disappear.

**How to avoid:** Change `QuickAddBar.DEFAULT_CSS` from `height: auto` to `height: 2`. Set explicit `height: 1` on both `#quickadd-label` and `#quickadd-input` to give the layout engine unambiguous sizes.

**Alternative if `height: 2` still has issues:** Use the placeholder approach — keep a single `Input` but embed the format hint as the placeholder text (it disappears on type, but that is the existing behavior and avoids the layout risk entirely). This is the fallback; the Static label approach is preferred.

---

## Code Examples

Verified patterns from direct source analysis and project research files:

### Complete VIEW-01 Migration: New `MainScreen.__init__` State

```python
# Source: main.py direct read + ARCHITECTURE.md §4

def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self._items: List[dict] = []
    self._filter_text: str = ""
    self._last_key: str = ""
    # Delete confirmation state (unchanged)
    self._delete_pending_id: Optional[int] = None
    # REMOVED: _view_mode, _current_room_id, _current_room_name,
    #          _current_container_id, _current_container_name
```

### Complete VIEW-01 Migration: New `compose()`

```python
# Source: main.py direct read + ARCHITECTURE.md §4

def compose(self) -> ComposeResult:
    from possession.tui.widgets.quickadd import QuickAddBar
    # Custom top bar (Breadcrumb replacement)
    yield Static("Possession", id="topbar")
    yield DataTable(cursor_type="row", show_header=True)
    yield Input(
        placeholder="Filter... (/ to open, Esc to clear)",
        id="filter-input",
        classes="hidden",
    )
    yield QuickAddBar(id="quickadd-bar", classes="hidden")
    yield Input(
        placeholder="Delete item? [y/N]",
        id="delete-confirm",
        classes="hidden",
    )
    # REMOVED: Breadcrumb import and yield
```

### `_load_items()` — Replaces `_load_view()`

```python
# Source: ARCHITECTURE.md §4

def _load_items(self) -> None:
    """Load all items and refresh the DataTable. No drill-down branches."""
    table = self.query_one(DataTable)
    try:
        table.clear(columns=True)
    except TypeError:
        table.clear()
    table.add_columns("Name", "Description", "Location", "Category", "Cost")
    self._items = list_items(self.app.db_path)
    self._apply_filter(self._filter_text)
```

### `_apply_filter()` — Items-only branch

```python
# Source: main.py direct read — existing items branch, now the only branch

def _apply_filter(self, query: str) -> None:
    """Filter the DataTable by query string (case-insensitive). Items only."""
    self._filter_text = query   # persist for _load_items() re-use
    table = self.query_one(DataTable)
    table.clear()
    q = query.lower().strip()
    for item in self._items:
        if q and not any(
            q in (item.get(f) or "").lower()
            for f in ("name", "description", "room_name",
                      "container_name", "category_name")
        ):
            continue
        table.add_row(
            item["name"],
            item.get("description") or "",
            _fmt_location(item),
            item.get("category_name") or "",
            _fmt_cost(item.get("cost")),
            key=str(item["id"]),
        )
```

### `PossessionApp` with Transparent Flag and TITLE

```python
# Source: STACK.md §3.2 + __main__.py direct read

# possession/tui/app.py
class PossessionApp(App):
    """Possession terminal inventory manager."""

    TITLE = "Possession"

    _CSS_DEFAULT = """
    Screen {
        background: $surface;
    }
    """
    _CSS_TRANSPARENT = """
    Screen {
        background: transparent;
    }
    DataTable {
        background: transparent;
    }
    """

    def __init__(self, db_path: Path, transparent: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.db_path = db_path
        self.CSS = self._CSS_TRANSPARENT if transparent else self._CSS_DEFAULT

    def on_mount(self) -> None:
        self.push_screen(MainScreen())
        self.push_screen(SplashScreen())

# possession/__main__.py — add --transparent flag
parser.add_argument(
    "--transparent",
    action="store_true",
    default=False,
    help="Use terminal native background (transparent mode)",
)
# ...
PossessionApp(db_path=resolved_path, transparent=args.transparent).run()
```

### SplashScreen — Full Implementation

```python
# Source: ARCHITECTURE.md §1, PITFALLS.md Pitfall 7, FEATURES.md §5

# possession/tui/screens/splash.py
from textual import events
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static

SPLASH_ART = r"""
 ____  ___  ____  ____  ____  ____  ____  ____  ___  _  _
(  _ \/ __)( ___)(  __)/ ___)(  __)/ ___)/ ___)/   \( \/ )
 ) __/\__ \ ) _)  ) _) \___ \ ) _) \___ \\___ \( () ) )  /
(__)  (___/(____)(____)(____/(____)(____/(____) \___/(_/\_/

                  press any key to continue
"""


class SplashScreen(Screen):
    DEFAULT_CSS = """
    SplashScreen {
        align: center middle;
        background: $surface;
    }
    #splash-art {
        color: $primary;
        text-align: center;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static(SPLASH_ART, id="splash-art")

    def on_key(self, event: events.Key) -> None:
        self.app.pop_screen()
```

### QuickAddBar Persistent Label — Minimal Diff

```python
# Source: quickadd.py direct read + ARCHITECTURE.md §7

QUICKADD_FORMAT_HINT = "name / description / room / container / category / date / cost"

# Modified compose():
def compose(self) -> ComposeResult:
    yield Static(QUICKADD_FORMAT_HINT, id="quickadd-label")
    yield Input(
        placeholder="",   # removed old placeholder — label carries the hint
        id="quickadd-input",
    )
    yield Input(
        placeholder="Room not found. Create it? [y/N]",
        id="quickadd-confirm",
        classes="hidden",
    )

# Modified DEFAULT_CSS:
DEFAULT_CSS = """
QuickAddBar {
    height: 2;
    dock: bottom;
}
QuickAddBar.hidden {
    display: none;
}
#quickadd-label {
    height: 1;
    color: $text-muted;
    padding: 0 1;
}
"""
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Drill-down state machine (`_view_mode: "rooms"|"containers"|"items"`) | Flat list with filter pickers (`_filter_room_id`, `_filter_container_id`) | Phase 4 (this phase) | Removes 6 guarded locations in main.py; enables Phase 5 detail panel and Phase 6 filter pickers |
| `Breadcrumb` widget shows navigation path | Persistent top bar shows app name; filter state shown in stats bar (Phase 5) | Phase 4 (this phase) | Breadcrumb is deleted; top bar is always visible |
| `Screen { background: $surface }` always-on | Opt-in `--transparent` flag; default keeps `$surface` | Phase 4 (this phase) | Transparent is safe for native emulators; `$surface` is safe for tmux |
| Long placeholder text in QuickAddBar input (disappears on type) | Persistent `Static` label above input (always visible) | Phase 4 (this phase) | Field order always visible while typing |

**Deprecated/outdated in this codebase after Phase 4:**
- `_view_mode` state variable: replaced by flat list + future filter state
- `_current_room_id`, `_current_room_name`, `_current_container_id`, `_current_container_name`: navigation state; replaced in Phase 6 by `_filter_room_id`, `_filter_container_id`
- `Breadcrumb` widget: the `breadcrumb.py` file becomes dead code; can be deleted
- `action_go_back()` method body: replaced by `self.app.exit()` one-liner

---

## Open Questions

1. **Top bar: `Header(show_clock=False)` or custom `Static`?**
   - What we know: Both work. `Header` uses `App.TITLE` automatically. Custom `Static` reuses the `Breadcrumb` pattern exactly. `Header` in Textual 8.0.0 may add command-palette-on-click behavior (not verified for 8.0.0).
   - What's unclear: Whether `Header` in Textual 8.0.0 has any default behaviors that need disabling.
   - Recommendation: Use custom `Static` (Pattern 3 Option B above). Lower risk, proven pattern in this codebase.

2. **`self.CSS` assignment at init time — reliable for conditional transparent?**
   - What we know: Textual reads `CSS` class attribute at compose time. Setting `self.CSS` (instance attribute) in `__init__` overrides the class attribute.
   - What's unclear: Whether instance-level `CSS` assignment before `run()` is officially supported in Textual 8.0.0 or whether the supported pattern is `DEFAULT_CSS` + class toggle.
   - Recommendation: Use the class-attribute approach with a helper; if instance assignment proves unreliable, the fallback is `App.DEFAULT_CSS` with a CSS class toggled in `__init__`: `self.add_class("transparent-mode")`.

3. **`on_screen_resume` double-fire after splash?**
   - What we know: Pushing `SplashScreen` on top of `MainScreen` means `on_screen_resume` fires on `MainScreen` when splash is popped. This triggers `_load_items()` again.
   - What's unclear: Whether this is acceptable for typical DB sizes (yes — fast) or causes a visible flicker.
   - Recommendation: Accept as-is. Document as known behavior (Pitfall 14 in PITFALLS.md). If flicker is visible, add a `_initial_load_done: bool` flag to skip the resume reload on first pop.

---

## Sources

### Primary (HIGH confidence)

- Direct source code read: `possession/tui/screens/main.py` — all 6 `_view_mode` guard locations identified and line numbers confirmed
- Direct source code read: `possession/tui/app.py` — current CSS and `on_mount` pattern confirmed
- Direct source code read: `possession/tui/widgets/quickadd.py` — `height: auto; dock: bottom` confirmed; compose structure confirmed
- Direct source code read: `possession/tui/widgets/breadcrumb.py` — `Static` subclass, `dock` CSS confirmed
- Direct source code read: `possession/__main__.py` — existing `argparse` pattern confirmed; `--db` flag as model for `--transparent` flag
- `.planning/research/SUMMARY.md` — milestone-level research confirming no new dependencies needed; transparent pitfall documented
- `.planning/research/ARCHITECTURE.md` — component specs with code examples verified against source
- `.planning/research/PITFALLS.md` — 14 pitfalls from direct codebase analysis
- `.planning/research/STACK.md` — Textual 8.0.0 confirmed installed; CSS variable system documented
- Textual 8.0.0 install confirmed: project root file `=0.47.0` contains pip install log showing `textual-8.0.0-py3-none-any.whl`

### Secondary (MEDIUM confidence)

- Textual `App.CSS` instance assignment before `run()` — inferred from Textual compose lifecycle; should be verified during implementation
- Textual 8.0.0 `Header` widget behavior — training knowledge; exact command-palette-on-click behavior in 8.0.0 not verified from source
- `background: transparent` behavior in tmux — terminal ecosystem knowledge; verify by manual test in tmux before marking THEME-01 done

### Tertiary (LOW confidence — verify before use)

- Exact `Theme` dataclass field names in Textual 8.0.0 — not needed for Phase 4 (programmatic theme registration not required); flag for Phase 4+ if custom theme registration is added
- `App.CSS` vs `DEFAULT_CSS` instance override behavior — may need smoke test; fallback (CSS class toggle) is documented

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new packages; Textual 8.0.0 confirmed; all APIs used are stable since ≥0.20
- Architecture: HIGH — patterns based on direct source code read of all 5 affected files; drill-down state machine fully mapped with line numbers
- Pitfalls: HIGH for codebase-specific issues (view_mode guards, breadcrumb, push order); MEDIUM for Textual internals (transparent in tmux, CSS assignment timing)

**Research date:** 2026-02-24
**Valid until:** 2026-03-24 (stable codebase; Textual 8.0.0 installed; no moving targets)
