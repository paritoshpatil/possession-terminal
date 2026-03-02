from pathlib import Path
from typing import Optional

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
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
    """Parse a slash-separated quick-add string into a field dict."""
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


class QuickAddScreen(ModalScreen):
    """Modal overlay for quickly adding inventory items via slash-separated input."""

    DEFAULT_CSS = """
    QuickAddScreen {
        align: center middle;
    }
    #quickadd-container {
        width: 64;
        border: heavy $primary;
        background: $surface;
        padding: 0 1;
    }
    #quickadd-title {
        text-style: bold;
        color: $surface;
        background: $primary-darken-2;
        text-align: center;
        padding: 0 1;
        margin-bottom: 1;
        margin: 0 -1 1 -1;
    }
    #quickadd-hint {
        color: $text-muted;
        height: 1;
        margin-bottom: 1;
    }
    #quickadd-input {
        width: 1fr;
        height: 3;
        border: tall $surface-darken-1;
        background: $surface-darken-1;
        margin-bottom: 1;
    }
    #quickadd-confirm {
        width: 1fr;
        height: 3;
        border: tall $surface-darken-1;
        background: $surface-darken-1;
        margin-bottom: 1;
    }
    #quickadd-footer {
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

    _FOOTER_TEXT = "enter: save  |  esc: cancel"

    def __init__(self, db_path: Path):
        super().__init__()
        self._db_path = db_path
        self._pending_parsed: Optional[dict] = None
        self._pending_room_id: Optional[int] = None
        self._pending_room_name: Optional[str] = None
        self._pending_container_id: Optional[int] = None
        self._confirm_mode: str = ""  # "room" or "container"

    def compose(self) -> ComposeResult:
        with Vertical(id="quickadd-container"):
            yield Static("Quick Add", id="quickadd-title")
            yield Static(QUICKADD_FORMAT_HINT, id="quickadd-hint")
            yield Input(placeholder="Item name / ...", id="quickadd-input")
            yield Input(placeholder="", id="quickadd-confirm", classes="hidden")
            yield Static(self._FOOTER_TEXT, id="quickadd-footer")

    def on_mount(self) -> None:
        self.query_one("#quickadd-input", Input).focus()

    # ------------------------------------------------------------------
    # Input event handlers
    # ------------------------------------------------------------------

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "quickadd-input":
            self._handle_main_submitted(event.value)
        elif event.input.id == "quickadd-confirm":
            self._handle_confirm_submitted(event.value)

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(None)
            event.prevent_default()

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
        self.dismiss({"saved": True})

    def _resolve_and_save(
        self,
        parsed: dict,
        room_id: Optional[int],
        container_id: Optional[int],
    ) -> None:
        category_id: Optional[int] = None
        if parsed.get("category"):
            cats = list_categories(self._db_path)
            match = next(
                (c for c in cats if c["name"].lower() == parsed["category"].lower()),
                None,
            )
            if match:
                category_id = match["id"]
        self._save_item(parsed, room_id, container_id, category_id)

    def _handle_main_submitted(self, text: str) -> None:
        parsed = _parse_quickadd(text)
        if parsed is None:
            self.dismiss(None)
            return

        self._pending_parsed = parsed

        room_id: Optional[int] = None
        if parsed["room"]:
            rooms = list_rooms(self._db_path)
            match = next(
                (r for r in rooms if r["name"].lower() == parsed["room"].lower()),
                None,
            )
            if match is None:
                self._confirm_mode = "room"
                self._pending_room_name = parsed["room"]
                self._show_confirm(
                    f"Room '{parsed['room']}' not found. Create it? [y/N] "
                )
                return
            room_id = match["id"]
        self._pending_room_id = room_id

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
            self.dismiss(None)
            return

        if self._confirm_mode == "room":
            room_id = create_room(self._db_path, self._pending_room_name)
            self._pending_room_id = room_id

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
