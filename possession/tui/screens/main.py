from typing import List, Optional

from textual import events
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import DataTable, Input

from possession.models import list_items, list_rooms, list_containers


def _fmt_location(row: dict) -> str:
    """Format location as 'Room > Container', 'Room', 'Container', or ''."""
    room = row.get("room_name") or ""
    container = row.get("container_name") or ""
    if room and container:
        return f"{room} > {container}"
    return room or container or ""


def _fmt_cost(cost) -> str:
    """Format cost as '$X.XX' or '' if None."""
    if cost is None:
        return ""
    return f"${cost:.2f}"


class MainScreen(Screen):
    """Main inventory screen with filter bar, drill-down navigation, and breadcrumb."""

    CSS = """
    .hidden {
        display: none;
    }
    DataTable {
        height: 1fr;
    }
    """

    BINDINGS = [
        ("j", "cursor_down", "Down"),
        ("k", "cursor_up", "Up"),
        ("G", "cursor_bottom", "Bottom"),
        ("/", "open_filter", "Filter"),
        ("q", "go_back", "Back"),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._items: List[dict] = []
        self._rooms: List[dict] = []
        self._containers: List[dict] = []
        self._last_key: str = ""
        # Drill-down state
        self._view_mode: str = "rooms"
        self._current_room_id: Optional[int] = None
        self._current_room_name: str = ""
        self._current_container_id: Optional[int] = None
        self._current_container_name: str = ""

    def compose(self) -> ComposeResult:
        from possession.tui.widgets.breadcrumb import Breadcrumb
        yield Breadcrumb(id="breadcrumb")
        yield DataTable(cursor_type="row", show_header=True)
        yield Input(
            placeholder="Filter... (/ to open, Esc to clear)",
            id="filter-input",
            classes="hidden",
        )

    def on_mount(self) -> None:
        self._view_mode = "rooms"
        self._load_view()
        self._update_breadcrumb()

    # ------------------------------------------------------------------
    # Filter bar
    # ------------------------------------------------------------------

    def action_open_filter(self) -> None:
        """Open the filter input bar."""
        inp = self.query_one("#filter-input", Input)
        inp.remove_class("hidden")
        inp.focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Live-filter the DataTable as the user types."""
        self._apply_filter(event.value)

    def _apply_filter(self, query: str) -> None:
        """Filter the DataTable by query string (case-insensitive). Works in all view modes."""
        table = self.query_one(DataTable)
        table.clear()
        q = query.lower().strip()

        if self._view_mode == "rooms":
            for room in self._rooms:
                if q and q not in room["name"].lower():
                    continue
                table.add_row(
                    room["name"],
                    str(room["_container_count"]),
                    key=str(room["id"]),
                )
        elif self._view_mode == "containers":
            for c in self._containers:
                if q and q not in c["name"].lower():
                    continue
                table.add_row(
                    c["name"],
                    str(c["_item_count"]),
                    key=str(c["id"]),
                )
        else:  # items
            for item in self._items:
                if q and not any(
                    q in (item.get(f) or "").lower()
                    for f in ("name", "description", "room_name",
                              "container_name", "category_name")
                ):
                    continue
                table.add_row(
                    item["name"],
                    item.get("description") or "",
                    _fmt_location(item),
                    item.get("category_name") or "",
                    _fmt_cost(item.get("cost")),
                    key=str(item["id"]),
                )

    # ------------------------------------------------------------------
    # Drill-down state machine
    # ------------------------------------------------------------------

    def _load_view(self) -> None:
        """Load data for the current view mode and refresh the DataTable."""
        table = self.query_one(DataTable)
        try:
            table.clear(columns=True)
        except TypeError:
            table.clear()

        if self._view_mode == "rooms":
            table.add_columns("Room", "Containers")
            rooms = list_rooms(self.app.db_path)
            self._rooms = []
            for room in rooms:
                containers = list_containers(self.app.db_path, room_id=room["id"])
                self._rooms.append({**room, "_container_count": len(containers)})
            self._apply_filter("")

        elif self._view_mode == "containers":
            table.add_columns("Container", "Items")
            containers = list_containers(
                self.app.db_path, room_id=self._current_room_id
            )
            self._containers = []
            for c in containers:
                items = list_items(self.app.db_path, container_id=c["id"])
                self._containers.append({**c, "_item_count": len(items)})
            self._apply_filter("")

        else:  # "items"
            table.add_columns("Name", "Description", "Location", "Category", "Cost")
            items = list_items(
                self.app.db_path,
                room_id=self._current_room_id,
                container_id=self._current_container_id,
            )
            self._items = items
            self._apply_filter("")

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Drill into a row based on current view mode."""
        row_key = event.row_key.value  # the string ID we passed as key=
        if self._view_mode == "items":
            # No drill-in from items in Phase 2 (Phase 3 will use this for edit)
            return
        elif self._view_mode == "rooms":
            room_id = int(row_key)
            rooms = list_rooms(self.app.db_path)
            room = next((r for r in rooms if r["id"] == room_id), None)
            if room:
                self._current_room_id = room_id
                self._current_room_name = room["name"]
                self._view_mode = "containers"
                self._load_view()
                self._update_breadcrumb()
        elif self._view_mode == "containers":
            container_id = int(row_key)
            containers = list_containers(
                self.app.db_path, room_id=self._current_room_id
            )
            container = next((c for c in containers if c["id"] == container_id), None)
            if container:
                self._current_container_id = container_id
                self._current_container_name = container["name"]
                self._view_mode = "items"
                self._load_view()
                self._update_breadcrumb()

    def action_go_back(self) -> None:
        """Go back one level in the drill-down hierarchy."""
        if self._view_mode == "items" and self._current_container_id is not None:
            # Was in container drill-down → go back to containers list for this room
            self._current_container_id = None
            self._current_container_name = ""
            self._view_mode = "containers"
            self._load_view()
            self._update_breadcrumb()
        elif self._view_mode == "items" and self._current_room_id is not None:
            # Was in room drill-down (no container) → go back to rooms list
            self._current_room_id = None
            self._current_room_name = ""
            self._view_mode = "rooms"
            self._load_view()
            self._update_breadcrumb()
        elif self._view_mode == "containers":
            self._current_room_id = None
            self._current_room_name = ""
            self._view_mode = "rooms"
            self._load_view()
            self._update_breadcrumb()
        elif self._view_mode == "rooms":
            # Already at top — exit app
            self.app.exit()

    # ------------------------------------------------------------------
    # Breadcrumb
    # ------------------------------------------------------------------

    def _update_breadcrumb(self) -> None:
        """Update breadcrumb to reflect current drill-down path."""
        from possession.tui.widgets.breadcrumb import Breadcrumb
        if self._view_mode == "rooms":
            path = "All Rooms"
        elif self._view_mode == "containers":
            path = self._current_room_name
        else:  # items
            if self._current_container_name:
                path = f"{self._current_room_name} > {self._current_container_name}"
            elif self._current_room_name:
                path = self._current_room_name
            else:
                path = "All Items"
        self.query_one(Breadcrumb).set_path(path)

    # ------------------------------------------------------------------
    # Key handling
    # ------------------------------------------------------------------

    def on_key(self, event: events.Key) -> None:
        """Handle multi-key sequences and filter bar escape."""
        if event.key == "escape":
            inp = self.query_one("#filter-input", Input)
            if not inp.has_class("hidden"):
                inp.value = ""
                inp.add_class("hidden")
                self.query_one(DataTable).focus()
                self._apply_filter("")
                event.prevent_default()
                return
        if event.key == "g":
            if self._last_key == "g":
                self._last_key = ""
                self.action_cursor_top()
                return
            self._last_key = "g"
        else:
            self._last_key = ""

    # ------------------------------------------------------------------
    # Cursor actions
    # ------------------------------------------------------------------

    def action_cursor_down(self) -> None:
        """Move cursor down one row."""
        self.query_one(DataTable).action_cursor_down()

    def action_cursor_up(self) -> None:
        """Move cursor up one row."""
        self.query_one(DataTable).action_cursor_up()

    def action_cursor_bottom(self) -> None:
        """Jump cursor to the last row."""
        table = self.query_one(DataTable)
        table.move_cursor(row=table.row_count - 1)

    def action_cursor_top(self) -> None:
        """Jump cursor to the first row."""
        table = self.query_one(DataTable)
        table.move_cursor(row=0)
