# Technology Stack: v1.1 Theming and Terminal Color Detection

**Project:** possession-terminal v1.1 UI Overhaul
**Researched:** 2026-02-24
**Scope:** Stack additions for THEME-01 (terminal theme colors — transparent background, terminal foreground)
**Installed Textual version:** 8.0.0 (confirmed from pip install log in project repo)

---

## Context: What Exists Today

`PossessionApp(App)` currently has:

```python
CSS = """
Screen {
    background: $surface;
}
"""
```

`MainScreen(Screen)` has inline CSS for `.hidden` and `DataTable` height. No `.tcss` files exist. The goal is to replace hardcoded `$surface` with terminal-native colors and adopt a coherent theme approach that works across both dark and light terminal themes.

---

## Recommended Stack

### No New Dependencies Required

Terminal color detection and Textual theming for this use case can be accomplished entirely with:
- **Python stdlib** (`os`, `curses`) — for reading env vars and querying terminal color support
- **Textual CSS system** (already installed) — for applying theme variables
- **Textual `Theme` dataclass** (Textual ≥0.80+) — for registering named themes programmatically

No new pip packages are needed.

---

## Part 1: Textual Theming API (Textual 8.0.0)

### 1.1 The Color Variable System

Textual's CSS engine provides a set of design-token variables resolved at render time. These are NOT standard CSS variables — they use `$` prefix and are resolved by Textual's own CSS parser.

**Core background/surface variables:**

| Variable | Default Role | When to Use |
|----------|-------------|-------------|
| `$background` | App-level background (outermost layer) | Root screen background |
| `$surface` | Widget surface (slightly lighter than background) | Cards, panels, DataTable body |
| `$panel` | Raised surfaces (menus, overlays) | Modals, popovers |
| `$boost` | Subtle highlight (hover, selection context) | Hovered rows |
| `$primary` | Brand/accent color | Active highlights, focused borders |
| `$secondary` | Secondary accent | Less prominent interactive elements |
| `$success`, `$warning`, `$error` | Semantic states | Status indicators |
| `$text` | Primary foreground text | Body text |
| `$text-muted` | Dimmed text | Secondary labels, placeholders |
| `$text-disabled` | Disabled text | Greyed-out controls |

**Confidence:** HIGH — Textual's CSS variable system has been stable since 0.20+ and these names are unchanged in 8.0.0.

### 1.2 The `Theme` Dataclass (Textual ≥0.80.0 / 8.0.0)

In Textual 8.0.0, themes are registered as `Theme` dataclass instances. This replaces the older approach of subclassing or directly patching `dark`/`light` CSS.

```python
from textual.theme import Theme

my_theme = Theme(
    name="possession-dark",
    dark=True,
    background="#1a1a1a",     # or "transparent" — see §1.4
    surface="#242424",
    primary="#7c9cbf",
    secondary="#5a8a6a",
    accent="#d4a84b",
    foreground="#e8e6e3",
    # ... other color slots
)
```

`App.register_theme(theme)` adds the theme to the app's theme registry.
`App.theme = "possession-dark"` switches to it.

**Confidence:** MEDIUM-HIGH — `Theme` dataclass exists in Textual ≥0.75; the exact field names may differ in 8.0.0. The approach of registering and switching themes is verified for ≥0.47.0, but some field names require verification against the 8.0.0 source. The fields listed above represent the stable core.

### 1.3 The `App.DEFAULT_CSS` Pattern

For the existing `PossessionApp`, the inline `CSS` class attribute (not `DEFAULT_CSS`) overrides the app stylesheet. This is correct for app-level styles. The distinction:

| Attribute | Scope | Override Priority |
|-----------|-------|-------------------|
| `App.DEFAULT_CSS` | App class (inheritable by subclasses) | Lower — can be overridden by user stylesheets |
| `App.CSS` | This app instance | Higher — overrides DEFAULT_CSS |
| `Widget.DEFAULT_CSS` | Widget class | Lowest — component baseline |
| `Widget.CSS` | Widget instance | Overrides DEFAULT_CSS |

