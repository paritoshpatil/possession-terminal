# Research Summary: v1.1 UI Overhaul

**Project:** possession-terminal v1.1
**Domain:** Python + Textual TUI inventory manager — UI overhaul milestone
**Researched:** 2026-02-24
**Confidence:** MEDIUM-HIGH

---

## Executive Summary

The v1.1 UI overhaul is a focused refactor of an already-working Textual 8.0.0 app. No new dependencies are needed. The work falls into two categories: structural changes (migrating from drill-down navigation to a flat list with filter pickers) and additive polish (splash screen, stats bar, top bar, detail panel, persistent format label). The structural migration — VIEW-01, the flat list default — is the load-bearing change that everything else builds on. It must land first and completely, because six separate guards in `main.py` silently no-op on `e`, `d`, and Enter if any `_view_mode` reference is left in place.

The recommended architecture keeps Textual's standard primitives throughout: `ModalScreen` for the filter pickers (not a widget overlay), CSS `.hidden` class toggling for show/hide (not dynamic `mount()`/`remove()`), and `MainScreen` as the sole owner of filter state and DB calls. Widgets (StatsBar, ItemDetailPanel) receive computed data from the screen; they do not query the database directly. This is consistent with the pattern already established in v1.0 and keeps the codebase easy to reason about.

The primary risk is the transparent background feature (THEME-01): `background: transparent` works correctly in native terminal emulators but renders as opaque black in tmux, screen, and most SSH sessions — precisely the environment TUI power users live in. The mitigation is to ship transparent as an opt-in flag (`--transparent`), not the default, and keep `$surface` as the default background. Every other risk in this milestone is a known Textual pattern with clear prevention steps documented in PITFALLS.md.

---

## Key Findings

### Recommended Stack

No new packages required. Textual 8.0.0 is already installed and satisfies all needs: `ModalScreen` for filter pickers, `Header` or docked `Static` for the top bar, `Theme` dataclass for programmatic theme registration, and `COLORFGBG` env var for dark/light detection. The only new file-level addition is `possession/tui/theme_detect.py` for the `detect_color_mode()` utility.

**Core technologies:**
- **Textual 8.0.0** (installed) — all new widgets, screens, and CSS are in stdlib; no upgrades needed
- **Python `os` stdlib** — `COLORFGBG` env var parsing for dark/light detection; no third-party color detection packages
- **Textual `Theme` dataclass** — programmatic theme registration (verify exact field names against 8.0.0 source before use)
- **Textual CSS `background: transparent`** — terminal background passthrough; confirmed supported in Textual ≥0.38.0

**Key version note:** `pyproject.toml` specifies `textual>=0.47.0` but 8.0.0 is installed — a major jump. All new code should target the 8.0.0 API. Consider tightening the constraint to `textual>=8.0.0`.

### Expected Features

**Must have (table stakes):**
- **VIEW-01** — Flat item list as default view; the current drill-down (rooms → containers → items) is removed and replaced with a flat list plus filter pickers
- **STAT-01** — Stats bar (item count, room count, container count, total value); standard in inventory tools
- **TOPBAR-01** — Persistent top bar with app name; orients users at all times
- **PANEL-01** — Item detail panel on Enter; the DataTable columns are too narrow for full field data
- **QADD-04** — Persistent format label above the QuickAddBar input; placeholder disappears on first keystroke, losing field-order context

**Should have (differentiators):**
- **FILT-01/02/03** — VIM-style filter pickers for Room, Container, Category; keyboard-first, no typo friction, consistent with VIM nav conventions already in v1.0
- **SPSH-01** — Splash screen; sets identity on launch, standard TUI convention, zero functional cost

**Defer to v1.2+:**
- Position highlighting in QuickAddBar label (nice-to-have; slash counting adds ~15 LOC)
- `--no-splash` CLI flag
- Stacked multi-field filters (room AND category simultaneously)
- Fuzzy/substring matching in filter pickers (exact prefix match is sufficient for small value sets)

