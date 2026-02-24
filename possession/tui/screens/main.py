from typing import List, Optional

from textual import events
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import DataTable, Input, Static

from possession.models import list_items, delete_item


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
    """Main inventory screen — flat list of all items with filter, add, edit, delete."""

    DEFAULT_CSS = """
    .hidden {
        display: none;
    }
    DataTable {
        height: 1fr;
    }
    #topbar {
        dock: top;
        height: 1;
        background: $primary-darken-2;
        color: $text;
        padding: 0 1;
        text-style: bold;
    }
    """

    BINDINGS = [
        ("j", "cursor_down", "Down"),
        ("k", "cursor_up", "Up"),
        ("G", "cursor_bottom", "Bottom"),
        ("/", "open_filter", "Filter"),
        ("a", "open_quickadd", "Add"),
        ("e", "edit_item", "Edit"),
        ("d", "delete_item", "Delete"),
        ("q", "go_back", "Back"),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._items: List[dict] = []
        self._last_key: str = ""
        self._delete_pending_id: Optional[int] = None
        self._filter_text: str = ""

    def compose(self) -> ComposeResult:
        from possession.tui.widgets.quickadd import QuickAddBar
        yield Static("Possession", id="topbar")
        yield DataTable(cursor_type="row", show_header=True)
        yield Input(
            placeholder="Filter... (/ to open, Esc to clear)",
            id="filter-input",
            classes="hidden",
        )
        yield QuickAddBar(id="quickadd-bar", classes="hidden")
        yield Input(
            placeholder="Delete item? [y/N]",
            id="delete-confirm",
            classes="hidden",
        )

    def on_mount(self) -> None:
        self._load_items()

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def _load_items(self) -> None:
        """Load all items and refresh the DataTable. No drill-down branches."""
        table = self.query_one(DataTable)
        try:
            table.clear(columns=True)
        except TypeError:
            table.clear()
        table.add_columns("Name", "Description", "Location", "Category", "Cost")
        self._items = list_items(self.app.db_path)
        self._apply_filter(self._filter_text)

    # ------------------------------------------------------------------
    # Filter bar
    # ------------------------------------------------------------------

    def action_open_filter(self) -> None:
        """Open the filter input bar."""
        inp = self.query_one("#filter-input", Input)
        inp.remove_class("hidden")
        inp.focus()

    def action_open_quickadd(self) -> None:
        """Open the quick-add bar."""
        from possession.tui.widgets.quickadd import QuickAddBar
        self.query_one("#quickadd-bar", QuickAddBar).open(self.app.db_path)

    def on_quick_add_bar_item_saved(self, event) -> None:
        """Reload the DataTable after a quick-add save."""
        self._load_items()

    def on_screen_resume(self) -> None:
        """Reload DataTable whenever this screen returns to the foreground (e.g. after edit)."""
        self._load_items()

    def _get_current_row_key_str(self) -> Optional[str]:
        """Return the string row key for the currently highlighted DataTable row, or None."""
        table = self.query_one(DataTable)
        row_keys = list(table.rows.keys())
        if table.cursor_row < len(row_keys):
            return row_keys[table.cursor_row].value
        return None

    def action_edit_item(self) -> None:
        """Open EditItemScreen for the currently selected item."""
        row_key_str = self._get_current_row_key_str()
        if row_key_str is None:
            return
        item = next((i for i in self._items if str(i["id"]) == row_key_str), None)
        if item is not None:
            from possession.tui.screens.edit import EditItemScreen
            self.app.push_screen(EditItemScreen(item, self.app.db_path))

    def action_delete_item(self) -> None:
        """Show delete confirmation prompt for the currently selected item."""
        row_key_str = self._get_current_row_key_str()
        if row_key_str is None:
            return
        item = next((i for i in self._items if str(i["id"]) == row_key_str), None)
        if item is not None:
            self._delete_pending_id = item["id"]
            del_inp = self.query_one("#delete-confirm", Input)
            del_inp.placeholder = f"Delete '{item['name']}'? [y/N]"
            del_inp.remove_class("hidden")
            del_inp.focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter on the delete confirmation input."""
        if event.input.id == "delete-confirm":
            val = event.value.strip().lower()
            event.input.value = ""
            event.input.add_class("hidden")
            self.query_one(DataTable).focus()
            if val == "y" and self._delete_pending_id is not None:
                try:
                    delete_item(self.app.db_path, self._delete_pending_id)
                except ValueError:
                    pass  # already gone
                self._delete_pending_id = None
                self._load_items()
            else:
                self._delete_pending_id = None
            return

    def on_input_changed(self, event: Input.Changed) -> None:
        """Live-filter the DataTable as the user types."""
        if event.input.id == "filter-input":
            self._apply_filter(event.value)

    def _apply_filter(self, query: str) -> None:
        """Filter the DataTable by query string (case-insensitive). Items only."""
        self._filter_text = query
        table = self.query_one(DataTable)
        table.clear()
        q = query.lower().strip()
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

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Enter on a row is a no-op in Phase 4 (Phase 5 will wire detail panel)."""
        return

    def action_go_back(self) -> None:
        self.app.exit()

    # ------------------------------------------------------------------
    # Key handling
    # ------------------------------------------------------------------

    def on_key(self, event: events.Key) -> None:
        """Handle multi-key sequences and filter bar escape."""
        if event.key == "escape":
            del_inp = self.query_one("#delete-confirm", Input)
            if not del_inp.has_class("hidden"):
                del_inp.value = ""
                del_inp.add_class("hidden")
                self._delete_pending_id = None
                self.query_one(DataTable).focus()
                event.prevent_default()
                return
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
