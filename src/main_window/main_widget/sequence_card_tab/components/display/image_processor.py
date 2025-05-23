# src/main_window/main_widget/sequence_card_tab/components/display/image_processor.py
import os
import logging
import collections  # Import collections for OrderedDict
from typing import (
    Dict,
    Optional,
    TYPE_CHECKING,
    OrderedDict as OrderedDictType,
)  # For type hinting
from PyQt6.QtGui import QPixmap, QImage, QPainter, QColor, QFont
from PyQt6.QtCore import Qt, QSize, QRect
from PyQt6.QtWidgets import QApplication

if TYPE_CHECKING:
    from ..pages.printable_factory import PrintablePageFactory

DEFAULT_IMAGE_CACHE_SIZE = (
    1000  # Defines a default maximum number of images in the LRU cache
)

# Image processor for sequence card images
# Handles loading, scaling, and caching of images for display and export


class ImageProcessor:
    """
    Handles image loading, scaling, and caching for sequence card images.

    This class is responsible for:
    1. Loading images from disk
    2. Scaling images consistently based on grid dimensions and column count (for screen display)
    3. Scaling images for high-quality export
    4. Maintaining aspect ratios during scaling
    5. Caching images for performance using a two-level LRU cache:
        - First level: Raw QImage objects keyed by image_path
        - Second level: Scaled QPixmap objects (for screen display) keyed by image_path + scaling parameters
    6. Applying proper margins and scaling adjustments (for screen display)
    """

    def __init__(
        self,
        page_factory: "PrintablePageFactory",
        columns_per_row: int = 2,
        cache_size: int = DEFAULT_IMAGE_CACHE_SIZE,
    ):
        self.page_factory = page_factory
        self.columns_per_row = columns_per_row

        # Two-level caching system:
        # Level 1: Raw image cache (path -> QImage)
        self.raw_image_cache: OrderedDictType[str, QImage] = collections.OrderedDict()

        # Level 2: Scaled image cache (cache_key -> QPixmap) - for screen display
        self.scaled_image_cache: OrderedDictType[str, QPixmap] = (
            collections.OrderedDict()
        )

        # For backward compatibility (though direct use of scaled_image_cache is preferred for clarity)
        self.image_cache = self.scaled_image_cache

        # Cache size limits
        self.raw_cache_size = cache_size // 2  # Half for raw images
        self.scaled_cache_size = (
            cache_size  # Full size for scaled images (primarily for screen previews)
        )
        self.cache_size = (
            cache_size  # Retained for compatibility if anything uses it directly
        )

        # Cache statistics
        self.cache_hits = 0  # General L2 cache hits for screen display
        self.cache_misses = 0  # General L2 cache misses for screen display
        # Note: L1 cache hits/misses are logged directly in methods

    def set_columns_per_row(self, columns: int) -> None:
        """
        Set the number of columns per row for screen scaling calculations.

        Args:
            columns: Number of columns (limited to 1-4)
        """
        if columns < 1:
            columns = 1
        elif columns > 4:
            columns = 4

        self.columns_per_row = columns

    def clear_cache(self) -> None:
        """Clear all image caches (raw and scaled)."""
        # Count items before clearing (for logging)
        raw_count = len(self.raw_image_cache)
        scaled_count = len(self.scaled_image_cache)

        # Clear both cache levels
        self.raw_image_cache.clear()
        self.scaled_image_cache.clear()

        # Reset cache statistics
        self.cache_hits = 0
        self.cache_misses = 0

        # Log cache clearing
        logging.debug(
            f"Image cache cleared: {raw_count} raw items and {scaled_count} scaled items removed."
        )

    def _get_raw_qimage(self, image_path: str) -> Optional[QImage]:
        """
        Helper to retrieve a raw QImage, from cache or by loading from disk.
        Manages the raw_image_cache.

        Args:
            image_path: Path to the image file.

        Returns:
            QImage if successful, None otherwise.
        """
        if image_path in self.raw_image_cache:
            # Use cached raw image
            image = self.raw_image_cache[image_path]
            # Mark as recently used
            self.raw_image_cache.move_to_end(image_path)
            logging.debug(f"L1 cache hit for raw image: {os.path.basename(image_path)}")
            return image
        else:
            # Load from disk
            logging.debug(
                f"L1 cache miss. Loading raw image from disk: {os.path.basename(image_path)}"
            )
            image = QImage(image_path)
            if image.isNull():
                logging.error(f"Failed to load raw image {image_path}")
                return None

            # Add to Level 1 cache (raw images)
            self.raw_image_cache[image_path] = image
            self.raw_image_cache.move_to_end(image_path)

            # Enforce Level 1 cache size limit
            if len(self.raw_image_cache) > self.raw_cache_size:
                removed_item = self.raw_image_cache.popitem(
                    last=False
                )  # Remove least recently used
                logging.debug(
                    f"L1 cache full. Removed: {os.path.basename(removed_item[0])}"
                )
            return image

    def load_image_with_consistent_scaling(
        self,
        image_path: str,
        page_scale_factor: float = 1.0,
        current_page_index: int = -1,  # Retained for update_card_aspect_ratio logic
    ) -> QPixmap:
        """
        Load image with consistent scaling FOR SCREEN DISPLAY.

        This method ensures:
        1. Consistent relative sizing across all images based on grid dimensions and column count
        2. Proper margins around each image
        3. High-quality scaling using SmoothTransformation
        4. Efficient LRU caching for performance
        5. Images fit completely within their grid cells
        6. Aspect ratio is maintained
        7. No overflow occurs
        8. Proper scaling adjustment based on preview columns

        Args:
            image_path: Path to the image file
            page_scale_factor: Scale factor to apply (from the page, for screen preview)
            current_page_index: Current page index (-1 for first image, used for aspect ratio update)

        Returns:
            QPixmap: The scaled image for screen display
        """
        # Get cell_size early as it's part of the cache key components for scaled images
        cell_size = self.page_factory.get_cell_size()

        # Create a more robust cache key that captures all parameters affecting the final scaled pixmap:
        key_parts = (
            image_path,
            cell_size.width(),
            cell_size.height(),
            self.columns_per_row,
            f"{page_scale_factor:.4f}",  # Format float to ensure consistent string representation
        )
        cache_key = "_".join(map(str, key_parts))

        # Check Level 2 cache (scaled images for screen) first
        if cache_key in self.scaled_image_cache:
            self.scaled_image_cache.move_to_end(cache_key)
            self.cache_hits += 1  # L2 cache hit
            logging.debug(
                f"L2 cache hit for screen display: {os.path.basename(image_path)}"
            )
            return self.scaled_image_cache[cache_key]

        self.cache_misses += 1  # L2 cache miss

        try:
            # Get the raw QImage (from L1 cache or disk)
            image = self._get_raw_qimage(image_path)
            if not image or image.isNull():
                # _get_raw_qimage already logs error if image is null after loading
                return self._create_error_pixmap(
                    cell_size
                )  # Use cell_size for error pixmap in this context

            # --- Screen-specific scaling logic ---
            column_adjustment = 1.0
            if self.columns_per_row == 3:
                column_adjustment = 0.98
            elif self.columns_per_row == 4:
                column_adjustment = 0.95

            margin_percent = 0.05
            if self.columns_per_row == 3:
                margin_percent = 0.04
            elif self.columns_per_row == 4:
                margin_percent = 0.03

            margin = min(
                15,
                max(
                    3, int(min(cell_size.width(), cell_size.height()) * margin_percent)
                ),
            )

            available_width_for_image = cell_size.width() - (margin * 2)
            available_height_for_image = cell_size.height() - (margin * 2)

            target_available_width = int(
                available_width_for_image * page_scale_factor * column_adjustment
            )
            target_available_height = int(
                available_height_for_image * page_scale_factor * column_adjustment
            )

            original_width = image.width()
            original_height = image.height()

            scaled_qimage: QImage  # Renamed from scaled_image to avoid confusion
            if original_width <= 0 or original_height <= 0:
                scaled_qimage = QImage()  # Null QImage
            else:
                aspect_ratio = original_height / original_width
                if target_available_width * aspect_ratio <= target_available_height:
                    target_width = target_available_width
                    target_height = int(target_width * aspect_ratio)
                else:
                    target_height = target_available_height
                    target_width = int(target_height / aspect_ratio)

                target_width = max(0, target_width)
                target_height = max(0, target_height)

                scaled_qimage = image.scaled(
                    target_width,
                    target_height,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )

            # Update card aspect ratio in page factory for the first image processed in a batch
            # This logic seems specific to the initial setup of page layout based on first image.
            if (
                current_page_index == -1
            ):  # Typically means it's the first image determining aspect for layout
                if original_width > 0 and original_height > 0:
                    self.page_factory.update_card_aspect_ratio(
                        original_width / original_height  # card's width/height ratio
                    )

            pixmap = QPixmap.fromImage(scaled_qimage)

            # Add to Level 2 cache (scaled images for screen)
            self.scaled_image_cache[cache_key] = pixmap
            self.scaled_image_cache.move_to_end(cache_key)

            if len(self.scaled_image_cache) > self.scaled_cache_size:
                removed_item = self.scaled_image_cache.popitem(last=False)
                logging.debug(
                    f"L2 cache full. Removed: {os.path.basename(removed_item[0].split('_')[0])}"
                )

            QApplication.processEvents()  # Keep UI responsive during multiple loads
            return pixmap

        except Exception as e:
            import traceback

            logging.error(f"Error loading image for screen {image_path}: {e}")
            traceback.print_exc()
            return self._create_error_pixmap(cell_size)

    def load_image_for_export(
        self, image_path: str, export_target_width_px: int, export_target_height_px: int
    ) -> QPixmap:
        """
        Load and scale an image specifically for high-quality export.

        This method bypasses screen-related scaling factors and UI constraints,
        focusing solely on producing the highest quality image for export at the
        specified pixel dimensions, maintaining aspect ratio within those bounds.

        Args:
            image_path: Path to the image file.
            export_target_width_px: The maximum target width in pixels for the exported image.
                                    The final width will maintain aspect ratio.
            export_target_height_px: The maximum target height in pixels for the exported image.
                                     The final height will maintain aspect ratio.

        Returns:
            QPixmap: The high-quality scaled image for export, or an error pixmap.
        """
        logging.debug(
            f"Loading image for EXPORT: {os.path.basename(image_path)} to fit within {export_target_width_px}x{export_target_height_px}px"
        )
        try:
            # Get the raw QImage (from L1 cache or disk)
            image = self._get_raw_qimage(image_path)

            if not image or image.isNull():
                # _get_raw_qimage already logs error if image is null after loading
                return self._create_error_pixmap(
                    QSize(export_target_width_px, export_target_height_px)
                )

            original_width = image.width()
            original_height = image.height()

            if original_width <= 0 or original_height <= 0:
                logging.error(
                    f"Invalid original image dimensions for export: {original_width}x{original_height} for {image_path}"
                )
                return self._create_error_pixmap(
                    QSize(export_target_width_px, export_target_height_px)
                )

            # Calculate final dimensions to fit within export_target_width_px and export_target_height_px
            # while maintaining aspect ratio.
            final_width = original_width
            final_height = original_height

            # Calculate scaling factor based on width and height constraints
            width_scale = (
                export_target_width_px / original_width if original_width > 0 else 0
            )
            height_scale = (
                export_target_height_px / original_height if original_height > 0 else 0
            )

            # Determine the limiting dimension for scaling
            if width_scale > 0 and height_scale > 0:
                scale = min(width_scale, height_scale)
            elif width_scale > 0:
                scale = width_scale
            elif height_scale > 0:
                scale = height_scale
            else:  # Both target dimensions are zero or negative, or original is zero
                logging.warning(
                    f"Cannot determine scale for export {image_path}, using original size or error pixmap."
                )
                if (
                    original_width <= 0 or original_height <= 0
                ):  # Should have been caught above, but double check
                    return self._create_error_pixmap(
                        QSize(
                            max(1, export_target_width_px),
                            max(1, export_target_height_px),
                        )
                    )
                scale = 0

            if scale > 0:
                final_width = int(original_width * scale)
                final_height = int(original_height * scale)
            else:
                final_width = 0
                final_height = 0

            final_width = max(0, final_width)
            final_height = max(0, final_height)

            if final_width == 0 or final_height == 0:
                logging.warning(
                    f"Calculated export dimensions are zero for {image_path}. Creating error pixmap."
                )
                return self._create_error_pixmap(
                    QSize(
                        max(1, export_target_width_px), max(1, export_target_height_px)
                    )
                )

            logging.debug(
                f"Scaling {os.path.basename(image_path)} from {original_width}x{original_height} to {final_width}x{final_height} for export."
            )

            scaled_qimage = image.scaled(
                final_width,
                final_height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

            # Debug logging for the scaled image
            if not scaled_qimage.isNull():
                logging.debug(
                    f"Successfully scaled image for export: {os.path.basename(image_path)} to {scaled_qimage.width()}x{scaled_qimage.height()}"
                )
            else:
                logging.warning(
                    f"scaled_qimage is null for {image_path}, will return error pixmap."
                )

            if scaled_qimage.isNull():
                logging.error(
                    f"QImage.scaled() returned a null image for export: {image_path}"
                )
                return self._create_error_pixmap(
                    QSize(export_target_width_px, export_target_height_px)
                )

            pixmap = QPixmap.fromImage(scaled_qimage)
            logging.debug(
                f"Successfully created export pixmap for {os.path.basename(image_path)} with size {pixmap.width()}x{pixmap.height()}"
            )
            return pixmap

        except Exception as e:
            import traceback

            logging.error(f"Error in load_image_for_export for {image_path}: {e}")
            traceback.print_exc()
            return self._create_error_pixmap(
                QSize(export_target_width_px, export_target_height_px)
            )

    def _create_error_pixmap(self, size: Optional[QSize] = None) -> QPixmap:
        """
        Create a pixmap indicating an error loading the image.

        Args:
            size: Size of the error pixmap. If None or invalid, uses a default size.

        Returns:
            QPixmap: An error indicator pixmap
        """
        if (
            size is None
            or not size.isValid()
            or size.width() <= 0
            or size.height() <= 0
        ):
            target_size = QSize(100, 100)  # Default error pixmap size
        else:
            target_size = size

        pixmap = QPixmap(target_size)
        pixmap.fill(QColor(220, 50, 50))  # Red background

        painter = QPainter(pixmap)
        font = QFont()
        font.setPointSize(
            max(8, min(10, target_size.height() // 10))
        )  # Dynamic font size
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor(255, 255, 255))  # White text

        text_rect = QRect(5, 5, target_size.width() - 10, target_size.height() - 10)
        painter.drawText(
            text_rect, Qt.AlignmentFlag.AlignCenter, "Error\nLoading\nImage"
        )
        painter.end()
        return pixmap

    def load_image(
        self,
        image_path: str,
        page_scale_factor: float = 1.0,
        current_page_index: int = -1,
    ) -> QPixmap:
        """
        Legacy method for backward compatibility.
        Use load_image_with_consistent_scaling for screen display.
        """
        logging.warning(
            "Legacy `load_image` called. Redirecting to `load_image_with_consistent_scaling`."
        )
        return self.load_image_with_consistent_scaling(
            image_path, page_scale_factor, current_page_index
        )
