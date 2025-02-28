from PyQt6.QtWidgets import QPushButton
from PyQt6.QtGui import QCursor, QFont
from PyQt6.QtCore import Qt
from typing import TYPE_CHECKING
from styles.dark_theme_styler import DarkThemeStyler

if TYPE_CHECKING:
    from main_window.main_widget.settings_dialog.ui.image_export.image_export_tab import (
        ImageExportTab,
    )
    from main_window.settings_manager.settings_manager import SettingsManager


class ImageExportTabButton(QPushButton):
    """A button styled with modern effects, just like its cool cousin, VisibilityButton."""

    def __init__(
        self,
        name: str,
        setting_key: str,
        settings_manager: "SettingsManager",
        image_export_tab: "ImageExportTab",
    ):
        super().__init__(name, image_export_tab)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setting_key = setting_key
        self.settings_manager = settings_manager
        self.is_toggled = False  # Track active state, because why not?
        self.clicked.connect(self._toggle_state)
        self._initialize_state()  # Make sure we start looking good

    def _initialize_state(self):
        """Retrieve toggle state and apply styles on initialization."""
        self.update_is_toggled()
        self.repaint()  # Ensure UI updates immediately, because we're impatient

    def update_is_toggled(self):
        """Updates the button state based on saved settings."""
        is_toggled = self.settings_manager.image_export.get_image_export_setting(
            self.setting_key
        )
        self.is_toggled = is_toggled
        self._apply_style(self.is_toggled)

    def _toggle_state(self):
        """Handle button toggle state."""
        self.is_toggled = not self.is_toggled
        self.settings_manager.image_export.set_image_export_setting(
            self.setting_key, self.is_toggled
        )
        self._apply_style(self.is_toggled)  # Update button style, keeping it fresh

    def set_active(self, is_active: bool):
        """Updates the button style when toggled."""
        self.is_toggled = is_active
        self._apply_style(is_active)

    def _apply_style(self, is_active=False):
        """Applies styling dynamically based on active state."""
        if is_active:
            self.setStyleSheet(
                f"""
                QPushButton {{
                    {DarkThemeStyler.ACTIVE_BG_GRADIENT}
                    border: 2px solid {DarkThemeStyler.ACCENT_COLOR};
                    color: white;
                    padding: 8px 12px;
                    border-radius: 8px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    {DarkThemeStyler.ACTIVE_BG_GRADIENT}
                }}
                QPushButton:pressed {{
                    background-color: {DarkThemeStyler.BORDER_COLOR};
                }}
            """
            )
        else:
            self.setStyleSheet(
                f"""
                QPushButton {{
                    {DarkThemeStyler.DEFAULT_BG_GRADIENT}
                    border: 2px solid {DarkThemeStyler.BORDER_COLOR};
                    color: {DarkThemeStyler.TEXT_COLOR};
                    padding: 8px 12px;
                    border-radius: 8px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    {DarkThemeStyler.DARK_HOVER_GRADIENT}
                }}
                QPushButton:pressed {{
                    background-color: {DarkThemeStyler.BORDER_COLOR};
                }}
            """
            )
        self.update()  # Ensure the UI updates, because we care
        self.repaint()  # Force an immediate refresh, just to be sure

    def resizeEvent(self, event):
        """Dynamically adjust button size without affecting layout."""
        super().resizeEvent(event)
        # Calculate font size based on the parent's width.  Good luck figuring out the perfect divisor!
        parent_width = (
            self.parentWidget().width() if self.parentWidget() else 200
        )  # Fallback width
        font_size = int(parent_width / 60)  # Adjust divisor as needed
        font = QFont()
        font.setPointSize(font_size)
        self.setFont(font)
