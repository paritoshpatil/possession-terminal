from pathlib import Path
from typing import Optional

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Input, Static
from textual.containers import Vertical

from possession.models import (
    update_item,
    list_rooms,
    list_containers,
    list_categories,
    create_room,
    create_container,
    create_category,
)


class EditItemScreen(Screen):
    """Form screen for editing an existing inventory item."""

    DEFAULT_CSS = """
    EditItemScreen Vertical {
        padding: 1 2;
    }
    EditItemScreen Input {
        margin-bottom: 1;
    }
    """

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
        ("ctrl+s", "save", "Save"),
    ]

    def __init__(self, item: dict, db_path: Path, **kwargs):
        super().__init__(**kwargs)
        self._item = item
        self._db_path = db_path

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("Edit Item  (Tab to move, Ctrl+S to save, Escape to cancel)")
            yield Input(
                value=self._item.get("name") or "",
                id="edit-name",
                placeholder="Item name",
            )
            yield Input(
                value=self._item.get("description") or "",
                id="edit-description",
                placeholder="Description",
            )
            yield Input(
                value=self._item.get("room_name") or "",
                id="edit-room",
                placeholder="Room name (leave blank to clear)",
            )
            yield Input(
                value=self._item.get("container_name") or "",
                id="edit-container",
                placeholder="Container name (leave blank to clear)",
            )
            yield Input(
                value=self._item.get("category_name") or "",
                id="edit-category",
                placeholder="Category name (leave blank to clear)",
            )
            yield Input(
                value=self._item.get("purchase_date") or "",
                id="edit-purchase-date",
                placeholder="Purchase date (YYYY-MM-DD)",
            )
            cost_val = self._item.get("cost")
            yield Input(
                value=str(cost_val) if cost_val is not None else "",
                id="edit-cost",
                placeholder="Cost (e.g. 9.99)",
            )

    def action_cancel(self) -> None:
        """Dismiss the edit screen without saving."""
        self.app.pop_screen()

    def action_save(self) -> None:
        """Read form values, resolve names to IDs, and call update_item()."""
        name_val = self.query_one("#edit-name", Input).value.strip()
        desc_val = self.query_one("#edit-description", Input).value.strip()
        room_val = self.query_one("#edit-room", Input).value.strip()
        container_val = self.query_one("#edit-container", Input).value.strip()
        category_val = self.query_one("#edit-category", Input).value.strip()
        date_val = self.query_one("#edit-purchase-date", Input).value.strip()
        cost_str = self.query_one("#edit-cost", Input).value.strip()

        # Resolve room name -> room_id
        room_id: Optional[int] = None
        if room_val:
            rooms = list_rooms(self._db_path)
            room = next((r for r in rooms if r["name"].lower() == room_val.lower()), None)
            if room:
                room_id = room["id"]
            else:
                room_id = create_room(self._db_path, room_val)

        # Resolve container name -> container_id (only if room is set)
        container_id: Optional[int] = None
        if container_val and room_id is not None:
            containers = list_containers(self._db_path, room_id=room_id)
            container = next(
                (c for c in containers if c["name"].lower() == container_val.lower()), None
            )
            if container:
                container_id = container["id"]
            else:
                container_id = create_container(self._db_path, container_val, room_id)
        # If room is empty, container_id stays None (can't have container without room)

        # Resolve category name -> category_id
        category_id: Optional[int] = None
        if category_val:
            categories = list_categories(self._db_path)
            category = next(
                (c for c in categories if c["name"].lower() == category_val.lower()), None
            )
            if category:
                category_id = category["id"]
            else:
                category_id = create_category(self._db_path, category_val)

        # Parse cost
        cost_val: Optional[float] = float(cost_str) if cost_str else None

        # Call update_item with all fields explicitly
        # name and description: pass empty string to clear (model uses != None check,
        # empty string is not None so it will be included in the UPDATE)
        update_item(
            self._db_path,
            self._item["id"],
            name=name_val if name_val else self._item.get("name"),
            description=desc_val if desc_val else None,
            room_id=room_id,
            container_id=container_id,
            category_id=category_id,
            purchase_date=date_val if date_val else None,
            cost=cost_val,
        )

        self.app.pop_screen()
