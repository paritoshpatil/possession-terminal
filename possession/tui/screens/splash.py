from textual import events
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static

SPLASH_ART = r"""
 ____  ___  ____  ____  ____  ____  ____  ____  ___  _  _
(  _ \/ __)( ___)(  __)/ ___)(  __)/ ___)/ ___)/   \( \/ )
 ) __/\__ \ ) _)  ) _) \___ \ ) _) \___ \\___ \( () ) )  /
(__)  (___/(____)(____)(____/(____)(____/(____) \___/(_/\_/

                  press any key to continue
"""


class SplashScreen(Screen):
    DEFAULT_CSS = """
    SplashScreen {
        align: center middle;
        background: $surface;
    }
    #splash-art {
        color: $primary;
        text-align: center;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static(SPLASH_ART, id="splash-art")

    def on_key(self, event: events.Key) -> None:
        from possession.tui.screens.main import MainScreen
        self.app.switch_screen(MainScreen())
