"""
Loading Indicator - Modern glassmorphism loading indicator for thumbnails.

Provides visual feedback during image loading with:
- Glassmorphism styling (10-15% opacity, 15-25px blur)
- Smooth fade transitions (200-300ms)
- Subtle animations and micro-interactions
- Error state handling
"""

import logging
from typing import Optional
from PyQt6.QtCore import (
    QTimer,
    QPropertyAnimation,
    QEasingCurve,
    QRect,
    pyqtSignal,
    QSize,
    Qt,
)
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont, QLinearGradient, QPen
from PyQt6.QtWidgets import QLabel, QGraphicsOpacityEffect, QWidget

from styles.glassmorphism_styler import GlassmorphismStyler


class LoadingIndicator(QLabel):
    """
    Modern glassmorphism loading indicator for thumbnail images.

    Features:
    - Glassmorphism background with blur effect
    - Smooth fade-in/out transitions
    - Animated loading state
    - Error state display
    - Seamless image transition
    """

    # Signals
    animation_finished = pyqtSignal()

    def __init__(self, parent: QWidget):
        super().__init__(parent)

        self.parent_widget = parent
        self._current_pixmap: Optional[QPixmap] = None
        self._is_loading = False
        self._is_error = False

        # Animation components
        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)

        self.fade_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_animation.setDuration(250)  # 250ms for smooth transitions
        self.fade_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.fade_animation.finished.connect(self.animation_finished)

        # Loading animation timer
        self.loading_timer = QTimer()
        self.loading_timer.timeout.connect(self._update_loading_animation)
        self.loading_animation_frame = 0

        # Setup initial state
        self._setup_styling()
        self._create_placeholder()
        self.show_placeholder()

    def _setup_styling(self) -> None:
        """Apply glassmorphism styling to the indicator."""
        # Create glassmorphism card styling
        style = GlassmorphismStyler.create_glassmorphism_card(
            self,
            blur_radius=20,  # 15-25px blur range
            opacity=0.12,  # 10-15% opacity range
            border_radius=14,  # 12-16px rounded corners
        )

        # Enhanced styling with modern aesthetics
        enhanced_style = f"""
        QLabel {{
            {style}
            background: qlineargradient(
                x1: 0, y1: 0, x2: 1, y2: 1,
                stop: 0 rgba(255, 255, 255, 0.15),
                stop: 1 rgba(255, 255, 255, 0.08)
            );
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 14px;
        }}
        
        QLabel:hover {{
            background: qlineargradient(
                x1: 0, y1: 0, x2: 1, y2: 1,
                stop: 0 rgba(255, 255, 255, 0.18),
                stop: 1 rgba(255, 255, 255, 0.10)
            );
            border: 1px solid rgba(255, 255, 255, 0.25);
            transform: translateY(-2px);
        }}
        """

        self.setStyleSheet(enhanced_style)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Add subtle shadow effect
        GlassmorphismStyler.add_shadow_effect(
            self, offset_y=4, blur_radius=12, color="rgba(0, 0, 0, 0.1)"
        )

    def _create_placeholder(self) -> None:
        """Create a glassmorphism-styled placeholder pixmap."""
        try:
            # Use parent size or default size
            if self.parent_widget:
                size = self.parent_widget.size()
                if size.width() <= 0 or size.height() <= 0:
                    size = QSize(200, 150)
            else:
                size = QSize(200, 150)

            self.placeholder_pixmap = QPixmap(size)
            self.placeholder_pixmap.fill(QColor(0, 0, 0, 0))  # Transparent

            painter = QPainter(self.placeholder_pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # Create subtle gradient background
            gradient = QLinearGradient(0, 0, size.width(), size.height())
            gradient.setColorAt(0, QColor(248, 250, 252, 30))  # Very light blue-gray
            gradient.setColorAt(1, QColor(241, 245, 249, 20))

            painter.fillRect(self.placeholder_pixmap.rect(), gradient)

            # Draw subtle border
            pen = QPen(QColor(203, 213, 225, 40))  # Light gray border
            pen.setWidth(1)
            painter.setPen(pen)
            painter.drawRoundedRect(
                self.placeholder_pixmap.rect().adjusted(0, 0, -1, -1), 12, 12
            )

            painter.end()

        except Exception as e:
            logging.warning(f"Failed to create placeholder pixmap: {e}")
            # Fallback to simple placeholder
            self.placeholder_pixmap = QPixmap(200, 150)
            self.placeholder_pixmap.fill(QColor(248, 250, 252, 50))

    def _create_loading_pixmap(self) -> QPixmap:
        """Create animated loading pixmap with glassmorphism styling."""
        try:
            size = (
                self.placeholder_pixmap.size()
                if self.placeholder_pixmap
                else QSize(200, 150)
            )
            pixmap = QPixmap(size)
            pixmap.fill(QColor(0, 0, 0, 0))  # Transparent

            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # Background gradient
            gradient = QLinearGradient(0, 0, size.width(), size.height())
            gradient.setColorAt(0, QColor(99, 102, 241, 25))  # Indigo tint
            gradient.setColorAt(1, QColor(139, 92, 246, 15))  # Purple tint

            painter.fillRect(pixmap.rect(), gradient)

            # Animated loading indicator
            center_x = size.width() // 2
            center_y = size.height() // 2

            # Draw animated dots or spinner
            dot_radius = 3
            dot_spacing = 12
            num_dots = 3

            for i in range(num_dots):
                # Calculate opacity based on animation frame
                opacity = (
                    0.3
                    + 0.7 * abs((self.loading_animation_frame + i * 10) % 60 - 30) / 30
                )

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
            painter.setPen(QColor(255, 255, 255, 180))
            font = QFont("Segoe UI", 9, QFont.Weight.Medium)
            painter.setFont(font)

            text_rect = QRect(0, center_y + 20, size.width(), 30)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, "Loading...")

            painter.end()
            return pixmap

        except Exception as e:
            logging.warning(f"Failed to create loading pixmap: {e}")
            return self.placeholder_pixmap or QPixmap(200, 150)

    def _create_error_pixmap(self) -> QPixmap:
        """Create error state pixmap with glassmorphism styling."""
        try:
            size = (
                self.placeholder_pixmap.size()
                if self.placeholder_pixmap
                else QSize(200, 150)
            )
            pixmap = QPixmap(size)
            pixmap.fill(QColor(0, 0, 0, 0))  # Transparent

            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # Error background gradient
            gradient = QLinearGradient(0, 0, size.width(), size.height())
            gradient.setColorAt(0, QColor(239, 68, 68, 25))  # Red tint
            gradient.setColorAt(1, QColor(220, 38, 38, 15))

            painter.fillRect(pixmap.rect(), gradient)

            # Error icon (simple X)
            center_x = size.width() // 2
            center_y = size.height() // 2

            pen = QPen(QColor(255, 255, 255, 200))
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
            font = QFont("Segoe UI", 8, QFont.Weight.Medium)
            painter.setFont(font)

            text_rect = QRect(0, center_y + 20, size.width(), 30)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, "Load Error")

            painter.end()
            return pixmap

        except Exception as e:
            logging.warning(f"Failed to create error pixmap: {e}")
            return self.placeholder_pixmap or QPixmap(200, 150)

    def show_placeholder(self) -> None:
        """Show the placeholder state."""
        self._is_loading = False
        self._is_error = False

        if self.placeholder_pixmap:
            self.setPixmap(self.placeholder_pixmap)

        self._fade_in()

    def show_loading(self) -> None:
        """Show the loading state with animation."""
        self._is_loading = True
        self._is_error = False

        # Start loading animation
        self.loading_timer.start(100)  # Update every 100ms
        self._update_loading_animation()

        self._fade_in()

    def show_image(self, pixmap: QPixmap) -> None:
        """Show the loaded image with smooth transition."""
        self._is_loading = False
        self._is_error = False
        self._current_pixmap = pixmap

        # Stop loading animation
        self.loading_timer.stop()

        # Fade out, then show image
        self.fade_animation.finished.connect(self._show_image_after_fade)
        self._fade_out()

    def show_error(self) -> None:
        """Show the error state."""
        self._is_loading = False
        self._is_error = True

        # Stop loading animation
        self.loading_timer.stop()

        error_pixmap = self._create_error_pixmap()
        self.setPixmap(error_pixmap)

        self._fade_in()

    def reset(self) -> None:
        """Reset the indicator to placeholder state."""
        self.loading_timer.stop()
        self._current_pixmap = None
        self.show_placeholder()

    def _update_loading_animation(self) -> None:
        """Update the loading animation frame."""
        if self._is_loading:
            self.loading_animation_frame = (self.loading_animation_frame + 1) % 60
            loading_pixmap = self._create_loading_pixmap()
            self.setPixmap(loading_pixmap)

    def _show_image_after_fade(self) -> None:
        """Show the image after fade out completes."""
        self.fade_animation.finished.disconnect()

        if self._current_pixmap:
            self.setPixmap(self._current_pixmap)
            self._fade_in()

    def _fade_in(self) -> None:
        """Fade in the indicator."""
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.start()

    def _fade_out(self) -> None:
        """Fade out the indicator."""
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.start()
