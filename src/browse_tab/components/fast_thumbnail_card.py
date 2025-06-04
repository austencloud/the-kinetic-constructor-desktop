"""
Fast Thumbnail Card Component - High-Performance Implementation.

Optimized thumbnail widget designed for 120fps performance with minimal overhead.
Uses pre-processed data and deferred image loading for instant UI creation.

Performance Features:
- Pre-processed widget data (no computation during construction)
- Deferred image loading (structure first, content later)
- Minimal UI operations during initialization
- Optimized for batch creation in parallel workers
- <5ms widget creation target

Performance Targets:
- <5ms widget creation (vs 36ms current)
- <50ms image loading (async)
- Zero blocking operations during construction
- Instant UI structure display
"""

import logging
from typing import Dict, Optional
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
)
from PyQt6.QtCore import pyqtSignal, QTimer, QSize, Qt
from PyQt6.QtGui import QPixmap

from ..core.interfaces import BrowseTabConfig

logger = logging.getLogger(__name__)


class FastThumbnailCard(QWidget):
    """
    High-performance thumbnail card optimized for parallel creation.

    Key Optimizations:
    - Uses pre-processed widget data (no computation during __init__)
    - Deferred image loading (async after widget is visible)
    - Minimal UI setup during construction
    - Optimized for 120fps batch creation
    """

    # Signals for interaction
    clicked = pyqtSignal()
    double_clicked = pyqtSignal()
    favorite_toggled = pyqtSignal(bool)

    def __init__(
        self, widget_data: Dict, config: BrowseTabConfig = None, parent: QWidget = None
    ):
        super().__init__(parent)

        # Store pre-processed data (no computation needed)
        self.widget_data = widget_data
        self.config = config or BrowseTabConfig()
        self.sequence = widget_data["sequence"]

        # State management
        self._is_loading = True
        self._has_error = False
        self._is_favorite = False
        self._image_loaded = False
        self._image_timer = None

        # UI components (will be created in setup)
        self.image_label = None
        self.title_label = None
        self.info_label = None
        self.favorite_button = None
        self.loading_indicator = None

        # Performance optimization: minimal setup during construction
        self._target_size = QSize(280, 210)

        # Fast UI setup (structure only, no expensive operations)
        self._setup_ui_structure()
        self._apply_fast_styling()

        # Defer image loading until after widget is shown
        QTimer.singleShot(0, self._load_image_deferred)

        logger.debug(f"FastThumbnailCard created for: {widget_data['title']}")

    def _setup_ui_structure(self):
        """Setup UI structure only (no expensive operations)."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # Image container (structure only)
        self._create_image_container_fast(layout)

        # Info container (using pre-processed data)
        self._create_info_container_fast(layout)

        # Set size policy to allow vertical expansion while maintaining fixed width
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        self.setFixedWidth(self._target_size.width())
        self.setMinimumHeight(self._target_size.height())
        self.setMaximumHeight(
            self._target_size.height() + 50
        )  # Allow expansion for overflow

    def _create_image_container_fast(self, layout):
        """Create image container with minimal operations."""
        # Image label with dynamic height based on aspect ratio
        self.image_label = QLabel()
        # Calculate image height based on card width and aspect ratio
        image_height = self._calculate_image_height()
        # Use setMinimumHeight instead of setFixedHeight to allow expansion
        self.image_label.setMinimumHeight(image_height)
        self.image_label.setMaximumHeight(
            image_height + 50
        )  # Allow some expansion for overflow
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setScaledContents(False)

        # Loading indicator (initially visible)
        self.loading_indicator = QLabel("Loading...")
        self.loading_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self.image_label)
        layout.addWidget(self.loading_indicator)

    def _create_info_container_fast(self, layout):
        """Create favorites button overlay - REDESIGNED to remove separate info sections."""
        # REDESIGN: Remove all separate info sections (title, info labels)
        # Only create favorites button as overlay on the image container
        # Note: layout parameter kept for interface compatibility but not used

        # Favorite button overlay (positioned over image container)
        self.favorite_button = QPushButton("♡")
        self.favorite_button.setFixedSize(24, 24)
        self.favorite_button.setCheckable(True)
        self.favorite_button.clicked.connect(self._toggle_favorite)
        self.favorite_button.setParent(
            self.image_label
        )  # Make it a child of image label for overlay

        # Apply glassmorphism styling to favorites button
        self.favorite_button.setStyleSheet(
            """
            QPushButton {
                background: rgba(255, 255, 255, 0.15);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 12px;
                color: white;
                font-size: 12px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.25);
                border: 1px solid rgba(255, 255, 255, 0.4);
            }
            QPushButton:checked {
                background: rgba(255, 100, 100, 0.4);
                border: 1px solid rgba(255, 100, 100, 0.6);
                color: #ff6b6b;
            }
        """
        )

        # Position favorites button in top-right corner (will be positioned in resizeEvent)
        # Note: No info container added to layout - only the image with overlay button

    def _calculate_image_height(self) -> int:
        """Calculate optimal image height using efficient estimation."""
        try:
            # Use sequence length as a proxy for aspect ratio (same logic as grid_view)
            sequence = self.widget_data.get("sequence")
            if sequence and hasattr(sequence, "length") and sequence.length:
                length = sequence.length
                if length <= 4:
                    # Short sequences: more square (1:1 ratio)
                    aspect_ratio = 1.0
                elif length <= 8:
                    # Medium sequences: slightly wider (4:3 ratio)
                    aspect_ratio = 0.75
                else:
                    # Long sequences: wider (16:9 ratio)
                    aspect_ratio = 0.56

                # Width-first scaling: use full card width minus margins
                available_width = self._target_size.width() - 16  # Account for margins
                calculated_height = int(available_width * aspect_ratio)
                # Clamp to reasonable bounds
                return max(120, min(calculated_height, 280))

            # Fallback: use default aspect ratio (4:3)
            available_width = self._target_size.width() - 16
            default_height = int(available_width * 0.75)
            return max(120, min(default_height, 240))

        except Exception as e:
            logger.debug(f"Failed to calculate image height: {e}")
            return 160  # Fallback to original fixed height

    def _apply_fast_styling(self):
        """Apply styling with minimal overhead."""
        try:
            self.setStyleSheet(
                """
                FastThumbnailCard {
                    background: rgba(255, 255, 255, 0.08);
                    border-radius: 12px;
                    border: 1px solid rgba(255, 255, 255, 0.15);
                }
                FastThumbnailCard:hover {
                    background: rgba(255, 255, 255, 0.12);
                    border-color: rgba(255, 255, 255, 0.25);
                }
            """
            )

            if self.image_label:
                self.image_label.setStyleSheet(
                    """
                    QLabel {
                        background: rgba(255, 255, 255, 0.05);
                        border-radius: 8px;
                        border: 1px solid rgba(255, 255, 255, 0.1);
                    }
                """
                )

            if self.loading_indicator:
                self.loading_indicator.setStyleSheet("color: rgba(255, 255, 255, 0.7);")

            if self.title_label:
                self.title_label.setStyleSheet("color: white;")

            if self.info_label:
                self.info_label.setStyleSheet("color: rgba(255, 255, 255, 0.7);")

            if self.favorite_button:
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

        except Exception as e:
            logger.warning(f"Failed to apply fast styling: {e}")

    def _load_image_deferred(self):
        """Load image asynchronously after widget creation."""
        if not self.widget_data.get("thumbnail_path"):
            self._show_no_image_state()
            return

        # Use async image loading to avoid blocking UI
        # Store timer reference to prevent deletion issues
        self._image_timer = QTimer()
        self._image_timer.setSingleShot(True)
        self._image_timer.timeout.connect(
            lambda: self._load_image_async(self.widget_data["thumbnail_path"])
        )
        self._image_timer.start(10)

    def _load_image_async(self, image_path: str):
        """Load image asynchronously - SIMPLIFIED to load pre-generated professional images."""
        try:
            # Check if widget is still valid before proceeding
            if not self._is_widget_valid():
                return

            # Load image directly (images are now pre-generated with professional overlays)
            pixmap = QPixmap(image_path)
            if pixmap.isNull():
                if self._is_widget_valid():
                    self._show_error_state()
                return

            # Scale image efficiently
            scaled_pixmap = self._scale_image_fast(pixmap)
            if self._is_widget_valid():
                self._display_image(scaled_pixmap)

        except Exception as e:
            logger.error(f"Failed to load image {image_path}: {e}")
            if self._is_widget_valid():
                self._show_error_state()

    # NOTE: Professional rendering methods removed - images are now pre-generated
    # with professional overlays during dictionary image regeneration process

    def resizeEvent(self, event):
        """Handle resize events to position favorites button overlay."""
        super().resizeEvent(event)
        self._position_favorite_button()

    def _position_favorite_button(self):
        """Position the favorites button in the top-right corner of the image."""
        if (
            hasattr(self, "favorite_button")
            and self.favorite_button
            and self.image_label
        ):
            # Get image label size
            label_size = self.image_label.size()
            button_size = self.favorite_button.size()

            # Position in top-right corner with small margin
            x = label_size.width() - button_size.width() - 8
            y = 8

            self.favorite_button.move(x, y)
            self.favorite_button.raise_()  # Ensure it's on top

    def _is_widget_valid(self) -> bool:
        """Check if widget and its components are still valid."""
        try:
            # Check if the widget itself is still valid
            if (
                not self
                or not hasattr(self, "image_label")
                or not hasattr(self, "loading_indicator")
            ):
                return False

            # Check if the QLabel objects are still valid
            if not self.image_label or not self.loading_indicator:
                return False

            # Try to access a property to ensure the C++ object isn't deleted
            _ = self.image_label.width()
            _ = self.loading_indicator.text()

            return True
        except (RuntimeError, AttributeError):
            # Widget has been deleted or is invalid
            return False

    def _scale_image_fast(self, pixmap: QPixmap) -> QPixmap:
        """High-quality image scaling with width-first approach for 100% width usage."""
        if pixmap.isNull():
            return pixmap

        # Check if widget is still valid before accessing UI components
        if not self._is_widget_valid():
            return pixmap

        # Calculate target size using 100% width approach
        image_size = pixmap.size()
        target_width = self.image_label.width() - 16  # Account for margins

        # Width-first scaling: always use full width, calculate proportional height
        scale_factor = target_width / image_size.width()
        new_height = int(image_size.height() * scale_factor)

        # Check if image needs more height than container allows
        max_container_height = self.image_label.maximumHeight()
        if new_height > max_container_height:
            # If image is too tall, expand the image container
            self.image_label.setMaximumHeight(new_height + 10)
            # Also expand the parent card if needed
            current_card_height = self.height()
            needed_card_height = current_card_height + (
                new_height - max_container_height
            )
            self.setMaximumHeight(needed_card_height + 20)

        # Use the calculated dimensions (no height constraint for width-first scaling)
        final_width = target_width
        final_height = new_height

        # Scale the pixmap using smooth transformation for quality
        scaled_pixmap = pixmap.scaled(
            final_width,
            final_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,  # Better quality than FastTransformation
        )

        return scaled_pixmap

    def _display_image(self, pixmap: QPixmap):
        """Display the loaded image."""
        if not self._is_widget_valid():
            return
        self.image_label.setPixmap(pixmap)
        self.loading_indicator.hide()
        self._is_loading = False
        self._image_loaded = True
        self._has_error = False

        # Position favorites button after image is loaded
        self._position_favorite_button()

    def _show_no_image_state(self):
        """Show state when no image is available."""
        if not self._is_widget_valid():
            return
        self.loading_indicator.setText("No image available")
        self.loading_indicator.setStyleSheet("color: rgba(255, 255, 255, 0.5);")
        self._is_loading = False
        self._has_error = False

    def _show_error_state(self):
        """Show error state when image loading fails."""
        if not self._is_widget_valid():
            return
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

    # Event handlers (minimal overhead)
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

    # Public interface
    def get_sequence(self):
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

    def cleanup(self):
        """Clean up resources when widget is being destroyed."""
        if self._image_timer:
            self._image_timer.stop()
            self._image_timer.deleteLater()
            self._image_timer = None

    def closeEvent(self, event):
        """Handle widget close event."""
        self.cleanup()
        super().closeEvent(event)
