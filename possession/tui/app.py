from pathlib import Path
from textual.app import App


class PossessionApp(App):
    """Possession terminal inventory manager."""

    TITLE = "Possession"

    def __init__(self, db_path: Path, transparent: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.db_path = db_path

        from possession.settings import build_css, get_setting
        saved_theme = get_setting(db_path, "theme", "catppuccin-mocha")
        saved_transparent = get_setting(db_path, "transparent", "0") == "1"
        # CLI --transparent flag overrides DB setting for this session (not persisted)
        effective_transparent = transparent or saved_transparent
        self._current_theme = saved_theme
        self._transparent = effective_transparent
        self.CSS = build_css(saved_theme, effective_transparent)

    def on_mount(self) -> None:
        from possession.tui.screens.splash import SplashScreen
        self.push_screen(SplashScreen())  # only splash on launch; MainScreen pushed on dismiss

    def apply_theme(self, theme: str, transparent: bool, persist: bool = True) -> None:
        """Apply a new theme and refresh the app CSS live.

        Args:
            theme: Name of the theme to apply (must be a key in THEMES).
            transparent: Whether to use a transparent Screen background.
            persist: If True (default), saves settings to DB. Pass False for live preview.
        """
        from possession.settings import build_css, set_setting
        self._current_theme = theme
        self._transparent = transparent
        if persist:
            set_setting(self.db_path, "theme", theme)
            set_setting(self.db_path, "transparent", "1" if transparent else "0")
        self.CSS = build_css(theme, transparent)
        self.refresh_css()
