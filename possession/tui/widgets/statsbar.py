from typing import Optional

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import Static


class StatsBar(Widget):
    """Horizontal bar showing 4 aggregate inventory stats.

    Renders two rows (label on top, value below) in 4 equal-width columns:
        Items   Rooms   Containers   Value
        42      8       12           $1,240.00

    Do NOT dock this widget — MainScreen yields it in normal compose flow
    between the topbar and the main body.
    """

    DEFAULT_CSS = """
StatsBar {
    height: 4;
    background: transparent;
    border: heavy $primary-darken-2;
    border-title-align: left;
}
StatsBar Horizontal {
    height: 2;
}
.stats-column {
    width: 1fr;
    height: 2;
    padding: 0 1;
    content-align: center middle;
}
.stats-label {
    height: 1;
    color: $text-muted;
    text-align: center;
    text-style: bold;
}
.stats-value {
    height: 1;
    text-align: center;
}
"""

    def compose(self) -> ComposeResult:
        with Horizontal():
            with Vertical(classes="stats-column"):
                yield Static("Items", classes="stats-label", id="stat-label-items")
                yield Static("0", classes="stats-value", id="stat-val-items")
            with Vertical(classes="stats-column"):
                yield Static("Rooms", classes="stats-label", id="stat-label-rooms")
                yield Static("0", classes="stats-value", id="stat-val-rooms")
            with Vertical(classes="stats-column"):
                yield Static("Containers", classes="stats-label", id="stat-label-containers")
                yield Static("0", classes="stats-value", id="stat-val-containers")
            with Vertical(classes="stats-column"):
                yield Static("Value", classes="stats-label", id="stat-label-value")
                yield Static("$0.00", classes="stats-value", id="stat-val-value")

    def on_mount(self) -> None:
        self.border_title = "Stats"

    def refresh_stats(
        self,
        db_path,
        item_count_override: Optional[int] = None,
        filter_tags: str = "",
    ) -> None:
        """Query the database and update all four stat value widgets.

        Args:
            db_path: Path to the SQLite database file.
            item_count_override: When provided, display this count instead of the
                global item_count from get_stats(). Used to show the filtered count.
            filter_tags: When non-empty, appended after the item count (e.g.
                "[Room: Kitchen] [Category: Audio]").
        """
        from possession.models import get_stats
        stats = get_stats(db_path)
        display_count = item_count_override if item_count_override is not None else stats["item_count"]
        item_text = str(display_count)
        if filter_tags:
            item_text = f"{item_text} {filter_tags}"
        self.query_one("#stat-val-items", Static).update(item_text)
        self.query_one("#stat-val-rooms", Static).update(str(stats["room_count"]))
        self.query_one("#stat-val-containers", Static).update(str(stats["container_count"]))
        self.query_one("#stat-val-value", Static).update(f"${stats['total_value']:.2f}")
