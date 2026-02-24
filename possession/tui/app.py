from pathlib import Path
from typing import Optional
from textual.app import App, ComposeResult
from possession.tui.screens.main import MainScreen


class PossessionApp(App):
    """Possession terminal inventory manager."""

    CSS = """
    Screen {
        background: $surface;
    }
    """

    def __init__(self, db_path: Path, **kwargs):
        super().__init__(**kwargs)
        self.db_path = db_path

    def on_mount(self) -> None:
        self.push_screen(MainScreen())
