"""
Visual State Manager - Manages loading states, transitions, and visual feedback.

Responsibilities:
- Loading state visualization
- Smooth fade transitions
- Glassmorphism styling
- Visual feedback coordination
"""

import logging
from typing import Optional
from PyQt6.QtCore import QObject, QPropertyAnimation, QEasingCurve, QSize, pyqtSignal
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont, QLinearGradient, QPen
from PyQt6.QtWidgets import QLabel, QGraphicsOpacityEffect
from PyQt6.QtCore import Qt

from styles.glassmorphism_styler import GlassmorphismStyler


class VisualState:
    """Enumeration of visual states."""

    PLACEHOLDER = "placeholder"
    LOADING = "loading"
    LOADED = "loaded"
    ERROR = "error"


class VisualStateManager(QObject):
    """
    Manages visual states and transitions for thumbnail display.

    Features:
    - Smooth fade transitions (250ms)
    - Glassmorphism loading indicators
    - State-based visual feedback
    - Animation coordination
    """

    # Signals
    transition_started = pyqtSignal(str)  # state
    transition_completed = pyqtSignal(str)  # state

    def __init__(self, label_widget: QLabel):
        super().__init__()

        self.label_widget = label_widget
        self.current_state = VisualState.PLACEHOLDER

        # Animation setup
        self._opacity_effect = QGraphicsOpacityEffect()
        self.label_widget.setGraphicsEffect(self._opacity_effect)

        self._fade_animation = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._fade_animation.setDuration(
            0
        )  # CRITICAL FIX: Disable animations to prevent layout shifts
        self._fade_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._fade_animation.finished.connect(self._on_animation_finished)

        # State tracking
        self._target_state: Optional[str] = None
        self._pending_pixmap: Optional[QPixmap] = None

        # Animation frame for loading state
        self._loading_frame = 0

        logging.debug("VisualStateManager initialized")

    def show_placeholder(self, size: QSize) -> None:
        """Show placeholder state with glassmorphism styling."""
        placeholder_pixmap = self._create_placeholder_pixmap(size)
        self._transition_to_state(VisualState.PLACEHOLDER, placeholder_pixmap)

    def show_loading(self, size: QSize) -> None:
        """Show loading state with animated indicator."""
        loading_pixmap = self._create_loading_pixmap(size)
        self._transition_to_state(VisualState.LOADING, loading_pixmap)

    def show_loaded_image(self, pixmap: QPixmap) -> None:
        """Show loaded image with smooth transition."""
        self._transition_to_state(VisualState.LOADED, pixmap)

    def show_error(self, size: QSize) -> None:
        """Show error state."""
        error_pixmap = self._create_error_pixmap(size)
        self._transition_to_state(VisualState.ERROR, error_pixmap)

    def update_loading_animation(self) -> None:
        """Update loading animation frame."""
        if self.current_state == VisualState.LOADING:
            self._loading_frame = (self._loading_frame + 1) % 60
            # Recreate loading pixmap with new frame
            if hasattr(self, "_last_size"):
                loading_pixmap = self._create_loading_pixmap(self._last_size)
                self.label_widget.setPixmap(loading_pixmap)

    def _transition_to_state(self, new_state: str, pixmap: QPixmap) -> None:
        """Transition to a new visual state with animation."""
        if new_state == self.current_state and not self._fade_animation.state():
            # Same state and no animation running, just update pixmap
            self.label_widget.setPixmap(pixmap)
            return

        self._target_state = new_state
        self._pending_pixmap = pixmap

        # Store size for loading animation updates
        if pixmap:
            self._last_size = pixmap.size()

        # Emit transition started signal
        self.transition_started.emit(new_state)

        # Start fade out animation
        self._fade_animation.setStartValue(1.0)
        self._fade_animation.setEndValue(0.3)
        self._fade_animation.start()

    def _on_animation_finished(self) -> None:
        """Handle animation completion."""
        if self._fade_animation.endValue() == 0.3:
            # Fade out completed, now set new pixmap and fade in
            if self._pending_pixmap:
                self.label_widget.setPixmap(self._pending_pixmap)

            # Update current state
            if self._target_state:
                self.current_state = self._target_state

            # Start fade in
            self._fade_animation.setStartValue(0.3)
            self._fade_animation.setEndValue(1.0)
            self._fade_animation.start()
        else:
            # Fade in completed
            self.transition_completed.emit(self.current_state)

            # Clear pending state
            self._target_state = None
            self._pending_pixmap = None

    def _create_placeholder_pixmap(self, size: QSize) -> QPixmap:
        """Create glassmorphism-styled placeholder pixmap."""
        try:
            pixmap = QPixmap(size)
            pixmap.fill(QColor(0, 0, 0, 0))  # Transparent

            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # Glassmorphism background gradient
            gradient = QLinearGradient(0, 0, size.width(), size.height())
            gradient.setColorAt(0, QColor(248, 250, 252, 25))  # Very light blue-gray
            gradient.setColorAt(1, QColor(241, 245, 249, 15))

            painter.fillRect(pixmap.rect(), gradient)

            # Subtle border
            pen = QPen(QColor(203, 213, 225, 40))
            pen.setWidth(1)
            painter.setPen(pen)
            painter.drawRoundedRect(pixmap.rect().adjusted(0, 0, -1, -1), 12, 12)

            painter.end()
            return pixmap

        except Exception as e:
            logging.warning(f"Error creating placeholder pixmap: {e}")
            # Fallback
            pixmap = QPixmap(size)
            pixmap.fill(QColor(248, 250, 252))
            return pixmap

    def _create_loading_pixmap(self, size: QSize) -> QPixmap:
        """Create animated loading pixmap with glassmorphism styling."""
        try:
            pixmap = QPixmap(size)
            pixmap.fill(QColor(0, 0, 0, 0))  # Transparent

            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # Glassmorphism background with subtle color
            gradient = QLinearGradient(0, 0, size.width(), size.height())
            gradient.setColorAt(0, QColor(99, 102, 241, 20))  # Indigo tint
            gradient.setColorAt(1, QColor(139, 92, 246, 12))  # Purple tint

            painter.fillRect(pixmap.rect(), gradient)

            # Border
            pen = QPen(QColor(255, 255, 255, 30))
            pen.setWidth(1)
            painter.setPen(pen)
            painter.drawRoundedRect(pixmap.rect().adjusted(0, 0, -1, -1), 12, 12)

            # Animated loading dots
            center_x = size.width() // 2
            center_y = size.height() // 2

            dot_radius = 3
            dot_spacing = 12
            num_dots = 3

            for i in range(num_dots):
                # Calculate opacity based on animation frame
                phase = (self._loading_frame + i * 20) % 60
                opacity = 0.3 + 0.7 * (0.5 + 0.5 * abs((phase - 30) / 30))

                dot_color = QColor(255, 255, 255, int(opacity * 255))
                painter.setBrush(dot_color)
                painter.setPen(Qt.PenStyle.NoPen)

                dot_x = center_x + (i - 1) * dot_spacing
                dot_y = center_y

                painter.drawEllipse(
                    dot_x - dot_radius,
                    dot_y - dot_radius,
                    dot_radius * 2,
                    dot_radius * 2,
                )

            # Loading text
            painter.setPen(QColor(255, 255, 255, 160))
            font = QFont("Segoe UI", 9, QFont.Weight.Medium)
            painter.setFont(font)

            text_rect = pixmap.rect()
            text_rect.setTop(center_y + 20)
            text_rect.setHeight(30)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, "Loading...")

            painter.end()
            return pixmap

        except Exception as e:
            logging.warning(f"Error creating loading pixmap: {e}")
            return self._create_placeholder_pixmap(size)

    def _create_error_pixmap(self, size: QSize) -> QPixmap:
        """Create error state pixmap with glassmorphism styling."""
        try:
            pixmap = QPixmap(size)
            pixmap.fill(QColor(0, 0, 0, 0))  # Transparent

            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # Error background gradient
            gradient = QLinearGradient(0, 0, size.width(), size.height())
            gradient.setColorAt(0, QColor(239, 68, 68, 20))  # Red tint
            gradient.setColorAt(1, QColor(220, 38, 38, 12))

            painter.fillRect(pixmap.rect(), gradient)

            # Border
            pen = QPen(QColor(255, 255, 255, 40))
            pen.setWidth(1)
            painter.setPen(pen)
            painter.drawRoundedRect(pixmap.rect().adjusted(0, 0, -1, -1), 12, 12)

            # Error icon (X)
            center_x = size.width() // 2
            center_y = size.height() // 2

            pen = QPen(QColor(255, 255, 255, 180))
            pen.setWidth(3)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)

            # Draw X
            icon_size = 16
            painter.drawLine(
                center_x - icon_size // 2,
                center_y - icon_size // 2,
                center_x + icon_size // 2,
                center_y + icon_size // 2,
            )
            painter.drawLine(
                center_x + icon_size // 2,
                center_y - icon_size // 2,
                center_x - icon_size // 2,
                center_y + icon_size // 2,
            )

            # Error text
            painter.setPen(QColor(255, 255, 255, 160))
            font = QFont("Segoe UI", 8, QFont.Weight.Medium)
            painter.setFont(font)

            text_rect = pixmap.rect()
            text_rect.setTop(center_y + 20)
            text_rect.setHeight(30)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, "Load Error")

            painter.end()
            return pixmap

        except Exception as e:
            logging.warning(f"Error creating error pixmap: {e}")
            return self._create_placeholder_pixmap(size)

    def set_opacity(self, opacity: float) -> None:
        """Set the opacity of the label widget."""
        self._opacity_effect.setOpacity(opacity)

    def get_current_state(self) -> str:
        """Get the current visual state."""
        return self.current_state

    def is_animating(self) -> bool:
        """Check if currently animating."""
        return self._fade_animation.state() == QPropertyAnimation.State.Running

    def stop_animation(self) -> None:
        """Stop any running animation."""
        if self.is_animating():
            self._fade_animation.stop()
            self.set_opacity(1.0)

            # Clear pending state
            self._target_state = None
            self._pending_pixmap = None
