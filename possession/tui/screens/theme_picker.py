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
        width: 48;
        max-height: 20;
        border: heavy $primary;
        background: $surface;
        padding: 0 1;
    }
    #theme-title {
        text-style: bold;
        margin-bottom: 1;
        color: $surface;
        background: $primary-darken-2;
        text-align: center;
        padding: 0 1;
    }
    #theme-list {
        width: 1fr;
        height: auto;
        max-height: 12;
        border: tall $surface;
    }
    #theme-list:focus {
        border: tall $border;
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

    _FOOTER_TEXT = "j/k: move | enter: select | t: toggle transparent | esc: close"

    def compose(self) -> ComposeResult:
        with Vertical(id="theme-container"):
            yield Static("Theme", id="theme-title")
            yield ListView(id="theme-list")
            yield Static(self._FOOTER_TEXT, id="theme-footer")

    def on_mount(self) -> None:
        self._rebuild_list()
        self.query_one("#theme-list", ListView).focus()

    def _rebuild_list(self) -> None:
        """Rebuild the theme list, marking the active theme with an asterisk."""
        from possession.settings import THEMES
        lv = self.query_one("#theme-list", ListView)

        # Store current index so we can restore focus after rebuild
        current_index = lv.index

        # Clear and repopulate
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

        # Transparent toggle row at the bottom
        trans_label = "ON " if self._transparent else "OFF"
        lv.append(
            ListItem(
                Label(f"  [transparent: {trans_label}]"),
                id="theme-__transparent__",
            )
        )

        # Move cursor to previously active theme on first load
        if current_index is None:
            try:
                idx = self._theme_names.index(self._current_theme)
                lv.index = idx
            except ValueError:
                pass

    def _update_transparent_row(self) -> None:
        """Update the transparent toggle label in-place without full rebuild."""
        lv = self.query_one("#theme-list", ListView)
        trans_item = self.query_one("#theme-__transparent__", ListItem)
        # Replace the label content
        trans_item.query_one(Label).update(
            f"  [transparent: {'ON ' if self._transparent else 'OFF'}]"
        )

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        """Live-preview the theme as the cursor moves through the list."""
        if event.item is None:
            return
        item_id = event.item.id or ""
        if item_id.startswith("theme-") and item_id != "theme-__transparent__":
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
            # Toggle transparent, preview live (no persist until Enter)
            self._transparent = not self._transparent
            self._update_transparent_row()
            self.app.apply_theme(self._current_theme, self._transparent, persist=False)
            event.prevent_default()

        elif event.key == "enter":
            idx = lv.index
            if idx is None:
                event.prevent_default()
                return

            if idx < len(self._theme_names):
                # Theme already previewed live — persist and close
                self.app.apply_theme(self._current_theme, self._transparent, persist=True)
                self.dismiss({"theme": self._current_theme, "transparent": self._transparent})
            else:
                # Transparent toggle row — toggle, persist, preview
                self._transparent = not self._transparent
                self._update_transparent_row()
                self.app.apply_theme(self._current_theme, self._transparent, persist=True)
            event.prevent_default()

        elif event.key == "escape":
            # Revert to the state before the picker was opened
            self.app.apply_theme(self._original_theme, self._original_transparent, persist=True)
            self.dismiss(None)
            event.prevent_default()
