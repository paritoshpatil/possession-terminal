from pathlib import Path
from textual.app import App


class PossessionApp(App):
    """Possession terminal inventory manager."""

    TITLE = "Possession"

    _CSS_DEFAULT = """
    $primary: #cba6f7;
    $primary-darken-2: #fab387;
    $surface: #1e1e2e;
    $surface-darken-1: #11111b;
    $text: #cdd6f4;
    $text-muted: #bac2de;
    $panel: $primary-darken-2;

    Screen {
        background: $surface;
    }
    DataTable {
        background: transparent;
    }
    DataTable > .datatable--cursor {
        background: $primary;
    }
    DataTable > .datatable--header {
        color: $surface;
    }
    Input:focus {
        border: tall $primary;
    }
    """
    _CSS_TRANSPARENT = """
    $primary: #cba6f7;
    $primary-darken-2: #fab387;
    $surface: #1e1e2e;
    $surface-darken-1: #11111b;
    $text: #cdd6f4;
    $text-muted: #bac2de;
    $panel: $primary-darken-2;

    Screen {
        background: transparent;
    }
    DataTable {
        background: transparent;
    }
    DataTable > .datatable--cursor {
        background: $primary;
    }
    DataTable > .datatable--header {
        color: $surface;
    }
    Input:focus {
        border: tall $primary;
    }
    """

    def __init__(self, db_path: Path, transparent: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.db_path = db_path
        self.CSS = self._CSS_TRANSPARENT if transparent else self._CSS_DEFAULT

    def on_mount(self) -> None:
        from possession.tui.screens.splash import SplashScreen
        self.push_screen(SplashScreen())  # only splash on launch; MainScreen pushed on dismiss