### Architecture Approach

The v1.1 target architecture replaces the three-mode state machine (`_view_mode: "rooms" | "containers" | "items"`) with a flat filter model (`_filter_room_id`, `_filter_container_id`, `_filter_category_id`, `_filter_text`). `MainScreen` owns all filter state; `FilterPickerScreen(ModalScreen)` handles picker UI and returns a selected string via `dismiss()`; `MainScreen` resolves strings to IDs and reloads. The `Horizontal` layout container wraps `DataTable` + `ItemDetailPanel` for the split-pane detail view. `StatsBar` and `ItemDetailPanel` are display-only widgets that receive data from `MainScreen` — they do not query the DB.

**Major components:**
1. **`SplashScreen(Screen)`** — new, in `screens/splash.py`; full-screen ASCII art, any-key dismiss via `switch_screen(MainScreen())`
2. **`MainScreen`** — heavily modified; removes drill-down state machine, adds filter state, wires all new widgets
3. **`FilterPickerScreen(ModalScreen)`** — new, in `screens/filter_picker.py`; reusable across Room/Container/Category via `__init__` params
4. **`StatsBar(Static)`** — new, in `widgets/statsbar.py`; display-only, updated by MainScreen after each `_load_items()` call
5. **`ItemDetailPanel(Widget)`** — new, in `widgets/detail_panel.py`; side panel (width: 35), `can_focus=False`, toggled with `.hidden` class
6. **`QuickAddBar`** — modified; adds `Static` format label in `compose()`, explicit `height: 2` required
7. **`Breadcrumb` widget** — deleted; replaced by `Header()` for the top bar and filter-state indicator in `StatsBar`

**Data flow (filter picker):**
```
User presses 'r' → action_pick_room_filter()
  → push_screen(FilterPickerScreen("Filter by Room", room_names), callback)
  → User selects → dismiss("Kitchen")
  → _on_room_filter_selected("Kitchen") → resolve to room_id=3
  → _filter_room_id = 3 → _load_items() → StatsBar.refresh_stats()
```

### Critical Pitfalls

1. **Dead `_view_mode` guards silently block e/d/Enter (Pitfall 1)** — Six locations in `main.py` check `_view_mode` before allowing item actions. Remove ALL of them in the same commit as VIEW-01. Test `e`, `d`, and Enter on the first item immediately after migration.

2. **Transparent background fails in tmux/multiplexers (Pitfall 4)** — `background: transparent` renders as opaque black in tmux. Ship as `--transparent` opt-in flag; keep `$surface` as default. Verify in tmux before marking THEME-01 done.

3. **Filter picker key events leak to DataTable (Pitfall 5)** — Without `event.stop()` in the picker, pressing `j` in the picker also scrolls the DataTable. Guard: `event.stop()` in picker on all owned keys + `_picker_open` flag in MainScreen actions.

4. **DataTable `height: 1fr` breaks split layout (Pitfall 8)** — Adding `ItemDetailPanel` as a sibling of `DataTable` without a `Horizontal` wrapper produces a vertical stack. Move `height: 1fr` from `DataTable` to the `Horizontal` container. Set `can_focus=False` on all panel widgets to preserve j/k navigation.

5. **Cursor resets to row 0 on every `_load_items()` call (Pitfall 6)** — `table.clear(columns=True)` always resets cursor. Save `_last_row_key` before clearing, restore it by key (not index) after repopulation. This matters most for STAT-01 and PANEL-01 phases.

---

## Implementation Approach

The 8 v1.1 features map to 3 phases based on dependency topology. Each phase has a clear gate condition.

### Feature Dependency Map

```
SPSH-01    TOPBAR-01    QADD-04        (no dependencies — any order)
     \          |           /
      [can be batched with VIEW-01]

VIEW-01                                (prerequisite for everything below)
   |
   +--------> STAT-01                 (DB counts + filter state)
   |
   +--------> PANEL-01                (detail panel, reuses _items)
   |
   +--------> FILT-01 / FILT-02 / FILT-03  (most complex; needs filter state)
```

