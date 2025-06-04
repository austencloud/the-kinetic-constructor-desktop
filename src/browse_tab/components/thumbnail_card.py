"""
Thumbnail Card Component - Clean Architecture Implementation.

Individual thumbnail widget with single responsibility for displaying sequence thumbnails.
Handles image display, hover effects, click handling, and caching integration.

Features:
- Width-first image scaling with aspect ratio preservation
- Progressive image loading with cache integration
- Hover effects with glassmorphism styling
- Click and double-click handling
- Loading states and error handling
- Performance optimized rendering

Performance Targets:
- <50ms widget creation
- <16ms hover response
- Cached image display for instant loading
- Smooth animations at 60fps
"""

import logging
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QSizePolicy,
)
from PyQt6.QtCore import pyqtSignal, QTimer, QElapsedTimer, QSize
from PyQt6.QtGui import QPixmap, QFont, QPainter, QBrush, QColor
from PyQt6.QtCore import Qt

from ..core.interfaces import SequenceModel, BrowseTabConfig

logger = logging.getLogger(__name__)


class ThumbnailCard(QWidget):
    """
    Individual thumbnail card widget for sequence display.

    Single Responsibility: Display individual sequence thumbnail with interactions

    Features:
    - Progressive image loading with cache integration
    - Width-first scaling with aspect ratio preservation
    - Hover effects with glassmorphism styling
    - Click and double-click handling
    - Loading and error states
    - Performance optimized rendering
    """

    # Signals for interaction
    clicked = pyqtSignal()
    double_clicked = pyqtSignal()
    favorite_toggled = pyqtSignal(bool)

    def __init__(
        self,
        sequence: SequenceModel,
        config: BrowseTabConfig = None,
        parent: QWidget = None,
    ):
        super().__init__(parent)

        self.sequence = sequence
        self.config = config or BrowseTabConfig()

        # State management
        self._is_loading = True
        self._has_error = False
        self._is_favorite = False
        self._is_hovered = False
        self._image_loaded = False

        # Performance tracking
        self._performance_timer = QElapsedTimer()
        self._hover_timer = QTimer()
        self._hover_timer.setSingleShot(True)
        self._hover_timer.timeout.connect(self._apply_hover_effect)

        # UI components
        self.image_label = None
        self.title_label = None
        self.info_label = None
        self.favorite_button = None
        self.loading_indicator = None

        # Cached pixmap for performance
        self._cached_pixmap = None
        self._target_size = QSize(280, 210)

        self._setup_ui()
        self._setup_styling()
        self._load_image()

        logger.debug(f"ThumbnailCard created for sequence: {sequence.name}")

    def _setup_ui(self):
        """Setup the thumbnail card UI layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # Image container
        self._create_image_container(layout)

        # Info container
        self._create_info_container(layout)

        # Set size policy
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setFixedSize(self._target_size)

    def _create_image_container(self, layout):
        """Create image display container."""
        image_container = QFrame()
        image_container.setFixedHeight(160)
        image_layout = QVBoxLayout(image_container)
        image_layout.setContentsMargins(0, 0, 0, 0)

        # Image label
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setScaledContents(False)  # We'll handle scaling manually
        self.image_label.setStyleSheet(
            """
            QLabel {
                background: rgba(255, 255, 255, 0.05);
                border-radius: 8px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
        """
        )

        # Loading indicator (initially visible)
        self.loading_indicator = QLabel("Loading...")
        self.loading_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_indicator.setStyleSheet("color: rgba(255, 255, 255, 0.7);")

        image_layout.addWidget(self.image_label)
        image_layout.addWidget(self.loading_indicator)

        layout.addWidget(image_container)

    def _create_info_container(self, layout):
        """Create info display container."""
        info_container = QWidget()
        info_layout = QHBoxLayout(info_container)
        info_layout.setContentsMargins(4, 0, 4, 0)
        info_layout.setSpacing(4)

        # Text info
        text_container = QWidget()
        text_layout = QVBoxLayout(text_container)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)

        # Title label
        self.title_label = QLabel(self.sequence.name or "Untitled")
        self.title_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: white;")
        self.title_label.setWordWrap(True)
        text_layout.addWidget(self.title_label)

        # Info label (difficulty, length, etc.)
        info_text = self._format_sequence_info()
        self.info_label = QLabel(info_text)
        self.info_label.setFont(QFont("Segoe UI", 8))
        self.info_label.setStyleSheet("color: rgba(255, 255, 255, 0.7);")
        text_layout.addWidget(self.info_label)

        info_layout.addWidget(text_container, 1)

        # Favorite button
        self.favorite_button = QPushButton("♡")
        self.favorite_button.setFixedSize(24, 24)
        self.favorite_button.setCheckable(True)
        self.favorite_button.setStyleSheet(
            """
            QPushButton {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 12px;
                color: white;
                font-size: 12px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.2);
            }
            QPushButton:checked {
                background: rgba(255, 100, 100, 0.3);
                color: #ff6b6b;
            }
        """
        )
        self.favorite_button.clicked.connect(self._toggle_favorite)
        info_layout.addWidget(self.favorite_button)

        layout.addWidget(info_container)

    def _format_sequence_info(self) -> str:
        """Format sequence information for display."""
        info_parts = []

        # Add difficulty if available
        if hasattr(self.sequence, "difficulty") and self.sequence.difficulty:
            info_parts.append(f"Difficulty: {self.sequence.difficulty}")

        # Add length if available
        if hasattr(self.sequence, "length") and self.sequence.length:
            info_parts.append(f"Length: {self.sequence.length}")

        # Add author if available
        if hasattr(self.sequence, "author") and self.sequence.author:
            info_parts.append(f"By: {self.sequence.author}")

        return " • ".join(info_parts) if info_parts else "No additional info"

    def _setup_styling(self):
        """Apply glassmorphism styling to the card."""
        try:
            self.setStyleSheet(
                """
                ThumbnailCard {
                    background: rgba(255, 255, 255, 0.08);
                    border-radius: 12px;
                    border: 1px solid rgba(255, 255, 255, 0.15);
                }
                ThumbnailCard:hover {
                    background: rgba(255, 255, 255, 0.12);
                    border-color: rgba(255, 255, 255, 0.25);
                }
            """
            )

            logger.debug("Thumbnail card styling applied")

        except Exception as e:
            logger.warning(f"Failed to apply thumbnail card styling: {e}")

    def _load_image(self):
        """Load thumbnail image with async cache integration."""
        self._performance_timer.start()

        try:
            # Check if sequence has thumbnail paths
            if not hasattr(self.sequence, "thumbnails") or not self.sequence.thumbnails:
                self._show_no_image_state()
                return

            thumbnail_path = self.sequence.thumbnails[0]

            # Try to get from cache first (if cache service is available)
            cached_pixmap = self._get_cached_image(thumbnail_path)
            if cached_pixmap and not cached_pixmap.isNull():
                self._display_image(cached_pixmap)
                elapsed = self._performance_timer.elapsed()
                logger.debug(
                    f"Cached image loaded in {elapsed}ms for {self.sequence.name}"
                )
                return

            # Load from disk asynchronously to avoid blocking UI
            QTimer.singleShot(0, lambda: self._load_image_from_disk(thumbnail_path))

        except Exception as e:
            logger.error(f"Failed to load image for {self.sequence.name}: {e}")
            self._show_error_state()

    def _get_cached_image(self, image_path: str) -> Optional[QPixmap]:
        """Get image from cache if available."""
        try:
            # Try to get cache service from parent or config
            cache_service = getattr(self.parent(), "cache_service", None)
            if cache_service and hasattr(cache_service, "get_image_sync"):
                return cache_service.get_image_sync(image_path)

            return None

        except Exception as e:
            logger.debug(f"Cache access failed: {e}")
            return None

    def _load_image_from_disk(self, image_path: str):
        """Load image from disk with progressive display."""
        try:
            # Load image
            pixmap = QPixmap(image_path)
            if pixmap.isNull():
                self._show_error_state()
                return

            # Scale image using width-first scaling
            scaled_pixmap = self._scale_image_width_first(pixmap)
            self._display_image(scaled_pixmap)

            elapsed = self._performance_timer.elapsed()
            logger.debug(
                f"Image loaded from disk in {elapsed}ms for {self.sequence.name}"
            )

            # Performance target: <50ms image loading
            if elapsed > 50:
                logger.warning(f"Image loading exceeded 50ms target: {elapsed}ms")

        except Exception as e:
            logger.error(f"Failed to load image from disk: {e}")
            self._show_error_state()

    def _scale_image_width_first(self, pixmap: QPixmap) -> QPixmap:
        """Scale image using width-first scaling with aspect ratio preservation."""
        if pixmap.isNull():
            return pixmap

        # Calculate target size (maintain aspect ratio)
        image_size = pixmap.size()
        target_width = self.image_label.width() - 16  # Account for margins
        target_height = self.image_label.height() - 16

        # Width-first scaling
        scale_factor = target_width / image_size.width()
        new_height = int(image_size.height() * scale_factor)

        # Ensure height doesn't exceed target
        if new_height > target_height:
            scale_factor = target_height / image_size.height()
            target_width = int(image_size.width() * scale_factor)
            new_height = target_height
        else:
            target_width = int(target_width)

        # Scale the pixmap using smooth transformation for quality
        scaled_pixmap = pixmap.scaled(
            target_width,
            new_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,  # Better quality than FastTransformation
        )

        return scaled_pixmap

    def _display_image(self, pixmap: QPixmap):
        """Display the loaded image."""
        self._cached_pixmap = pixmap
        self.image_label.setPixmap(pixmap)
        self.loading_indicator.hide()
        self._is_loading = False
        self._image_loaded = True
        self._has_error = False

    def _show_no_image_state(self):
        """Show state when no image is available."""
        self.loading_indicator.setText("No image available")
        self.loading_indicator.setStyleSheet("color: rgba(255, 255, 255, 0.5);")
        self._is_loading = False
        self._has_error = False

    def _show_error_state(self):
        """Show error state when image loading fails."""
        self.loading_indicator.setText("Failed to load")
        self.loading_indicator.setStyleSheet("color: rgba(255, 100, 100, 0.7);")
        self._is_loading = False
        self._has_error = True

    def _toggle_favorite(self):
        """Toggle favorite status."""
        self._is_favorite = not self._is_favorite
        self.favorite_button.setText("♥" if self._is_favorite else "♡")
        self.favorite_button.setChecked(self._is_favorite)
        self.favorite_toggled.emit(self._is_favorite)

        logger.debug(f"Favorite toggled for {self.sequence.name}: {self._is_favorite}")

    def _apply_hover_effect(self):
        """Apply hover effect with performance optimization."""
        if self._is_hovered:
            # Add subtle glow effect
            self.setStyleSheet(
                self.styleSheet()
                + """
                ThumbnailCard {
                    background: rgba(255, 255, 255, 0.15);
                    border-color: rgba(255, 255, 255, 0.3);
                }
            """
            )

    # Event handlers
    def enterEvent(self, event):
        """Handle mouse enter for hover effects."""
        super().enterEvent(event)
        self._is_hovered = True

        # Debounce hover effect for performance
        self._hover_timer.stop()
        self._hover_timer.start(50)  # 50ms delay for smooth hover

    def leaveEvent(self, event):
        """Handle mouse leave for hover effects."""
        super().leaveEvent(event)
        self._is_hovered = False
        self._hover_timer.stop()

        # Remove hover styling
        self._setup_styling()

    def mousePressEvent(self, event):
        """Handle mouse press events."""
        super().mousePressEvent(event)
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()

    def mouseDoubleClickEvent(self, event):
        """Handle mouse double click events."""
        super().mouseDoubleClickEvent(event)
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit()

    # Public interface methods
    def set_sequence(self, sequence: SequenceModel):
        """Update the sequence displayed by this card."""
        self.sequence = sequence

        # Update title
        self.title_label.setText(sequence.name or "Untitled")

        # Update info
        info_text = self._format_sequence_info()
        self.info_label.setText(info_text)

        # Reload image
        self._is_loading = True
        self._image_loaded = False
        self.loading_indicator.show()
        self._load_image()

    def get_sequence(self) -> SequenceModel:
        """Get the sequence displayed by this card."""
        return self.sequence

    def is_loading(self) -> bool:
        """Check if the card is currently loading."""
        return self._is_loading

    def has_error(self) -> bool:
        """Check if the card has an error state."""
        return self._has_error

    def is_image_loaded(self) -> bool:
        """Check if the image is loaded."""
        return self._image_loaded

    def refresh_image(self):
        """Refresh the thumbnail image."""
        self._load_image()

    def cleanup(self):
        """Cleanup resources."""
        try:
            self._hover_timer.stop()
            if self._cached_pixmap:
                self._cached_pixmap = None
            logger.debug(f"ThumbnailCard cleanup completed for {self.sequence.name}")
        except Exception as e:
            logger.error(f"ThumbnailCard cleanup failed: {e}")
