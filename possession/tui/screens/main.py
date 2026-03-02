from typing import List, Optional

from textual import events
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import DataTable, Input, Static

from possession.models import list_items, delete_item
from possession.tui.widgets.statsbar import StatsBar
from possession.tui.widgets.detailpanel import DetailPanel


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
    #topbar {
        dock: top;
        height: 1;
        background: $primary-darken-2;
        color: $text;
        padding: 0 1;
        text-style: bold;
        text-align: center;
        margin-bottom: 1;
    }
    #main-body {
        height: 1fr;
    }
    DataTable {
        width: 7fr;
        height: 1fr;
        color: $text;
        padding: 0 1;
        padding-top: 1;
        background: transparent;
        border: heavy $primary;
        border-title-align: left;
    }

    DataTable > .datatable--header {
        background: $primary;
        color: $surface;
    }
    #detail-panel {
        width: 3fr;
        height: 1fr;
    }
    #footer {
        dock: bottom;
        height: 1;
        background: $primary-darken-2;
        color: $surface;
        padding: 0 1;
        text-align: center;
        text-style: bold;
    }
    #filter-input {
        margin: 0;
        border: heavy $primary;
        background: transparent;
    }

    #delete-confirm {
        margin: 0;
        border: heavy $primary;
        background: transparent;
    }
    """

    BINDINGS = [
        ("j", "cursor_down", "Down"),
        ("k", "cursor_up", "Up"),
        ("G", "cursor_bottom", "Bottom"),
        ("h", "scroll_left", "Scroll left"),
        ("l", "scroll_right", "Scroll right"),
        ("/", "open_filter", "Filter"),
        ("r", "open_room_picker", "Room"),
        ("c", "open_container_picker", "Container"),
        ("t", "open_category_picker", "Category"),
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
        self._filter_room_id: Optional[int] = None
        self._filter_room_name: Optional[str] = None
        self._filter_container_id: Optional[int] = None
        self._filter_container_name: Optional[str] = None
        self._filter_category_id: Optional[int] = None
        self._filter_category_name: Optional[str] = None

    _FOOTER_TEXT = (
        "add: a | edit: e | delete item: d | rooms: r | containers: c | categories: t"
        " | details: enter | close: esc | quit: q"
    )

    app_title = r"""
    ▗▄▄▖  ▗▄▖  ▗▄▄▖ ▗▄▄▖▗▄▄▄▖ ▗▄▄▖ ▗▄▄▖▗▄▄▄▖ ▗▄▖ ▗▖  ▗▖
    ▐▌ ▐▌▐▌ ▐▌▐▌   ▐▌   ▐▌   ▐▌   ▐▌     █  ▐▌ ▐▌▐▛▚▖▐▌
    ▐▛▀▘ ▐▌ ▐▌ ▝▀▚▖ ▝▀▚▖▐▛▀▀▘ ▝▀▚▖ ▝▀▚▖  █  ▐▌ ▐▌▐▌ ▝▜▌
    ▐▌   ▝▚▄▞▘▗▄▄▞▘▗▄▄▞▘▐▙▄▄▖▗▄▄▞▘▗▄▄▞▘▗▄█▄▖▝▚▄▞▘▐▌  ▐▌                                         
    """
    def compose(self) -> ComposeResult:
        yield Static("possession", id="topbar")
        yield StatsBar(id="stats-bar")
        with Horizontal(id="main-body"):
            table = DataTable(cursor_type="row", show_header=True)
            table.border_title = "Items"
            table.border_subtitle = "<- -> to scroll"
            yield table
            yield DetailPanel(id="detail-panel", classes="hidden")
        yield Input(
            placeholder="Filter... (/ to open, Esc to clear)",
            id="filter-input",
            classes="hidden",
        )
        yield Input(
            placeholder="Delete item? [y/N]",
            id="delete-confirm",
            classes="hidden",
        )
        yield Static(self._FOOTER_TEXT, id="footer")

    def on_mount(self) -> None:
        self._load_items()

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def _refresh_stats(self) -> None:
        """Update stats bar with current DB counts, filtered count, and active filter tags."""
        tags = self._build_filter_tags()
        self.query_one(StatsBar).refresh_stats(
            self.app.db_path,
            item_count_override=len(self._items),
            filter_tags=tags,
        )

    def _load_items(self) -> None:
        """Load items (with active filters) and refresh the DataTable and stats bar."""
        table = self.query_one(DataTable)
        try:
            table.clear(columns=True)
        except TypeError:
            table.clear()
        table.add_columns("Name", "Description", "Location", "Category", "Cost")
        self._items = list_items(
            self.app.db_path,
            room_id=self._filter_room_id,
            container_id=self._filter_container_id,
            category_id=self._filter_category_id,
        )
        self._apply_filter(self._filter_text)
        self._refresh_stats()  # Always refresh stats after loading items

    def _build_filter_tags(self) -> str:
        """Build a string of active filter tags for display in the stats bar."""
        parts = []
        if self._filter_room_id is not None and self._filter_room_name:
            parts.append(f"[Room: {self._filter_room_name}]")
        if self._filter_container_id is not None and self._filter_container_name:
            parts.append(f"[Container: {self._filter_container_name}]")
        if self._filter_category_id is not None and self._filter_category_name:
            parts.append(f"[Category: {self._filter_category_name}]")
        return " ".join(parts)

    def _any_filter_active(self) -> bool:
        """Return True if any picker filter (room/container/category) is active."""
        return any([
            self._filter_room_id is not None,
            self._filter_container_id is not None,
            self._filter_category_id is not None,
        ])

    def _any_input_active(self) -> bool:
        """Return True if any text input overlay (filter, delete-confirm) is open."""
        filter_inp = self.query_one("#filter-input", Input)
        del_inp = self.query_one("#delete-confirm", Input)
        return (
            not filter_inp.has_class("hidden")
            or not del_inp.has_class("hidden")
        )

    # ------------------------------------------------------------------
    # Filter bar
    # ------------------------------------------------------------------

    def action_open_filter(self) -> None:
        """Open the filter input bar."""
        inp = self.query_one("#filter-input", Input)
        inp.remove_class("hidden")
        inp.focus()

    def action_open_quickadd(self) -> None:
        """Open the quick-add modal overlay."""
        if self._any_input_active():
            return
        from possession.tui.screens.quickadd import QuickAddScreen
        self.app.push_screen(QuickAddScreen(self.app.db_path), self._on_quickadd_done)

    def _on_quickadd_done(self, result) -> None:
        if result and result.get("saved"):
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
        if table.row_count == 0 and self._any_filter_active():
            table.add_row(
                "No items match the current filters", "", "", "", "",
                key="__empty__",
            )

    # ------------------------------------------------------------------
    # Picker actions (r / c / t)
    # ------------------------------------------------------------------

    def action_open_room_picker(self) -> None:
        """Open the Room filter picker modal."""
        if self._any_input_active():
            return
        from possession.models import list_rooms
        from possession.tui.screens.filter_picker import FilterPickerScreen
        rooms = list_rooms(self.app.db_path)
        self.app.push_screen(
            FilterPickerScreen("Room", rooms, self._filter_room_id, db_path=self.app.db_path, kind="room"),
            self._on_room_picked,
        )

    def action_open_container_picker(self) -> None:
        """Open the Container filter picker modal."""
        if self._any_input_active():
            return
        from possession.models import list_containers
        from possession.tui.screens.filter_picker import FilterPickerScreen
        containers = list_containers(self.app.db_path)
        self.app.push_screen(
            FilterPickerScreen("Container", containers, self._filter_container_id, db_path=self.app.db_path, kind="container"),
            self._on_container_picked,
        )

    def action_open_category_picker(self) -> None:
        """Open the Category filter picker modal."""
        if self._any_input_active():
            return
        from possession.models import list_categories
        from possession.tui.screens.filter_picker import FilterPickerScreen
        categories = list_categories(self.app.db_path)
        self.app.push_screen(
            FilterPickerScreen("Category", categories, self._filter_category_id, db_path=self.app.db_path, kind="category"),
            self._on_category_picked,
        )

    def _on_room_picked(self, result: Optional[dict]) -> None:
        """Callback from the Room picker. Toggles filter if same room selected, else sets."""
        if result is None:
            return  # Escape — no change
        if result.get("deleted"):
            # Entity was deleted — clear filter if it was active, reload
            if self._filter_room_id == result["id"]:
                self._filter_room_id = None
                self._filter_room_name = None
            self._load_items()
            return
        if result["id"] == self._filter_room_id:
            self._filter_room_id = None
            self._filter_room_name = None
        else:
            self._filter_room_id = result["id"]
            self._filter_room_name = result["name"]
        self._load_items()

    def _on_container_picked(self, result: Optional[dict]) -> None:
        """Callback from the Container picker. Toggles filter if same container selected."""
        if result is None:
            return
        if result.get("deleted"):
            # Entity was deleted — clear filter if it was active, reload
            if self._filter_container_id == result["id"]:
                self._filter_container_id = None
                self._filter_container_name = None
            self._load_items()
            return
        if result["id"] == self._filter_container_id:
            self._filter_container_id = None
            self._filter_container_name = None
        else:
            self._filter_container_id = result["id"]
            self._filter_container_name = result["name"]
        self._load_items()

    def _on_category_picked(self, result: Optional[dict]) -> None:
        """Callback from the Category picker. Toggles filter if same category selected."""
        if result is None:
            return
        if result.get("deleted"):
            # Entity was deleted — clear filter if it was active, reload
            if self._filter_category_id == result["id"]:
                self._filter_category_id = None
                self._filter_category_name = None
            self._load_items()
            return
        if result["id"] == self._filter_category_id:
            self._filter_category_id = None
            self._filter_category_name = None
        else:
            self._filter_category_id = result["id"]
            self._filter_category_name = result["name"]
        self._load_items()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Enter toggles the detail panel open/closed."""
        panel = self.query_one("#detail-panel", DetailPanel)
        panel.display = not panel.display
        if panel.display:
            # Panel just opened — populate with current row
            row_key_str = event.row_key.value if event.row_key else None
            if row_key_str:
                item = next(
                    (i for i in self._items if str(i["id"]) == row_key_str),
                    None,
                )
                if item:
                    panel.show_item(item)
        self.query_one(DataTable).focus()

    def on_data_table_row_highlighted(
        self, event: DataTable.RowHighlighted
    ) -> None:
        """Update detail panel live as cursor moves (only when panel is open)."""
        panel = self.query_one("#detail-panel", DetailPanel)
        if not panel.display:
            return
        if not self._items:
            return
        row_key_str = event.row_key.value if event.row_key else None
        if row_key_str is None:
            return
        item = next(
            (i for i in self._items if str(i["id"]) == row_key_str), None
        )
        if item is not None:
            panel.show_item(item)

    def action_go_back(self) -> None:
        self.app.exit()

    # ------------------------------------------------------------------
    # Key handling
    # ------------------------------------------------------------------

    def on_key(self, event: events.Key) -> None:
        """Handle escape hierarchy: panel > delete-confirm > filter > (app exit via binding)."""
        if event.key == "escape":
            # 1. Delete confirm (existing)
            del_inp = self.query_one("#delete-confirm", Input)
            if not del_inp.has_class("hidden"):
                del_inp.value = ""
                del_inp.add_class("hidden")
                self._delete_pending_id = None
                self.query_one(DataTable).focus()
                event.prevent_default()
                return
            # 2. Filter input (existing)
            inp = self.query_one("#filter-input", Input)
            if not inp.has_class("hidden"):
                inp.value = ""
                inp.add_class("hidden")
                self.query_one(DataTable).focus()
                self._apply_filter("")
                event.prevent_default()
                return
            # 3. Nothing open -> fall through (action_go_back binding handles exit)
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

    _H_SCROLL_STEP = 8

    def action_cursor_down(self) -> None:
        self.query_one(DataTable).action_cursor_down()

    def action_cursor_up(self) -> None:
        self.query_one(DataTable).action_cursor_up()

    def action_cursor_bottom(self) -> None:
        table = self.query_one(DataTable)
        table.move_cursor(row=table.row_count - 1, animate=False)

    def action_cursor_top(self) -> None:
        table = self.query_one(DataTable)
        table.move_cursor(row=0, animate=False)

    def action_scroll_left(self) -> None:
        self.query_one(DataTable).scroll_relative(x=-self._H_SCROLL_STEP, animate=False)

    def action_scroll_right(self) -> None:
        self.query_one(DataTable).scroll_relative(x=self._H_SCROLL_STEP, animate=False)   
