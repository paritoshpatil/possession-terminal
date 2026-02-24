from textual.widgets import Static


class Breadcrumb(Static):
    """Displays the current drill-down navigation path."""

    DEFAULT_CSS = """
    Breadcrumb {
        height: 1;
        padding: 0 1;
        background: $primary-darken-2;
        color: $text;
    }
    """

    def __init__(self, path: str = "All Items", **kwargs):
        super().__init__(path, **kwargs)

    def set_path(self, path: str) -> None:
        """Update the displayed path string."""
        self.update(path)
