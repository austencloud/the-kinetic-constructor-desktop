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
from .processing.image_processor import ImageProcessor

if TYPE_CHECKING:
    from .thumbnail_box import ThumbnailBox


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
        self.metadata_extractor = MetaDataExtractor()
        self.selected = False
        self.current_path: Optional[str] = None

        # Private attributes
        self._border_width = 4
        self._border_color: Optional[str] = None
        self._original_pixmap: Optional[QPixmap] = None
        self._cached_available_size: Optional[QSize] = None

        # Image processor
        self.image_processor = ImageProcessor()

        # Deferred loading to prevent UI blocking
        self._load_timer = QTimer()
        self._load_timer.setSingleShot(True)
        self._load_timer.timeout.connect(self._load_pending_image)
        self._pending_path: Optional[str] = None
        self._pending_index: Optional[int] = None

        # Quality enhancement timer
        self._quality_timer = QTimer()
        self._quality_timer.setSingleShot(True)
        self._quality_timer.timeout.connect(self._enhance_image_quality)
        self._needs_quality_enhancement = False

        # Initialize cache system
        self._cache_metadata = {}
        self._ensure_cache_directory()
        self._load_cache_metadata()

        # Setup UI
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Set object name to exclude from glassmorphism styling
        self.setObjectName("thumbnail_image_label")

    @property
    def border_width(self) -> int:
        return self._border_width

    @property
    def is_in_sequence_viewer(self) -> bool:
        return self.thumbnail_box.in_sequence_viewer

    @property
    def aspect_ratio(self) -> float:
        """Get aspect ratio of the original image"""
        return (
            self._original_pixmap.width() / self._original_pixmap.height()
            if self._original_pixmap and self._original_pixmap.height() > 0
            else 1
        )

    def update_thumbnail(self, index: int) -> None:
        """Update the displayed image based on the given index (synchronous)."""
        thumbnails = self.thumbnail_box.state.thumbnails
        if not thumbnails or not (0 <= index < len(thumbnails)):
            return

        path = thumbnails[index]
        if path != self.current_path:
            self.current_path = path
            self._original_pixmap = QPixmap(path)
            self._cached_available_size = None

        self._resize_pixmap_to_ultra_quality()

    def update_thumbnail_async(self, index: int) -> None:
        """Update the displayed image asynchronously with ultra quality processing."""
        thumbnails = self.thumbnail_box.state.thumbnails
        if not thumbnails or not (0 <= index < len(thumbnails)):
            return

        path = thumbnails[index]
        if path != self.current_path:
            self._pending_path = path
            self._pending_index = index

            # Load with ultra quality processing (no cache)
            self._load_timer.start(1)
        else:
            self._resize_pixmap_to_ultra_quality()

    def _load_pending_image(self) -> None:
        """Load pending image with ultra quality processing."""
        if self._pending_path and self._pending_index is not None:
            try:
                # Process with ultra quality (no cache)
                if os.path.exists(self._pending_path):
                    self.current_path = self._pending_path
                    self._original_pixmap = QPixmap(self._pending_path)
                    self._cached_available_size = None

                    # Always use ultra quality processing
                    self._resize_pixmap_to_ultra_quality()

            except Exception as e:
                logging.error(f"Error in ultra quality loading: {e}")
            finally:
                self._pending_path = None
                self._pending_index = None

    def _calculate_available_space(self) -> QSize:
        """Calculate available space - ENHANCED FOR MAXIMUM QUALITY."""
        if self._cached_available_size:
            return self._cached_available_size

        if self.is_in_sequence_viewer:
            available_size = self._calculate_sequence_viewer_size()
        else:
            available_size = self._calculate_normal_view_size_enhanced()

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
        """Resize pixmap using ULTRA QUALITY processing with user settings."""
        if not self.current_path:
            return

        available_size = self._calculate_available_space()

        # Check cache first
        cached_pixmap = self._get_cached_thumbnail(available_size)
        if cached_pixmap and not cached_pixmap.isNull():
            self.setFixedSize(available_size)
            self.setPixmap(cached_pixmap)
            logging.debug(
                f"✅ Loaded cached thumbnail: {os.path.basename(self.current_path)}"
            )
            return

        # HIGH QUALITY PROCESSING - always use SmoothTransformation
        processed_pixmap = self.image_processor.process_image(
            self.current_path,
            available_size,
        )

        # CRITICAL: Ensure pixmap is not null before proceeding
        if processed_pixmap.isNull():
            logging.warning(
                f"Failed to create processed pixmap for {self.current_path}"
            )
            # Fallback to standard processing
            self._resize_pixmap_to_fit_smooth()
            return

        # Cache the high-quality thumbnail
        self._cache_thumbnail(processed_pixmap, available_size)

        self.setFixedSize(available_size)
        self.setPixmap(processed_pixmap)

        logging.debug(
            f"✅ High-quality thumbnail processed: {os.path.basename(self.current_path)}"
        )

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
        """Get cached thumbnail if available and valid."""
        if not self.current_path:
            return None

        cache_key = self._generate_cache_key(self.current_path, target_size)
        cache_file = self.CACHE_DIR / f"{cache_key}.png"

        try:
            # Check if cache file exists and metadata is valid
            if cache_file.exists() and cache_key in self._cache_metadata:
                metadata = self._cache_metadata[cache_key]

                # Validate cache entry
                if (
                    metadata.get("source_path") == self.current_path
                    and metadata.get("target_width") == target_size.width()
                    and metadata.get("target_height") == target_size.height()
                ):

                    # Load cached pixmap
                    pixmap = QPixmap(str(cache_file))
                    if not pixmap.isNull():
                        return pixmap

        except Exception as e:
            logging.debug(f"Error loading cached thumbnail: {e}")

        return None

    def _cache_thumbnail(self, pixmap: QPixmap, target_size: QSize) -> None:
        """Cache thumbnail to disk."""
        if not self.current_path or pixmap.isNull():
            return

        cache_key = self._generate_cache_key(self.current_path, target_size)
        cache_file = self.CACHE_DIR / f"{cache_key}.png"

        try:
            # Save pixmap to cache
            if pixmap.save(str(cache_file), "PNG"):
                # Update metadata
                self._cache_metadata[cache_key] = {
                    "source_path": self.current_path,
                    "target_width": target_size.width(),
                    "target_height": target_size.height(),
                    "cached_at": os.path.getmtime(self.current_path),
                    "cache_file": str(cache_file),
                }

                # Save metadata (async to avoid blocking)
                QTimer.singleShot(100, self._save_cache_metadata)

                logging.debug(
                    f"✅ Cached thumbnail: {os.path.basename(self.current_path)}"
                )
            else:
                logging.warning(f"Failed to save thumbnail cache: {cache_file}")

        except Exception as e:
            logging.warning(f"Error caching thumbnail: {e}")

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

    # Removed cache initialization and word/variation tracking - no longer needed

    def _enhance_image_quality(self) -> None:
        """Legacy method - now handled by ultra_processor."""
        pass  # Ultra quality processing handles all enhancement

    def _check_viewport_visibility(self) -> bool:
        """Check if this thumbnail is currently visible in the viewport."""
        try:
            scroll_widget = self.thumbnail_box.sequence_picker.scroll_widget
            scroll_area = scroll_widget.scroll_area

            thumbnail_global_pos = self.mapToGlobal(self.rect().topLeft())
            scroll_area_global_pos = scroll_area.mapToGlobal(
                scroll_area.rect().topLeft()
            )

            relative_pos = thumbnail_global_pos - scroll_area_global_pos
            visible_rect = scroll_area.viewport().rect()
            thumbnail_rect = self.rect()
            thumbnail_rect.moveTopLeft(relative_pos)

            return visible_rect.intersects(thumbnail_rect)

        except Exception:
            return True