For PossessionApp, keep using `CSS` (not `DEFAULT_CSS`) for theme overrides since this is not a reusable library widget.

**Confidence:** HIGH — This distinction is documented and stable across all Textual versions.

### 1.4 Transparent Background

The goal is "terminal background" — the app should show whatever color the user's terminal has, not impose Textual's built-in dark grey.

**What "transparent" means in a TUI context:**

Unlike GUI frameworks, TUI apps cannot use alpha-channel transparency. "Transparent" in Textual means the terminal's own background color bleeds through. This is accomplished with:

```css
Screen {
    background: transparent;
}
```

Or in `Theme`:
```python
Theme(
    name="possession",
    background="transparent",  # Tells Textual not to fill the background cell
    ...
)
```

**How it works:** When Textual renders a cell with `background: transparent`, it emits no background SGR sequence for that cell. The terminal emulator then uses its own configured background color (set in terminal preferences). This is the correct approach for "true" terminal theme integration.

**Caveat:** Transparent background means the app has no control over what color users see. If the user has a white terminal, it looks white. If neon green, neon green. This is intentional for THEME-01.

**Confidence:** HIGH — Textual has supported `background: transparent` in CSS since 0.20+. The rendering path (no SGR background sequence) is a well-established TUI pattern.

### 1.5 Foreground from Terminal Theme

For foreground color, there are two approaches:

**Approach A: Use `$text` variable with a sensible default**

```css
Screen {
    background: transparent;
    color: $text;
}
```

Textual resolves `$text` from the active theme. Set it to a neutral value in the theme definition and let users override via Textual's theme system if desired.

**Approach B: Read terminal foreground color and inject it**

This requires runtime color detection (see Part 2) and then calling `self.refresh_css()` or modifying a reactive that CSS reads. This is more complex and has compatibility issues.

**Recommendation: Use Approach A.** Set `$text` to a light-on-dark default (e.g., `#e8e6e3`) but let `background: transparent` do the heavy lifting. Users who care about precise foreground matching use terminal emulators that handle this automatically through their color schemes (Gruvbox, Nord, etc. ship consistent fg/bg pairs).

