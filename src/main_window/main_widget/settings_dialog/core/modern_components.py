"""
Modern UI Components for the settings dialog with glassmorphism design.
"""

from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtSignal, QTimer
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QCheckBox,
    QSlider,
    QComboBox,
    QFrame,
    QSizePolicy,
    QToolTip,
    QGraphicsOpacityEffect,
)
from styles.glassmorphism_styler import GlassmorphismStyler


class SettingCard(QFrame):
    """
    Modern glassmorphism card container for settings.
    """

    def __init__(self, title: str, description: str = "", parent=None):
        super().__init__(parent)
        self.title = title
        self.description = description
        self._setup_ui()
        self._apply_styling()

    def _setup_ui(self):
        """Setup the card UI layout."""
        self.setFrameStyle(QFrame.Shape.NoFrame)

        # Main layout with compact spacing
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(12, 8, 12, 8)  # Much more compact
        self.layout.setSpacing(6)  # Tighter spacing

        # Header section
        self.header_layout = QVBoxLayout()
        self.header_layout.setSpacing(2)  # Very tight spacing

        # Title
        self.title_label = QLabel(self.title)
        self.title_label.setFont(GlassmorphismStyler.get_font("heading_small"))
        self.title_label.setStyleSheet(
            f"color: {GlassmorphismStyler.get_color('text_primary')};"
        )
        self.header_layout.addWidget(self.title_label)

        # Description
        if self.description:
            self.description_label = QLabel(self.description)
            self.description_label.setFont(GlassmorphismStyler.get_font("body_small"))
            self.description_label.setStyleSheet(
                f"color: {GlassmorphismStyler.get_color('text_muted')};"
            )
            self.description_label.setWordWrap(True)
            self.header_layout.addWidget(self.description_label)

        self.layout.addLayout(self.header_layout)

        # Content area for controls
        self.content_layout = QVBoxLayout()
        self.content_layout.setSpacing(4)  # Compact spacing for controls
        self.layout.addLayout(self.content_layout)

    def _apply_styling(self):
        """Apply glassmorphism styling to the card."""
        style = GlassmorphismStyler.create_glassmorphism_card(self)
        self.setStyleSheet(style)

        # Add shadow effect
        GlassmorphismStyler.add_shadow_effect(self, offset_y=2, blur_radius=8)

    def add_control(self, control: QWidget):
        """Add a control widget to the card."""
        self.content_layout.addWidget(control)

    def add_layout(self, layout):
        """Add a layout to the card."""
        self.content_layout.addLayout(layout)


class ModernToggle(QCheckBox):
    """
    Modern animated toggle switch.
    """

    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self._setup_styling()

    def _setup_styling(self):
        """Apply modern toggle styling."""
        style = GlassmorphismStyler.create_modern_toggle()
        self.setStyleSheet(style)


class ModernButton(QPushButton):
    """
    Modern button with glassmorphism styling and animations.
    """

    def __init__(self, text: str, button_type: str = "primary", parent=None):
        super().__init__(text, parent)
        self.button_type = button_type
        self._setup_styling()
        self._setup_animations()

    def _setup_styling(self):
        """Apply modern button styling."""
        style = GlassmorphismStyler.create_modern_button(self.button_type)
        self.setStyleSheet(style)

        # Set minimum size
        self.setMinimumHeight(40)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

    def _setup_animations(self):
        """Setup hover animations."""
        # Opacity animation for press effect
        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)

        self.opacity_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.opacity_animation.setDuration(150)
        self.opacity_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

    def enterEvent(self, event):
        """Handle mouse enter for hover effect."""
        super().enterEvent(event)
        self.opacity_animation.stop()
        self.opacity_animation.setStartValue(self.opacity_effect.opacity())
        self.opacity_animation.setEndValue(0.9)
        self.opacity_animation.start()

    def leaveEvent(self, event):
        """Handle mouse leave for hover effect."""
        super().leaveEvent(event)
        self.opacity_animation.stop()
        self.opacity_animation.setStartValue(self.opacity_effect.opacity())
        self.opacity_animation.setEndValue(1.0)
        self.opacity_animation.start()


