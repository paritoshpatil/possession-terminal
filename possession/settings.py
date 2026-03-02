"""Settings persistence and theme management for Possession."""

import sqlite3
from pathlib import Path
from typing import Dict

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