### Phase 4: Foundation — Flat List + Visual Anchors

**Features:** VIEW-01, TOPBAR-01, THEME-01, QADD-04, SPSH-01

**Rationale:** VIEW-01 is the prerequisite for everything else; TOPBAR-01 and THEME-01 are isolated CSS changes that establish the visual baseline all subsequent phases build on; QADD-04 and SPSH-01 are fully independent and low-risk. Bundle the independent features with the foundation to avoid partial-looking app states between phases.

**Delivers:** A fully working flat-list inventory view with terminal-native theming, persistent top bar, splash screen, and corrected QuickAddBar format hint. The drill-down state machine is gone. Edit, delete, and add all continue to work.

**Must avoid:**
- Leaving any `_view_mode` guard in `main.py` after VIEW-01 lands (Pitfall 1)
- Leaving `Breadcrumb` in `compose()` after removing drill-down (Pitfall 2)
- `q` key behavior must be explicitly decided (Pitfall 3) — recommend binding `q` to app exit
- Transparent background must be opt-in, not default (Pitfall 4)
- Splash push order: push `MainScreen` first, then push `SplashScreen` on top (Pitfall 7)
- QuickAddBar label height: set explicit `height: 2` on the widget, not `height: auto` (Pitfall 9)

**Implementation order within phase:**
1. VIEW-01 (remove drill-down state machine first — all other changes in this phase are safe once this is done)
2. TOPBAR-01 + THEME-01 (CSS-only changes)
3. SPSH-01 (new file, modify `on_mount` in `app.py`)
4. QADD-04 (modify `quickadd.py` compose only)

---

### Phase 5: Data Layer — Stats Bar + Detail Panel

**Features:** STAT-01, PANEL-01

**Rationale:** Both depend on VIEW-01 (flat item list must exist). Both are medium-complexity additions that share the compose layout rework in `MainScreen` (adding `Horizontal` container). Doing them together means the `Horizontal` layout wrapper is introduced once and both features validate against it simultaneously.

**Delivers:** A stats bar with live item/room/container/value counts, and a right-side detail panel that shows all item fields when Enter is pressed. The main list and detail panel coexist in a split-pane layout.

**Must avoid:**
- Cursor reset to row 0 on stats update — separate stats computation from `table.clear()` (Pitfall 6)
- Stale stats count — always call `StatsBar.refresh_stats()` at the end of `_load_items()` (Pitfall 12)
- Focus moving to detail panel — `can_focus=False` on all `ItemDetailPanel` children (Pitfall 8)
- `DataTable { height: 1fr }` breaking split layout — move rule to `Horizontal { height: 1fr }` (Pitfall 8)
- DB queries in widget methods — `StatsBar` and `ItemDetailPanel` receive data from `MainScreen` (Anti-pattern 3)

**Implementation order within phase:**
1. STAT-01 (simpler; no layout change; adds `StatsBar` above DataTable)
2. PANEL-01 (introduces `Horizontal` wrapper — larger layout change; validate CSS after)

---

### Phase 6: Keyboard UX — Filter Pickers

**Features:** FILT-01 (Room), FILT-02 (Container), FILT-03 (Category)

**Rationale:** Most complex feature set; depends on VIEW-01's filter state (`_filter_room_id` etc.) being in place. All three pickers share one `FilterPickerScreen(ModalScreen)` class, so FILT-01/02/03 are implemented together as one unit. Placed last because the picker needs stable layout (from Phase 5) to test keyboard interaction without layout regressions.

**Delivers:** VIM-style modal filter pickers triggered by `r` (Room), `c` (Container), `t` (Category). Each picker narrows by typing, navigates with `j`/`k`, confirms with Enter, dismisses without change on Escape. Active filters display in the stats bar / filter indicator. `/` text filter continues to work alongside pickers.

