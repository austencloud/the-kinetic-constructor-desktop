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

        # Initialize coordinator to handle complex operations
        self.coordinator = ThumbnailCoordinator(thumbnail_box)

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

        # Use coordinator for processing
        processed_pixmap = self.coordinator.process_thumbnail_sync(
            path, self.is_in_sequence_viewer
        )

        if not processed_pixmap.isNull():
            self.setPixmap(processed_pixmap)
            self._update_size_from_pixmap(processed_pixmap)

    def update_thumbnail_async(self, index: int) -> None:
        """Update the displayed image asynchronously with ultra quality processing."""
        thumbnails = self.thumbnail_box.state.thumbnails
        if not thumbnails or not (0 <= index < len(thumbnails)):
            return

        path = thumbnails[index]
        if path != self.current_path:
            self.current_path = path
            # Use coordinator for async processing
            self.coordinator.process_thumbnail_async(path, index)
            # Set up a timer to update the display when processing completes
            QTimer.singleShot(10, lambda: self._update_display_from_coordinator())
        else:
            # Use coordinator for processing
            processed_pixmap = self.coordinator.process_thumbnail_sync(
                path, self.is_in_sequence_viewer
            )

            if not processed_pixmap.isNull():
                self.setPixmap(processed_pixmap)
                self._update_size_from_pixmap(processed_pixmap)

    def _update_display_from_coordinator(self) -> None:
        """Update display after coordinator processing."""
        if self.current_path:
            processed_pixmap = self.coordinator.process_thumbnail_sync(
                self.current_path, self.is_in_sequence_viewer
            )

            if not processed_pixmap.isNull():
                self.setPixmap(processed_pixmap)
                self._update_size_from_pixmap(processed_pixmap)

    def _update_size_from_pixmap(self, pixmap: QPixmap) -> None:
        """Update widget size based on pixmap."""
        if not pixmap.isNull():
            # Calculate appropriate size for the widget
            target_size = self.coordinator.size_calculator.calculate_target_size(
                self.is_in_sequence_viewer
            )
            self.setFixedSize(target_size)

    # Legacy method - now handled by coordinator
    def _load_pending_image(self) -> None:
        """Legacy method - processing now handled by coordinator."""
        pass

    # Size calculation now handled by coordinator
    def _calculate_available_space(self) -> QSize:
        """Legacy method - size calculation now handled by coordinator."""
        return self.coordinator.size_calculator.calculate_target_size(
            self.is_in_sequence_viewer
        )

    def _resize_pixmap_to_ultra_quality(self) -> None:
        """Legacy method - processing now handled by coordinator."""
        if not self.current_path:
            return

        # Use coordinator for processing
        processed_pixmap = self.coordinator.process_thumbnail_sync(
            self.current_path, self.is_in_sequence_viewer
        )

        if not processed_pixmap.isNull():
            self.setPixmap(processed_pixmap)
            self._update_size_from_pixmap(processed_pixmap)

    # Removed _get_quality_settings - now always using maximum quality

    def _resize_pixmap_to_fit_smooth(self) -> None:
        """Legacy method - processing now handled by coordinator."""
        self._resize_pixmap_to_ultra_quality()

    # Legacy methods - processing now handled by coordinator
    def _calculate_scaled_pixmap_size(self, available_size: QSize) -> QSize:
        """Legacy method - calculations now handled by coordinator."""
        return available_size

    def _create_enhanced_scaled_pixmap(self, target_size: QSize) -> QPixmap:
        """Legacy method - scaling now handled by coordinator."""
        if self.current_path:
            return self.coordinator.process_thumbnail_sync(
                self.current_path, self.is_in_sequence_viewer
            )
        return QPixmap()

    # Cache management now handled by coordinator

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press events."""
        self.coordinator.handle_mouse_press(event)
        if not self.is_in_sequence_viewer:
            self.thumbnail_box.browse_tab.selection_handler.on_thumbnail_clicked(self)

    def enterEvent(self, event) -> None:
        """Highlight border on hover."""
        self.coordinator.handle_enter_event(event)
        self._border_color = self.coordinator.get_border_color() or BLUE
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        """Remove border highlight when leaving hover."""
        self.coordinator.handle_leave_event(event)
        self._border_color = GOLD if self.selected else None
        self.update()
        super().leaveEvent(event)

    def set_selected(self, selected: bool) -> None:
        """Set selection state."""
        self.selected = selected
        self.coordinator.set_selection_state(selected)
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

    # Legacy methods - functionality now handled by coordinator
    def _enhance_image_quality(self) -> None:
        """Legacy method - now handled by coordinator."""
        pass

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
