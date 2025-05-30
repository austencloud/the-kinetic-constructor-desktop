from PyQt6.QtWidgets import QPushButton
from PyQt6.QtGui import QCursor, QIcon, QFont
from PyQt6.QtCore import (
    Qt,
    pyqtSignal,
    QEvent,
    QPropertyAnimation,
    QEasingCurve,
    pyqtProperty,
)
from styles.button_state import ButtonState
from enum import Enum


class ButtonContext(Enum):
    """Defines different button contexts for appropriate styling."""

    STANDARD = "standard"  # Default filter buttons, dialog buttons
    COMPACT = "compact"  # Social media icons, small UI elements
    NAVIGATION = "navigation"  # Menu navigation bar buttons
    WORKBENCH = "workbench"  # Sequence workbench circular buttons
    SETTINGS = "settings"  # Settings and configuration buttons


class StyledButton(QPushButton):
    """A context-aware modern 2025 QPushButton with adaptive styling based on usage context."""

    clicked_signal = pyqtSignal(str)

    def __init__(
        self,
        label: str,
        icon_path: str = None,
        context: ButtonContext = ButtonContext.STANDARD,
    ):
        super().__init__(label)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._state = ButtonState.NORMAL
        self._context = context
        self._animation_scale = 1.0

        # Context-aware properties
        self._setup_context_properties()
        self._setup_animations()

        if icon_path:
            self.setIcon(QIcon(icon_path))

        # Modern typography
        self._setup_modern_font()

        # Defer appearance update to avoid crashes during initialization
        try:
            self.update_appearance()
        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to update appearance during initialization: {e}")
            # Apply basic fallback styling
            self.setStyleSheet(
                "QPushButton { background: lightgray; border: 1px solid gray; padding: 4px; }"
            )

        self.clicked.connect(self._on_clicked)

    def _setup_context_properties(self):
        """Setup properties based on button context."""
        if self._context == ButtonContext.COMPACT:
            self._border_radius = 8
            self._padding = "4px 8px"
            self._min_size = (24, 24)
            self._font_size_base = 10
        elif self._context == ButtonContext.NAVIGATION:
            self._border_radius = 8
            self._padding = "8px 16px"
            self._min_size = (80, 40)
            self._font_size_base = 14
        elif self._context == ButtonContext.WORKBENCH:
            self._border_radius = None  # Will be set to circular in update_appearance
            self._padding = "8px"
            self._min_size = (40, 40)
            self._font_size_base = 12
        elif self._context == ButtonContext.SETTINGS:
            self._border_radius = None  # Will be set to circular
            self._padding = "6px"
            self._min_size = (32, 32)
            self._font_size_base = 11
        else:  # STANDARD
            self._border_radius = 12
            self._padding = "12px 24px"
            self._min_size = (80, 32)
            self._font_size_base = 14

    def _setup_animations(self):
        """Setup smooth animations for modern interactions."""
        self._scale_animation = QPropertyAnimation(self, b"animationScale")
        self._scale_animation.setDuration(150)
        self._scale_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

    def _setup_modern_font(self):
        """Setup modern typography with proper font weights."""
        font = QFont()
        font.setFamily("Segoe UI, Arial, sans-serif")
        font.setWeight(QFont.Weight.Medium)
        font.setStyleHint(QFont.StyleHint.SansSerif)
        self.setFont(font)

    @property
    def state(self) -> ButtonState:
        return self._state

    @state.setter
    def state(self, new_state: ButtonState) -> None:
        if self._state != new_state:
            self._state = new_state
            self.update_appearance()

    def update_appearance(self) -> None:
        """Update button appearance with context-aware modern styling."""
        try:
            # Get context-specific properties safely
            padding, border_radius = self._get_safe_context_properties()

            # Get beautiful modern styling with glass-morphism
            styles = self._get_beautiful_context_styles(padding, border_radius)

            self.setStyleSheet(styles)
        except Exception as e:
            # Ultimate fallback
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(f"Error in update_appearance: {e}")
            self.setStyleSheet(
                "QPushButton { background: lightgray; border: 1px solid gray; padding: 4px; }"
            )

    def _get_safe_context_properties(self):
        """Get context properties safely without crashing."""
        if self._context == ButtonContext.COMPACT:
            return "4px 8px", "8px"
        elif self._context == ButtonContext.NAVIGATION:
            return "8px 16px", "8px"
        elif self._context in [ButtonContext.WORKBENCH, ButtonContext.SETTINGS]:
            # Safe circular radius calculation
            size = max(self.width() if self.width() > 0 else 32, 32)
            return "8px", f"{size // 2}px"
        else:  # STANDARD
            return "12px 24px", "12px"

    def _get_beautiful_context_styles(self, padding: str, border_radius: str) -> str:
        """Get beautiful glass-morphism styling based on context."""
        # Simple but beautiful glass-morphism effect
        if self._state == ButtonState.ACTIVE:
            # Active state - Beautiful blue glow
            background = "rgba(64, 150, 255, 0.8)"
            border_color = "rgba(255, 255, 255, 0.6)"
        else:
            # Normal state - Glass-morphism transparency
            background = "rgba(255, 255, 255, 0.1)"
            border_color = "rgba(255, 255, 255, 0.3)"

        # Context-specific adjustments
        if self._context == ButtonContext.COMPACT:
            border_width = "1px"
            margin = "1px"
        elif self._context == ButtonContext.NAVIGATION:
            border_width = "2px"
            margin = "2px"
        else:
            border_width = "2px"
            margin = "2px"

        return f"""
            QPushButton {{
                background: {background};
                border: {border_width} solid {border_color};
                border-radius: {border_radius};
                color: white;
                padding: {padding};
                margin: {margin};
                font-weight: 500;
            }}
            QPushButton:hover {{
                background: rgba(120, 180, 255, 0.6);
                border: {border_width} solid rgba(255, 255, 255, 0.8);
            }}
            QPushButton:pressed {{
                background: rgba(40, 120, 200, 0.8);
                border: {border_width} solid rgba(255, 255, 255, 0.9);
            }}
            QPushButton:disabled {{
                background: rgba(128, 128, 128, 0.1);
                color: rgba(255, 255, 255, 0.4);
                border: {border_width} solid rgba(128, 128, 128, 0.3);
            }}
        """

    def _get_context_border_radius(self) -> str:
        """Get border radius based on context and current size."""
        if self._context in [ButtonContext.WORKBENCH, ButtonContext.SETTINGS]:
            # Circular buttons - ensure we have valid dimensions
            width = max(self.width(), 32)  # Fallback to minimum size
            height = max(self.height(), 32)  # Fallback to minimum size
            return f"{min(width, height) // 2}px"
        else:
            return f"{self._border_radius}px"

    def _get_context_styles(self, theme) -> str:
        """Get context-specific stylesheet."""
        border_radius = self._get_context_border_radius()

        if self._context == ButtonContext.COMPACT:
            return self._get_compact_styles(theme, border_radius)
        elif self._context == ButtonContext.NAVIGATION:
            return self._get_navigation_styles(theme, border_radius)
        elif self._context == ButtonContext.WORKBENCH:
            return self._get_workbench_styles(theme, border_radius)
        elif self._context == ButtonContext.SETTINGS:
            return self._get_settings_styles(theme, border_radius)
        else:  # STANDARD
            return self._get_standard_styles(theme, border_radius)

    def _get_compact_styles(self, theme, border_radius: str) -> str:
        """Compact button styles for social media icons."""
        return f"""
            QPushButton {{
                background: {theme.background};
                border-radius: {border_radius};
                color: {theme.font_color};
                padding: {self._padding};
                font-size: {self._font_size_base}px;
                border: 1px solid {theme.border_color};
                margin: 1px;
                min-height: {self._min_size[1]}px;
                min-width: {self._min_size[0]}px;
            }}
            QPushButton:hover {{
                background: {theme.hover_background};
                color: {theme.hover_font_color};
                border: 1px solid rgba(255, 255, 255, 0.6);
                margin: 0px;
                padding: {self._padding};
            }}
            QPushButton:pressed {{
                background: {theme.pressed_background};
                color: {theme.pressed_font_color};
                border: 1px solid rgba(255, 255, 255, 0.8);
                margin: 2px;
                padding: {self._padding};
            }}
            QPushButton:disabled {{
                background: {theme.background};
                color: rgba(255, 255, 255, 0.4);
                border: 1px solid rgba(128, 128, 128, 0.3);
            }}
        """

    def _get_navigation_styles(self, theme, border_radius: str) -> str:
        """Navigation button styles with better text readability."""
        return f"""
            QPushButton {{
                background: {theme.background};
                border-radius: {border_radius};
                color: {theme.font_color};
                padding: {self._padding};
                font-weight: 600;
                font-size: {self._font_size_base}px;
                text-align: center;
                border: 2px solid {theme.border_color};
                margin: 2px;
                min-height: {self._min_size[1]}px;
                min-width: {self._min_size[0]}px;
            }}
            QPushButton:hover {{
                background: {theme.hover_background};
                color: {theme.hover_font_color};
                border: 2px solid rgba(255, 255, 255, 0.6);
                margin: 1px;
                padding: {self._padding};
            }}
            QPushButton:pressed {{
                background: {theme.pressed_background};
                color: {theme.pressed_font_color};
                border: 2px solid rgba(255, 255, 255, 0.8);
                margin: 3px;
                padding: {self._padding};
            }}
            QPushButton:disabled {{
                background: {theme.background};
                color: rgba(255, 255, 255, 0.4);
                border: 2px solid rgba(128, 128, 128, 0.3);
            }}
        """

    def _get_workbench_styles(self, theme, border_radius: str) -> str:
        """Workbench button styles with circular design."""
        return f"""
            QPushButton {{
                background: {theme.background};
                border-radius: {border_radius};
                color: {theme.font_color};
                padding: {self._padding};
                font-size: {self._font_size_base}px;
                border: 2px solid {theme.border_color};
                margin: 2px;
                min-height: {self._min_size[1]}px;
                min-width: {self._min_size[0]}px;
            }}
            QPushButton:hover {{
                background: {theme.hover_background};
                color: {theme.hover_font_color};
                border: 2px solid rgba(255, 255, 255, 0.6);
                margin: 1px;
                padding: {self._padding};
            }}
            QPushButton:pressed {{
                background: {theme.pressed_background};
                color: {theme.pressed_font_color};
                border: 2px solid rgba(255, 255, 255, 0.8);
                margin: 3px;
                padding: {self._padding};
            }}
            QPushButton:disabled {{
                background: {theme.background};
                color: rgba(255, 255, 255, 0.4);
                border: 2px solid rgba(128, 128, 128, 0.3);
            }}
        """

    def _get_settings_styles(self, theme, border_radius: str) -> str:
        """Settings button styles with circular design."""
        return f"""
            QPushButton {{
                background: {theme.background};
                border-radius: {border_radius};
                color: {theme.font_color};
                padding: {self._padding};
                font-size: {self._font_size_base}px;
                border: 2px solid {theme.border_color};
                margin: 1px;
                min-height: {self._min_size[1]}px;
                min-width: {self._min_size[0]}px;
            }}
            QPushButton:hover {{
                background: {theme.hover_background};
                color: {theme.hover_font_color};
                border: 2px solid rgba(255, 255, 255, 0.6);
                margin: 0px;
                padding: {self._padding};
            }}
            QPushButton:pressed {{
                background: {theme.pressed_background};
                color: {theme.pressed_font_color};
                border: 2px solid rgba(255, 255, 255, 0.8);
                margin: 2px;
                padding: {self._padding};
            }}
            QPushButton:disabled {{
                background: {theme.background};
                color: rgba(255, 255, 255, 0.4);
                border: 2px solid rgba(128, 128, 128, 0.3);
            }}
        """

    def _get_standard_styles(self, theme, border_radius: str) -> str:
        """Standard button styles for filter buttons and dialogs."""
        return f"""
            QPushButton {{
                background: {theme.background};
                border-radius: {border_radius};
                color: {theme.font_color};
                padding: {self._padding};
                font-weight: 500;
                font-size: {self._font_size_base}px;
                text-align: center;
                border: 2px solid {theme.border_color};
                margin: 2px;
                min-height: {self._min_size[1]}px;
                min-width: {self._min_size[0]}px;
            }}
            QPushButton:hover {{
                background: {theme.hover_background};
                color: {theme.hover_font_color};
                border: 2px solid rgba(255, 255, 255, 0.6);
                margin: 1px;
                padding: {self._padding};
            }}
            QPushButton:pressed {{
                background: {theme.pressed_background};
                color: {theme.pressed_font_color};
                border: 2px solid rgba(255, 255, 255, 0.8);
                margin: 3px;
                padding: {self._padding};
            }}
            QPushButton:disabled {{
                background: {theme.background};
                color: rgba(255, 255, 255, 0.4);
                border: 2px solid rgba(128, 128, 128, 0.3);
            }}
        """

    def set_selected(self, selected: bool) -> None:
        """Update selection state and restyle the button."""
        self.state = ButtonState.ACTIVE if selected else ButtonState.NORMAL

    def setEnabled(self, enabled: bool) -> None:
        """Enable or disable the button and update its style dynamically."""
        super().setEnabled(enabled)
        self.setCursor(
            QCursor(
                Qt.CursorShape.PointingHandCursor
                if enabled
                else Qt.CursorShape.ForbiddenCursor
            )
        )
        self.update_appearance()

    def _on_clicked(self) -> None:
        """Emit a signal when clicked with modern animation feedback."""
        self._animate_click()
        self.clicked_signal.emit(self.text())

    def _animate_click(self):
        """Provide visual feedback with smooth scale animation."""
        self._scale_animation.setStartValue(1.0)
        self._scale_animation.setEndValue(0.95)
        self._scale_animation.finished.connect(self._animate_click_release)
        self._scale_animation.start()

    def _animate_click_release(self):
        """Complete the click animation by scaling back up."""
        self._scale_animation.finished.disconnect()
        self._scale_animation.setStartValue(0.95)
        self._scale_animation.setEndValue(1.0)
        self._scale_animation.start()

    @pyqtProperty(float)
    def animationScale(self):
        """Property for animation scaling."""
        return self._animation_scale

    @animationScale.setter
    def animationScale(self, scale):
        """Set animation scale and update transform."""
        self._animation_scale = scale
        # Note: CSS transform is handled in stylesheet

    def resizeEvent(self, event: QEvent) -> None:
        """Handle resizing with modern responsive design principles."""
        # Modern border radius calculation for better proportions
        min_dimension = min(self.height(), self.width())
        self._border_radius = max(8, min(16, min_dimension // 8))

        # Update font size responsively
        font = self.font()
        font_size = max(10, min(18, min_dimension // 6))
        font.setPointSize(font_size)
        self.setFont(font)

        self.update_appearance()
        super().resizeEvent(event)
