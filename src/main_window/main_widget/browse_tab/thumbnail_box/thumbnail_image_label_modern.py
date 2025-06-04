"""
Thumbnail Image Label - Clean, component-based thumbnail display.

This implementation uses focused components following SRP:
- ImageLoadingManager: Handles async loading and caching
- VisualStateManager: Manages states and transitions
- LazyLoadingCoordinator: Interfaces with lazy loading system

Features:
- Lazy loading with visual feedback
- Smooth 250ms fade transitions
- Glassmorphism loading indicators
- High-quality image processing
- Backward compatibility with existing API
"""

import logging
from typing import TYPE_CHECKING, Optional
from PyQt6.QtCore import QSize, QTimer, Qt
from PyQt6.QtGui import QPixmap, QCursor, QMouseEvent, QColor, QPainter
from PyQt6.QtWidgets import QLabel

from data.constants import GOLD, BLUE
from main_window.main_widget.metadata_extractor import MetaDataExtractor

# Import focused components
from .components import (
    ImageLoadingManager,
    VisualStateManager,
    VisualState,
    LazyLoadingCoordinator,
)

if TYPE_CHECKING:
    from .thumbnail_box import ThumbnailBox
    from ..lazy_loading.browse_tab_lazy_loader import BrowseTabLazyLoader


class ImageProcessor:
    """
    Simple, consistent image processor using Qt SmoothTransformation.

    Provides high-quality image scaling for all thumbnails and exports
    using Qt's built-in SmoothTransformation for consistent, sharp results.
    """

    @staticmethod
    def process_image(source_path: str, target_size: QSize) -> QPixmap:
        """
        Process image using Qt SmoothTransformation for consistent quality.

        Args:
            source_path: Path to source image
            target_size: Target size for thumbnail

        Returns:
            High-quality QPixmap using SmoothTransformation
        """
        return ImageProcessor._process_with_qt(source_path, target_size)

    @staticmethod
    def _process_with_qt(source_path: str, target_size: QSize) -> QPixmap:
        """
        Fallback processing using Qt when PIL is not available.
        Enhanced Qt-only processing with multi-step scaling.
        """
        try:
            # Load original image
            original_pixmap = QPixmap(source_path)
            if original_pixmap.isNull():
                logging.error(f"Failed to load image: {source_path}")
                return ImageProcessor._create_error_pixmap(target_size)

            # Calculate target dimensions maintaining aspect ratio
            original_size = original_pixmap.size()
            aspect_ratio = original_size.width() / original_size.height()

            if target_size.width() / target_size.height() > aspect_ratio:
                new_h = target_size.height()
                new_w = int(target_size.height() * aspect_ratio)
            else:
                new_w = target_size.width()
                new_h = int(target_size.width() / aspect_ratio)

            target_w, target_h = new_w, new_h
            scale_factor = min(
                target_w / original_size.width(), target_h / original_size.height()
            )

            # Enhanced multi-step scaling with Qt
            if scale_factor < 0.6:  # Lower threshold than before
                # Multi-step scaling
                intermediate_factor = 0.75 if scale_factor < 0.4 else 0.8
                intermediate_w = int(original_size.width() * intermediate_factor)
                intermediate_h = int(original_size.height() * intermediate_factor)

                # Step 1: Scale to intermediate size
                intermediate_pixmap = original_pixmap.scaled(
                    intermediate_w,
                    intermediate_h,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )

                # Step 2: Scale to final size
                final_pixmap = intermediate_pixmap.scaled(
                    target_w,
                    target_h,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            else:
                # Single-step high-quality scaling
                final_pixmap = original_pixmap.scaled(
                    target_w,
                    target_h,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )

            return final_pixmap

        except Exception as e:
            logging.error(f"Qt fallback processing failed for {source_path}: {e}")
            return ImageProcessor._create_error_pixmap(target_size)

    @staticmethod
    def _create_error_pixmap(size: QSize) -> QPixmap:
        """Create error pixmap when image processing fails."""
        pixmap = QPixmap(size)
        pixmap.fill(QColor(200, 200, 200))

        painter = QPainter(pixmap)
        painter.setPen(QColor(100, 100, 100))
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "Image\nError")
        painter.end()

        return pixmap


