---
phase: quick-3
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - possession/schema.sql
  - possession/settings.py
  - possession/tui/app.py
  - possession/tui/screens/theme_picker.py
  - possession/tui/screens/main.py
autonomous: true
requirements: [QUICK-3]

must_haves:
  truths:
    - "User can press X in MainScreen to open a theme picker modal"
    - "Theme picker shows all built-in themes with current theme marked"
    - "Selecting a theme applies it immediately (live CSS update)"
    - "Selected theme persists across app restarts (stored in SQLite)"
    - "Theme picker includes a transparent toggle that persists"
  artifacts:
    - path: "possession/settings.py"
      provides: "get_setting / set_setting functions backed by SQLite settings table"
      exports: ["get_setting", "set_setting", "THEMES", "build_css"]
    - path: "possession/tui/screens/theme_picker.py"
      provides: "ThemePickerScreen modal"
      exports: ["ThemePickerScreen"]
    - path: "possession/schema.sql"
      provides: "settings table migration"
      contains: "CREATE TABLE IF NOT EXISTS settings"
  key_links:
    - from: "possession/tui/screens/main.py"
      to: "ThemePickerScreen"
      via: "action_open_theme_picker / X binding"
    - from: "ThemePickerScreen"
      to: "possession/settings.py set_setting"
      via: "dismiss callback persisting theme + transparent"
    - from: "possession/tui/app.py"
      to: "possession/settings.py get_setting"
      via: "load saved theme in __init__ before CSS is set"
---

<objective>
Add multi-theme switching with SQLite persistence and a transparent background toggle.

Purpose: Users can switch between built-in color schemes without restarting, and their choice survives restarts.
Output: ThemePickerScreen modal reachable from MainScreen (X key), 5 built-in themes, transparent toggle, settings table in SQLite.
</objective>

<execution_context>
@/Users/paritoshpatil/.claude/get-shit-done/workflows/execute-plan.md
@/Users/paritoshpatil/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
</context>

<tasks>

<task type="auto">
  <name>Task 1: Settings persistence — schema migration + settings.py module</name>
  <files>possession/schema.sql, possession/settings.py</files>
  <action>
**possession/schema.sql** — append at the end (after items table):

```sql
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
```

**possession/settings.py** — new file. Implement:

1. `THEMES` dict — maps theme name (str) to a CSS variable block (str). Include exactly these 5 themes with their color palettes:

   - `"catppuccin-mocha"` — primary: #cba6f7, primary-darken-2: #fab387, surface: #1e1e2e, surface-darken-1: #11111b, text: #cdd6f4, text-muted: #bac2de
   - `"dracula"` — primary: #bd93f9, primary-darken-2: #ff79c6, surface: #282a36, surface-darken-1: #1e1f29, text: #f8f8f2, text-muted: #6272a4
   - `"nord"` — primary: #88c0d0, primary-darken-2: #81a1c1, surface: #2e3440, surface-darken-1: #242933, text: #eceff4, text-muted: #d8dee9
   - `"tokyo-night"` — primary: #7aa2f7, primary-darken-2: #bb9af7, surface: #1a1b26, surface-darken-1: #16161e, text: #c0caf5, text-muted: #9aa5ce
   - `"gruvbox"` — primary: #d3869b, primary-darken-2: #fabd2f, surface: #282828, surface-darken-1: #1d2021, text: #ebdbb2, text-muted: #bdae93

2. `build_css(theme_name: str, transparent: bool = False) -> str` — generates full app CSS string from THEMES[theme_name]. Use the same CSS structure as PossessionApp._CSS_DEFAULT in app.py (variable block + Screen/DataTable rules). Screen background is `transparent` if transparent=True else `$surface`. Raise KeyError if theme_name not in THEMES. Default to "catppuccin-mocha" if lookup fails (safe fallback).

   The variable block must include all these vars derived from the theme palette:
   - `$primary`, `$primary-darken-2`, `$surface`, `$surface-darken-1`, `$text`, `$text-muted`
   - `$panel: $primary-darken-2`
   - `$border: {primary}`
   - `$block-cursor-background: {primary}`, `$block-cursor-foreground: {surface}`
   - `$block-cursor-blurred-background: {primary}40`
   - `$scrollbar`, `$scrollbar-hover`, `$scrollbar-active`: all set to `{primary-darken-2}`
   - `$scrollbar-background`, `$scrollbar-corner-color`: both set to `{surface}`

3. `get_setting(db_path: Path, key: str, default: str = "") -> str` — SELECT value FROM settings WHERE key=?; return default if no row. Use per-call connection pattern (open/operate/close).

4. `set_setting(db_path: Path, key: str, value: str) -> None` — INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?); commit; close.

Settings keys used by the app:
- `"theme"` — theme name string, default `"catppuccin-mocha"`
- `"transparent"` — `"1"` or `"0"`, default `"0"`
  </action>
  <verify>
    <automated>python -c "
import sys; sys.path.insert(0, '.')
from possession.settings import THEMES, build_css, get_setting, set_setting
assert len(THEMES) == 5
css = build_css('catppuccin-mocha', False)
assert '\$primary' not in css and 'cba6f7' in css
css_t = build_css('catppuccin-mocha', True)
assert 'transparent' in css_t
print('settings.py OK')
"
</automated>
  </verify>
  <done>THEMES has 5 entries; build_css produces valid CSS strings with correct colors; get_setting/set_setting follow per-call pattern; settings table in schema.sql.</done>
</task>

<task type="auto">
  <name>Task 2: ThemePickerScreen modal + wire into app</name>
  <files>possession/tui/screens/theme_picker.py, possession/tui/app.py, possession/tui/screens/main.py</files>
  <action>
