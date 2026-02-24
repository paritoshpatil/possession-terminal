# Domain Pitfalls: possession-terminal v1.1 UI Overhaul

**Domain:** Adding UI overhaul features to an existing Python + Textual TUI
**Researched:** 2026-02-24
**Overall confidence:** MEDIUM-HIGH (codebase analysis is HIGH confidence; Textual internals based on training knowledge, flagged where verification needed)

---

## Critical Pitfalls

Mistakes that cause silent bugs, rewrites, or broken interactions.

---

### Pitfall 1: Flat List Migration Leaves Dead `_view_mode` Guards

**What goes wrong:** The existing `_view_mode` state machine (`"rooms"` / `"containers"` / `"items"`) is referenced in six places across `main.py`. If you replace the drill-down with a flat list but do not remove all guards, item-level actions silently no-op.

**Why it happens:** The plan sounds simple — set `_view_mode = "items"` on mount and call `list_items()` without filters. But `action_edit_item`, `action_delete_item`, and `on_data_table_row_selected` all check `if self._view_mode != "items": return` before doing anything. If the state machine is partially removed (e.g. `_load_view` changed but guards left in place), all item interaction breaks — no error raised, the app just silently ignores `e`, `d`, and Enter key.

**Affected code (all must be updated together):**
- `action_edit_item` — line 119: `if self._view_mode != "items": return`
- `action_delete_item` — line 131: `if self._view_mode != "items": return`
- `on_data_table_row_selected` — lines 253-277: full three-way branch on `_view_mode`
- `_load_view` — lines 212-248: three-way branch drives column definitions
- `action_go_back` — lines 279-303: entire function is drill-down logic; calling `self.app.exit()` at "rooms" level must not fire if flat list replaces rooms view
- `_update_breadcrumb` — lines 309-323: breadcrumb displays drill-down path text; must be replaced or removed

**Consequences:** Edit and delete are unreachable via keyboard. Enter on a row does nothing. No exception is thrown. The app appears to work but nothing happens on item interaction.

**Prevention:** Treat the migration as a coordinated replacement, not an incremental tweak. In the implementation phase, define a checklist: for each of the six locations above, explicitly decide "remove / replace / keep." Do not leave any `_view_mode` branch that checks for `"rooms"` or `"containers"` if those view modes no longer exist.

**Detection:** After migration, verify `e`, `d`, and Enter all work on the very first item in the flat list. A manual smoke test catches this immediately — CI with `pytest-textual-snapshot` would catch it automatically.

**Phase:** Address in whichever phase implements VIEW-01 (flat list). Must be the first phase of v1.1 since all other features build on the flat list.

---

### Pitfall 2: Breadcrumb Widget Left Mounted When Drill-Down Is Removed

**What goes wrong:** `Breadcrumb` is yielded in `compose()` unconditionally. When the flat list replaces the drill-down, `_update_breadcrumb()` still runs. If the breadcrumb remains but the state machine is gone, it will always show "All Items" — harmless but misleading. The bigger risk is that the `Breadcrumb` widget occupies a fixed `height: 1` row in the vertical layout. If the new design adds a persistent top bar and stats bar, the breadcrumb row becomes dead space that shifts layout.

**Why it happens:** Widgets in `compose()` are composed at mount time. Removing the breadcrumb means removing it from `compose()` and all call sites of `_update_breadcrumb()`. It's easy to remove the calls but forget to remove the widget from `compose()`, leaving an invisible-but-space-consuming widget.

**Consequences:** Layout has an unexplained gap. Persistent top bar and stats bar cause vertical crowding. The breadcrumb's `background: $primary-darken-2` bar may appear as a colored stripe with no text.

**Prevention:** When implementing VIEW-01, do not leave `Breadcrumb` in `compose()`. Decide at the start: "Breadcrumb is replaced by the persistent top bar (TOPBAR-01)." Remove it from `compose()` and delete all `_update_breadcrumb()` call sites in the same commit.