**Must avoid:**
- Key event leakage from picker to DataTable — `event.stop()` in picker for all owned keys; `_picker_open` guard on MainScreen actions (Pitfall 5)
- Old `/` filter binding coexisting with new picker bindings — remove `action_open_filter` and `/` binding in this phase (Pitfall 10)
- `on_input_submitted` bubbling from picker input to MainScreen handler — `event.stop()` inside `FilterPickerScreen` (Pitfall 11)
- `_last_key` leaking `g` state across picker open/close — reset `_last_key = ""` on picker open (Pitfall 13)
- Widget overlay approach instead of `ModalScreen` — use `push_screen(FilterPickerScreen(...), callback)` (Anti-pattern 1)

**Implementation order within phase:**
1. `FilterPickerScreen(ModalScreen)` — one reusable class, Room picker first to validate the pattern
2. FILT-02 (Container) and FILT-03 (Category) — wire additional bindings; reuse same screen class
3. Filter indicator in StatsBar — show active filter context (e.g. `[Room: Kitchen]`)

---

## Risk Register

| Risk | Severity | Likelihood | Mitigation |
|------|----------|------------|------------|
| `_view_mode` guards left in place after VIEW-01 migration | HIGH | HIGH | Audit checklist of all 6 locations; test e/d/Enter immediately after migration |
| Transparent background breaks in tmux | MEDIUM | HIGH | Ship as `--transparent` opt-in; keep `$surface` as default |
| Filter picker key events leak to DataTable | HIGH | MEDIUM | `event.stop()` in picker; `_picker_open` guard in Screen actions |
| Cursor resets to row 0 on table reload | MEDIUM | HIGH | Save/restore cursor by row key in `_load_items()` |
| Detail panel breaks DataTable `height: 1fr` layout | MEDIUM | MEDIUM | Use `Horizontal { height: 1fr }` not `DataTable { height: 1fr }` |
| `Theme` dataclass field names differ in Textual 8.0.0 | LOW | MEDIUM | Verify field names against installed source before implementing programmatic theme |
| App-level CSS `Screen { background: transparent }` not inherited by pushed screens | LOW | MEDIUM | Add `background: transparent` to each Screen's own CSS; smoke-test in Phase 4 |
| QuickAddBar `height: auto` clips format label | LOW | MEDIUM | Use explicit `height: 2` on QuickAddBar when label is present |

---

## Open Questions

These decisions must be made before or during Phase 4 implementation — they are not purely technical and require a product judgment call.

1. **What does `q` do in flat-list mode?**
   - v1.0: `q` goes back one drill-down level (exits app at top level)
   - v1.1 options: (a) `q` exits the app immediately (no levels to go back through), (b) `q` does nothing and only `ctrl+c` / `ctrl+q` exits
   - Recommendation: (a) `q` exits; consistent with vim-style TUI convention that `q` = quit when there's nothing to dismiss

2. **Top bar: built-in `Header()` or custom `Static`?**
   - ARCHITECTURE.md recommends `Header()` (lower maintenance, theme-integrated)
   - FEATURES.md recommends custom `Static` (full control, no unwanted clock/command-palette behavior)
   - Decision needed: if `show_clock=False` is sufficient, use `Header(show_clock=False)`. If command-palette-on-click is disruptive, use custom `Static`.
   - Recommendation: start with `Header(show_clock=False)` — simpler; switch to custom `Static` if behavior is annoying during testing

3. **Transparent background: opt-in flag or always-on?**
   - PITFALLS.md strongly recommends opt-in via `--transparent`
   - FEATURES.md specifies THEME-01 as transparent background
   - Decision: ship transparent as opt-in for v1.1; revisit as default in v1.2 once tmux behavior is documented

