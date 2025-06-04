"""
Enhanced ModernThumbnailCard with Layout Consistency Fixes

This enhanced version ensures perfect integration with the consistent grid system
and prevents any size-related inconsistencies during rendering and loading phases.

Key improvements:
1. Strengthened fixed sizing enforcement
2. Enhanced resize event prevention during critical phases
3. Improved image scaling for consistent appearance
4. Better integration with chunked loading
5. Defensive programming against layout disruption
"""

import logging
from typing import Optional, List
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QGraphicsDropShadowEffect,
    QSizePolicy,
)
from PyQt6.QtCore import (
    Qt,
    QSize,
    QPropertyAnimation,
    QEasingCurve,
    QParallelAnimationGroup,
    pyqtSignal,
    QTimer,
    QRect,
)
from PyQt6.QtGui import (
    QPainter,
    QColor,
    QPalette,
    QPixmap,
    QFont,
    QFontMetrics,
    QPainterPath,
    QLinearGradient,
    QBrush,
    QPen,
)

from ..core.state import SequenceModel
from ..core.interfaces import BrowseTabConfig

logger = logging.getLogger(__name__)


class LayoutConsistentThumbnailCard(QWidget):
    """
    Enhanced thumbnail card with guaranteed layout consistency.

    This version works seamlessly with the ConsistentResponsiveThumbnailGrid
    to ensure uniform appearance across all grid positions and loading phases.
    """

    # Signals
    clicked = pyqtSignal(str)  # sequence_id
    double_clicked = pyqtSignal(str)  # sequence_id
    favorite_toggled = pyqtSignal(str, bool)  # sequence_id, is_favorite
    context_menu_requested = pyqtSignal(str, object)  # sequence_id, position

    # Card states
    STATE_NORMAL = "normal"
    STATE_HOVER = "hover"
    STATE_SELECTED = "selected"
    STATE_LOADING = "loading"
    STATE_ERROR = "error"

    def __init__(self, sequence, config=None, parent: QWidget = None):
        super().__init__(parent)

        self.sequence = sequence
        self.config = config or self._default_config()

        # Layout consistency controls
        self._fixed_width = 280  # Default, will be overridden
        self._fixed_height = 320  # Default, will be overridden
        self._size_locked = False
        self._grid_managed = False  # True when managed by consistent grid

        # Resize event throttling
        self._resize_count = 0
        self._last_resize_time = 0
        self._max_resize_events_per_second = 2

        # State management
        self._current_state = self.STATE_NORMAL
        self._is_selected = False
        self._is_favorite = getattr(sequence, "is_favorite", False)
        self._hover_scale = 1.0
        self._glow_opacity = 0.0

        # Animation system
        self._hover_animation: Optional[QParallelAnimationGroup] = None
        self._selection_animation: Optional[QPropertyAnimation] = None

        # Chunked loading manager
        self._chunked_loading_manager = None

        # UI components
        self.thumbnail_label: Optional[QLabel] = None
        self.title_label: Optional[QLabel] = None
        self.metadata_label: Optional[QLabel] = None
        self.favorite_button: Optional[QPushButton] = None

        # Styling
        self.card_radius = 20
        self.card_padding = 15
        self.thumbnail_radius = 15

        self._setup_ui()
        self._setup_styling()
        self._setup_animations()
        self._load_thumbnail()

        # Enable mouse tracking for hover effects
        self.setMouseTracking(True)

        logger.debug(f"LayoutConsistentThumbnailCard created for: {sequence.name}")

    def _default_config(self):
        """Provide default configuration."""

        class DefaultConfig:
            enable_animations = True

        return DefaultConfig()

    def _setup_ui(self):
        """Setup the card UI structure with layout consistency in mind."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            self.card_padding, self.card_padding, self.card_padding, self.card_padding
        )
        layout.setSpacing(12)

        # Thumbnail container with fixed proportions
        thumbnail_container = QFrame()
        thumbnail_container.setObjectName("thumbnailContainer")
        thumbnail_container.setFixedHeight(180)  # Fixed height for consistency

        thumbnail_layout = QVBoxLayout(thumbnail_container)
        thumbnail_layout.setContentsMargins(0, 0, 0, 0)

        # Thumbnail image with consistent sizing
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setObjectName("thumbnailImage")
        self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail_label.setScaledContents(False)  # Prevent auto-scaling
        self.thumbnail_label.setMinimumHeight(160)
        self.thumbnail_label.setMaximumHeight(180)

        thumbnail_layout.addWidget(self.thumbnail_label)
        layout.addWidget(thumbnail_container)

        # Content section with fixed height
        content_frame = QFrame()
        content_frame.setObjectName("contentFrame")
        content_frame.setFixedHeight(100)  # Fixed height for consistency
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(8)

        # Title and favorite button row
        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)

        # Title with text truncation for consistency
        self.title_label = QLabel(self._truncate_text(self.sequence.name, 25))
        self.title_label.setObjectName("titleLabel")
        self.title_label.setWordWrap(False)  # Prevent wrapping for consistency
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        self.title_label.setFont(title_font)

        # Favorite button with fixed size
        self.favorite_button = QPushButton("♡" if not self._is_favorite else "♥")
        self.favorite_button.setObjectName("favoriteButton")
        self.favorite_button.setFixedSize(24, 24)
        self.favorite_button.clicked.connect(self._toggle_favorite)

        title_row.addWidget(self.title_label)
        title_row.addWidget(self.favorite_button)
        content_layout.addLayout(title_row)

        # Metadata with consistent formatting
        metadata_text = self._format_metadata_consistently()
        self.metadata_label = QLabel(metadata_text)
        self.metadata_label.setObjectName("metadataLabel")
        metadata_font = QFont()
        metadata_font.setPointSize(10)
        self.metadata_label.setFont(metadata_font)
        self.metadata_label.setWordWrap(False)  # Prevent wrapping

        content_layout.addWidget(self.metadata_label)
        content_layout.addStretch()  # Push content to top

        layout.addWidget(content_frame)

        # Set initial size policy for fixed layout
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        # Apply default fixed size
        self.setFixedSize(self._fixed_width, self._fixed_height)

    def _truncate_text(self, text: str, max_length: int) -> str:
        """Truncate text to ensure consistent display."""
        if len(text) <= max_length:
            return text
        return text[: max_length - 3] + "..."

    def _format_metadata_consistently(self) -> str:
        """Format metadata with consistent length and format."""
        metadata_parts = []

        if hasattr(self.sequence, "difficulty") and self.sequence.difficulty:
            metadata_parts.append(f"Diff: {self.sequence.difficulty}")

        if hasattr(self.sequence, "length") and self.sequence.length:
            metadata_parts.append(f"Len: {self.sequence.length}")

        if hasattr(self.sequence, "category") and self.sequence.category:
            category = self._truncate_text(str(self.sequence.category), 10)
            metadata_parts.append(f"Cat: {category}")

        result = " • ".join(metadata_parts) if metadata_parts else "No data"

        # Ensure consistent length
        return self._truncate_text(result, 40)

    def _setup_styling(self):
        """Apply modern glassmorphic styling."""
        self.setStyleSheet(
            f"""
            LayoutConsistentThumbnailCard {{
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: {self.card_radius}px;
            }}

            LayoutConsistentThumbnailCard:hover {{
                background: rgba(255, 255, 255, 0.15);
                border: 1px solid rgba(255, 255, 255, 0.3);
            }}

            QFrame#thumbnailContainer {{
                background: rgba(0, 0, 0, 0.1);
                border-radius: {self.thumbnail_radius}px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }}

            QLabel#thumbnailImage {{
                background: rgba(255, 255, 255, 0.05);
                border-radius: {self.thumbnail_radius - 2}px;
                border: none;
            }}

            QFrame#contentFrame {{
                background: transparent;
                border: none;
            }}

            QLabel#titleLabel {{
                color: rgba(255, 255, 255, 0.9);
                background: transparent;
                border: none;
            }}

            QLabel#metadataLabel {{
                color: rgba(255, 255, 255, 0.7);
                background: transparent;
                border: none;
            }}

            QPushButton#favoriteButton {{
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 12px;
                color: rgba(255, 255, 255, 0.8);
                font-size: 14px;
            }}

            QPushButton#favoriteButton:hover {{
                background: rgba(255, 255, 255, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.4);
                color: rgba(255, 255, 255, 1.0);
            }}
        """
        )

        # Add drop shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

    def _setup_animations(self):
        """Setup animation system for smooth transitions."""
        pass  # Animations created dynamically

    def _load_thumbnail(self):
        """Load and display the thumbnail image."""
        self.set_loading_state(True)

        if not hasattr(self.sequence, "thumbnails") or not self.sequence.thumbnails:
            self.set_error_state("No thumbnails")
            return

        thumbnail_path = self.sequence.thumbnails[0]

        import os

        if not os.path.exists(thumbnail_path):
            logger.warning(f"Thumbnail not found: {thumbnail_path}")
            self.set_error_state("Image not found")
            return

        try:
            if self._chunked_loading_manager:
                # Use chunked loading
                self._chunked_loading_manager.queue_image_load(self, thumbnail_path)
            else:
                # Use direct synchronous loading
                self._load_image_sync(thumbnail_path)
        except Exception as e:
            logger.error(f"Error loading thumbnail: {e}")
            self.set_error_state("Load error")

    def _load_image_sync(self, image_path: str):
        """Synchronous image loading with consistent scaling."""
        try:
            pixmap = QPixmap(image_path)

            if pixmap.isNull():
                self._on_image_load_failed(image_path, "Failed to load")
                return

            self._on_image_loaded(pixmap, image_path)

        except Exception as e:
            logger.error(f"Sync image loading error: {e}")
            self._on_image_load_failed(image_path, str(e))

    def _on_image_loaded(self, pixmap, image_path: str):
        """Handle successful image loading with consistent display."""
        try:
            self.set_thumbnail_image(pixmap)
            self.set_loading_state(False)
        except Exception as e:
            logger.error(f"Error setting loaded image: {e}")
            self.set_error_state("Display error")

    def _on_image_load_failed(self, image_path: str, error_msg: str):
        """Handle failed image loading."""
        logger.warning(f"Failed to load thumbnail {image_path}: {error_msg}")
        self.set_error_state("Load failed")

    def set_thumbnail_image(self, pixmap: QPixmap):
        """Set thumbnail image with guaranteed consistent scaling."""
        if pixmap and not pixmap.isNull():
            # Calculate container size from thumbnail label
            container_size = self.thumbnail_label.size()

            if container_size.width() <= 0 or container_size.height() <= 0:
                # Use fixed size based on card dimensions
                container_size = QSize(self._fixed_width - 40, 160)

            # Scale image consistently
            scaled_pixmap = self._scale_image_consistently(pixmap, container_size)

            # Set the scaled pixmap
            self.thumbnail_label.setPixmap(scaled_pixmap)
            self.thumbnail_label.setText("")

            logger.debug(f"Set thumbnail: {pixmap.size()} -> {scaled_pixmap.size()}")
        else:
            self.thumbnail_label.setText("No Image")
            self.thumbnail_label.setPixmap(QPixmap())

    def _scale_image_consistently(self, pixmap: QPixmap, container_size: QSize):
        """Scale image with guaranteed consistency across all cards."""
        try:
            # Always scale to fit container while maintaining aspect ratio
            scaled_pixmap = pixmap.scaled(
                container_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

            # If scaled image is smaller than container, center it
            if (
                scaled_pixmap.width() < container_size.width()
                or scaled_pixmap.height() < container_size.height()
            ):

                # Create a new pixmap with container size and fill with transparent
                centered_pixmap = QPixmap(container_size)
                centered_pixmap.fill(Qt.GlobalColor.transparent)

                # Paint the scaled image centered
                painter = QPainter(centered_pixmap)
                x = (container_size.width() - scaled_pixmap.width()) // 2
                y = (container_size.height() - scaled_pixmap.height()) // 2
                painter.drawPixmap(x, y, scaled_pixmap)
                painter.end()

                return centered_pixmap

            return scaled_pixmap

        except Exception as e:
            logger.error(f"Image scaling error: {e}")
            return pixmap.scaled(container_size, Qt.AspectRatioMode.KeepAspectRatio)

    def apply_fixed_size(self, width: int, height: int):
        """Apply fixed size with maximum enforcement and grid integration."""
        self._fixed_width = width
        self._fixed_height = height
        self._size_locked = True
        self._grid_managed = True

        # Apply multiple size constraints for absolute stability
        self.setFixedSize(width, height)
        self.setMinimumSize(width, height)
        self.setMaximumSize(width, height)

        # Ensure size policy is absolutely fixed
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        # Force immediate geometry update
        self.updateGeometry()

        # Update thumbnail container proportionally
        thumbnail_height = int(height * 0.6)  # 60% of card height
        if hasattr(self, "thumbnail_label") and self.thumbnail_label:
            self.thumbnail_label.setFixedHeight(thumbnail_height - 20)

        logger.debug(f"Applied fixed size {width}x{height} to {self.sequence.name}")

    def resizeEvent(self, event):
        """Override resize event with strong consistency protection."""
        import time

        # Initialize tracking
        if not hasattr(self, "_card_resize_count"):
            self._card_resize_count = 0
            self._last_resize_time = 0

        current_time = time.time()

        # Reset counter after 1 second
        if current_time - self._last_resize_time > 1.0:
            self._card_resize_count = 0

        self._card_resize_count += 1
        self._last_resize_time = current_time

        old_size = event.oldSize()
        new_size = event.size()

        # If we're grid-managed and size is locked, enforce it strictly
        if self._grid_managed and self._size_locked:
            expected_size = QSize(self._fixed_width, self._fixed_height)

            # Only allow resize if it matches our expected size
            if new_size != expected_size:
                logger.debug(
                    f"Preventing unwanted resize on {self.sequence.name}: "
                    f"{new_size.width()}x{new_size.height()} "
                    f"!= expected {expected_size.width()}x{expected_size.height()}"
                )

                # Force back to correct size
                self.setFixedSize(expected_size)
                return

        # Throttle excessive resize events
        if self._card_resize_count > self._max_resize_events_per_second:
            # Skip if size didn't actually change
            if old_size == new_size:
                return

        # Log significant resize events
        if (
            self._card_resize_count <= 2
            or abs(new_size.width() - self._fixed_width) > 5
            or abs(new_size.height() - self._fixed_height) > 5
        ):

            logger.debug(
                f"Card resize #{self._card_resize_count} - {self.sequence.name}: "
                f"{old_size.width()}x{old_size.height()} -> "
                f"{new_size.width()}x{new_size.height()}"
            )

        super().resizeEvent(event)

    def set_loading_state(self, loading: bool):
        """Set the loading state."""
        if loading:
            self._current_state = self.STATE_LOADING
            self.thumbnail_label.setText("Loading...")
        else:
            self._current_state = self.STATE_NORMAL

    def set_error_state(self, error_message: str = "Error"):
        """Set the error state."""
        self._current_state = self.STATE_ERROR
        self.thumbnail_label.setText(error_message)
        self.thumbnail_label.setStyleSheet(
            """
            QLabel {
                color: #ff6b6b;
                background: rgba(255, 107, 107, 0.1);
            }
        """
        )

    def _toggle_favorite(self):
        """Toggle favorite status."""
        self._is_favorite = not self._is_favorite
        self.favorite_button.setText("♥" if self._is_favorite else "♡")

        if self._is_favorite:
            self.favorite_button.setStyleSheet(
                """
                QPushButton#favoriteButton {
                    color: #ff6b6b;
                    background: rgba(255, 107, 107, 0.2);
                    border: 1px solid rgba(255, 107, 107, 0.4);
                }
            """
            )
        else:
            self.favorite_button.setStyleSheet("")

        self.favorite_toggled.emit(self.sequence.id, self._is_favorite)

    def set_chunked_loading_manager(self, manager):
        """Set the chunked loading manager."""
        self._chunked_loading_manager = manager

    def mousePressEvent(self, event):
        """Handle mouse press events."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.sequence.id)
        elif event.button() == Qt.MouseButton.RightButton:
            self.context_menu_requested.emit(self.sequence.id, event.globalPosition())
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        """Handle mouse double click events."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit(self.sequence.id)
        super().mouseDoubleClickEvent(event)

    def sizeHint(self) -> QSize:
        """Provide consistent size hint."""
        return QSize(self._fixed_width, self._fixed_height)

    def minimumSizeHint(self) -> QSize:
        """Provide consistent minimum size hint."""
        return QSize(self._fixed_width, self._fixed_height)

    def get_sequence_id(self) -> str:
        """Get the sequence ID."""
        return self.sequence.id

    def is_grid_managed(self) -> bool:
        """Check if this card is managed by a consistent grid."""
        return self._grid_managed

    def is_size_locked(self) -> bool:
        """Check if size is locked."""
        return self._size_locked
