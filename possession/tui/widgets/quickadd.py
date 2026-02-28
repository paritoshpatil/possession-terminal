from pathlib import Path
from typing import Optional

from textual.app import ComposeResult
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Input, Static

from possession.models import (
    create_item,
    create_room,
    create_container,
    list_rooms,
    list_containers,
    list_categories,
)

QUICKADD_FORMAT_HINT = "name / description / room / container / category / date / cost"


def _parse_quickadd(text: str) -> Optional[dict]:
    """Parse a slash-separated quick-add string into a field dict.

    Fields (positional):
      0: name (required)
      1: description
      2: room (name string)
      3: container (name string)
      4: category (name string)
      5: purchase_date
      6: cost (float or None)

    Returns None if name is empty after strip.
    """
    parts = [p.strip() for p in text.split("/")]

    def _get(index: int) -> Optional[str]:
        if index < len(parts):
            val = parts[index]
            return val if val else None
        return None

    name = _get(0) or ""
    if not name:
        return None

    cost_raw = _get(6)
    cost: Optional[float] = None
    if cost_raw is not None:
        try:
            cost = float(cost_raw)
        except ValueError:
            cost = None

    return {
        "name": name,
        "description": _get(1),
        "room": _get(2),
        "container": _get(3),
        "category": _get(4),
        "purchase_date": _get(5),
        "cost": cost,
    }