class ThumbnailImageLabelModern(QLabel):
    """
    Thumbnail image label with component-based architecture.

    This class maintains the same external API as the original ThumbnailImageLabel
    while using focused components internally for better maintainability.
    """

    # Constants for backward compatibility
    BORDER_WIDTH_RATIO = 0.01
    SEQUENCE_VIEWER_BORDER_SCALE = 0.8

    def __init__(self, thumbnail_box: "ThumbnailBox"):
        super().__init__()

        # Core attributes
        self.thumbnail_box = thumbnail_box
        self.metadata_extractor = MetaDataExtractor()
        self.selected = False
        self.current_path: Optional[str] = None

        # Border attributes for compatibility
        self._border_width = 4
        self._border_color: Optional[str] = None

        # Initialize image processor
        self.image_processor = ImageProcessor()

        # Initialize focused components
        self._image_loading_manager = ImageLoadingManager(self.image_processor)
        self._visual_state_manager = VisualStateManager(self)
        self._lazy_loading_coordinator = LazyLoadingCoordinator(self)

        # Connect component signals
        self._connect_component_signals()

        # Loading animation timer
        self._animation_timer = QTimer()
        self._animation_timer.timeout.connect(self._update_loading_animation)

        # Setup UI
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setObjectName("thumbnail_image_label")

        # Set size policy to expand and fill available space
        from PyQt6.QtWidgets import QSizePolicy

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Set minimum size to ensure proper display
        self.setMinimumSize(180, 135)

        # Initialize with placeholder
        self._show_initial_placeholder()

        logging.debug(
            f"🚀 ModernThumbnailImageLabel initialized with lazy loading support"
        )

    def _connect_component_signals(self) -> None:
        """Connect signals between components."""
        # Image loading manager signals
        self._image_loading_manager.image_loaded.connect(self._on_image_loaded)
        self._image_loading_manager.loading_started.connect(self._on_loading_started)
        self._image_loading_manager.loading_failed.connect(self._on_loading_failed)

        # Visual state manager signals
        self._visual_state_manager.transition_started.connect(
            self._on_transition_started
        )
        self._visual_state_manager.transition_completed.connect(
            self._on_transition_completed
        )

        # Lazy loading coordinator signals
        self._lazy_loading_coordinator.lazy_load_requested.connect(
            self._on_lazy_load_requested
        )
        self._lazy_loading_coordinator.lazy_load_completed.connect(
            self._on_lazy_load_completed
        )
        self._lazy_loading_coordinator.lazy_load_failed.connect(
            self._on_lazy_load_failed
        )
        self._lazy_loading_coordinator.fallback_triggered.connect(
            self._on_fallback_triggered
        )

    # Public API methods (backward compatibility)

    def update_thumbnail(self, index: int) -> None:
        """Update the displayed image synchronously (backward compatibility)."""
        thumbnails = self.thumbnail_box.state.thumbnails
        if not thumbnails or not (0 <= index < len(thumbnails)):
            return

        path = thumbnails[index]
        target_size = self._calculate_available_space()

        # Load synchronously
        pixmap = self._image_loading_manager.load_image_sync(path, target_size)
        if pixmap:
            self.current_path = path
            self._visual_state_manager.show_loaded_image(pixmap)

    def update_thumbnail_async(self, index: int) -> None:
        """Update the displayed image asynchronously with lazy loading support."""
        thumbnails = self.thumbnail_box.state.thumbnails
        if not thumbnails or not (0 <= index < len(thumbnails)):
            return

        path = thumbnails[index]

        # CACHE FIX: Use standard thumbnail size for caching consistency
        # This ensures all thumbnails use the same cache key regardless of container size
        standard_thumbnail_size = QSize(200, 150)  # Standard size for caching
        display_size = self._calculate_available_space()  # Actual display size

        # Store both sizes for proper handling
        self._standard_size = standard_thumbnail_size
        self._display_size = display_size

        # PERFORMANCE FIX: Skip lazy loading for modern components to prevent timeouts
        # Use direct async loading instead for better performance and reliability
        # if self._lazy_loading_coordinator.is_lazy_loading_enabled:
        #     success = self._lazy_loading_coordinator.request_image_load(
        #         path, standard_thumbnail_size, self._on_image_loaded
        #     )
        #     if success:
        #         return

        # Use standard thumbnail size for loading/caching, then scale to display size
        self._image_loading_manager.load_image_async(
            path, standard_thumbnail_size, index
        )

    def enable_lazy_loading(self, lazy_loader: "BrowseTabLazyLoader") -> None:
        """Enable lazy loading for this thumbnail."""
        self._lazy_loading_coordinator.enable_lazy_loading(lazy_loader)
        logging.debug(f"✅ Lazy loading enabled for thumbnail")

    def disable_lazy_loading(self) -> None:
        """Disable lazy loading for this thumbnail."""
        self._lazy_loading_coordinator.disable_lazy_loading()
        logging.debug("Lazy loading disabled for thumbnail")

    # Component signal handlers

    def _on_image_loaded(self, image_path: str, pixmap: QPixmap) -> None:
        """Handle image loaded from any source with display size scaling."""
        self.current_path = image_path

        # CACHE FIX: Scale from standard thumbnail size to actual display size
        if hasattr(self, "_display_size") and self._display_size and pixmap:
            # Scale the cached thumbnail to the actual display size
            scaled_pixmap = pixmap.scaled(
                self._display_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            display_pixmap = scaled_pixmap
            logging.debug(
                f"🔄 Scaled thumbnail from {pixmap.size().width()}x{pixmap.size().height()} "
                f"to {scaled_pixmap.size().width()}x{scaled_pixmap.size().height()} for display"
            )
        else:
            display_pixmap = pixmap

        self._visual_state_manager.show_loaded_image(display_pixmap)

    def _on_loading_started(self, image_path: str) -> None:
        """Handle loading started."""
        logging.debug(f"🔄 Loading started for: {image_path}")
        target_size = self._calculate_available_space()
        self._visual_state_manager.show_loading(target_size)

        # Start loading animation
        self._animation_timer.start(100)  # Update every 100ms

    def _on_loading_failed(self, image_path: str, error: str) -> None:
        """Handle loading failure."""
        logging.warning(f"Image loading failed for {image_path}: {error}")
        target_size = self._calculate_available_space()
        self._visual_state_manager.show_error(target_size)

        # Stop loading animation
        self._animation_timer.stop()

    def _on_transition_started(self, state: str) -> None:
        """Handle visual transition started."""
        if state == VisualState.LOADING:
            self._animation_timer.start(100)
        elif state in [VisualState.LOADED, VisualState.ERROR]:
            self._animation_timer.stop()

    def _on_transition_completed(self, state: str) -> None:
        """Handle visual transition completed."""
        logging.debug(f"Transition completed to state: {state}")

    def _on_lazy_load_requested(self, image_path: str, target_size: QSize) -> None:
        """Handle lazy load request."""
        logging.debug(f"🎯 Lazy load requested for: {image_path}")
        self._visual_state_manager.show_loading(target_size)

    def _on_lazy_load_completed(self, image_path: str, pixmap: QPixmap) -> None:
        """Handle lazy load completion."""
        self._on_image_loaded(image_path, pixmap)

    def _on_lazy_load_failed(self, image_path: str, error: str) -> None:
        """Handle lazy load failure."""
        self._on_loading_failed(image_path, error)

    def _on_fallback_triggered(self, image_path: str) -> None:
        """Handle fallback to regular loading."""
        logging.debug(f"Fallback triggered for: {image_path}")
        # Use standard thumbnail size for consistency
        standard_thumbnail_size = QSize(200, 150)
        self._image_loading_manager.load_image_async(
            image_path, standard_thumbnail_size
        )

    def _update_loading_animation(self) -> None:
        """Update loading animation frame."""
        self._visual_state_manager.update_loading_animation()

    def _show_initial_placeholder(self) -> None:
        """Show initial placeholder state."""
        target_size = self._calculate_available_space()
        self._visual_state_manager.show_placeholder(target_size)
        logging.debug(
            f"📱 Showing initial placeholder for thumbnail (size: {target_size.width()}x{target_size.height()})"
        )

    # Size calculation methods (from original implementation)

    def _calculate_available_space(self) -> QSize:
        """Calculate available space for the thumbnail."""
        if self.is_in_sequence_viewer:
            return self._calculate_sequence_viewer_size()
        else:
            return self._calculate_normal_view_size()

    def _calculate_normal_view_size(self) -> QSize:
        """Calculate size for normal browse view."""
        scroll_widget = self.thumbnail_box.sequence_picker.scroll_widget
        scroll_widget_width = scroll_widget.width()

        # Account for scrollbar and margins
        scrollbar_width = scroll_widget.calculate_scrollbar_width()
        total_margins = (3 * self.thumbnail_box.margin * 2) + 5
        usable_width = scroll_widget_width - scrollbar_width - total_margins

        # Calculate thumbnail width (3 columns)
        thumbnail_width = max(200, int(usable_width // 3))
        available_width = max(180, int(thumbnail_width - 8))

        # Calculate height based on aspect ratio (default 4:3)
        aspect_ratio = 4 / 3
        available_height = max(135, int(available_width / aspect_ratio))

        return QSize(available_width, available_height)

    def _calculate_sequence_viewer_size(self) -> QSize:
        """Calculate size for sequence viewer mode."""
        try:
            # Check if sequence_viewer exists and is accessible
            if (
                hasattr(self.thumbnail_box, "browse_tab")
                and hasattr(self.thumbnail_box.browse_tab, "sequence_viewer")
                and self.thumbnail_box.browse_tab.sequence_viewer is not None
            ):

                sequence_viewer = self.thumbnail_box.browse_tab.sequence_viewer
                available_width = max(400, int(sequence_viewer.width() * 0.8))
                available_height = max(300, int(sequence_viewer.height() * 0.65))
            else:
                # Fallback when sequence_viewer is not yet available
                available_width = 500
                available_height = 400

        except (AttributeError, TypeError):
            # Final fallback
            available_width = 500
            available_height = 400

        return QSize(available_width, available_height)

    # Properties for backward compatibility

    @property
    def border_width(self) -> int:
        """Get border width."""
        return self._border_width

    @property
    def is_in_sequence_viewer(self) -> bool:
        """Check if in sequence viewer mode."""
        try:
            return getattr(self.thumbnail_box, "in_sequence_viewer", False)
        except AttributeError:
            return False

    @property
    def aspect_ratio(self) -> float:
        """Get aspect ratio (default to 4:3 if no image loaded)."""
        return 4 / 3  # Default aspect ratio

    # Event handling

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press events."""
        if not self.is_in_sequence_viewer:
            self.thumbnail_box.browse_tab.selection_handler.on_thumbnail_clicked(self)

    # Utility methods

    def get_loading_stats(self) -> dict:
        """Get comprehensive loading statistics."""
        return {
            "current_path": self.current_path,
            "visual_state": self._visual_state_manager.get_current_state(),
            "is_animating": self._visual_state_manager.is_animating(),
            "image_loading": self._image_loading_manager.get_cache_stats(),
            "lazy_loading": self._lazy_loading_coordinator.get_loading_stats(),
        }

    def force_reload(self) -> None:
        """Force reload the current image."""
        if self.current_path:
            # Use standard thumbnail size for consistency
            standard_thumbnail_size = QSize(200, 150)
            self._display_size = (
                self._calculate_available_space()
            )  # Update display size
            self._image_loading_manager.load_image_async(
                self.current_path, standard_thumbnail_size
            )

    def set_selected(self, selected: bool) -> None:
        """Set the selection state of this thumbnail (backward compatibility)."""
        self.selected = selected
        # Update visual appearance based on selection state
        if selected:
            self.setStyleSheet("border: 3px solid #4A90E2;")  # Blue selection border
        else:
            self.setStyleSheet("")  # Remove selection styling