**Detection:** Visual inspection of the screen layout immediately reveals the extra colored bar.

**Phase:** VIEW-01 implementation phase.

---

### Pitfall 3: `q` Key at Top Level Calls `self.app.exit()` — Will Exit App During Flat-List Use

**What goes wrong:** `action_go_back` currently calls `self.app.exit()` when `_view_mode == "rooms"` (the top of the hierarchy). In the flat list design, there is no hierarchy to go back from. If `action_go_back` is left intact and `q` is bound to it, pressing `q` in the flat list view exits the app immediately — the same behavior a user who drilled down to rooms then back up would expect, but now triggered on the default screen.

**Why it happens:** The `q` binding and `action_go_back` were designed for the drill-down model. In a flat list, `q` should either do nothing or quit (this is a UX decision). If the developer forgets to change the binding, quitting is the default.

**Consequences:** Users pressing `q` to "go back" from a filter picker or detail panel (a natural vim reflex) exit the entire application instead.

**Prevention:** In the VIEW-01 phase, explicitly decide what `q` does in flat-list mode. If quitting on `q` is intentional, document it. If `q` should dismiss overlays/panels instead, rebind accordingly. Remove the rooms/containers fallthrough from `action_go_back`.

**Detection:** Manual test: open the app in flat list mode, press `q`. If it exits, confirm this is intended.

**Phase:** VIEW-01.

---

### Pitfall 4: Transparent Background Breaks in tmux / screen / Multiplexers

**What goes wrong:** Setting `Screen { background: transparent; }` in Textual passes the "use terminal background" instruction to the terminal emulator. In native terminal windows (iTerm2, Alacritty, Kitty with background opacity configured), this works correctly and shows the terminal's wallpaper or color through. In `tmux`, `screen`, or any multiplexer, `transparent` renders as opaque black because the multiplexer intercepts the escape sequences and cannot propagate transparency from the inner terminal to the outer one.

**Why it happens:** Textual's `transparent` CSS keyword emits ANSI escape sequences asking the terminal not to paint a background. Multiplexers capture these and either ignore them or substitute black. The behavior is terminal-dependent and cannot be controlled from Python.

**Specific failure modes:**
- `tmux` without `set -g default-terminal "tmux-256color"` and `set -ga terminal-overrides ",*256col*:Tc"`: entire app background renders black regardless of terminal theme
- `tmux` with passthrough configured: works, but only if the outer terminal supports 24-bit color and transparency
- SSH sessions: almost always black, since the remote terminal has no concept of the local desktop's wallpaper
- VS Code integrated terminal: works if terminal opacity is configured, breaks when terminal has no transparency setting

**Consequences:** The feature works perfectly in the developer's local setup and fails for users running in tmux (extremely common for TUI users). The regression is invisible in CI.

**Prevention:** Implement `transparent` as a configurable option, not the default. Use a CSS variable or an `--theme` CLI flag. The default should be a solid dark background using Textual's `$surface` (already in place at `app.py` line 11). Add a `--transparent` flag that swaps the CSS variable to `transparent`. Document that multiplexer behavior varies.

**Detection:** Test the app inside `tmux` before releasing as the default. Check that a black background in tmux is acceptable as fallback (it usually is visually, just not the "theme color" effect intended).

**Confidence:** MEDIUM — Textual's CSS `transparent` behavior in multiplexers is based on terminal behavior knowledge, not a verified Textual changelog entry. Verify by testing in tmux before implementing.

**Phase:** THEME-01 implementation phase. Flag for explicit tmux test in that phase's acceptance criteria.

---

### Pitfall 5: Filter Picker Overlay Captures Keys That Belong to the Parent Screen

**What goes wrong:** When a filter picker (room/container/category) is shown as an overlay Widget inside MainScreen, key events bubble through the widget tree. If the picker does not call `event.stop()` on the keys it consumes (arrow keys, Enter, Escape, letter keys), those events reach the MainScreen's `on_key` handler and the DataTable's built-in key handling. The result: pressing `j` in the picker both moves the picker's selection AND scrolls the DataTable underneath.