**possession/tui/screens/theme_picker.py** — new ModalScreen. Model after FilterPickerScreen layout (align: center middle, fixed-width container, heavy $primary border).

Layout (compose):
- Static title bar "Theme" — same style as picker-title in FilterPickerScreen
- ListView of theme names — show `"> {name}  [transparent]"` for currently active theme+transparent combo, else just `"  {name}"`. The transparent state is shown as a tag on the active entry only. Each ListItem label: `"* {name}"` if active (no transparent indicator here; transparent is a separate toggle line). Actually keep it simple: show theme list as ListItem rows with `"* {name}"` for active theme, `"  {name}"` for others. Add a separator ListItem at bottom: `"  [toggle transparent background]"` — key `"__transparent__"`. When `__transparent__` is selected it should toggle and persist immediately and re-render the list marker (e.g. `"* [transparent: ON]"` or `"  [transparent: OFF]"`).
- Static hint at bottom: `"enter: select | t: toggle transparent | esc: close"`

State: `__init__(self, db_path, current_theme, transparent)` — store these. Build ListItem list from `THEMES.keys()`.

Key handling:
- `j`/`k` — move ListView cursor down/up programmatically (same pattern as FilterPickerScreen: `lv.action_cursor_down()`)
- `enter` — if highlighted item is `__transparent__` row, toggle transparent and re-render; else dismiss with `{"theme": selected_name, "transparent": self._transparent}`
- `t` — toggle transparent, persist immediately via `set_setting`, update the transparent ListItem label in-place, and call `self.app.refresh_css(theme=self._current_theme, transparent=self._transparent)` — see app.py changes below
- `escape` — dismiss(None)

CSS: same pattern as FilterPickerScreen — width 48, border heavy $primary, background $surface.

**possession/tui/app.py** — refactor:

1. Remove `_CSS_DEFAULT` and `_CSS_TRANSPARENT` class attributes entirely.
2. Import `build_css`, `get_setting`, `set_setting` from `possession.settings` (lazy import inside `__init__` or at top — avoid circular import risk; lazy inside method is safest).
3. In `__init__`: load saved theme and transparent setting from DB, then set `self.CSS = build_css(theme, transparent)`. The `transparent` CLI arg should OVERRIDE the DB setting only on this launch (do not persist CLI arg — it is a one-time override). Signature stays `def __init__(self, db_path: Path, transparent: bool = False, **kwargs)`. Logic:

   ```python
   from possession.settings import build_css, get_setting
   saved_theme = get_setting(db_path, "theme", "catppuccin-mocha")
   saved_transparent = get_setting(db_path, "transparent", "0") == "1"
   effective_transparent = transparent or saved_transparent  # CLI flag wins if set
   self._current_theme = saved_theme
   self._transparent = effective_transparent
   self.CSS = build_css(saved_theme, effective_transparent)
   ```

4. Add method `apply_theme(self, theme: str, transparent: bool) -> None`:
   ```python
   from possession.settings import build_css, set_setting
   self._current_theme = theme
   self._transparent = transparent
   set_setting(self.db_path, "theme", theme)
   set_setting(self.db_path, "transparent", "1" if transparent else "0")
   self.CSS = build_css(theme, transparent)
   self.refresh_css()
   ```

**possession/tui/screens/main.py** — add theme picker binding:

1. Add to BINDINGS: `("X", "open_theme_picker", "Theme")` (capital X — avoids conflict with existing lowercase bindings).
2. Add action:
   ```python
   def action_open_theme_picker(self) -> None:
       if self._any_input_active():
           return
       from possession.tui.screens.theme_picker import ThemePickerScreen
       self.app.push_screen(
           ThemePickerScreen(
               self.app.db_path,
               self.app._current_theme,
               self.app._transparent,
           ),
           self._on_theme_picked,
       )

   def _on_theme_picked(self, result) -> None:
       if result is None:
           return
       self.app.apply_theme(result["theme"], result["transparent"])
   ```
3. Update `_FOOTER_TEXT` to include `| theme: X` at the end (before `| quit: q`).
  </action>
  <verify>
    <automated>python -c "
import sys; sys.path.insert(0, '.')
import ast, pathlib
src = pathlib.Path('possession/tui/screens/theme_picker.py').read_text()
ast.parse(src)
src2 = pathlib.Path('possession/tui/app.py').read_text()
ast.parse(src2)
src3 = pathlib.Path('possession/tui/screens/main.py').read_text()
ast.parse(src3)
assert 'apply_theme' in src2
assert 'action_open_theme_picker' in src3
assert 'ThemePickerScreen' in src
print('syntax OK, key symbols present')
"
</automated>
  </verify>
  <done>ThemePickerScreen exists and is syntax-valid; app.py has apply_theme and loads theme from DB on init; main.py has X binding and callback; footer updated.</done>
</task>

</tasks>

<verification>
After both tasks, manually verify by launching the app:
```
python -m possession
```
Press X to open theme picker. Navigate with j/k. Select a theme — colors change immediately. Press t to toggle transparent. Quit and relaunch — previous theme and transparent state are restored.
</verification>

<success_criteria>
- 5 named themes available in picker (catppuccin-mocha, dracula, nord, tokyo-night, gruvbox)
- Theme selection applies CSS live via app.apply_theme() / refresh_css()
- Theme and transparent setting stored in SQLite settings table
- Settings survive app restart (loaded in PossessionApp.__init__)
- --transparent CLI flag still works (overrides DB transparent for that session, does not persist)
- X binding opens picker from MainScreen without conflicting with other keys
</success_criteria>

<output>
After completion, create `.planning/quick/3-add-theme-switching-with-multiple-built-/3-SUMMARY.md` with what was built, files changed, and any notable implementation decisions.
</output>
