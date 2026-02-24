from typing import List, Optional

from textual import events
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import DataTable

from possession.models import list_items


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
    """Main inventory list screen with DataTable and VIM-style navigation."""

    BINDINGS = [
        ("j", "cursor_down", "Down"),
        ("k", "cursor_up", "Up"),
        ("G", "cursor_bottom", "Bottom"),
        ("q", "app.pop_screen", "Back"),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._items: List[dict] = []
        self._last_key: str = ""

    def compose(self) -> ComposeResult:
        table: DataTable = DataTable(cursor_type="row", show_header=True)
        table.add_column("Name", key="name")
        table.add_column("Description", key="description")
        table.add_column("Location", key="location")
        table.add_column("Category", key="category")
        table.add_column("Cost", key="cost")
        yield table

    def on_mount(self) -> None:
        self._items = list_items(self.app.db_path)
        table = self.query_one(DataTable)
        for row in self._items:
            table.add_row(
                row.get("name") or "",
                row.get("description") or "",
                _fmt_location(row),
                row.get("category_name") or "",
                _fmt_cost(row.get("cost")),
            )

    def on_key(self, event: events.Key) -> None:
        """Handle multi-key sequences (gg = go to top)."""
        if event.key == "g":
            if self._last_key == "g":
                self._last_key = ""
                self.action_cursor_top()
                return
            self._last_key = "g"
        else:
            self._last_key = ""

    def action_cursor_down(self) -> None:
        """Move cursor down one row."""
        self.query_one(DataTable).action_scroll_cursor_down()

    def action_cursor_up(self) -> None:
        """Move cursor up one row."""
        self.query_one(DataTable).action_scroll_cursor_up()

    def action_cursor_bottom(self) -> None:
        """Jump cursor to the last row."""
        table = self.query_one(DataTable)
        table.move_cursor(row=table.row_count - 1)

    def action_cursor_top(self) -> None:
        """Jump cursor to the first row."""
        table = self.query_one(DataTable)
        table.move_cursor(row=0)
