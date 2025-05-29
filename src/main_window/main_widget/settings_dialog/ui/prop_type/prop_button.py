from typing import TYPE_CHECKING
from PyQt6.QtWidgets import QPushButton
from PyQt6.QtGui import QIcon, QCursor
from PyQt6.QtCore import Qt, QSize
from enums.prop_type import PropType
from styles.glassmorphism_styler import GlassmorphismStyler

if TYPE_CHECKING:
    from .prop_type_tab import PropTypeTab


class PropButton(QPushButton):
    """A modern glassmorphism button representing a prop type with beautiful styling and animations."""

    def __init__(
        self, prop: str, icon_path: str, prop_type_tab: "PropTypeTab", callback
    ):
        super().__init__(prop_type_tab)
        self.prop_type_tab = prop_type_tab
        self.prop = prop
        self.setIcon(QIcon(icon_path))
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.clicked.connect(lambda: callback(PropType.get_prop_type(prop)))

        self._is_active = False
        self._setup_initial_styling()

    def _setup_initial_styling(self):
        """Setup initial modern glassmorphism styling."""
        self.setFixedSize(QSize(100, 100))  # Larger size for better visibility
        self.setIconSize(QSize(64, 64))  # Larger icon size
        self.set_button_style(False)

    def set_active(self, is_active: bool):
        """Updates the button's active state and applies styling accordingly."""
        self._is_active = is_active
        self.set_button_style(is_active)

    def set_button_style(self, is_active=False):
        """Set the modern glassmorphism button style based on active state."""
        if is_active:
            # Active state - highlighted with primary color
            self.setStyleSheet(
                f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {GlassmorphismStyler.get_color('primary', 0.8)},
                        stop:1 {GlassmorphismStyler.get_color('primary_dark', 0.9)});
                    border: 2px solid {GlassmorphismStyler.get_color('primary', 1.0)};
                    border-radius: {GlassmorphismStyler.RADIUS['lg']}px;
                    color: white;
                    font-weight: bold;
                    padding: 8px;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {GlassmorphismStyler.get_color('primary', 0.9)},
                        stop:1 {GlassmorphismStyler.get_color('primary_dark', 1.0)});
                    border: 2px solid {GlassmorphismStyler.get_color('primary_light', 1.0)};
                }}
                QPushButton:pressed {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {GlassmorphismStyler.get_color('primary_dark', 0.9)},
                        stop:1 {GlassmorphismStyler.get_color('primary', 0.8)});
                }}
            """
            )
        else:
            # Inactive state - subtle glassmorphism
            self.setStyleSheet(
                f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {GlassmorphismStyler.get_color('surface', 0.6)},
                        stop:1 {GlassmorphismStyler.get_color('surface_light', 0.4)});
                    border: 1px solid {GlassmorphismStyler.get_color('border', 0.4)};
                    border-radius: {GlassmorphismStyler.RADIUS['lg']}px;
                    color: {GlassmorphismStyler.get_color('text_secondary')};
                    padding: 8px;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {GlassmorphismStyler.get_color('surface_light', 0.7)},
                        stop:1 {GlassmorphismStyler.get_color('surface_lighter', 0.5)});
                    border: 1px solid {GlassmorphismStyler.get_color('border_light', 0.6)};
                    color: {GlassmorphismStyler.get_color('text_primary')};
                }}
                QPushButton:pressed {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {GlassmorphismStyler.get_color('surface', 0.8)},
                        stop:1 {GlassmorphismStyler.get_color('surface_light', 0.6)});
                }}
            """
            )

        self.update()

    def resizeEvent(self, event):
        """Handle resize events - maintain fixed size for consistency."""
        super().resizeEvent(event)

    def update_size(self):
        """Update size - no longer needed as we use fixed sizes for consistency."""
        pass  # Keep for compatibility but don't change sizes
