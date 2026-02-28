from typing import Dict, List, Optional

from textual import events
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Input, Label, ListItem, ListView, Static


class FilterPickerScreen(ModalScreen):
    """Reusable VIM-style picker modal used for Room, Container, and Category filters.

    Opens as a floating overlay over MainScreen. Returns the selected item dict (with 'id'
    and 'name' keys) on confirmation, or None on Escape/cancel.
    """

    DEFAULT_CSS = """
    FilterPickerScreen {
        align: center middle;
    }
    #picker-container {
        width: 52;
        max-height: 16;
        border: solid $primary;
        background: $surface;
        padding: 0 1;
    }
    #picker-title {
        text-style: bold;
        margin-bottom: 1;
    }
    #picker-search {
        width: 1fr;
        height: 1;
        border: none;
        background: $surface-darken-1;
        margin-bottom: 1;
    }
    #picker-list {
        width: 1fr;
        height: auto;
        max-height: 10;
    }
    #picker-hint {
        height: 1;
        color: $text-muted;
        text-align: center;
    }
    """

    def __init__(
        self,
        title: str,
        items: List[Dict],
        active_id: Optional[int] = None,
    ):
        """
        Args:
            title: Display title (e.g. "Room"). Used in header and empty-state message.
            items: List of dicts with 'id' (int) and 'name' (str) keys.
            active_id: ID of the currently active filter, or None.
        """
        super().__init__()
        self._title = title
        self._items = items
        self._active_id = active_id
        self._filtered: List[Dict] = []

    def compose(self) -> ComposeResult:
        with Vertical(id="picker-container"):
            yield Static(self._title, id="picker-title")
            yield Input(placeholder="Type to filter...", id="picker-search")
            yield ListView(id="picker-list")
            yield Static("", id="picker-hint")

    def on_mount(self) -> None:
        self._rebuild_list("")
        self.query_one("#picker-search", Input).focus()

    def _rebuild_list(self, query: str) -> None:
        """Rebuild the picker list, floating active item to top and applying query filter."""
        lv = self.query_one("#picker-list", ListView)
        lv.clear()
        q = query.lower().strip()

        # Separate active item (floats to top with checkmark) from the rest
        active_item = None
        other_items = []
        for item in self._items:
            if item["id"] == self._active_id:
                active_item = item
            else:
                other_items.append(item)

        ordered = ([active_item] if active_item else []) + other_items

        # Apply type-ahead filter and populate filtered list
        self._filtered = []
        for item in ordered:
            if q and q not in item["name"].lower():
                continue
            self._filtered.append(item)
            marker = "✓ " if item["id"] == self._active_id else "  "
            lv.append(
                ListItem(
                    Label(f"{marker}{item['name']}"),
                    id=f"item-{item['id']}",
                )
            )

        # Empty-state rows (not added to self._filtered — not interactive)
        if not self._items:
            lv.append(ListItem(Label(f"  No {self._title.lower()}s yet")))
        elif not self._filtered:
            lv.append(ListItem(Label("  (no matches)")))

    def on_input_changed(self, event: Input.Changed) -> None:
        """Live-filter the list as the user types."""
        if event.input.id == "picker-search":
            self._rebuild_list(event.value)

    def on_key(self, event: events.Key) -> None:
        """Handle VIM navigation and confirm/dismiss."""
        lv = self.query_one("#picker-list", ListView)
        if event.key == "escape":
            self.dismiss(None)
        elif event.key == "j":
            lv.action_cursor_down()
            event.prevent_default()
        elif event.key == "k":
            lv.action_cursor_up()
            event.prevent_default()
        elif event.key == "enter":
            idx = lv.index
            if idx is not None and idx < len(self._filtered):
                self.dismiss(self._filtered[idx])
            event.prevent_default()

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        """Update hint line when cursor moves over the active filter item."""
        hint = self.query_one("#picker-hint", Static)
        if event.item is not None:
            item_id_str = event.item.id  # format: "item-{id}"
            try:
                item_id = int(item_id_str.split("-", 1)[1])
                if item_id == self._active_id:
                    hint.update("Enter to clear filter")
                    return
            except (ValueError, AttributeError, IndexError):
                pass
        hint.update("")
