"""
Whisk Desktop — Theme Manager.

Manages the triadic color palette (purple-teal-amber) with light/dark mode switching.
Uses QSS template files with {{token}} placeholders replaced at runtime.
"""
from PySide6.QtCore import QObject, Signal
from app.utils import resource_path


class ThemeManager(QObject):
    """Manages application theme (light/dark) with triadic color palette."""

    theme_changed = Signal(str)  # Emits "light" or "dark"

    PALETTES = {
        "light": {
            "bg-primary": "#FFFFFF",
            "bg-secondary": "#F5F3FF",
            "bg-sidebar": "#F0ECFF",
            "bg-hover": "#EDE9FE",
            "bg-card": "#FFFFFF",
            "text-primary": "#1F2937",
            "text-secondary": "#6B7280",
            "text-inverse": "#FFFFFF",
            "color-primary": "#7C3AED",
            "color-primary-light": "#A78BFA",
            "color-primary-dark": "#5B21B6",
            "color-primary-hover": "#6D28D9",
            "color-secondary": "#14B8A6",
            "color-secondary-light": "#5EEAD4",
            "color-secondary-hover": "#0D9488",
            "color-accent": "#F59E0B",
            "color-accent-light": "#FCD34D",
            "color-danger": "#EF4444",
            "color-danger-light": "#FCA5A5",
            "border": "#E5E7EB",
            "border-light": "#F3F4F6",
            "shadow": "rgba(0, 0, 0, 0.08)",
            "scrollbar-bg": "#F3F4F6",
            "scrollbar-handle": "#D1D5DB",
        },
        "dark": {
            "bg-primary": "#1E1B2E",
            "bg-secondary": "#2D2A3E",
            "bg-sidebar": "#252238",
            "bg-hover": "#3D3A4E",
            "bg-card": "#2D2A3E",
            "text-primary": "#F9FAFB",
            "text-secondary": "#9CA3AF",
            "text-inverse": "#1F2937",
            "color-primary": "#A78BFA",
            "color-primary-light": "#C4B5FD",
            "color-primary-dark": "#7C3AED",
            "color-primary-hover": "#8B5CF6",
            "color-secondary": "#2DD4BF",
            "color-secondary-light": "#5EEAD4",
            "color-secondary-hover": "#14B8A6",
            "color-accent": "#FBBF24",
            "color-accent-light": "#FDE68A",
            "color-danger": "#F87171",
            "color-danger-light": "#FCA5A5",
            "border": "#4B5563",
            "border-light": "#374151",
            "shadow": "rgba(0, 0, 0, 0.3)",
            "scrollbar-bg": "#252238",
            "scrollbar-handle": "#4B5563",
        },
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_theme = "dark"

    @property
    def current_theme(self) -> str:
        """Return current theme name ('light' or 'dark')."""
        return self._current_theme

    @property
    def is_dark(self) -> bool:
        """Return True if dark mode is active."""
        return self._current_theme == "dark"

    @property
    def palette(self) -> dict[str, str]:
        """Return the current palette tokens."""
        return self.PALETTES[self._current_theme]

    def set_theme(self, mode: str) -> None:
        """Set theme to 'light' or 'dark'.

        Args:
            mode: Theme mode, either 'light' or 'dark'.
        """
        if mode not in ("light", "dark"):
            raise ValueError(f"Invalid theme: {mode}. Must be 'light' or 'dark'.")
        if mode != self._current_theme:
            self._current_theme = mode
            self.theme_changed.emit(mode)

    def toggle_theme(self) -> str:
        """Toggle between light and dark theme.

        Returns:
            The new theme name after toggling.
        """
        new_theme = "dark" if self._current_theme == "light" else "light"
        self.set_theme(new_theme)
        return new_theme

    def get_stylesheet(self) -> str:
        """Load and process the QSS stylesheet for the current theme.

        Reads the QSS template file and replaces all {{token}} placeholders
        with actual color values from the current palette.

        Returns:
            Processed QSS stylesheet string.
        """
        qss_file = resource_path(f"app/theme/{self._current_theme}.qss")
        try:
            with open(qss_file, "r", encoding="utf-8") as f:
                qss = f.read()
        except FileNotFoundError:
            return ""

        palette = self.palette
        for token, value in palette.items():
            qss = qss.replace(f"{{{{{token}}}}}", value)

        # Replace icons path
        icons_dir = resource_path("app/theme/icons").replace("\\", "/")
        qss = qss.replace("{{icons-path}}", icons_dir)
        return qss
