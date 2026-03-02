from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widget import Widget
from textual.widgets import Static


class DetailPanel(Widget):
    """Side panel displaying all fields for the currently selected inventory item.

    Layout:
        [bold]Item Name[/bold]
        [dim]Room:[/dim] Living Room
        [dim]Container:[/dim] —
        [dim]Category:[/dim] Electronics
        [dim]Description:[/dim] —
        [dim]Acquired:[/dim] 2024-01-15
        [dim]Cost:[/dim] $299.99

    Call show_item(item_dict) to populate with item data.
    """

    FIELDS = [
        ("room_name",      "Room"),
        ("container_name", "Container"),
        ("category_name",  "Category"),
        ("description",    "Description"),
        ("purchase_date",  "Acquired"),
        ("cost",           "Cost"),
    ]

    DEFAULT_CSS = """
DetailPanel {
    height: 1fr;
    padding: 0 1;
    padding-top: 1;
    margin-left: 1;
    border: $primary heavy;
    border-title-align: left;
}
#panel-title {
    text-style: bold;
    text-align: center;
    color: $text;
    background: $primary;
    margin-bottom: 1;
    height: 1;
}
VerticalScroll {
    height: 1fr;
}
"""

    def compose(self) -> ComposeResult:
        yield Static("", id="panel-title")
        with VerticalScroll():
            for field_key, label in self.FIELDS:
                yield Static(f"[dim]{label}:[/dim] —", id=f"field-{field_key}")

    def on_mount(self) -> None:
        self.border_title = "Details"

    def show_item(self, item: dict) -> None:
        """Update all field Static widgets with data from item dict.

        Falls back to — for missing string fields and $0.00 for missing cost.
        """
        self.query_one("#panel-title", Static).update(
            f"[bold]  {item.get('name', '')}  [/bold]"
        )
        from possession.settings import format_currency
        for field_key, label in self.FIELDS:
            if field_key == "cost":
                display = format_currency(item.get("cost")) or "—"
            else:
                val = item.get(field_key)
                display = val if val else "—"
            self.query_one(f"#field-{field_key}", Static).update(
                f"[dim]{label}:[/dim] {display}"
            )