**Why it happens:** Textual routes key events up the DOM from the focused widget. If the picker Widget has focus and handles `j` for its own cursor movement, but does not stop propagation, the event continues up to `MainScreen.on_key` which calls `action_cursor_down` on the DataTable.

**Existing precedent in the codebase:** `QuickAddBar.on_key` correctly calls `event.prevent_default()` and `event.stop()` for Escape (lines 197-200). The filter picker must follow this same pattern for all keys it owns.

**Consequences:** Pressing letter keys while picker is open types in the picker and simultaneously triggers BINDINGS on MainScreen (`a` opens QuickAddBar, `e` opens edit, `d` shows delete confirm). This causes concurrent UI state — both the picker and the delete confirmation can be visible at once.

**Prevention:**
1. The filter picker widget must call `event.stop()` (stops bubbling) for every key it handles internally.
2. While the picker is open, MainScreen's BINDINGS for `a`, `e`, `d`, `/` must be disabled or guarded. Use a `_picker_open: bool` flag and early-return in those action methods when true.
3. Focus must move explicitly to the picker widget on open and back to the DataTable on close.

**Detection:** Open a filter picker, then press `a`. If the QuickAddBar also opens, propagation is not stopped.

**Phase:** FILT-01/02/03 implementation phase.

---

### Pitfall 6: DataTable Loses Row Position When Stats Bar Forces Re-render

**What goes wrong:** When a stats bar is added that reactively updates on item add/delete/filter change, and its update mechanism triggers a full `_load_view()` call, the DataTable is cleared and repopulated (`table.clear(columns=True)` then `add_row`). This resets the cursor to row 0. The user's selected row is lost on every stats update.

**Why it happens:** `_load_view()` calls `table.clear(columns=True)` unconditionally (line 217). The DataTable has no built-in "preserve cursor position across clear" behavior. After the clear, the cursor always starts at row 0. If stats updates are wired to the same `_load_view()` call that populates the table, frequent stats changes (e.g. on every filter keystroke) reset the cursor constantly.

**Consequences:** User scrolls to item 50, applies a filter, item 50 is still in the filtered results but cursor jumps back to row 1. User edits an item, saves, `on_screen_resume` fires `_load_view()`, cursor resets to row 1 even if item was at row 30.

**Prevention:**
1. Separate stats computation from DataTable population. Stats bar should query counts independently (e.g. a separate `_compute_stats()` function), not as a side effect of `_load_view()`.
2. After repopulating the DataTable, restore the cursor to the previously selected row key (not row index), using `table.move_cursor(row=N)` with the row index that corresponds to the same `row_key.value` as before the clear.
3. Save `_last_row_key: Optional[str]` before any `_load_view()` call, then after repopulation find the new row index for that key and restore it.

**Detection:** Scroll to item 10 in the flat list. Press a filter key. If the cursor jumps to row 0, the pitfall is present.

**Phase:** STAT-01 implementation phase (stats bar) and VIEW-01 (flat list) should both include cursor preservation as an explicit requirement.

---

## Moderate Pitfalls

---

### Pitfall 7: Splash Screen Push Order Fires MainScreen `on_mount` Before Splash Is Visible

**What goes wrong:** If `SplashScreen` is implemented by pushing it in `PossessionApp.on_mount()` after `MainScreen` is already composed, MainScreen's `on_mount` fires and calls `_load_view()` (a DB query) while the splash is nominally on top. The splash appears momentarily with the DB already loaded beneath it. On fast machines this is fine; on slow machines or large databases, the first keypress "dismiss" happens during DB load and is lost.

**More dangerous variant:** If the push order is reversed — SplashScreen pushed first, MainScreen pushed second — the MainScreen mounts and its `on_screen_resume` fires when SplashScreen is dismissed. This is actually the correct behavior.

**Current `app.py` pattern (line 20-21):**
```python
def on_mount(self) -> None:
    self.push_screen(MainScreen())
```

