from pathlib import Path
from textual.app import App


class PossessionApp(App):
    """Possession terminal inventory manager."""

    TITLE = "Possession"

    _CSS_DEFAULT = """
    Screen {
        background: $surface;
    }
    """
    _CSS_TRANSPARENT = """
    Screen {
        background: transparent;
    }
    DataTable {
        background: transparent;
    }
    """

    def __init__(self, db_path: Path, transparent: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.db_path = db_path
        self.CSS = self._CSS_TRANSPARENT if transparent else self._CSS_DEFAULT

    def on_mount(self) -> None:
        from possession.tui.screens.splash import SplashScreen
        self.push_screen(SplashScreen())  # only splash on launch; MainScreen pushed on dismiss