class QuickAddBar(Widget):
    """A keyboard-driven bar for quickly adding inventory items.

    Opens on 'a' keypress, accepts slash-separated input, and posts
    QuickAddBar.ItemSaved when an item is successfully saved.
    """

    DEFAULT_CSS = """
    QuickAddBar {
        height: 2;
        dock: bottom;
    }
    QuickAddBar.hidden {
        display: none;
    }
    #quickadd-label {
        height: 1;
        color: $text-muted;
        padding: 0 1;
    }
    #quickadd-input {
        height: 1;
        border: none;
        padding: 0 1;
        background: $surface-darken-1;
    }
    #quickadd-confirm {
        height: 1;
        border: none;
        padding: 0 1;
        background: $surface-darken-1;
    }
    """

    class ItemSaved(Message):
        """Posted when a new item has been saved to the database."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._db_path: Optional[Path] = None
        # Pending state for confirmation flow
        self._pending_parsed: Optional[dict] = None
        self._pending_room_id: Optional[int] = None
        self._pending_room_name: Optional[str] = None
        self._pending_container_id: Optional[int] = None
        self._confirm_mode: str = ""  # "room" or "container"

    def compose(self) -> ComposeResult:
        yield Static(QUICKADD_FORMAT_HINT, id="quickadd-label")
        yield Input(
            placeholder="",
            id="quickadd-input",
        )
        yield Input(
            placeholder="Room not found. Create it? [y/N]",
            id="quickadd-confirm",
            classes="hidden",
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def open(self, db_path: Path) -> None:
        """Show the quick-add bar and focus the input."""
        self._db_path = db_path
        self._reset_pending()
        self.remove_class("hidden")
        self.query_one("#quickadd-input", Input).focus()

    def close(self) -> None:
        """Hide the quick-add bar and clear inputs."""
        self.add_class("hidden")
        main_input = self.query_one("#quickadd-input", Input)
        main_input.value = ""
        main_input.remove_class("hidden")
        confirm = self.query_one("#quickadd-confirm", Input)
        confirm.value = ""
        confirm.add_class("hidden")
        self._reset_pending()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _reset_pending(self) -> None:
        self._pending_parsed = None
        self._pending_room_id = None
        self._pending_room_name = None
        self._pending_container_id = None
        self._confirm_mode = ""

    def _show_confirm(self, message: str) -> None:
        self.query_one("#quickadd-input", Input).add_class("hidden")
        confirm = self.query_one("#quickadd-confirm", Input)
        confirm.placeholder = message
        confirm.value = ""
        confirm.remove_class("hidden")
        confirm.focus()

    def _save_item(
        self,
        parsed: dict,
        room_id: Optional[int],
        container_id: Optional[int],
        category_id: Optional[int],
    ) -> None:
        """Write the item to the database and post ItemSaved."""
        create_item(
            self._db_path,
            name=parsed["name"],
            description=parsed["description"],
            room_id=room_id,
            container_id=container_id,
            category_id=category_id,
            purchase_date=parsed["purchase_date"],
            cost=parsed["cost"],
        )
        self.post_message(self.ItemSaved())
        self.close()

    def _resolve_and_save(
        self,
        parsed: dict,
        room_id: Optional[int],
        container_id: Optional[int],
    ) -> None:
        """Resolve category then save the item."""
        category_id: Optional[int] = None
        if parsed.get("category"):
            cats = list_categories(self._db_path)
            match = next(
                (c for c in cats if c["name"].lower() == parsed["category"].lower()),
                None,
            )
            if match:
                category_id = match["id"]
            # If not found, we silently store NULL (category auto-create not required)

        self._save_item(parsed, room_id, container_id, category_id)

    # ------------------------------------------------------------------
    # Input event handlers
    # ------------------------------------------------------------------

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter in either the main input or the confirm input."""
        if event.input.id == "quickadd-input":
            self._handle_main_submitted(event.value)
        elif event.input.id == "quickadd-confirm":
            self._handle_confirm_submitted(event.value)

    def on_key(self, event) -> None:
        """Handle Escape to dismiss the bar."""
        if event.key == "escape":
            self.close()
            event.prevent_default()
            event.stop()

    def _handle_main_submitted(self, text: str) -> None:
        parsed = _parse_quickadd(text)
        if parsed is None:
            # Empty name — dismiss without saving
            self.close()
            return

        self._pending_parsed = parsed

        # Resolve room
        room_id: Optional[int] = None
        if parsed["room"]:
            rooms = list_rooms(self._db_path)
            match = next(
                (r for r in rooms if r["name"].lower() == parsed["room"].lower()),
                None,
            )
            if match is None:
                # Room not found — ask user
                self._confirm_mode = "room"
                self._pending_room_name = parsed["room"]
                self._show_confirm(
                    f"Room '{parsed['room']}' not found. Create it? [y/N] "
                )
                return
            room_id = match["id"]
        self._pending_room_id = room_id

        # Resolve container (only if room resolved)
        container_id: Optional[int] = None
        if parsed["container"] and room_id is not None:
            containers = list_containers(self._db_path, room_id=room_id)
            match = next(
                (c for c in containers if c["name"].lower() == parsed["container"].lower()),
                None,
            )
            if match is None:
                self._confirm_mode = "container"
                self._show_confirm(
                    f"Container '{parsed['container']}' not found in '{parsed['room']}'. Create it? [y/N] "
                )
                return
            container_id = match["id"]
        self._pending_container_id = container_id

        self._resolve_and_save(parsed, room_id, container_id)

    def _handle_confirm_submitted(self, text: str) -> None:
        answer = text.strip().lower()
        parsed = self._pending_parsed

        if answer != "y":
            self.close()
            return

        if self._confirm_mode == "room":
            room_name = self._pending_room_name
            room_id = create_room(self._db_path, room_name)
            self._pending_room_id = room_id

            # Now check container
            container_id: Optional[int] = None
            if parsed["container"]:
                containers = list_containers(self._db_path, room_id=room_id)
                match = next(
                    (c for c in containers if c["name"].lower() == parsed["container"].lower()),
                    None,
                )
                if match is None:
                    self._confirm_mode = "container"
                    self._show_confirm(
                        f"Container '{parsed['container']}' not found. Create it? [y/N] "
                    )
                    return
                container_id = match["id"]
            self._pending_container_id = container_id
            self._resolve_and_save(parsed, room_id, container_id)

        elif self._confirm_mode == "container":
            room_id = self._pending_room_id
            container_id = create_container(
                self._db_path, parsed["container"], room_id
            )
            self._pending_container_id = container_id
            self._resolve_and_save(parsed, room_id, container_id)
