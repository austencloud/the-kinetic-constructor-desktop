# src/main_window/main_widget/sequence_card_tab/export/export_page_renderer.py
import logging
from typing import Dict, Any, Optional
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPixmap, QPainter, QImage, QImageReader
from PyQt6.QtCore import Qt, QRect, QElapsedTimer
import os

# Try to import PIL for image enhancement, but make it optional
try:
    from PIL import Image, ImageEnhance

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from .export_config import ExportConfig
from .export_grid_calculator import ExportGridCalculator
from .color_manager import ColorManager


class ExportPageRenderer:
    """
    Renders high-quality sequence card pages for export.

    This class handles:
    1. Creating high-quality pages from original images
    2. Rendering pages to image files
    3. Applying proper scaling and quality settings
    """

    def __init__(
        self, export_config: ExportConfig, grid_calculator: ExportGridCalculator
    ):
        self.config = export_config
        self.grid_calculator = grid_calculator
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)  # Ensure INFO level logging

        # Add console handler if not already present
        if not any(isinstance(h, logging.StreamHandler) for h in self.logger.handlers):
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            formatter = logging.Formatter(
                "%(asctime)s.%(msecs)03d - EXPORT - %(levelname)s - %(message)s",
                datefmt="%H:%M:%S",
            )
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

        # Export statistics
        self.export_stats = {
            "pages_processed": 0,
            "items_processed": 0,
            "total_export_time": 0,
            "slow_operations": [],
        }

        # Configure image reader for high quality
        QImageReader.setAllocationLimit(0)  # No memory limit for image loading

        # Initialize color manager for color correction
        color_management_settings = self.config.get_export_setting(
            "color_management", {}
        )
        self.color_manager = ColorManager(color_management_settings)

        # Get image processing settings with performance optimizations
        self.image_processing = self.config.get_export_setting("image_processing", {})
        self.scaling_algorithm = self.image_processing.get(
            "scaling_algorithm", Qt.TransformationMode.SmoothTransformation
        )

        # Performance optimizations - disable expensive operations that don't affect color
        self.maintain_larger_dimensions = False  # Disable upscaling for speed
        self.upscale_factor = 1.0  # No upscaling
        self.sharpen_after_scaling = False  # Disable PIL temp file operations

        # Performance optimization: Image cache for processed images
        self._image_cache = {}
        self._max_cache_size = 50  # Limit cache size to prevent memory issues

        self.logger.info(
            "Export renderer optimized for speed while preserving color accuracy"
        )

    def _get_image_cache_key(
        self, image_path: str, cell_width: int, cell_height: int
    ) -> str:
        """Generate a cache key for processed images."""
        return f"{image_path}_{cell_width}_{cell_height}"

    def _add_to_cache(self, cache_key: str, image: QImage):
        """Add processed image to cache with size management."""
        if len(self._image_cache) >= self._max_cache_size:
            # Remove oldest entry (simple FIFO)
            oldest_key = next(iter(self._image_cache))
            del self._image_cache[oldest_key]

        self._image_cache[cache_key] = image.copy()

    def _get_from_cache(self, cache_key: str) -> Optional[QImage]:
        """Get processed image from cache."""
        return self._image_cache.get(cache_key)

    def render_page_to_image(self, page: QWidget, filepath: str) -> bool:
        """
        Render a page as a high-quality print-ready image with performance monitoring.

        Args:
            page (QWidget): The page widget to render.
            filepath (str): Path to save the rendered image.

        Returns:
            bool: True if successful, False otherwise.
        """
        timer = QElapsedTimer()
        timer.start()

        import os

        page_filename = os.path.basename(filepath)
        self.logger.info(f"[PAGE] Starting render: {page_filename}")

        self.logger.debug(f"Rendering page to image: {filepath}")

        try:
            # Create a high-quality page
            page_timer = QElapsedTimer()
            page_timer.start()
            self.logger.info(f"[PAGE] Creating high-quality page widget")
            pixmap = self._create_high_quality_page(page)
            page_creation_time = page_timer.elapsed()
            self.logger.info(
                f"[PAGE] Page creation completed in {page_creation_time}ms"
            )

            if pixmap.isNull():
                self.logger.error("Failed to create high-quality page")
                return False

            # Convert QPixmap to QImage for better color management
            conversion_timer = QElapsedTimer()
            conversion_timer.start()
            self.logger.info(f"[PAGE] Converting pixmap to image for color management")
            image = pixmap.toImage()
            conversion_time = conversion_timer.elapsed()
            self.logger.info(
                f"[PAGE] Pixmap conversion completed in {conversion_time}ms"
            )

            # PERFORMANCE OPTIMIZATION: Skip full-page color processing since individual items are already processed
            color_timer = QElapsedTimer()
            color_timer.start()
            self.logger.info(
                f"[PAGE] SKIPPING full-page color management ({image.width()}x{image.height()}) - items already processed"
            )
            # image = self.color_manager.process_image(image)  # DISABLED for performance
            color_processing_time = color_timer.elapsed()
            self.logger.info(
                f"[PAGE] Color management skipped in {color_processing_time}ms"
            )

            # Convert back to QPixmap
            final_conversion_timer = QElapsedTimer()
            final_conversion_timer.start()
            self.logger.info(f"[PAGE] Converting processed image back to pixmap")
            pixmap = QPixmap.fromImage(image)
            final_conversion_time = final_conversion_timer.elapsed()
            self.logger.info(
                f"[PAGE] Final conversion completed in {final_conversion_time}ms"
            )

            # Save the pixmap as a high-quality image with optimized settings
            save_timer = QElapsedTimer()
            save_timer.start()
            format_setting = self.config.get_export_setting("format", "PNG")
            quality_setting = self.config.get_export_setting("quality", 100)
            self.logger.info(
                f"[PAGE] Saving image (format: {format_setting}, quality: {quality_setting})"
            )

            result = pixmap.save(
                filepath,
                format_setting,
                quality_setting,
            )
            save_time = save_timer.elapsed()
            self.logger.info(f"[PAGE] Save operation completed in {save_time}ms")

            total_time = timer.elapsed()

            if result:
                self.logger.info(f"[PAGE] ✅ Successfully saved: {page_filename}")
                self.logger.info(
                    f"[PAGE] TIMING BREAKDOWN - Total: {total_time}ms | "
                    f"Page: {page_creation_time}ms | "
                    f"Convert: {conversion_time}ms | "
                    f"Color: {color_processing_time}ms | "
                    f"Final: {final_conversion_time}ms | "
                    f"Save: {save_time}ms"
                )
            else:
                self.logger.error(f"[PAGE] ❌ Failed to save: {page_filename}")

            return result

        except Exception as e:
            self.logger.error(f"Error rendering page to image: {e}")
            return False

    def _create_high_quality_page(self, page: QWidget) -> QPixmap:
        """
        Create a high-quality page from scratch using original images.

        This method:
        1. Extracts sequence data from the page's widgets
        2. Finds the original high-resolution source images
        3. Creates a new page layout with these images
        4. Renders the page at ultra-high resolution

        Args:
            page: The page widget containing sequence data

        Returns:
            QPixmap: A high-quality rendered page
        """
        # Get the sequence data from the page
        sequence_items = page.property("sequence_items")

        self.logger.info(
            f"[PAGE] Processing page with {len(sequence_items) if sequence_items else 0} sequence items"
        )

        if (
            not sequence_items
            or not isinstance(sequence_items, list)
            or len(sequence_items) == 0
        ):
            self.logger.warning(
                "No sequence items found on page, falling back to direct rendering"
            )
            return self._render_widget_directly(page)

        # Create a new pixmap with the print dimensions
        page_width = self.config.get_print_setting("page_width_pixels", 5100)
        page_height = self.config.get_print_setting("page_height_pixels", 6600)

        pixmap = QPixmap(page_width, page_height)
        pixmap.fill(
            self.config.get_export_setting("background_color", Qt.GlobalColor.white)
        )

        # Create a painter for the pixmap
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)

        # Try to determine the sequence length from the metadata
        sequence_length = None
        if sequence_items and "sequence_data" in sequence_items[0]:
            metadata = sequence_items[0]["sequence_data"].get("metadata", {})
            if "sequence" in metadata and len(metadata["sequence"]) > 0:
                sequence_length = len(metadata["sequence"])
                self.logger.debug(f"Detected sequence length: {sequence_length}")

        # Calculate the optimal grid dimensions based on the number of items and sequence length
        rows, cols = self.grid_calculator.calculate_optimal_grid_dimensions(
            len(sequence_items), sequence_length
        )

        # Calculate the cell dimensions
        cell_dimensions = self.grid_calculator.calculate_cell_dimensions(rows, cols)
        cell_width = cell_dimensions["width"]
        cell_height = cell_dimensions["height"]

        # Render each sequence item in its grid cell
        self.logger.info(
            f"[PAGE] Starting to render {len(sequence_items)} items in {rows}x{cols} grid"
        )

        for idx, item in enumerate(sequence_items):
            # Skip if we've processed all cells in the grid
            if idx >= rows * cols:
                self.logger.warning(
                    f"Skipping item {idx+1} as it exceeds grid capacity ({rows}x{cols})"
                )
                continue

            # Progress logging every 5 items
            if idx % 5 == 0 or idx == len(sequence_items) - 1:
                progress = ((idx + 1) / len(sequence_items)) * 100
                self.logger.info(
                    f"[PAGE] Item progress: {idx+1}/{len(sequence_items)} ({progress:.1f}%)"
                )

            self.logger.debug(f"Processing sequence item {idx+1}/{len(sequence_items)}")

            # Get the sequence data
            sequence_data = item["sequence_data"]

            # Check if we have grid position information from the UI
            if (
                "grid_position" in item
                and item["grid_position"]["row"] >= 0
                and item["grid_position"]["column"] >= 0
            ):
                # Use the grid position from the UI
                row = item["grid_position"]["row"]
                col = item["grid_position"]["column"]
                self.logger.debug(
                    f"Using grid position from UI: row={row}, column={col}"
                )
            else:
                # Calculate the row and column for this item based on index
                row = idx // cols
                col = idx % cols
                self.logger.debug(
                    f"Using calculated grid position: row={row}, column={col}"
                )

            # Calculate the position of this cell
            cell_x, cell_y = self.grid_calculator.calculate_cell_position(
                row, col, cell_width, cell_height
            )

            # Render the sequence item in this cell
            self._render_sequence_item(
                painter, sequence_data, cell_x, cell_y, cell_width, cell_height
            )

        # End painting
        painter.end()

        return pixmap

    def _render_sequence_item(
        self,
        painter: QPainter,
        sequence_data: Dict[str, Any],
        cell_x: int,
        cell_y: int,
        cell_width: int,
        cell_height: int,
    ) -> None:
        """
        Render a sequence item in a grid cell.

        Args:
            painter: QPainter to use for rendering
            sequence_data: Sequence data dictionary
            cell_x: X position of the cell
            cell_y: Y position of the cell
            cell_width: Width of the cell
            cell_height: Height of the cell
        """
        import os  # Import os locally for path operations

        item_timer = QElapsedTimer()
        item_timer.start()

        # Get the image path
        image_path = sequence_data.get("path")
        image_name = os.path.basename(image_path) if image_path else "unknown"
        self.logger.info(
            f"[ITEM] Starting: {image_name} at ({cell_x},{cell_y}) size {cell_width}x{cell_height}"
        )

        if not image_path or not os.path.exists(image_path):
            self.logger.warning(f"[ITEM] ❌ Image path not found: {image_path}")
            return

        # Calculate the available space in the cell (accounting for padding)
        available_width, available_height = (
            self.grid_calculator.calculate_available_cell_space(cell_width, cell_height)
        )

        # Load the original image at full resolution
        load_timer = QElapsedTimer()
        load_timer.start()
        self.logger.info(f"[ITEM] Loading image: {image_name}")
        image = QImage(image_path)
        load_time = load_timer.elapsed()

        if image.isNull():
            self.logger.warning(f"[ITEM] ❌ Failed to load image: {image_path}")
            return

        self.logger.info(
            f"[ITEM] Image loaded in {load_time}ms: {image.width()}x{image.height()}"
        )

        # Calculate the final image dimensions first for optimized processing
        self.logger.info(
            f"[ITEM] Available cell space: {available_width}x{available_height}"
        )

        image_width, image_height = self.grid_calculator.calculate_image_dimensions(
            image.width(),
            image.height(),
            available_width,
            available_height,
        )

        # OPTIMIZED PROCESSING: Use balanced size for quality and printer compatibility
        image_processing = self.config.get_export_setting("image_processing", {})
        OPTIMAL_PROCESSING_SIZE = image_processing.get(
            "printer_output_size", 650
        )  # Balanced size for both quality and printer compatibility

        # Determine processing dimensions
        if (
            image_width > OPTIMAL_PROCESSING_SIZE
            or image_height > OPTIMAL_PROCESSING_SIZE
        ):
            # Scale down to optimal size for both quality and printer compatibility
            scale_factor = min(
                OPTIMAL_PROCESSING_SIZE / image_width,
                OPTIMAL_PROCESSING_SIZE / image_height,
            )
            color_processing_width = int(image_width * scale_factor)
            color_processing_height = int(image_height * scale_factor)
            self.logger.info(
                f"[ITEM] Optimizing processing size from {image_width}x{image_height} to {color_processing_width}x{color_processing_height} for printer compatibility"
            )
        else:
            # Image is already at optimal size
            color_processing_width = image_width
            color_processing_height = image_height

        self.logger.info(
            f"[ITEM] Target dimensions: {image_width}x{image_height}, Processing: {color_processing_width}x{color_processing_height} (reduction: {(image.width()*image.height())/(color_processing_width*color_processing_height):.1f}x)"
        )

        # Apply optimized color management: scale first, then apply color corrections
        self.logger.debug(
            f"Applying optimized color management to image: {os.path.basename(image_path)}"
        )

        # Apply optimized color processing at printer-compatible resolution
        self.logger.info(
            f"[ITEM] Processing colors at printer-optimized size: {color_processing_width}x{color_processing_height}"
        )
        enhanced_image = self.color_manager.process_image_with_target_size(
            image, color_processing_width, color_processing_height
        )

        # Scale back up to target size for proper page layout if needed
        if (
            color_processing_width != image_width
            or color_processing_height != image_height
        ):
            self.logger.info(
                f"[ITEM] Scaling processed image to target size: {image_width}x{image_height}"
            )
            scale_timer = QElapsedTimer()
            scale_timer.start()
            enhanced_image = enhanced_image.scaled(
                image_width,
                image_height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            scale_time = scale_timer.elapsed()
            self.logger.info(f"[ITEM] Final scaling completed in {scale_time}ms")

        # Note: Image is already at the correct dimensions from optimized processing
        # No additional scaling needed since process_image_with_target_size() handles it

        # Calculate the position to center the image in the cell
        image_x, image_y = self.grid_calculator.calculate_image_position_in_cell(
            cell_x, cell_y, cell_width, cell_height, image_width, image_height
        )

        # Apply sharpening if enabled (helps maintain detail after scaling)
        if self.sharpen_after_scaling:
            try:
                import tempfile
                import os

                # Create a temporary file for the conversion
                with tempfile.NamedTemporaryFile(
                    suffix=".png", delete=False
                ) as temp_file:
                    temp_path = temp_file.name

                try:
                    # Save QImage to temporary file
                    self.logger.debug(
                        f"Saving image to temporary file for sharpening: {temp_path}"
                    )
                    enhanced_image.save(temp_path, "PNG")

                    # Open with PIL
                    pil_image = Image.open(temp_path)

                    # Apply sharpening
                    self.logger.debug("Applying sharpening with PIL")
                    sharpened = ImageEnhance.Sharpness(pil_image).enhance(
                        1.3
                    )  # Moderate sharpening

                    # Save sharpened image back to temporary file
                    sharpened.save(temp_path, "PNG")

                    # Load back into QImage
                    enhanced_image = QImage(temp_path)

                    if enhanced_image.isNull():
                        self.logger.warning(
                            "Failed to load sharpened image. Using original image."
                        )
                finally:
                    # Clean up the temporary file
                    try:
                        if os.path.exists(temp_path):
                            os.unlink(temp_path)
                    except Exception as cleanup_error:
                        self.logger.warning(
                            f"Error cleaning up temporary file: {cleanup_error}"
                        )
            except Exception as e:
                # If PIL processing fails, continue with the unsharpened image
                self.logger.warning(
                    f"Error applying sharpening: {e}. Using unsharpened image."
                )

        # Draw the image with high-quality scaling
        painter.drawImage(
            QRect(image_x, image_y, image_width, image_height),
            enhanced_image,
            QRect(0, 0, enhanced_image.width(), enhanced_image.height()),
        )

        # REMOVED: Draw the sequence name (word is already part of the image)
        # word = sequence_data.get("word", "")
        # if word:
        #     # Set up the font
        #     font = QFont("Arial", 14, QFont.Weight.Bold)
        #     painter.setFont(font)
        #
        #     # Calculate the text position (centered below the image)
        #     text_rect = QRect(cell_x, image_y + image_height + 10, cell_width, 30)
        #
        #     # Draw the text
        #     painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, word)

        # Log completion timing
        item_time = item_timer.elapsed()
        self.logger.info(f"[ITEM] ✅ Completed: {image_name} in {item_time}ms")

    def _render_widget_directly(self, widget: QWidget) -> QPixmap:
        """
        Render a widget directly to a pixmap.

        This is a fallback method when we can't extract sequence data.

        Args:
            widget: The widget to render

        Returns:
            QPixmap: The rendered pixmap
        """
        self.logger.debug("Rendering widget directly")

        # Get the widget size
        widget_size = widget.size()

        # Calculate the scale factor to match the print resolution
        scale_factor = (
            self.config.get_print_setting("dpi", 600) / 96
        )  # Assuming screen DPI is 96

        # Create a pixmap with the scaled dimensions
        pixmap = QPixmap(
            int(widget_size.width() * scale_factor),
            int(widget_size.height() * scale_factor),
        )
        pixmap.fill(
            self.config.get_export_setting("background_color", Qt.GlobalColor.white)
        )

        # Create a painter for the pixmap
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)

        # Scale the painter
        painter.scale(scale_factor, scale_factor)

        # Render the widget
        widget.render(painter)

        # End painting
        painter.end()

        return pixmap
