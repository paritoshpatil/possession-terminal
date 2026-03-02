from pathlib import Path
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

    When the user presses 'd' on a highlighted item, an inline confirmation prompt appears
    with impact details. Pressing 'y' deletes the entity and dismisses with
    {"deleted": True, "id": ..., "name": ...}. Pressing 'n' or Escape cancels deletion.
    """

    DEFAULT_CSS = """
    FilterPickerScreen {
        align: center middle;
    }
    #picker-container {
        width: 64;
        max-height: 24;
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
    #picker-list > ListItem.--highlight {
        background: $primary;
        color: $surface;
    }
    #picker-hint {
        height: 1;
        color: $text;
        text-align: center;
        margin-top: 2;
    }
    #picker-delete-confirm {
        height: auto;
        color: $text;
        text-align: center;
        background: $surface;
        padding: 0 1;
        margin-top: 1;
    }
    """

    def __init__(
        self,
        title: str,
        items: List[Dict],
        active_id: Optional[int] = None,
        db_path: Optional[Path] = None,
        kind: str = "room",
    ):
        """
        Args:
            title: Display title (e.g. "Room"). Used in header and empty-state message.
            items: List of dicts with 'id' (int) and 'name' (str) keys.
            active_id: ID of the currently active filter, or None.
            db_path: Path to the SQLite database file (needed for delete and count queries).
            kind: One of "room", "container", "category" — determines delete behavior.
        """
        super().__init__()
        self._title = title
        self._items = items
        self._active_id = active_id
        self._db_path = db_path
        self._kind = kind
        self._filtered: List[Dict] = []
        self._delete_mode: bool = False
        self._delete_candidate: Optional[Dict] = None

    def compose(self) -> ComposeResult:
        with Vertical(id="picker-container"):
            yield Static(self._title, id="picker-title")
            yield Input(placeholder="Type to filter...", id="picker-search")
            yield ListView(id="picker-list")
            yield Static("", id="picker-hint")
            yield Static("", id="picker-delete-confirm", classes="hidden")

    async def on_mount(self) -> None:
        await self._rebuild_list("")
        self.query_one("#picker-search", Input).focus()

    async def _rebuild_list(self, query: str) -> None:
        """Rebuild the picker list, floating active item to top and applying query filter."""
        lv = self.query_one("#picker-list", ListView)
        await lv.clear()
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

    async def on_input_changed(self, event: Input.Changed) -> None:
        """Live-filter the list as the user types."""
        if event.input.id == "picker-search":
            await self._rebuild_list(event.value)

    def _get_impact_line(self, item: dict) -> str:
        """Build the impact description string for the delete confirmation prompt."""
        if self._kind == "room":
            from possession.models import count_room_contents
            counts = count_room_contents(self._db_path, item["id"])
            c = counts["containers"]
            i = counts["items"]
            return (
                f"This will also delete {c} container(s) and {i} item(s) will lose their room."
            )
        elif self._kind == "container":
            from possession.models import count_container_items
            counts = count_container_items(self._db_path, item["id"])
            i = counts["items"]
            return f"This will remove {i} item(s) from this container."
        else:  # category
            return "Items with this category will have their category cleared (not deleted)."

    def on_key(self, event: events.Key) -> None:
        """Handle VIM navigation, delete confirmation, and confirm/dismiss."""
        lv = self.query_one("#picker-list", ListView)

        # --- Delete mode: only respond to y / n / escape, block everything else ---
        if self._delete_mode:
            if event.key == "y":
                # Perform the deletion
                try:
                    if self._kind == "room":
                        from possession.models import delete_room
                        delete_room(self._db_path, self._delete_candidate["id"])
                    elif self._kind == "container":
                        from possession.models import delete_container
                        delete_container(self._db_path, self._delete_candidate["id"])
                    else:  # category
                        from possession.models import delete_category
                        delete_category(self._db_path, self._delete_candidate["id"])
                except ValueError:
                    pass  # already gone
                self.dismiss({
                    "deleted": True,
                    "id": self._delete_candidate["id"],
                    "name": self._delete_candidate["name"],
                })
                event.prevent_default()
                return
            elif event.key in ("n", "escape"):
                # Cancel deletion
                self._delete_mode = False
                self._delete_candidate = None
                confirm = self.query_one("#picker-delete-confirm", Static)
                confirm.add_class("hidden")
                confirm.update("")
                event.prevent_default()
                return
            else:
                # Block all other navigation while confirming
                event.prevent_default()
                return

        # --- Normal mode ---
        if event.key == "d":
            idx = lv.index
            if idx is not None and idx < len(self._filtered):
                candidate = self._filtered[idx]
                self._delete_candidate = candidate
                self._delete_mode = True
                impact = self._get_impact_line(candidate)
                confirm_text = f"Delete '{candidate['name']}'? {impact} [y/n]"
                confirm = self.query_one("#picker-delete-confirm", Static)
                confirm.remove_class("hidden")
                confirm.update(confirm_text)
            event.prevent_default()
        elif event.key == "escape":
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
        hint.update("[dim]d to delete[/dim]")
