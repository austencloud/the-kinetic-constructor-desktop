from PyQt6.QtCore import Qt, QRect, QSize, QTimer
from PyQt6.QtGui import QPixmap, QCursor, QMouseEvent, QPainter, QColor, QPen, QImage
from PyQt6.QtWidgets import QLabel
from typing import TYPE_CHECKING, Optional, Final
import logging
import os
import hashlib
import json
from pathlib import Path

from data.constants import GOLD, BLUE
from main_window.main_widget.metadata_extractor import MetaDataExtractor

# Import the new coordinator and components
from .core.thumbnail_coordinator import ThumbnailCoordinator

if TYPE_CHECKING:
    from .thumbnail_box import ThumbnailBox


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


class ThumbnailImageLabel(QLabel):
    BORDER_WIDTH_RATIO: Final = 0.01
    SEQUENCE_VIEWER_BORDER_SCALE: Final = 0.8

    # Cache configuration
    CACHE_DIR = Path("browse_thumbnails")
    CACHE_METADATA_FILE = "cache_metadata.json"

    def __init__(self, thumbnail_box: "ThumbnailBox"):
        super().__init__()
        # Instance attributes
        self.thumbnail_box = thumbnail_box
        self.selected = False
        self.current_path: Optional[str] = None

        # Initialize thumbnail coordinator
        self.thumbnail_coordinator = ThumbnailCoordinator(thumbnail_box)

        # UI state attributes
        self._border_width = 4
        self._border_color: Optional[str] = None
        self._cached_available_size: Optional[QSize] = None

        # Legacy attributes for backward compatibility
        self.metadata_extractor = MetaDataExtractor()
        self.image_processor = ImageProcessor()
        self._pending_path: Optional[str] = None
        self._pending_index: Optional[int] = None
        self._needs_quality_enhancement = False
        self._cache_metadata = {}

        # Setup timers (now delegated to coordinator)
        self._load_timer = QTimer()
        self._load_timer.setSingleShot(True)
        self._load_timer.timeout.connect(self._load_pending_image)

        self._quality_timer = QTimer()
        self._quality_timer.setSingleShot(True)
        self._quality_timer.timeout.connect(self._enhance_image_quality)

        # Setup UI
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setObjectName("thumbnail_image_label")

    @property
    def border_width(self) -> int:
        return self._border_width

    @property
    def is_in_sequence_viewer(self) -> bool:
        return self.thumbnail_box.in_sequence_viewer

    @property
    def aspect_ratio(self) -> float:
        """Get aspect ratio of the original image (delegates to coordinator)."""
        return self.thumbnail_coordinator.get_aspect_ratio(self.current_path)

    @property
    def _original_pixmap(self) -> Optional[QPixmap]:
        """Legacy property for backward compatibility."""
        return self.thumbnail_coordinator.get_original_pixmap(self.current_path)

    def update_thumbnail(self, index: int) -> None:
        """Update the displayed image based on the given index (delegates to coordinator)."""
        result = self.thumbnail_coordinator.update_thumbnail_sync(self, index)
        if result:
            self.current_path = result["path"]
            self._cached_available_size = None

    def update_thumbnail_async(self, index: int) -> None:
        """Update the displayed image asynchronously (delegates to coordinator)."""
        result = self.thumbnail_coordinator.update_thumbnail_async(self, index)
        if result:
            self.current_path = result["path"]
            self._pending_path = result.get("pending_path")
            self._pending_index = result.get("pending_index")

            if result.get("start_timer"):
                self._load_timer.start(1)

    def _load_pending_image(self) -> None:
        """Load pending image (delegates to coordinator)."""
        result = self.thumbnail_coordinator.load_pending_image(
            self, self._pending_path, self._pending_index
        )
        if result:
            self.current_path = result["path"]
            self._cached_available_size = None
            # Clear pending state
            self._pending_path = None
            self._pending_index = None

    def _calculate_available_space(self) -> QSize:
        """Calculate available space (delegates to coordinator)."""
        if self._cached_available_size:
            return self._cached_available_size

        available_size = self.thumbnail_coordinator.calculate_available_space(self)
        self._cached_available_size = available_size
        return available_size

    def _calculate_normal_view_size_enhanced(self) -> QSize:
        """Enhanced calculation for maximum quality thumbnails."""
        scroll_widget = self.thumbnail_box.sequence_picker.scroll_widget
        scroll_widget_width = scroll_widget.width()

        # Account for scrollbar and margins
        scrollbar_width = scroll_widget.calculate_scrollbar_width()

        # ULTRA QUALITY: Maximize thumbnail size for crisp display
        total_margins = (3 * self.thumbnail_box.margin * 2) + 5
        usable_width = scroll_widget_width - scrollbar_width - total_margins

        # Calculate thumbnail width (3 columns)
        thumbnail_width = max(200, int(usable_width // 3))  # Increased from 150 to 200

        # ULTRA QUALITY: Use maximum available space (minimal padding)
        available_width = int(thumbnail_width - 8)  # Minimal padding
        available_width = max(
            180, available_width
        )  # Increased from 140 to 180 for better quality

        # Calculate height based on aspect ratio
        available_height = int(available_width / self.aspect_ratio)

        # ULTRA QUALITY: Ensure minimum size for crisp display
        available_height = max(135, available_height)  # Increased from 100 to 135

        return QSize(available_width, available_height)

    def _calculate_sequence_viewer_size(self) -> QSize:
        """Calculate available space in sequence viewer mode."""
        sequence_viewer = self.thumbnail_box.browse_tab.sequence_viewer

        try:
            available_width = int(sequence_viewer.width() * 0.95)
            available_height = int(sequence_viewer.height() * 0.65)

            # ULTRA QUALITY: Higher minimums for sequence viewer
            available_width = max(400, available_width)
            available_height = max(300, available_height)

        except (AttributeError, TypeError):
            available_width = 500  # Higher fallback
            available_height = 400

        return QSize(available_width, available_height)

    def _resize_pixmap_to_ultra_quality(self) -> None:
        """Resize pixmap using ultra quality processing (delegates to coordinator)."""
        if not self.current_path:
            return

        result = self.thumbnail_coordinator.process_ultra_quality_thumbnail(
            self, self.current_path
        )

        if result and result.get("pixmap"):
            available_size = result["available_size"]
            pixmap = result["pixmap"]

            self.setFixedSize(available_size)
            self.setPixmap(pixmap)

            if result.get("from_cache"):
                logging.debug(
                    f"✅ Loaded cached thumbnail: {os.path.basename(self.current_path)}"
                )
            else:
                logging.debug(
                    f"✅ High-quality thumbnail processed: {os.path.basename(self.current_path)}"
                )
        else:
            # Fallback to legacy processing
            self._resize_pixmap_to_fit_smooth()

    # Removed _get_quality_settings - now always using maximum quality

    def _resize_pixmap_to_fit_smooth(self) -> None:
        """Enhanced smooth resizing with improved multi-step scaling."""
        if not self._original_pixmap:
            return

        available_size = self._calculate_available_space()
        scaled_size = self._calculate_scaled_pixmap_size(available_size)

        # Enhanced multi-step scaling for better quality
        scaled_pixmap = self._create_enhanced_scaled_pixmap(scaled_size)

        # CRITICAL: Ensure pixmap is not null before proceeding
        if scaled_pixmap.isNull():
            logging.warning(f"Failed to create scaled pixmap for {self.current_path}")
            return

        self.setFixedSize(available_size)
        self.setPixmap(scaled_pixmap)

        # Cache system removed - no longer needed
        logging.debug(
            f"✅ HIGH-QUALITY thumbnail processed: {os.path.basename(self.current_path)}"
        )

    def _calculate_scaled_pixmap_size(self, available_size: QSize) -> QSize:
        """Calculate the optimal size for the pixmap while maintaining aspect ratio."""
        if not self._original_pixmap:
            return QSize(0, 0)

        aspect_ratio = self._original_pixmap.height() / self._original_pixmap.width()
        target_width = available_size.width()
        target_height = int(target_width * aspect_ratio)

        if target_height > available_size.height():
            target_height = available_size.height()
            target_width = int(target_height / aspect_ratio)

        return QSize(target_width, target_height)

    def _create_enhanced_scaled_pixmap(self, target_size: QSize) -> QPixmap:
        """Create enhanced scaled pixmap with improved multi-step scaling."""
        if not self._original_pixmap:
            return QPixmap()

        original_size = self._original_pixmap.size()

        # Calculate scale factor
        scale_factor = min(
            target_size.width() / original_size.width(),
            target_size.height() / original_size.height(),
        )

        # Enhanced multi-step scaling with lower threshold
        if scale_factor < 0.75:  # Improved from 0.5
            # Multi-step scaling for better quality
            if scale_factor < 0.4:
                # Very aggressive downscaling - use 3 stages
                intermediate_factor1 = 0.7
                intermediate_factor2 = 0.5

                # Stage 1
                intermediate_size1 = QSize(
                    int(original_size.width() * intermediate_factor1),
                    int(original_size.height() * intermediate_factor1),
                )
                stage1_pixmap = self._original_pixmap.scaled(
                    intermediate_size1,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )

                # Stage 2
                intermediate_size2 = QSize(
                    int(original_size.width() * intermediate_factor2),
                    int(original_size.height() * intermediate_factor2),
                )
                stage2_pixmap = stage1_pixmap.scaled(
                    intermediate_size2,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )

                # Final stage
                final_pixmap = stage2_pixmap.scaled(
                    target_size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )

                return final_pixmap
            else:
                # Moderate downscaling - use 2 stages
                intermediate_factor = 0.75
                intermediate_size = QSize(
                    int(original_size.width() * intermediate_factor),
                    int(original_size.height() * intermediate_factor),
                )

                # Step 1: Scale to intermediate size
                intermediate_pixmap = self._original_pixmap.scaled(
                    intermediate_size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )

                # Step 2: Scale to final size
                final_pixmap = intermediate_pixmap.scaled(
                    target_size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )

                return final_pixmap
        else:
            # Single-step high-quality scaling for smaller scale changes
            return self._original_pixmap.scaled(
                target_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

    # Cache management methods
    def _ensure_cache_directory(self) -> None:
        """Ensure cache directory exists."""
        try:
            self.CACHE_DIR.mkdir(exist_ok=True)
        except Exception as e:
            logging.warning(f"Failed to create cache directory: {e}")

    def _load_cache_metadata(self) -> None:
        """Load cache metadata from disk."""
        metadata_path = self.CACHE_DIR / self.CACHE_METADATA_FILE
        try:
            if metadata_path.exists():
                with open(metadata_path, "r") as f:
                    self._cache_metadata = json.load(f)
            else:
                self._cache_metadata = {}
        except Exception as e:
            logging.warning(f"Failed to load cache metadata: {e}")
            self._cache_metadata = {}

    def _save_cache_metadata(self) -> None:
        """Save cache metadata to disk."""
        metadata_path = self.CACHE_DIR / self.CACHE_METADATA_FILE
        try:
            with open(metadata_path, "w") as f:
                json.dump(self._cache_metadata, f, indent=2)
        except Exception as e:
            logging.warning(f"Failed to save cache metadata: {e}")

    def _generate_cache_key(self, image_path: str, target_size: QSize) -> str:
        """Generate cache key based on image path, modification time, and size."""
        try:
            # Get file modification time
            mtime = os.path.getmtime(image_path)

            # Create cache key from path, mtime, and target size
            key_data = (
                f"{image_path}_{mtime}_{target_size.width()}x{target_size.height()}"
            )
            return hashlib.md5(key_data.encode()).hexdigest()
        except Exception:
            # Fallback to path-only key if mtime fails
            key_data = f"{image_path}_{target_size.width()}x{target_size.height()}"
            return hashlib.md5(key_data.encode()).hexdigest()

    def _get_cached_thumbnail(self, target_size: QSize) -> Optional[QPixmap]:
        """Get cached thumbnail (delegates to coordinator)."""
        return self.thumbnail_coordinator.get_cached_thumbnail(
            self.current_path, target_size
        )

    def _cache_thumbnail(self, pixmap: QPixmap, target_size: QSize) -> None:
        """Cache thumbnail (delegates to coordinator)."""
        self.thumbnail_coordinator.cache_thumbnail(
            self.current_path, pixmap, target_size
        )

    # Event handling methods
    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press events."""
        if not self.is_in_sequence_viewer:
            self.thumbnail_box.browse_tab.selection_handler.on_thumbnail_clicked(self)

    def enterEvent(self, event) -> None:
        """Highlight border on hover."""
        self._border_color = BLUE
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        """Remove border highlight when leaving hover."""
        self._border_color = GOLD if self.selected else None
        self.update()
        super().leaveEvent(event)

    def set_selected(self, selected: bool) -> None:
        """Set selection state."""
        self.selected = selected
        self._border_color = GOLD if selected else None
        self.update()

    # Legacy delegation methods for backward compatibility
    def _ensure_cache_directory(self) -> None:
        """Legacy method - now handled by coordinator."""
        pass

    def _load_cache_metadata(self) -> None:
        """Legacy method - now handled by coordinator."""
        pass

    def _save_cache_metadata(self) -> None:
        """Legacy method - now handled by coordinator."""
        pass

    def _generate_cache_key(self, image_path: str, target_size: QSize) -> str:
        """Legacy method - delegates to coordinator."""
        return self.thumbnail_coordinator.generate_cache_key(image_path, target_size)

    def _enhance_image_quality(self) -> None:
        """Legacy method - now handled by coordinator."""
        pass

    def _draw_border(self, painter: QPainter) -> None:
        """Draw border around the thumbnail."""
        if not self._original_pixmap or not (
            self._border_color or self.is_in_sequence_viewer
        ):
            return

        color = QColor(GOLD if self.is_in_sequence_viewer else self._border_color)
        border_width = int(
            self.border_width
            * (self.SEQUENCE_VIEWER_BORDER_SCALE if self.is_in_sequence_viewer else 1)
        )

        pen = QPen(color)
        pen.setWidth(border_width)
        pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
        painter.setPen(pen)

        img_width, img_height = self.pixmap().width(), self.pixmap().height()
        x = (self.width() - img_width) // 2
        y = (self.height() - img_height) // 2
        rect = QRect(x, y, img_width, img_height)

        border_offset = border_width // 2
        adjusted_rect = rect.adjusted(
            border_offset, border_offset, -border_offset, -border_offset
        )

        painter.drawRect(adjusted_rect)

    def paintEvent(self, event) -> None:
        """Handle paint events."""
        super().paintEvent(event)

        if self.is_in_sequence_viewer or self._border_color:
            painter = QPainter(self)
            self._draw_border(painter)

    def resizeEvent(self, event) -> None:
        """Handle resize events."""
        self._cached_available_size = None
        self._border_width = max(1, int(self.width() * self.BORDER_WIDTH_RATIO))
        super().resizeEvent(event)

    def _check_viewport_visibility(self) -> bool:
        """Check if this thumbnail is currently visible in the viewport (delegates to coordinator)."""
        return self.thumbnail_coordinator.check_viewport_visibility(self)

    # Performance and statistics methods
    def get_performance_stats(self) -> dict:
        """Get performance statistics from the coordinator."""
        return self.thumbnail_coordinator.get_performance_stats()

    def clear_cache(self) -> None:
        """Clear thumbnail cache (delegates to coordinator)."""
        self.thumbnail_coordinator.clear_cache()

    def get_cache_stats(self) -> dict:
        """Get cache statistics (delegates to coordinator)."""
        return self.thumbnail_coordinator.get_cache_stats()