class ModernSlider(QWidget):
    """
    Modern slider with value display and styling.
    """

    valueChanged = pyqtSignal(int)

    def __init__(
        self,
        minimum: int = 0,
        maximum: int = 100,
        value: int = 50,
        suffix: str = "",
        parent=None,
    ):
        super().__init__(parent)
        self.suffix = suffix
        self._setup_ui(minimum, maximum, value)
        self._apply_styling()

    def _setup_ui(self, minimum: int, maximum: int, value: int):
        """Setup slider UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(GlassmorphismStyler.SPACING["md"])

        # Slider
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(minimum)
        self.slider.setMaximum(maximum)
        self.slider.setValue(value)
        self.slider.valueChanged.connect(self._on_value_changed)
        layout.addWidget(self.slider, 1)

        # Value label
        self.value_label = QLabel(f"{value}{self.suffix}")
        self.value_label.setMinimumWidth(60)
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.value_label)

    def _apply_styling(self):
        """Apply modern slider styling."""
        slider_style = GlassmorphismStyler.create_modern_slider()
        self.slider.setStyleSheet(slider_style)

        label_style = f"""
        QLabel {{
            color: {GlassmorphismStyler.get_color('text_secondary')};
            font-size: {GlassmorphismStyler.FONTS['body_small']['size']}px;
            background-color: {GlassmorphismStyler.get_color('surface', 0.3)};
            border-radius: {GlassmorphismStyler.RADIUS['sm']}px;
            padding: {GlassmorphismStyler.SPACING['xs']}px {GlassmorphismStyler.SPACING['sm']}px;
        }}
        """
        self.value_label.setStyleSheet(label_style)

    def _on_value_changed(self, value: int):
        """Handle slider value change."""
        self.value_label.setText(f"{value}{self.suffix}")
        self.valueChanged.emit(value)

    def value(self) -> int:
        """Get current slider value."""
        return self.slider.value()

    def setValue(self, value: int):
        """Set slider value."""
        self.slider.setValue(value)


class ModernComboBox(QComboBox):
    """
    Modern combo box with glassmorphism styling.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_styling()

    def _setup_styling(self):
        """Apply modern combo box styling."""
        style = GlassmorphismStyler.create_modern_input()
        self.setStyleSheet(style)
        self.setMinimumHeight(40)


class StatusIndicator(QLabel):
    """
    Visual indicator for setting changes and status.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._setup_animations()

    def _setup_ui(self):
        """Setup indicator UI."""
        self.setFixedSize(12, 12)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._set_status("normal")

    def _setup_animations(self):
        """Setup status change animations."""
        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)

        self.fade_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_animation.setDuration(300)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

    def _set_status(self, status: str):
        """Set the visual status of the indicator."""
        colors = {
            "normal": GlassmorphismStyler.get_color("surface_light"),
            "modified": GlassmorphismStyler.get_color("warning"),
            "success": GlassmorphismStyler.get_color("success"),
            "error": GlassmorphismStyler.get_color("error"),
        }

        color = colors.get(status, colors["normal"])
        style = f"""
        QLabel {{
            background-color: {color};
            border-radius: 6px;
            border: 1px solid {GlassmorphismStyler.get_color('border', 0.3)};
        }}
        """
        self.setStyleSheet(style)

    def set_modified(self):
        """Show modified status."""
        self._set_status("modified")
        self._animate_change()

    def set_success(self):
        """Show success status."""
        self._set_status("success")
        self._animate_change()

        # Auto-revert to normal after 2 seconds
        QTimer.singleShot(2000, lambda: self._set_status("normal"))

    def set_error(self):
        """Show error status."""
        self._set_status("error")
        self._animate_change()

    def set_normal(self):
        """Show normal status."""
        self._set_status("normal")

    def _animate_change(self):
        """Animate status change."""
        self.fade_animation.stop()
        self.fade_animation.setStartValue(0.3)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.start()


class HelpTooltip(QLabel):
    """
    Contextual help tooltip with modern styling.
    """

    def __init__(self, help_text: str, parent=None):
        super().__init__("?", parent)
        self.help_text = help_text
        self._setup_ui()

    def _setup_ui(self):
        """Setup tooltip UI."""
        self.setFixedSize(20, 20)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCursor(Qt.CursorShape.WhatsThisCursor)

        style = f"""
        QLabel {{
            background-color: {GlassmorphismStyler.get_color('surface_light', 0.5)};
            color: {GlassmorphismStyler.get_color('text_muted')};
            border-radius: 10px;
            font-size: 10px;
            font-weight: bold;
        }}

        QLabel:hover {{
            background-color: {GlassmorphismStyler.get_color('primary', 0.3)};
            color: {GlassmorphismStyler.get_color('text_primary')};
        }}
        """
        self.setStyleSheet(style)

        # Set tooltip
        self.setToolTip(self.help_text)

    def mousePressEvent(self, event):
        """Show help on click."""
        QToolTip.showText(event.globalPosition().toPoint(), self.help_text, self)
