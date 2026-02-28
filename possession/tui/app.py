from pathlib import Path
from textual.app import App


class PossessionApp(App):
    """Possession terminal inventory manager."""

    TITLE = "Possession"

    _CSS_DEFAULT = """
    $primary: #8b5cf6;
    $primary-darken-2: #4338ca;
    $surface: #0f172a;
    $surface-darken-1: #1e1b4b;
    $text: #ffffff;
    $text-muted: #e0e7ff;
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
    """
    _CSS_TRANSPARENT = """
    $primary: #8b5cf6;
    $primary-darken-2: #4338ca;
    $surface: #0f172a;
    $surface-darken-1: #1e1b4b;
    $text: #ffffff;
    $text-muted: #e0e7ff;
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
    """

    def __init__(self, db_path: Path, transparent: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.db_path = db_path
        self.CSS = self._CSS_TRANSPARENT if transparent else self._CSS_DEFAULT

    def on_mount(self) -> None:
        from possession.tui.screens.splash import SplashScreen
        self.push_screen(SplashScreen())  # only splash on launch; MainScreen pushed on dismiss