If SplashScreen is inserted before this, `MainScreen` is never mounted until the splash is dismissed. Correct. If SplashScreen is inserted after (as a second push), MainScreen mounts first and immediately starts loading data in the background.

**Prevention:** Push SplashScreen first, push MainScreen as the base screen (either via `SCREENS` class variable or push in on_mount before splash). The correct Textual pattern is:

```python
# CORRECT: splash is on top, main is underneath ready
def on_mount(self) -> None:
    self.push_screen(MainScreen())
    self.push_screen(SplashScreen())  # pushed second, shown on top
```

Or use `install_screen` + `push_screen("splash")` for named screens.

**Confidence:** MEDIUM — Screen push ordering in Textual follows a stack (last pushed = on top). This is standard Textual design. Verify that `on_screen_resume` fires correctly on MainScreen when SplashScreen is popped.

**Phase:** SPSH-01 implementation phase. Write the push order in the plan before coding.

---

### Pitfall 8: Detail Panel Breaks `DataTable { height: 1fr; }` Layout

**What goes wrong:** The current `MainScreen.CSS` has `DataTable { height: 1fr; }` which makes the table fill all remaining vertical space. When a horizontal detail panel is added (split layout: table left, detail right), the CSS rule still applies but now the `DataTable` is inside a horizontal container. `1fr` in a vertical context means "fill remaining height"; inside a `Horizontal` container, `height: 1fr` means fill the parent's height, which is now controlled by the container — the behavior is correct but unexpected to developers who assume `1fr` always means "fill the screen."

**The actual breakage:** Adding the detail panel as a sibling of the DataTable in the vertical compose stack (not inside a horizontal container) causes the DataTable and panel to stack vertically, each taking half the screen. The split layout only works if both are wrapped in a `Horizontal` container.

**Focus problem:** When the detail panel opens (on Enter key), `DataTable.focus()` is not automatically retained unless explicitly called. If the panel contains any focusable widget (a `Static` with `can_focus=True`, or a `ScrollableContainer`), focus moves to the panel and `j`/`k` navigation stops working on the table.

**Prevention:**
1. Wrap `DataTable` + detail panel in an explicit `Horizontal` container in `compose()`.
2. On detail panel open, do NOT move focus to the panel unless the user presses Tab explicitly. The DataTable should keep focus. Set `can_focus=False` on all detail panel widgets.
3. Remove or override the `DataTable { height: 1fr; }` rule to `Horizontal { height: 1fr; }` so the split container fills the screen, not just the table.

**Detection:** Add the panel as a sibling of DataTable without a Horizontal container. The layout will stack vertically. Add a Horizontal container. Verify `j`/`k` still moves the DataTable cursor after pressing Enter.

**Phase:** PANEL-01 implementation phase.

---

### Pitfall 9: Quick-Add Label Overflows `height: auto` Widget Bounds

**What goes wrong:** `QuickAddBar` currently composes a single `Input` with `height: auto; dock: bottom;`. Adding a `Static` label above the `Input` inside the same widget adds a second child with its own height requirement. Textual's `height: auto` on the parent widget resolves to the sum of children heights, but only if children have explicit or auto heights. If the `Static` inherits a default height of `1` and the `Input` is also `1`, the widget should be `2` units tall. In practice, `dock: bottom` with `height: auto` and two children can render incorrectly in some Textual versions — the label may clip outside the docked area or the Input may disappear.

**Why it happens:** Textual's layout engine resolves `height: auto` for docked widgets differently than for inline widgets. The bottom dock reserves space equal to the widget's computed height, but if the computed height is wrong (off by one, or the Static is not counted), the label renders behind the DataTable.

**Specific risk:** `QuickAddBar.DEFAULT_CSS` uses `dock: bottom`. With one child (`Input`), the dock height is 1 cell. With two children (`Static` + `Input`), the expected dock height is 2 cells. If Textual computes this correctly, the table shrinks by one extra row when the bar is open — acceptable. If it does not, the label appears at the wrong position or is invisible.