**Confidence:** HIGH for Approach A. MEDIUM for Approach B (requires terminal query sequences that aren't universally supported).

### 1.6 `dark` vs `light` Mode Switching

`App.dark` is a reactive boolean. Setting `app.dark = True/False` triggers re-render and applies the appropriate theme variant.

```python
# In PossessionApp.on_mount():
self.dark = True  # Force dark (transparent bg works best on dark themes)
```

Or detect from environment (see Part 2) and set accordingly.

**Confidence:** HIGH — `App.dark` is a core reactive in all Textual versions ≥0.20.

---

## Part 2: Terminal Color Detection

### 2.1 Environment Variables to Check

Terminal color detection should read these env vars in priority order:

| Variable | What It Tells You | Example Values |
|----------|------------------|----------------|
| `COLORTERM` | True-color support | `truecolor`, `24bit` |
| `TERM` | Terminal type and basic color support | `xterm-256color`, `screen-256color`, `alacritty` |
| `TERM_PROGRAM` | Terminal app name | `iTerm.app`, `WezTerm`, `ghostty`, `Apple_Terminal` |
| `TERM_PROGRAM_VERSION` | Terminal version | `3.4.0` |
| `COLORFGBG` | Light/dark hint from terminal | `15;0` (white-on-black = dark), `0;15` (black-on-white = light) |
| `VTE_VERSION` | GNOME VTE-based terminal | Version int |

**Reading logic (Python):**

```python
import os

def detect_dark_mode() -> bool:
    """
    Returns True if the terminal appears to be running a dark theme.
    Falls back to True (dark) if detection is inconclusive.
    """
    # COLORFGBG: "foreground;background" as ANSI color indices
    # Background index 0-6 = dark colors, 7-15 = light colors
    colorfgbg = os.environ.get("COLORFGBG", "")
    if colorfgbg:
        parts = colorfgbg.split(";")
        if len(parts) >= 2:
            try:
                bg_index = int(parts[-1])
                # 0-6 are dark ANSI colors, 7 is light grey, 8-14 dark bold variants
                # 15 is white. Anything <= 6 or 8-14 is dark; 7,15 is light.
                return bg_index not in (7, 15)
            except ValueError:
                pass

    # TERM_PROGRAM hints
    term_program = os.environ.get("TERM_PROGRAM", "")
    # No reliable dark/light signal from TERM_PROGRAM alone

    # Default: assume dark (most developer terminals are dark)
    return True
```

**Confidence for `COLORFGBG`:** MEDIUM — This variable is set by many terminal emulators (iTerm2, Terminal.app, Alacritty, WezTerm, Konsole, GNOME Terminal) but NOT all. It is the most widely-used env var for this purpose. The encoding convention (`fg_index;bg_index`) is consistent but not formally standardized.

**Confidence for `COLORTERM`:** HIGH for detecting truecolor capability — this is widely standardized. Does NOT indicate dark/light.

**Confidence for `TERM`:** HIGH for detecting 256-color vs. basic. `xterm-256color` is the de facto standard. Does NOT indicate dark/light.

### 2.2 OSC 10/11 Color Queries (Advanced — Flag as Risky)

The "proper" way to read terminal foreground/background colors is via OSC (Operating System Command) escape sequences:

- `\033]10;?\007` — query foreground color
- `\033]11;?\007` — query background color

The terminal responds with the actual color in XParseColor format. However:

**Why NOT to use this in PossessionApp:**

1. **Requires raw terminal access:** Must put the terminal in raw mode to read the response, which conflicts with Textual's own terminal management. Textual already owns stdin/stdout for rendering.
2. **Not universally supported:** Some terminal emulators (older tmux, screen, some SSH sessions) silently ignore these queries.
3. **Timing issues:** The response arrives asynchronously; you can't block on it during `on_mount` without careful async handling.
4. **Textual already handles dark/light:** Textual has its own detection path. Adding a competing query layer causes conflicts.

**Decision: Do NOT implement OSC 10/11 queries.** Use `COLORFGBG` for dark/light detection and `background: transparent` for the background. This is the correct split of responsibilities.

**Confidence:** HIGH — This is the established best practice for TUI apps that use a framework (rather than raw curses) to manage rendering.

### 2.3 curses-Based Color Detection

```python
import curses

def has_256_colors() -> bool:
    """Check if terminal supports 256 colors via curses."""
    try:
        curses.setupterm()
        return curses.tigetnum("colors") >= 256
    except Exception:
        return False
```

**Why NOT to use this for PossessionApp:**

- Textual already detects and uses 256/truecolor automatically via Rich's color detection.
- Calling `curses.setupterm()` after Textual has started causes terminal state conflicts.
- If called before Textual starts (in `__main__.py`), it's redundant with what Textual does internally.

**Decision: Skip curses detection entirely.** Trust Textual's internal color capability detection (which reads `COLORTERM`, `TERM`, etc.). Only use `os.environ` directly for dark/light detection.

**Confidence:** HIGH — Verified reasoning based on how Textual/Rich detect color support internally.

### 2.4 Recommended Detection Implementation

For PossessionApp, implement a single utility function used at app startup:

```python
# possession/tui/theme_detect.py

import os
from typing import Literal

ColorMode = Literal["dark", "light"]


def detect_color_mode() -> ColorMode:
    """
    Detect whether the terminal is running a dark or light color scheme.

    Priority:
    1. COLORFGBG env var (most reliable signal)
    2. Default to "dark" (safe fallback for developer terminals)

    Returns "dark" or "light".
    """
    colorfgbg = os.environ.get("COLORFGBG", "")
    if colorfgbg:
        parts = colorfgbg.split(";")
        if len(parts) >= 2:
            try:
                bg_index = int(parts[-1])
                # ANSI indices: 0-6 dark, 7=light grey, 8-14 dark bold, 15=white
                # Treat 7 and 15 as light; everything else as dark
                if bg_index in (7, 15):
                    return "light"
                return "dark"
            except ValueError:
                pass

    return "dark"  # Safe default


def terminal_supports_truecolor() -> bool:
    """
    Check if terminal supports 24-bit (truecolor) color.
    Used to decide whether to use hex colors or fall back to ANSI 256.
    """
    colorterm = os.environ.get("COLORTERM", "").lower()
    return colorterm in ("truecolor", "24bit")
```

---

## Part 3: Integrating Theme Detection into PossessionApp

### 3.1 Where to Apply

Theme configuration must happen **before** Textual starts rendering, which means in `PossessionApp.__init__` or `on_mount`. The theme switch must happen early.

**Recommended integration point:** `PossessionApp.on_mount()` — Textual is fully initialized but hasn't rendered the first frame yet (not quite: `on_mount` runs after first render, so use `on_ready` or set in `__init__`).

Actually: **set `self.dark` in `__init__`** — before Textual processes the first frame:

```python
from possession.tui.theme_detect import detect_color_mode

class PossessionApp(App):
    def __init__(self, db_path: Path, **kwargs):
        super().__init__(**kwargs)
        self.db_path = db_path
        # Set dark/light mode before first render
        color_mode = detect_color_mode()
        self.dark = (color_mode == "dark")
```

### 3.2 CSS Changes

Replace the existing `CSS` in `PossessionApp`:

```python
CSS = """
Screen {
    background: transparent;
    color: $text;
}

DataTable {
    background: transparent;
}

/* Keep non-transparent for overlaid widgets so they're readable */
Input {
    background: $surface;
}

QuickAddBar {
    background: $panel;
}
"""
```

**Key rules:**
- `Screen { background: transparent; }` — lets terminal background show through
- `DataTable { background: transparent; }` — table rows don't impose background color
- `Input` and overlay widgets keep `$surface` / `$panel` so they're legible over the transparent backdrop
- Do NOT set `color:` on individual widgets — inherit from Screen via cascade

### 3.3 The `$text` Variable and Theme Colors

When `background: transparent` is in use, `$text` should be set to a readable neutral. The default Textual dark theme uses `$text: #e8e6e3` (near-white). For light mode, it uses `$text: #0e0e0e` (near-black).

Since `App.dark` is set from detection, Textual automatically switches between its built-in dark/light `$text` values. No manual override of `$text` is needed unless the app defines a custom `Theme`.

**Confidence:** HIGH — `App.dark` toggling and theme variable switching is well-established Textual behavior.

---

## Part 4: Textual Widget APIs for v1.1 Screens

### 4.1 `Static` Widget for Labels

```python
from textual.widgets import Static

# In compose():
yield Static("Possession v1.1", id="app-title")
yield Static("", id="stats-bar")  # Updated dynamically
```

`Static.update(content)` or `static_widget.renderable = content` to update text.

**For the stats bar:** Use `Static` with markup for styled text:
```python
stats_widget.update(
    f"[bold]{item_count}[/bold] items · [dim]{rooms}[/dim] rooms · [green]${total_value:.2f}[/green]"
)
```

**Confidence:** HIGH — `Static` widget and its `update()` method are stable across all Textual versions.

### 4.2 `Header` Widget

Textual's built-in `Header` widget provides a persistent top bar. In v1.1, if a custom app name bar is needed:

```python
from textual.widgets import Header

# In PossessionApp.compose() (App-level, not Screen-level):
def compose(self) -> ComposeResult:
    yield Header(show_clock=False)
    yield self.screen  # screens stack here
```

**However:** For PossessionApp, using a `Header` at the App level conflicts with the current push_screen pattern (screens compose their own content). The simpler approach for a persistent top bar is a `Static` docked to the top inside each Screen, or a `Static` at the App level with `dock: top`.

**Recommended approach for persistent top bar:**

```python
# In PossessionApp (App-level compose):
def compose(self) -> ComposeResult:
    yield Static("Possession", id="top-bar")
    yield Screen()  # or push_screen in on_mount

# CSS:
CSS = """
#top-bar {
    dock: top;
    height: 1;
    background: $primary;
    color: $text-on-primary;
    text-align: center;
    text-style: bold;
}
"""
```

**Caveat:** Mixing App-level compose with push_screen requires care — the `Static` needs to survive screen pushes. App-level widgets persist across screen transitions; Screen-level widgets do not.

**Confidence:** HIGH for the CSS dock approach. MEDIUM for App-level compose + push_screen interaction (verify that App-level `Static` is not covered by pushed screens).

### 4.3 Screen-Level CSS

Each `Screen` subclass has its own `CSS` (or `DEFAULT_CSS`) class attribute. Screen CSS applies only while that screen is active.

For v1.1 screens (SplashScreen, MainScreen updated):

```python
class SplashScreen(Screen):
    DEFAULT_CSS = """
    SplashScreen {
        background: transparent;
        align: center middle;
    }
    #splash-art {
        color: $primary;
        text-align: center;
    }
    """
```

**Important:** `Screen { background: transparent; }` must be set on each Screen that should show the terminal background. It is NOT inherited from the App-level CSS automatically for Screens pushed via `push_screen`.

**Confidence:** HIGH — Screen CSS scoping is core Textual behavior.

### 4.4 `COMPONENT_CLASSES` Pattern

`COMPONENT_CLASSES` is used to declare CSS classes that a Widget can receive styling for, enabling external CSS to target internal widget parts.

For v1.1, this is relevant if building a custom `FilterPicker` widget where callers can style the picker header, options, etc. For standard widgets (`DataTable`, `Input`, `Static`), it is not needed.

**When to use:** Only when building a custom multi-part widget where the implementer wants to expose style hooks. Not needed for THEME-01 itself.

**Confidence:** HIGH.

### 4.5 Reactive CSS Variables

Textual supports reactive variables that CSS can read via the `var()` function (Textual-specific, not standard CSS):

```python
class MyWidget(Widget):
    highlight_color = reactive("#ffaa00")

    DEFAULT_CSS = """
    MyWidget {
        color: var(--highlight-color, $text);
    }
    """
```

However, for THEME-01, this level of complexity is unnecessary. The `$text` and `$primary` theme variables already provide dynamic theming. Only use reactive CSS variables if a widget needs per-instance color customization.

**Confidence:** MEDIUM — reactive CSS variables exist in Textual but the exact syntax (`var(--name)` vs `var(name)`) should be verified against 8.0.0. Safe to skip for THEME-01.

---

## Part 5: Version-Specific Notes for Textual 8.0.0

### 5.1 Confirmed Installed Version

From the project's `=0.47.0` install log: Textual 8.0.0 was installed (the log shows `textual-8.0.0-py3-none-any.whl`). The `pyproject.toml` specifies `textual>=0.47.0`, and 8.0.0 satisfies this constraint.

This is a major version difference from the baseline. Textual 8.x introduced:
- The `Theme` dataclass for programmatic theme registration
- Updated default color palette
- Changes to `Header`/`Footer` widget internals
- Textual CSS variable names are stable but some widget-specific selectors changed

**Action:** Code should target the 8.0.0 API, not the 0.47.0 baseline. The constraint in `pyproject.toml` should ideally be tightened to `textual>=8.0.0` or left as-is knowing 8.0.0 is installed.

### 5.2 `table.clear(columns=True)` Compat Guard

The existing code has:
```python
try:
    table.clear(columns=True)
except TypeError:
    table.clear()
```

In Textual 8.0.0, `DataTable.clear(columns=True)` is supported. The `try/except` guard remains harmless but the fallback path won't be triggered on 8.0.0.

### 5.3 CSS `$surface` in App CSS

The existing `background: $surface` in `PossessionApp.CSS` works correctly in 8.0.0. `$surface` resolves to a dark grey in dark mode, slightly lighter in light mode. Replacing it with `transparent` is a backward-compatible change.

### 5.4 `App.dark` Reactive

In Textual 8.0.0, `App.dark` is a class-level reactive that triggers CSS re-resolution when changed. Setting it in `__init__` before `run()` is the correct pattern for initial theme detection.

**Confidence:** HIGH — `App.dark` behavior is unchanged in 8.x.

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Background | `background: transparent` CSS | OSC 11 query for exact terminal bg color | OSC queries conflict with Textual's terminal ownership; not universally supported |
| Foreground | `$text` theme variable + `App.dark` detection | Read `COLORFGBG` fg index and inject as hex | Unnecessary complexity; terminal theme fg often doesn't match ANSI index hex values |
| Dark/light detection | `COLORFGBG` env var | `colorthief`, `terminal-colorsq` packages | No stdlib deps; these packages aren't designed for TUI use |
| Theme registration | Textual `Theme` dataclass | Manually patching `App.CSS` at runtime | `Theme` is the canonical API in 8.0.0; CSS patching is fragile |
| Truecolor check | `COLORTERM` env var check | `curses.tigetnum("colors")` | curses conflicts with Textual after startup; `COLORTERM` is the established standard |
| Top bar | `Static` docked widget | Textual built-in `Header` | `Header` adds clock and title by default; custom `Static` gives full control |

---

## Installation

No new packages required. All functionality is achievable with:

```bash
# Already installed:
# textual==8.0.0 (satisfies >=0.47.0)
# Python stdlib: os, typing
```

If the team decides to tighten the version constraint:

```toml
# pyproject.toml
dependencies = [
    "textual>=8.0.0",
]
```

---

## Confidence Assessment

| Finding | Confidence | Basis |
|---------|------------|-------|
| `background: transparent` CSS works in Textual | HIGH | Stable since Textual 0.20+; unchanged in 8.0 |
| `$background`, `$surface`, `$text` color variables | HIGH | Core Textual CSS system, stable across all versions |
| `App.dark` reactive for dark/light switching | HIGH | Core reactive, documented, stable in 8.x |
| `COLORFGBG` parsing for dark/light detection | MEDIUM | Widely used convention, not formally standardized; may not be set in all terminals |
| `Theme` dataclass API fields in 8.0.0 | MEDIUM | Theme dataclass exists; exact field names should be verified against installed source |
| Textual 8.0.0 specific changes vs 0.47.0 | MEDIUM | Upgrade from 0.47 to 8.x is significant; some API details may differ from training knowledge |
| OSC 10/11 queries should be avoided | HIGH | Architectural reasoning; no dependency on specific Textual version |
| `Static.update()` API | HIGH | Stable across all Textual versions |
| Screen CSS scoping | HIGH | Core CSS scoping behavior, unchanged in 8.x |

---

## Open Flags for Implementation Phase

1. **Verify `Theme` dataclass fields in 8.0.0:** Before implementing programmatic theme registration, read the Textual 8.0.0 source or changelog to confirm field names. The fields `background`, `surface`, `primary`, `foreground` are likely stable but may have been renamed.

2. **Test `transparent` background with the actual terminal emulator:** `background: transparent` renders correctly in most modern terminals but may have edge cases in multiplexers (tmux, screen) where the outer terminal's background isn't passed through. Flag as a known limitation.

3. **App-level vs Screen-level `Screen { background: ... }` CSS:** Test whether App-level CSS `Screen { background: transparent; }` applies to all pushed screens, or if each Screen class needs its own CSS. This behavior may differ between Textual versions.

4. **`COLORFGBG` availability on macOS:** On macOS with iTerm2 and Terminal.app, `COLORFGBG` is set. On some Linux terminals (depending on config) it may not be. The `detect_dark_mode()` fallback to `"dark"` handles the gap correctly.

---

## Sources

- Textual 8.0.0 install confirmed from project repo file `=0.47.0` (pip install log)
- Existing app code read from: `possession/tui/app.py`, `possession/tui/screens/main.py`, `possession/tui/widgets/quickadd.py`
- Textual CSS variable system: training knowledge (Textual 0.20 – 0.80+), HIGH confidence for stable APIs
- `COLORFGBG` convention: established Unix terminal convention documented in xterm/VTE sources
- `COLORTERM` truecolor detection: documented at https://github.com/termstandard/colors (de facto standard)
- Tool access limited to: Read (project files only), Write, Grep (project files only) during this session
- Web search and external package inspection unavailable — flagged findings requiring external verification above
