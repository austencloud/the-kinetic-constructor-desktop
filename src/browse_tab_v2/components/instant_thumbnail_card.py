"""
Instant Thumbnail Card for Browse Tab v2

This component provides instant thumbnail display by prioritizing pre-cached images
and eliminating progressive loading delays. It ensures users see fully populated
thumbnail cards immediately when the Browse Tab becomes visible.

Key Features:
- Instant display of pre-cached thumbnails
- Zero progressive loading delays
- Fallback to fast loading for non-cached images
- Optimized for sub-50ms display times
"""

import logging
from typing import Optional
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QPainter, QFont

from ..core.interfaces import SequenceModel

logger = logging.getLogger(__name__)


class InstantThumbnailCard(QWidget):
    """
    Instant thumbnail card with pre-cached image prioritization.

    This card ensures instant display by:
    1. Checking cache for pre-loaded thumbnails first
    2. Displaying cached images immediately
    3. Using fast fallback loading for cache misses
    4. Eliminating all progressive loading states
    """

    # Signals
    clicked = pyqtSignal()
    double_clicked = pyqtSignal()

    def __init__(
        self, sequence: SequenceModel, cache_service=None, parent: QWidget = None
    ):
        super().__init__(parent)

        self.sequence = sequence
        self.cache_service = cache_service
        self._image_loaded = False
        self._cached_pixmap = None

        # Setup UI immediately
        self._setup_ui()
        self._setup_styling()

        # Try instant image loading
        self._load_instant_image()

        logger.debug(f"🚀 INSTANT_CARD: Created for sequence {sequence.id}")

    def _setup_ui(self):
        """Setup the card UI structure."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Image container
        self.image_container = QFrame()
        self.image_container.setFixedSize(260, 220)
        self.image_container.setObjectName("imageContainer")

        # Image label
        self.image_label = QLabel()
        self.image_label.setFixedSize(260, 220)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setScaledContents(False)
        self.image_label.setObjectName("imageLabel")

        # Add image to container
        image_layout = QVBoxLayout(self.image_container)
        image_layout.setContentsMargins(0, 0, 0, 0)
        image_layout.addWidget(self.image_label)

        # Title label
        self.title_label = QLabel(self.sequence.name)
        self.title_label.setFixedHeight(30)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setObjectName("titleLabel")

        # Set title font
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        self.title_label.setFont(font)

        layout.addWidget(self.image_container)
        layout.addWidget(self.title_label)

    def _setup_styling(self):
        """Apply modern glassmorphism styling."""
        self.setStyleSheet(
            """
            InstantThumbnailCard {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 15px;
                backdrop-filter: blur(10px);
            }
            
            InstantThumbnailCard:hover {
                background: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(255, 255, 255, 0.25);
                transform: translateY(-2px);
            }
            
            QFrame#imageContainer {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 10px;
            }
            
            QLabel#imageLabel {
                background: transparent;
                border: none;
                border-radius: 8px;
            }
            
            QLabel#titleLabel {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 8px;
                color: white;
                padding: 5px;
            }
        """
        )

    def _load_instant_image(self):
        """Load image instantly from cache or fast fallback."""
        if not self.sequence.thumbnails:
            self._show_placeholder()
            return

        thumbnail_path = self.sequence.thumbnails[0]

        # Try instant cache first (highest priority)
        if self.cache_service and hasattr(self.cache_service, "get_instant_thumbnail"):
            cached_pixmap = self.cache_service.get_instant_thumbnail(
                thumbnail_path, (260, 220)
            )
            if cached_pixmap:
                self._display_image(cached_pixmap)
                logger.debug(
                    f"🚀 INSTANT_CARD: Instant cache hit for {self.sequence.id}"
                )
                return

        # Try regular cache (second priority)
        if self.cache_service and hasattr(self.cache_service, "get_cached_image_sync"):
            cached_pixmap = self.cache_service.get_cached_image_sync(
                thumbnail_path, (260, 220)
            )
            if cached_pixmap:
                self._display_image(cached_pixmap)
                logger.debug(f"🚀 INSTANT_CARD: Cache hit for {self.sequence.id}")
                return

        # Handle case where cache service is not available
        if not self.cache_service:
            logger.debug(
                f"🚀 INSTANT_CARD: No cache service available for {self.sequence.id}, using direct fallback"
            )

        # Fast fallback loading (works with or without cache service)
        self._load_image_fast_fallback(thumbnail_path)

    def _load_image_fast_fallback(self, image_path: str):
        """Fast fallback image loading for cache misses."""
        try:
            logger.debug(
                f"🚀 INSTANT_CARD: Fast fallback loading for {self.sequence.id}"
            )

            # Load image directly (blocking but fast for local files)
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                # Scale to target size
                scaled_pixmap = pixmap.scaled(
                    260,
                    220,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )

                # Display immediately
                self._display_image(scaled_pixmap)

                # Cache for future use
                if self.cache_service and hasattr(
                    self.cache_service, "cache_image_sync"
                ):
                    self.cache_service.cache_image_sync(
                        image_path, scaled_pixmap, (260, 220)
                    )

                logger.debug(
                    f"🚀 INSTANT_CARD: Fast fallback successful for {self.sequence.id}"
                )
            else:
                self._show_placeholder()

        except Exception as e:
            logger.warning(f"Fast fallback loading failed for {self.sequence.id}: {e}")
            self._show_placeholder()

    def _load_image_fast(self):
        """
        Fast image loading method expected by EfficientVirtualGrid.

        This method provides compatibility with the virtual grid's viewport rendering
        system while maintaining instant loading performance.
        """
        if not hasattr(self, "_image_loaded") or not self._image_loaded:
            self._load_instant_image()
            self._image_loaded = True

    def _display_image(self, pixmap: QPixmap):
        """Display the image immediately."""
        self.image_label.setPixmap(pixmap)
        self._image_loaded = True
        self._cached_pixmap = pixmap
        logger.debug(f"🚀 INSTANT_CARD: Image displayed for {self.sequence.id}")

    def _show_placeholder(self):
        """Show a simple placeholder for missing images."""
        # Create a simple colored placeholder
        placeholder = QPixmap(260, 220)
        placeholder.fill(Qt.GlobalColor.darkGray)

        # Draw sequence name on placeholder
        painter = QPainter(placeholder)
        painter.setPen(Qt.GlobalColor.white)
        painter.drawText(
            placeholder.rect(), Qt.AlignmentFlag.AlignCenter, self.sequence.name[:10]
        )
        painter.end()

        self.image_label.setPixmap(placeholder)
        logger.debug(f"🚀 INSTANT_CARD: Placeholder shown for {self.sequence.id}")

    def mousePressEvent(self, event):
        """Handle mouse press events."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        """Handle mouse double click events."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit()
        super().mouseDoubleClickEvent(event)

    def sizeHint(self) -> QSize:
        """Provide size hint for layout."""
        return QSize(280, 280)

    def minimumSizeHint(self) -> QSize:
        """Provide minimum size hint."""
        return QSize(280, 280)

    def get_sequence(self) -> SequenceModel:
        """Get the sequence model."""
        return self.sequence

    def is_image_loaded(self) -> bool:
        """Check if image is loaded."""
        return self._image_loaded

    def get_cached_pixmap(self) -> Optional[QPixmap]:
        """Get the cached pixmap if available."""
        return self._cached_pixmap

    def update_sequence_info(self, sequence: SequenceModel):
        """Update sequence information (for compatibility)."""
        self.sequence = sequence
        self.title_label.setText(sequence.name)

    def refresh_image(self):
        """Refresh the image display."""
        self._load_instant_image()

    def preload_image(self, image_path: str):
        """Preload image for instant display (called during startup)."""
        try:
            if self.cache_service and hasattr(
                self.cache_service, "get_instant_thumbnail"
            ):
                # Check if already cached
                cached_pixmap = self.cache_service.get_instant_thumbnail(
                    image_path, (260, 220)
                )
                if cached_pixmap:
                    self._cached_pixmap = cached_pixmap
                    return True

            # Load and cache for instant access
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    260,
                    220,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )

                if self.cache_service and hasattr(
                    self.cache_service, "cache_image_instant"
                ):
                    self.cache_service.cache_image_instant(
                        image_path, scaled_pixmap, (260, 220)
                    )

                self._cached_pixmap = scaled_pixmap
                return True

        except Exception as e:
            logger.debug(f"Preload failed for {image_path}: {e}")

        return False