**Prevention:**
1. Add explicit `height: 1;` to both the `Static` label and the `Input` in `QuickAddBar.DEFAULT_CSS`.
2. Set `height: 2;` explicitly on `QuickAddBar` when the label is visible, not `height: auto`.
3. Alternatively, use a single `Input` with a format-string `placeholder` that already includes the format hint. This avoids the two-child layout entirely. This is the lowest-risk approach.

**Detection:** Open the QuickAddBar with the label present. Check that the label is visible, the Input is below it, and the DataTable has not grown to overlap the bar.

**Confidence:** MEDIUM — Textual layout with `dock: bottom` and `height: auto` is known to have edge cases. The simplest fix (use placeholder text with the format hint) avoids the layout problem entirely.

**Phase:** QADD-04 implementation phase.

---

### Pitfall 10: VIM Filter Picker Intercepting `/` Before It Reaches the Filter Bar

**What goes wrong:** The existing `BINDINGS` on `MainScreen` include `("/", "action_open_filter", "Filter")`. The v1.1 design replaces the raw `Input` filter with VIM-style filter pickers (`r` for Room, `c` for Container, `C` for Category). If both the old `/` filter binding and the new picker bindings exist simultaneously during development (common when adding features incrementally), pressing `/` opens the old `Input` filter bar while the picker is bound but not yet wired. Users see conflicting UI.

**Prevention:** In the implementation plan for FILT-01, explicitly mark the old `("/ ", "action_open_filter", "Filter")` binding for removal. Do not add the new picker bindings alongside the old one — remove the old one in the same phase.

**Detection:** Check `MainScreen.BINDINGS` after adding picker bindings. If `"/"` still appears, the old filter is still active.

**Phase:** FILT-01.

---

## Minor Pitfalls

---

### Pitfall 11: `on_input_submitted` Handlers Conflict When Multiple Inputs Are Visible

**What goes wrong:** `MainScreen.on_input_submitted` dispatches on `event.input.id` to distinguish the delete confirmation from other inputs. If the filter picker uses an `Input` widget inside a child widget (e.g. a search-within-picker input), `Input.Submitted` events bubble up to `MainScreen.on_input_submitted`. If the picker's Input has an id that is not handled by the `if event.input.id == "delete-confirm":` guard, the handler falls through silently. This is not a crash but the event is consumed by the wrong handler level.

**Prevention:** Filter picker Inputs should handle their own `on_input_submitted` inside the picker Widget, and call `event.stop()` to prevent bubbling. Only MainScreen-level Inputs (`#delete-confirm`, `#filter-input`) should be handled in the Screen's handler.

**Phase:** FILT-01.

---

### Pitfall 12: Stats Bar Reactive Count Is Stale After DataTable Clear

**What goes wrong:** If the stats bar uses a Textual `reactive` attribute (e.g. `item_count = reactive(0)`) and the watcher updates a `Static` label, the count is only refreshed when the reactive is explicitly set. After `_load_view()` repopulates the DataTable, if `self.item_count = len(self._items)` is not called, the stats bar shows the old count.

**Specific scenario:** User adds an item via QuickAddBar → `on_quick_add_bar_item_saved` fires → `_load_view()` called → DataTable updated. If the stats bar is not updated in `_load_view()`, it shows the count from the previous load.

**Prevention:** At the end of `_load_view()`, always update the stats bar counters. Either set reactive attributes or call a `_update_stats()` method. Do not rely on Textual's reactivity alone — explicit synchronization at the same call site as `_load_view()` is safer.

**Phase:** STAT-01.

---

### Pitfall 13: `_last_key` State Leaks Across Feature Boundaries

**What goes wrong:** The VIM `gg` sequence is tracked via `_last_key: str = ""` in `on_key`. When the flat list phase adds filter pickers with their own key handling, a partial key sequence (user pressed `g` then opened a picker) leaves `_last_key == "g"`. When the picker closes and the user presses `g` again, the sequence fires `gg` (jump to top) even though the user did not intend two consecutive `g` keypresses.

