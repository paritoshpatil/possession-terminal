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
    $border: #cba6f7;
    $block-cursor-background: #cba6f7;
    $block-cursor-foreground: #1e1e2e;
    $block-cursor-blurred-background: #cba6f740;
    $scrollbar: #fab387;
    $scrollbar-hover: #fab387;
    $scrollbar-active: #fab387;
    $scrollbar-background: #1e1e2e;
    $scrollbar-corner-color: #1e1e2e;

    Screen {
        background: $surface;
    }
    DataTable {
        background: transparent;
        scrollbar-size-vertical: 1;
    }
    DataTable > .datatable--cursor {
        background: $primary;
    }
    DataTable > .datatable--header {
        color: $surface;
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
    $border: #cba6f7;
    $block-cursor-background: #cba6f7;
    $block-cursor-foreground: #1e1e2e;
    $block-cursor-blurred-background: #cba6f740;
    $scrollbar: #fab387;
    $scrollbar-hover: #fab387;
    $scrollbar-active: #fab387;
    $scrollbar-background: #1e1e2e;
    $scrollbar-corner-color: #1e1e2e;

    Screen {
        background: transparent;
    }
    DataTable {
        background: transparent;
        scrollbar-size-vertical: 1;
    }
    DataTable > .datatable--cursor {
        background: $primary;
    }
    DataTable > .datatable--header {
        color: $surface;
    }
    """

    def __init__(self, db_path: Path, transparent: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.db_path = db_path
        self.CSS = self._CSS_TRANSPARENT if transparent else self._CSS_DEFAULT

    def on_mount(self) -> None:
        from possession.tui.screens.splash import SplashScreen
        self.push_screen(SplashScreen())  # only splash on launch; MainScreen pushed on dismiss
