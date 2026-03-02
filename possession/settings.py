"""Settings persistence and theme management for Possession."""

import locale
import sqlite3
from pathlib import Path
from typing import Dict, Optional

# ---------------------------------------------------------------------------
# Locale-aware currency formatting
# ---------------------------------------------------------------------------

_locale_ready = False


def _ensure_locale() -> None:
    """Activate the system locale once (best-effort, no-op on failure)."""
    global _locale_ready
    if not _locale_ready:
        try:
            locale.setlocale(locale.LC_ALL, "")
        except locale.Error:
            pass
        _locale_ready = True


def format_currency(amount: Optional[float]) -> str:
    """Format a monetary value using the user's system locale.

    Returns an empty string for None. Falls back to basic $X,XXX.XX formatting
    if the system locale does not provide currency data.

    Args:
        amount: The monetary value to format, or None.

    Returns:
        Locale-formatted currency string, or "" when amount is None.
    """
    if amount is None:
        return ""
    _ensure_locale()
    try:
        return locale.currency(amount, grouping=True)
    except (ValueError, locale.Error):
        return f"${amount:,.2f}"

# ---------------------------------------------------------------------------
# Theme palette definitions
# ---------------------------------------------------------------------------

THEMES: Dict[str, Dict[str, str]] = {
    "catppuccin-mocha": {
        "primary": "#cba6f7",
        "primary-darken-2": "#fab387",
        "surface": "#1e1e2e",
        "surface-darken-1": "#11111b",
        "text": "#cdd6f4",
        "text-muted": "#bac2de",
    },
    "dracula": {
        "primary": "#bd93f9",
        "primary-darken-2": "#ff79c6",
        "surface": "#282a36",
        "surface-darken-1": "#1e1f29",
        "text": "#f8f8f2",
        "text-muted": "#6272a4",
    },
    "nord": {
        "primary": "#88c0d0",
        "primary-darken-2": "#81a1c1",
        "surface": "#2e3440",
        "surface-darken-1": "#242933",
        "text": "#eceff4",
        "text-muted": "#d8dee9",
    },
    "tokyo-night": {
        "primary": "#7aa2f7",
        "primary-darken-2": "#bb9af7",
        "surface": "#1a1b26",
        "surface-darken-1": "#16161e",
        "text": "#c0caf5",
        "text-muted": "#9aa5ce",
    },
    "gruvbox": {
        "primary": "#d3869b",
        "primary-darken-2": "#fabd2f",
        "surface": "#282828",
        "surface-darken-1": "#1d2021",
        "text": "#ebdbb2",
        "text-muted": "#bdae93",
    },
    "one-dark": {
        "primary": "#61afef",
        "primary-darken-2": "#c678dd",
        "surface": "#282c34",
        "surface-darken-1": "#21252b",
        "text": "#abb2bf",
        "text-muted": "#5c6370",
    },
    "monokai": {
        "primary": "#a6e22e",
        "primary-darken-2": "#f92672",
        "surface": "#272822",
        "surface-darken-1": "#1e1f1c",
        "text": "#f8f8f2",
        "text-muted": "#75715e",
    },
    "rose-pine": {
        "primary": "#c4a7e7",
        "primary-darken-2": "#eb6f92",
        "surface": "#191724",
        "surface-darken-1": "#13111e",
        "text": "#e0def4",
        "text-muted": "#6e6a86",
    },
    "kanagawa": {
        "primary": "#7e9cd8",
        "primary-darken-2": "#957fb8",
        "surface": "#1f1f28",
        "surface-darken-1": "#16161d",
        "text": "#dcd7ba",
        "text-muted": "#727169",
    },
    "solarized-dark": {
        "primary": "#268bd2",
        "primary-darken-2": "#2aa198",
        "surface": "#002b36",
        "surface-darken-1": "#001e26",
        "text": "#839496",
        "text-muted": "#586e75",
    },
}

_DEFAULT_THEME = "catppuccin-mocha"


def build_css(theme_name: str, transparent: bool = False) -> str:
    """Generate a full app CSS string from the named theme palette.

    Args:
        theme_name: Key in THEMES dict.
        transparent: If True, Screen background is transparent; otherwise $surface.

    Returns:
        CSS string ready to assign to App.CSS.

    Raises:
        KeyError: If theme_name is not in THEMES (after safe fallback attempt).
    """
    palette = THEMES.get(theme_name)
    if palette is None:
        # Safe fallback — use default theme instead of crashing
        palette = THEMES[_DEFAULT_THEME]
        theme_name = _DEFAULT_THEME

    p = palette["primary"]
    pd2 = palette["primary-darken-2"]
    surf = palette["surface"]
    surf1 = palette["surface-darken-1"]
    text = palette["text"]
    text_muted = palette["text-muted"]

    screen_bg = "transparent" if transparent else surf

    return f"""
    $primary: {p};
    $primary-darken-2: {pd2};
    $surface: {surf};
    $surface-darken-1: {surf1};
    $text: {text};
    $text-muted: {text_muted};
    $panel: $primary-darken-2;
    $border: {p};
    $block-cursor-background: {p};
    $block-cursor-foreground: {surf};
    $block-cursor-blurred-background: {p}40;
    $scrollbar: {pd2};
    $scrollbar-hover: {pd2};
    $scrollbar-active: {pd2};
    $scrollbar-background: {surf};
    $scrollbar-corner-color: {surf};

    Screen {{
        background: {screen_bg};
    }}
    DataTable {{
        background: transparent;
        scrollbar-size-vertical: 0;
        scrollbar-size-horizontal: 0;
    }}
    DataTable > .datatable--cursor {{
        background: $primary;
    }}
    DataTable > .datatable--header {{
        color: $surface;
    }}
    """


# ---------------------------------------------------------------------------
# Settings persistence — per-call connection pattern
# ---------------------------------------------------------------------------

def get_setting(db_path: Path, key: str, default: str = "") -> str:
    """Retrieve a setting value from the settings table.

    Args:
        db_path: Path to the SQLite database file.
        key: Setting key string.
        default: Value to return if key is not found.

    Returns:
        Stored value string, or default if not present.
    """
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        )
        row = cur.fetchone()
        return row[0] if row is not None else default
    finally:
        conn.close()


def set_setting(db_path: Path, key: str, value: str) -> None:
    """Persist a setting value to the settings table.

    Args:
        db_path: Path to the SQLite database file.
        key: Setting key string.
        value: Value string to store.
    """
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, value),
        )
        conn.commit()
    finally:
        conn.close()
