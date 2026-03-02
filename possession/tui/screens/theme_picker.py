"""Theme picker modal for Possession — select from built-in color themes."""

from pathlib import Path

from textual import events
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Label, ListItem, ListView, Static


class ThemePickerScreen(ModalScreen):
    """VIM-style modal for selecting a color theme and toggling transparency.

    Dismisses with {"theme": name, "transparent": bool} on confirmation,
    or None on Escape/cancel.
    """

    DEFAULT_CSS = """
    ThemePickerScreen {
        align: center middle;
    }
    #theme-container {
        width: 64;
        max-height: 20;
        border: heavy $primary;
        background: $surface;
        padding: 0 1;
    }
    #theme-title {
        text-style: bold;
         color: $surface;
        background: $primary-darken-2;
        text-align: center;
        padding: 0 1;
    }
    #theme-list {
        width: 1fr;
        height: auto;
        padding: 1;
        margin: 0;
        max-height: 12;
        border: wide $surface;
    }
    #theme-list:focus {
        border: wide $border;
    }
    #theme-transparent-note {
        height: 1;
        color: $text-muted;
        text-style: italic;
        padding: 0 1;
        margin-bottom: 2;
        dock: bottom;
        text-align: center;
    }
    #theme-footer {
        dock: bottom;
        height: 1;
        background: $primary-darken-2;
        color: $surface;
        padding: 0 1;
        text-align: center;
        text-style: bold;
        margin: 0 -1;
    }
    """

    def __init__(self, db_path: Path, current_theme: str, transparent: bool):
        """
        Args:
            db_path: Path to the SQLite database for persisting settings.
            current_theme: Name of the currently active theme.
            transparent: Current transparent background state.
        """
        super().__init__()
        self._db_path = db_path
        self._current_theme = current_theme
        self._transparent = transparent
        # Stored so Escape can revert to the state before the picker was opened
        self._original_theme = current_theme
        self._original_transparent = transparent
        self._theme_names: list = []

    _FOOTER_TEXT = "j/k: move | enter: select | t: transparent | esc: cancel"

    def compose(self) -> ComposeResult:
        with Vertical(id="theme-container"):
            yield Static("Theme", id="theme-title")
            yield ListView(id="theme-list")
            yield Static(self._transparent_note(), id="theme-transparent-note")
            yield Static(self._FOOTER_TEXT, id="theme-footer")

    def _transparent_note(self) -> str:
        state = "on" if self._transparent else "off"
        return f"transparent: makes overlays and app bg transparent"

    def on_mount(self) -> None:
        self._rebuild_list()
        self.query_one("#theme-list", ListView).focus()

    def _rebuild_list(self) -> None:
        """Rebuild the theme list, marking the active theme with an asterisk."""
        from possession.settings import THEMES
        lv = self.query_one("#theme-list", ListView)

        current_index = lv.index
        lv._nodes._clear()  # type: ignore[attr-defined]

        self._theme_names = list(THEMES.keys())

        for name in self._theme_names:
            marker = "* " if name == self._current_theme else "  "
            lv.append(
                ListItem(
                    Label(f"{marker}{name}"),
                    id=f"theme-{name.replace(' ', '-')}",
                )
            )

        if current_index is None:
            try:
                idx = self._theme_names.index(self._current_theme)
                lv.index = idx
            except ValueError:
                pass

    def _update_transparent_note(self) -> None:
        self.query_one("#theme-transparent-note", Static).update(self._transparent_note())

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        """Live-preview the theme as the cursor moves through the list."""
        if event.item is None:
            return
        item_id = event.item.id or ""
        if item_id.startswith("theme-"):
            theme_name = item_id[len("theme-"):]
            self._current_theme = theme_name
            self.app.apply_theme(theme_name, self._transparent, persist=False)

    def on_key(self, event: events.Key) -> None:
        """Handle VIM navigation, theme selection, and transparent toggle."""
        lv = self.query_one("#theme-list", ListView)

        if event.key == "j":
            lv.action_cursor_down()
            event.prevent_default()

        elif event.key == "k":
            lv.action_cursor_up()
            event.prevent_default()

        elif event.key == "t":
            self._transparent = not self._transparent
            self._update_transparent_note()
            self.app.apply_theme(self._current_theme, self._transparent, persist=False)
            event.prevent_default()

        elif event.key == "enter":
            self.app.apply_theme(self._current_theme, self._transparent, persist=True)
            self.dismiss({"theme": self._current_theme, "transparent": self._transparent})
            event.prevent_default()

        elif event.key == "escape":
            self.app.apply_theme(self._original_theme, self._original_transparent, persist=True)
            self.dismiss(None)
            event.prevent_default()
