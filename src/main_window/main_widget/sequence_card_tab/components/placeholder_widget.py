from PyQt6.QtWidgets import QLabel, QVBoxLayout, QFrame
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont, QBrush, QPen
import logging


class SequenceCardPlaceholder(QFrame):
    """
    A placeholder widget that matches the size and layout of sequence cards.
    Shows a loading animation and can be replaced with actual sequence cards.
    """

    # Signal emitted when this placeholder should be replaced
    replace_requested = pyqtSignal(object)  # Emits the sequence data

    def __init__(self, placeholder_id: str, expected_sequence_data=None):
        super().__init__()
        self.placeholder_id = placeholder_id
        self.expected_sequence_data = expected_sequence_data
        self.logger = logging.getLogger(__name__)

        # Animation state
        self.animation_frame = 0
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self._update_animation)

        self._setup_placeholder_ui()
        self._start_animation()

    def _setup_placeholder_ui(self):
        """Set up the placeholder UI to match printable system dimensions and styling."""
        # Get the actual cell size from the page factory to match the printable system
        try:
            # This will be set by the parent when the placeholder is created
            # For now, use a reasonable default that will be updated
            self.setFixedSize(200, 150)  # Default size, will be updated by parent
        except:
            self.setFixedSize(200, 150)  # Fallback size

        # Match the styling of sequence cards with a loading state appearance
        self.setStyleSheet(
            """
            QFrame {
                background: rgba(255, 255, 255, 0.05);
                border: 2px dashed rgba(255, 255, 255, 0.3);
                border-radius: 12px;
                padding: 10px;
            }
            QFrame:hover {
                background: rgba(255, 255, 255, 0.08);
                border: 2px dashed rgba(255, 255, 255, 0.4);
            }
        """
        )

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        # Create placeholder image area (size will be set by parent)
        self.image_label = QLabel()
        # Size will be set by the progressive layout manager based on cell size
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet(
            """
            QLabel {
                background: rgba(0, 0, 0, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                color: #e1e5e9;
                font-size: 12px;
                font-weight: bold;
            }
        """
        )
        layout.addWidget(self.image_label)

        # Create placeholder info area
        self.info_label = QLabel()
        self.info_label.setText(
            "<b>Generating...</b><br>"
            "Creating sequence<br>"
            "Please wait<br>"
            "⏳ Processing"
        )
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label.setStyleSheet(
            """
            QLabel {
                color: #e1e5e9;
                font-size: 11px;
                background: transparent;
                border: none;
                padding: 5px;
            }
        """
        )
        layout.addWidget(self.info_label)

        # Create initial placeholder image
        self._create_placeholder_image()

    def _create_placeholder_image(self):
        """Create an animated placeholder image."""
        # Use the current widget size for the placeholder image
        widget_size = self.size()
        if widget_size.width() <= 0 or widget_size.height() <= 0:
            # Fallback size if widget hasn't been sized yet
            widget_size = QSize(200, 150)

        # Create image slightly smaller than widget to account for margins
        image_width = max(100, widget_size.width() - 30)
        image_height = max(80, widget_size.height() - 60)

        pixmap = QPixmap(image_width, image_height)
        pixmap.fill(QColor(0, 0, 0, 0))  # Transparent background

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw animated loading pattern
        center_x, center_y = image_width // 2, image_height // 2

        # Draw pulsing circles
        for i in range(3):
            alpha = max(0, 100 - abs((self.animation_frame + i * 20) % 100 - 50))
            color = QColor(255, 255, 255, alpha)
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(color, 2))

            base_radius = min(image_width, image_height) // 10
            radius = base_radius + (self.animation_frame + i * 5) % (base_radius // 2)
            painter.drawEllipse(
                center_x - radius, center_y - radius, radius * 2, radius * 2
            )

        # Draw loading text
        painter.setPen(QPen(QColor(255, 255, 255, 150), 1))
        font_size = max(8, min(image_width, image_height) // 12)
        painter.setFont(QFont("Segoe UI", font_size, QFont.Weight.Bold))
        text_rect = pixmap.rect()
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, "Generating...")

        painter.end()
        self.image_label.setPixmap(pixmap)

    def _start_animation(self):
        """Start the loading animation."""
        self.animation_timer.start(100)  # Update every 100ms

    def _stop_animation(self):
        """Stop the loading animation."""
        if hasattr(self, "animation_timer") and self.animation_timer:
            try:
                self.animation_timer.stop()
            except RuntimeError:
                pass

    def _update_animation(self):
        """Update the animation frame and redraw."""
        if not hasattr(self, "animation_timer") or not self.animation_timer:
            return
        self.animation_frame = (self.animation_frame + 5) % 100
        self._create_placeholder_image()

    def replace_with_sequence_card(self, sequence_card_widget):
        """
        Replace this placeholder with an actual sequence card widget.
        This method should be called by the parent layout manager.
        """
        self._stop_animation()
        self.logger.debug(
            f"Placeholder {self.placeholder_id} being replaced with actual sequence card"
        )

        # The parent layout manager will handle the actual replacement
        # This method is mainly for cleanup
        self.replace_requested.emit(sequence_card_widget)

    def set_generation_progress(self, status: str):
        """Update the placeholder with generation progress information."""
        if status == "generating":
            self.info_label.setText(
                "<b>Generating...</b><br>"
                "Creating sequence<br>"
                "Please wait<br>"
                "⏳ Processing"
            )
        elif status == "creating_image":
            self.info_label.setText(
                "<b>Creating Image...</b><br>"
                "Rendering sequence<br>"
                "Almost ready<br>"
                "🎨 Finalizing"
            )
        elif status == "complete":
            self.info_label.setText(
                "<b>Complete!</b><br>" "Sequence ready<br>" "Loading...<br>" "✅ Done"
            )
            self._stop_animation()

    def cleanup(self):
        """Clean up resources when the placeholder is no longer needed."""
        self._stop_animation()
        if hasattr(self, "animation_timer") and self.animation_timer:
            try:
                self.animation_timer.deleteLater()
            except RuntimeError:
                pass