4. **Category filter: DB-side or client-side?**
   - `list_items()` currently accepts `room_id` and `container_id` but not `category_id`
   - Adding `category_id` to `list_items()` requires a `models.py` change
   - Client-side filtering (filter `_all_items` in Python after DB load) works for typical inventory sizes
   - Recommendation: client-side for v1.1; add to models in v1.2 if performance becomes an issue

5. **Breadcrumb widget: delete or repurpose?**
   - ARCHITECTURE.md suggests repurposing Breadcrumb as a filter-context indicator
   - Simpler option: delete Breadcrumb, add filter-context display to `StatsBar`
   - Recommendation: delete `breadcrumb.py`; encode active filter context (e.g. `[Room: Kitchen]`) into the `StatsBar` content — one fewer widget class to maintain

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | No new packages; Textual 8.0.0 confirmed installed; all APIs targeted are stable since ≥0.20 |
| Features | HIGH | Feature specs verified against actual source code (`main.py`, `models.py`, `quickadd.py`); `list_items()` filter params confirmed |
| Architecture | HIGH | Based on direct source code analysis + Textual ≥0.47.0 API knowledge; ModalScreen, ListView, Horizontal all stable since ≥0.15.0 |
| Pitfalls | MEDIUM-HIGH | Codebase-specific pitfalls (view mode guards, breadcrumb, q key) are HIGH confidence; Textual internals (transparent CSS in tmux, dock+height:auto edge cases) are MEDIUM confidence — require smoke-test verification |

**Overall confidence:** MEDIUM-HIGH

### Gaps to Address

- **`Theme` dataclass field names in Textual 8.0.0** — Before implementing programmatic theme registration, read the installed Textual source (`import textual.theme; help(textual.theme.Theme)`) to confirm field names. Fields `background`, `surface`, `primary`, `foreground` are likely correct but should be verified.

- **`background: transparent` inheritance across pushed screens** — Smoke-test in Phase 4 whether App-level `Screen { background: transparent }` CSS applies to screens pushed via `push_screen()`, or whether each `Screen` subclass needs its own CSS rule. This determines whether the theme CSS lives in `PossessionApp.CSS` or must be duplicated in `MainScreen.DEFAULT_CSS`, `SplashScreen.DEFAULT_CSS`, etc.

- **`on_screen_resume` firing on splash dismiss** — Confirmed as expected behavior (Pitfall 14); document in SPSH-01 phase plan so it is not mistaken for a bug during implementation.

- **`Header` vs custom `Static` for top bar** — Final decision deferred to Phase 4 implementation. The behavior difference (`Header` command palette on click) should be evaluated against the actual Textual 8.0.0 `Header` widget behavior, which may differ from training knowledge.

---

## Sources

### Primary (HIGH confidence)
- Direct source code analysis — `possession/tui/screens/main.py`, `app.py`, `screens/edit.py`, `widgets/breadcrumb.py`, `widgets/quickadd.py`, `models.py` (read 2026-02-24)
- Textual 8.0.0 install log from project repo — confirmed installed version
- `list_items()` filter parameters — verified directly from `models.py` source

### Secondary (MEDIUM confidence)
- Textual ≥0.47.0 API knowledge (training data, August 2025 cutoff) — `ModalScreen`, `ListView`, `Header`, `Horizontal`, `background: transparent`, `App.dark`, `Static.update()`
- `COLORFGBG` env var convention — established Unix terminal convention (xterm/VTE sources)
- `COLORTERM` truecolor detection — documented at termstandard/colors (de facto standard)
- TUI UX conventions (splash screens, split panes, filter pickers) — htop, lazygit, ranger, neovim patterns

### Tertiary (LOW confidence — verify before use)
- `Theme` dataclass exact field names in Textual 8.0.0 — inferred from ≥0.75 patterns; verify against installed source
- `background: transparent` behavior in tmux — based on terminal ecosystem knowledge; requires manual test
- `dock: bottom` + `height: auto` with two children — Textual layout edge case; requires smoke-test

---

*Research completed: 2026-02-24*
*Ready for roadmap: yes*
