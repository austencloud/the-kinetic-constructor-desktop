"""
Modern Thumbnail Image Label with Maximum Display Integration.

This component maximizes image display area while leveraging the existing
glassmorphism system and maintaining all current functionality.
"""

import os
import logging
from typing import TYPE_CHECKING, Optional
from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QPixmap, QPainter, QPen, QColor, QMouseEvent
from PyQt6.QtCore import QRect

from styles.glassmorphism_coordinator import GlassmorphismCoordinator
from main_window.main_widget.browse_tab.thumbnail_box.thumbnail_image_label import (
    ImageProcessor,
)
from data.constants import BLUE, GOLD

if TYPE_CHECKING:
    from .modern_thumbnail_box_integrated import ModernThumbnailBoxIntegrated


class ModernThumbnailImageLabelIntegrated(QLabel):
    """
    Modern thumbnail image label with maximum display area.

    Key enhancements:
    - Uses 96% of container width (vs previous ~88%)
    - Leverages existing glassmorphism styling
    - Maintains all existing functionality
    - Enhanced image quality processing
    """

    # Enhanced display ratios for maximum image utilization
    MAIN_VIEW_UTILIZATION = 0.96  # Increased from ~0.88
    SEQUENCE_VIEWER_UTILIZATION = 0.95

    # Border styling
    BORDER_WIDTH_RATIO = 0.015
    SEQUENCE_VIEWER_BORDER_SCALE = 1.5

    # Shared glassmorphism coordinator for performance optimization
    _shared_glassmorphism_coordinator = None

    def __init__(self, thumbnail_box: "ModernThumbnailBoxIntegrated"):
        super().__init__(thumbnail_box)
        self.thumbnail_box = thumbnail_box
        self.current_path: Optional[str] = None
        self._original_pixmap: Optional[QPixmap] = None
        self._cached_available_size: Optional[QSize] = None

        # Use shared glassmorphism coordinator for performance
        self.glassmorphism = self._get_shared_glassmorphism_coordinator()

        # Image processing
        self.image_processor = ImageProcessor()

        # Visual state
        self._border_color: Optional[str] = None
        self.selected = False
        self.border_width = 3

        # Setup
        self._setup_styling()
        self._setup_properties()

    @classmethod
    def _get_shared_glassmorphism_coordinator(cls):
        """Get shared glassmorphism coordinator for performance optimization."""
        if cls._shared_glassmorphism_coordinator is None:
            cls._shared_glassmorphism_coordinator = GlassmorphismCoordinator()
        return cls._shared_glassmorphism_coordinator

    def _setup_styling(self):
        """Apply enhanced glassmorphism styling to image label."""
        # Apply modern image container styling with premium web app effects
        border_radius = self.glassmorphism.component_styler.get_radius("md")

        image_style = f"""
        QLabel {{
            border-radius: {border_radius}px;
            background: transparent;
            border: 1px solid {self.glassmorphism.get_color("border_light", 0.05)};
            transition: all 0.25s ease-in-out;
        }}

        QLabel:hover {{
            border: 1px solid {self.glassmorphism.get_color("primary", 0.3)};
            background: {self.glassmorphism.get_color("surface", 0.02)};
        }}
        """
        self.setStyleSheet(image_style)

        # Set object name for enhanced styling
        self.setObjectName("modern_thumbnail_image_enhanced")

    def _setup_properties(self):
        """Setup label properties."""
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setScaledContents(False)  # We handle scaling manually for quality

        # Enable mouse tracking and cursor for hover effects
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    @property
    def is_in_sequence_viewer(self) -> bool:
        """Check if in sequence viewer mode."""
        return self.thumbnail_box.in_sequence_viewer

    @property
    def aspect_ratio(self) -> float:
        """Get aspect ratio of the original image."""
        if self._original_pixmap and self._original_pixmap.height() > 0:
            return self._original_pixmap.width() / self._original_pixmap.height()
        return 1.0

    def update_thumbnail(self, index: int) -> None:
        """Update the displayed image based on the given index."""
        thumbnails = self.thumbnail_box.state.thumbnails
        if not thumbnails or not (0 <= index < len(thumbnails)):
            return

        path = thumbnails[index]
        if path != self.current_path:
            self.current_path = path
            self._original_pixmap = QPixmap(path)
            self._cached_available_size = None

        self._resize_pixmap_for_maximum_display()

    def update_thumbnail_async(self, index: int) -> None:
        """
        Update thumbnail asynchronously for compatibility with existing system.

        This method maintains compatibility with the existing thumbnail update system
        that expects async updates for performance.
        """
        # For now, delegate to synchronous update
        # In the future, this could be enhanced with actual async processing
        self.update_thumbnail(index)

    def update_for_maximum_display(self):
        """Update image for maximum display after container resize."""
        self._cached_available_size = None
        if self.current_path:
            self._resize_pixmap_for_maximum_display()

    def _calculate_available_space(self) -> QSize:
        """Calculate available space with maximum utilization."""
        if self._cached_available_size:
            return self._cached_available_size

        if self.is_in_sequence_viewer:
            available_size = self._calculate_sequence_viewer_maximum()
        else:
            available_size = self._calculate_main_view_maximum()

        self._cached_available_size = available_size
        return available_size

    def _calculate_main_view_maximum(self) -> QSize:
        """
        CRITICAL: Calculate maximum image size for main view.

        This is the core enhancement - maximizing image display area.
        """
        container_width = self.thumbnail_box._preferred_width

        # Account for container padding and margins (minimal for maximum display)
        padding = self.thumbnail_box.MIN_CONTAINER_PADDING * 2  # Both sides

        # CRITICAL ENHANCEMENT: Use 96% of available container space
        available_width = container_width - padding
        image_width = int(available_width * self.MAIN_VIEW_UTILIZATION)
        image_width = max(170, image_width)  # Minimum width for quality

        # Calculate height based on aspect ratio, maintaining proportions
        if self.aspect_ratio > 0:
            image_height = int(image_width / self.aspect_ratio)
        else:
            image_height = image_width

        # Ensure minimum height for quality but don't exceed reasonable bounds
        image_height = max(130, min(image_height, int(image_width * 1.5)))

        return QSize(image_width, image_height)

    def _calculate_sequence_viewer_maximum(self) -> QSize:
        """Calculate maximum size for sequence viewer mode."""
        sequence_viewer = self.thumbnail_box.browse_tab.sequence_viewer

        try:
            # Use 95% of sequence viewer dimensions for maximum display
            available_width = int(
                sequence_viewer.width() * self.SEQUENCE_VIEWER_UTILIZATION
            )
            available_height = int(sequence_viewer.height() * 0.65)

            # Enhanced minimums for sequence viewer
            available_width = max(400, available_width)
            available_height = max(300, available_height)

        except (AttributeError, TypeError):
            # Fallback values
            available_width = 500
            available_height = 400

        return QSize(available_width, available_height)

    def _resize_pixmap_for_maximum_display(self) -> None:
        """Resize pixmap for maximum display quality."""
        if not self.current_path or not self._original_pixmap:
            return

        available_size = self._calculate_available_space()

        # Calculate the optimal scaled size maintaining aspect ratio
        scaled_size = self._calculate_scaled_pixmap_size(available_size)

        # Use high-quality image processing with enhanced scaling
        try:
            processed_pixmap = self.image_processor.process_image(
                self.current_path,
                scaled_size,
            )
        except Exception as e:
            logging.warning(f"Image processor failed for {self.current_path}: {e}")
            # Fallback to direct scaling
            processed_pixmap = self._create_enhanced_scaled_pixmap(scaled_size)

        # Ensure pixmap is valid
        if processed_pixmap.isNull():
            logging.warning(f"Failed to process image: {self.current_path}")
            # Final fallback to original pixmap scaled
            processed_pixmap = self._original_pixmap.scaled(
                scaled_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

        if processed_pixmap.isNull():
            return

        # CRITICAL: Set to calculated available size (container size)
        self.setFixedSize(available_size)
        self.setPixmap(processed_pixmap)

        logging.debug(
            f"✅ Maximum display image processed: {os.path.basename(self.current_path)} "
            f"container: {available_size.width()}x{available_size.height()}, "
            f"image: {processed_pixmap.width()}x{processed_pixmap.height()}"
        )

    def _calculate_scaled_pixmap_size(self, available_size: QSize) -> QSize:
        """Calculate the optimal size for the pixmap while maintaining aspect ratio."""
        if not self._original_pixmap:
            return QSize(0, 0)

        original_width = self._original_pixmap.width()
        original_height = self._original_pixmap.height()

        if original_width == 0 or original_height == 0:
            return available_size

        # Calculate scale factors for both dimensions
        width_scale = available_size.width() / original_width
        height_scale = available_size.height() / original_height

        # Use the smaller scale factor to ensure the image fits within bounds
        scale_factor = min(width_scale, height_scale)

        # Calculate final dimensions
        target_width = int(original_width * scale_factor)
        target_height = int(original_height * scale_factor)

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

        # Enhanced multi-step scaling for better quality
        if scale_factor < 0.75:
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
                return stage2_pixmap.scaled(
                    target_size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
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
                return intermediate_pixmap.scaled(
                    target_size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
        else:
            # Single-step high-quality scaling for smaller scale changes
            return self._original_pixmap.scaled(
                target_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

    def get_size_comparison(self) -> dict:
        """
        Get size comparison metrics for validation.

        Returns metrics showing improvement in image display size.
        """
        if not self._original_pixmap:
            return {"improvement_percentage": 0, "size_gain_pixels": 0}

        current_size = self._calculate_available_space()
        container_width = self.thumbnail_box._preferred_width

        # Calculate old approach (88% utilization)
        old_width = int(container_width * 0.88)
        old_height = (
            int(old_width / self.aspect_ratio) if self.aspect_ratio > 0 else old_width
        )

        # Calculate improvement
        size_gain_pixels = (current_size.width() * current_size.height()) - (
            old_width * old_height
        )
        improvement_percentage = ((current_size.width() / old_width) - 1) * 100

        return {
            "improvement_percentage": improvement_percentage,
            "size_gain_pixels": size_gain_pixels,
            "old_size": f"{old_width}x{old_height}",
            "new_size": f"{current_size.width()}x{current_size.height()}",
        }

    # Event handling - maintain existing functionality
    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press events."""
        if not self.is_in_sequence_viewer:
            self.thumbnail_box.browse_tab.selection_handler.on_thumbnail_clicked(self)
        super().mousePressEvent(event)

    def enterEvent(self, event) -> None:
        """Apply glassmorphism hover effect with enhanced cursor."""
        self._border_color = BLUE
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        """Remove hover effect and restore cursor."""
        self._border_color = GOLD if self.selected else None
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.update()
        super().leaveEvent(event)

    def set_selected(self, selected: bool) -> None:
        """Set selection state with glassmorphism styling."""
        self.selected = selected
        self._border_color = GOLD if selected else None
        self.update()

    def _draw_border(self, painter: QPainter) -> None:
        """Draw border with glassmorphism styling."""
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
        """Handle paint events with glassmorphism effects."""
        super().paintEvent(event)

        if self.is_in_sequence_viewer or self._border_color:
            painter = QPainter(self)
            self._draw_border(painter)

    def resizeEvent(self, event) -> None:
        """Handle resize events."""
        self._cached_available_size = None
        self._border_width = max(1, int(self.width() * self.BORDER_WIDTH_RATIO))
        super().resizeEvent(event)
