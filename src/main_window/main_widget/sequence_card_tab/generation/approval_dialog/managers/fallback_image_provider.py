from PyQt6.QtGui import QPixmap, QPainter, QFont, QColor
from PyQt6.QtCore import Qt
from typing import Dict, Optional
import logging


class FallbackImageProvider:
    def __init__(self):
        self.fallback_images: Dict[str, QPixmap] = {}
        self.error_placeholder: Optional[QPixmap] = None
        self._create_error_placeholder()

    def _create_error_placeholder(self) -> None:
        """Create a standard error placeholder image"""
        try:
            size = (300, 200)
            self.error_placeholder = QPixmap(*size)
            self.error_placeholder.fill(QColor(240, 240, 240))

            painter = QPainter(self.error_placeholder)
            painter.setPen(QColor(120, 120, 120))
            painter.setFont(QFont("Arial", 12))

            text = "Image\nGeneration\nFailed"
            painter.drawText(
                self.error_placeholder.rect(),
                Qt.AlignmentFlag.AlignCenter,
                text,
            )
            painter.end()

        except Exception as e:
            logging.warning(f"Failed to create error placeholder: {e}")
            self.error_placeholder = QPixmap(300, 200)
            self.error_placeholder.fill(QColor(200, 200, 200))

    def get_fallback_image(self, sequence_id: str) -> Optional[QPixmap]:
        """Get a cached fallback image for a sequence"""
        return self.fallback_images.get(sequence_id)

    def set_fallback_image(self, sequence_id: str, pixmap: QPixmap) -> None:
        """Cache a fallback image for a sequence"""
        self.fallback_images[sequence_id] = pixmap

    def get_error_placeholder(self) -> Optional[QPixmap]:
        """Get the standard error placeholder image"""
        return self.error_placeholder

    def apply_fallback_to_card(
        self, sequence_id: str, card, error_message: str
    ) -> None:
        """Apply appropriate fallback image to a sequence card"""
        try:
            # Try to use a cached fallback first
            if sequence_id in self.fallback_images:
                card.set_image(self.fallback_images[sequence_id])
                logging.info(f"Applied cached fallback image for {sequence_id}")
            elif self.error_placeholder:
                card.set_image(self.error_placeholder)
                logging.info(f"Applied error placeholder for {sequence_id}")
            else:
                card.set_image_error(error_message)
                logging.info(f"Set error state for {sequence_id}")

        except Exception as e:
            logging.error(f"Error applying fallback for {sequence_id}: {e}")

    def create_custom_placeholder(
        self,
        text: str,
        size: tuple = (300, 200),
        bg_color: QColor = None,
        text_color: QColor = None,
    ) -> QPixmap:
        """Create a custom placeholder image with specified text and styling"""
        try:
            bg_color = bg_color or QColor(240, 240, 240)
            text_color = text_color or QColor(120, 120, 120)

            pixmap = QPixmap(*size)
            pixmap.fill(bg_color)

            painter = QPainter(pixmap)
            painter.setPen(text_color)
            painter.setFont(QFont("Arial", 12))
            painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, text)
            painter.end()

            return pixmap

        except Exception as e:
            logging.error(f"Error creating custom placeholder: {e}")
            return self.error_placeholder or QPixmap(*size)

    def clear_fallback_cache(self) -> None:
        """Clear all cached fallback images"""
        self.fallback_images.clear()