**Prevention:** Reset `_last_key = ""` whenever any overlay (filter picker, detail panel, quickadd bar) opens. This is a one-line addition to each open action.

**Phase:** FILT-01 (first phase to add an overlay).

---

### Pitfall 14: `on_screen_resume` Fires Unexpectedly After Splash Screen Dismiss

**What goes wrong:** `MainScreen.on_screen_resume` calls `_load_view()` whenever the screen returns to the foreground. This was added to reload after the edit screen. When a SplashScreen is pushed on top of MainScreen and then popped (on any keypress), `on_screen_resume` fires again and calls `_load_view()` — a DB query. This is harmless functionally but adds a DB query on every launch that is invisible to the developer.

**Prevention:** This is acceptable as-is since `_load_view()` is fast for typical inventory sizes. Document it as expected behavior. If performance becomes an issue, add a `_initial_load_done: bool` flag to skip the resume reload when the app first starts.

**Phase:** SPSH-01.

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| VIEW-01: Flat list | Dead `_view_mode` guards silently block e/d/Enter | Audit all six `_view_mode` references; replace or remove before any other feature |
| VIEW-01: Flat list | Breadcrumb occupies space after drill-down removed | Remove from `compose()` in same commit as state machine removal |
| VIEW-01: Flat list | `q` exits app on flat list | Decide and document `q` behavior before implementation |
| FILT-01/02/03: Filter pickers | Key events leak through picker to DataTable | `event.stop()` in picker; `_picker_open` guard in Screen actions |
| FILT-01: `/` binding conflict | Old filter bar and new pickers coexist | Remove old `/` binding in the same phase that adds picker bindings |
| SPSH-01: Splash screen | Push order fires MainScreen `on_mount` before splash visible | Push MainScreen first, then push SplashScreen on top |
| SPSH-01: Splash screen | `on_screen_resume` fires on splash dismiss | Accept as-is; document as known behavior |
| STAT-01: Stats bar | Stale count after `_load_view()` | Explicitly update stats at end of `_load_view()` |
| STAT-01: Stats bar | Cursor resets to row 0 on stats update | Separate stats query from table repopulation; restore cursor by key |
| PANEL-01: Detail panel | `DataTable { height: 1fr; }` breaks split layout | Wrap table+panel in `Horizontal`; move `1fr` to container |
| PANEL-01: Detail panel | Focus moves to panel, breaking j/k navigation | Set `can_focus=False` on all panel widgets |
| THEME-01: Transparent BG | Black background in tmux/multiplexers | Make transparent opt-in via `--transparent` flag; default to `$surface` |
| QADD-04: Quick-add label | Label clips under DataTable in `height: auto` dock | Use placeholder text instead of separate Static; or set explicit `height: 2` |
| All overlays | `_last_key` leaks partial gg sequence across open/close | Reset `_last_key = ""` on every overlay open |
| All new Input widgets | `on_input_submitted` events bubble to MainScreen handler | `event.stop()` inside child widget handlers; do not rely on Screen-level dispatch |

---

## Sources

- Codebase analysis (HIGH confidence): `/possession/tui/screens/main.py`, `/possession/tui/widgets/quickadd.py`, `/possession/tui/widgets/breadcrumb.py`, `/possession/tui/app.py` — all read directly
- Textual widget lifecycle, event propagation, CSS `transparent`, dock layout: training knowledge (MEDIUM confidence — behavior is consistent with Textual ≥0.47.0 patterns but not verified against current Textual changelog)
- Terminal multiplexer transparency behavior: training knowledge + terminal ecosystem knowledge (MEDIUM confidence — verify by manual test in tmux before shipping THEME-01)
- Note: WebSearch and WebFetch were unavailable during this research session. Claims about Textual internals should be validated against the Textual changelog at https://github.com/Textualize/textual/blob/main/CHANGELOG.md before implementation.
