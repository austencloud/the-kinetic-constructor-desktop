"""
Image Processor Coordinator - Orchestrates image processing components.

This coordinator replaces the monolithic ImageProcessor class with a clean
architecture that follows the Single Responsibility Principle.
"""

import logging
from typing import TYPE_CHECKING, Optional, Dict, Any, List
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import QSize


from .image_loader import ImageLoader
from .image_scaler import ImageScaler
from .image_cache_manager import ImageCacheManager

if TYPE_CHECKING:
    from main_window.main_widget.sequence_card_tab.components.pages.printable_factory import (
        PrintablePageFactory,
    )


class ImageProcessorCoordinator:
    """
    Coordinates image processing operations using focused components.

    This coordinator orchestrates:
    - Image loading and validation
    - Cache management (memory and disk)
    - Image scaling and quality enhancement
    - Performance monitoring
    - Error handling

    Each responsibility is handled by a dedicated component following SRP.
    """

    def __init__(
        self,
        page_factory: "PrintablePageFactory",
        columns_per_row: int = 2,
        cache_size: int = 1000,
    ):
        self.page_factory = page_factory
        self.columns_per_row = columns_per_row
        self.logger = logging.getLogger(__name__)

        # Initialize specialized components
        self.image_loader = ImageLoader()
        self.image_scaler = ImageScaler(page_factory)
        self.cache_manager = ImageCacheManager(cache_size)

        self.logger.info(
            "ImageProcessorCoordinator initialized with component architecture"
        )

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
        self.logger.debug(f"Columns per row set to: {columns}")

    def load_images_batch_if_cached(
        self,
        image_paths: List[str],
        page_scale_factor: float = 1.0,
        current_page_index: int = -1,
    ) -> Dict[str, QPixmap]:
        """
        Load multiple images instantly if they are cached, bypassing async loading.

        This method enables instant batch display of cached images, eliminating
        progressive loading behavior when switching between sequence length filters.

        Args:
            image_paths: List of image paths to load
            page_scale_factor: Scale factor for display
            current_page_index: Current page index for aspect ratio updates

        Returns:
            Dictionary mapping paths to pixmaps (only includes cache hits)
        """
        cached_images = {}

        for image_path in image_paths:
            try:
                # Create cache key for scaled images
                cache_key = self.image_scaler.create_cache_key(
                    image_path, self.columns_per_row, page_scale_factor
                )

                # Check Level 2 cache (scaled images) first
                cached_pixmap = self.cache_manager.get_scaled_image(cache_key)
                if cached_pixmap:
                    cached_images[image_path] = cached_pixmap
                    continue

                # Check disk cache
                cell_size = self.page_factory.get_cell_size()
                disk_cached_pixmap = self.cache_manager.get_disk_cached_image(
                    image_path, cell_size, page_scale_factor
                )
                if disk_cached_pixmap:
                    # Add to L2 cache for faster access next time
                    self.cache_manager.put_scaled_image(cache_key, disk_cached_pixmap)
                    cached_images[image_path] = disk_cached_pixmap
                    continue

                # Check if raw image is cached
                raw_image = self.cache_manager.get_raw_image(image_path)
                if raw_image and not raw_image.isNull():
                    # Scale the cached raw image
                    pixmap = self.image_scaler.scale_for_screen_display(
                        raw_image,
                        image_path,
                        self.columns_per_row,
                        page_scale_factor,
                        current_page_index,
                    )
                    if pixmap and not pixmap.isNull():
                        # Cache the scaled result
                        self.cache_manager.put_scaled_image(cache_key, pixmap)
                        self.cache_manager.cache_to_disk(
                            image_path, pixmap, cell_size, page_scale_factor
                        )
                        cached_images[image_path] = pixmap

            except Exception as e:
                self.logger.debug(f"Error checking cache for {image_path}: {e}")
                continue

        return cached_images

    def load_image_with_consistent_scaling(
        self,
        image_path: str,
        page_scale_factor: float = 1.0,
        current_page_index: int = -1,
    ) -> QPixmap:
        """
        Load image with consistent scaling for screen display.

        This method ensures:
        1. Consistent relative sizing across all images
        2. Proper margins around each image
        3. High-quality scaling using SmoothTransformation
        4. Efficient LRU caching for performance
        5. Images fit completely within their grid cells
        6. Aspect ratio is maintained

        Args:
            image_path: Path to the image file
            page_scale_factor: Scale factor to apply
            current_page_index: Current page index for aspect ratio updates

        Returns:
            QPixmap: The scaled image for screen display
        """
        try:
            # Create cache key for scaled images
            cache_key = self.image_scaler.create_cache_key(
                image_path, self.columns_per_row, page_scale_factor
            )

            # Check Level 2 cache (scaled images) first
            cached_pixmap = self.cache_manager.get_scaled_image(cache_key)
            if cached_pixmap:
                self.logger.debug(f"L2 cache hit for screen display: {image_path}")
                return cached_pixmap

            # Check disk cache
            cell_size = self.page_factory.get_cell_size()
            disk_cached_pixmap = self.cache_manager.get_disk_cached_image(
                image_path, cell_size, page_scale_factor
            )
            if disk_cached_pixmap:
                self.logger.debug(f"Disk cache hit for screen display: {image_path}")
                # Add to L2 cache for faster access next time
                self.cache_manager.put_scaled_image(cache_key, disk_cached_pixmap)
                return disk_cached_pixmap

            # Cache miss - need to load and process image
            self.logger.debug(f"Cache miss - processing image: {image_path}")

            # Get raw image (from L1 cache or load from disk)
            image = self._get_raw_image(image_path)
            if not image or image.isNull():
                return self.image_scaler.quality_enhancer.create_error_pixmap(cell_size)

            # Scale image for screen display
            pixmap = self.image_scaler.scale_for_screen_display(
                image,
                image_path,
                self.columns_per_row,
                page_scale_factor,
                current_page_index,
            )

            # Cache the result
            self.cache_manager.put_scaled_image(cache_key, pixmap)
            self.cache_manager.cache_to_disk(
                image_path, pixmap, cell_size, page_scale_factor
            )

            return pixmap

        except Exception as e:
            self.logger.error(f"Error loading image for screen {image_path}: {e}")
            cell_size = self.page_factory.get_cell_size()
            return self.image_scaler.quality_enhancer.create_error_pixmap(cell_size)

    def load_image_for_export(
        self, image_path: str, export_target_width_px: int, export_target_height_px: int
    ) -> QPixmap:
        """
        Load and scale an image specifically for high-quality export.

        This method bypasses screen-related scaling factors and UI constraints,
        focusing solely on producing the highest quality image for export.

        Args:
            image_path: Path to the image file
            export_target_width_px: Maximum target width in pixels
            export_target_height_px: Maximum target height in pixels

        Returns:
            QPixmap: The high-quality scaled image for export
        """
        self.logger.debug(
            f"Loading image for EXPORT: {image_path} to fit within "
            f"{export_target_width_px}x{export_target_height_px}px"
        )

        try:
            # Get raw image (from L1 cache or load from disk)
            image = self._get_raw_image(image_path)
            if not image or image.isNull():
                return self.image_scaler.quality_enhancer.create_error_pixmap(
                    QSize(export_target_width_px, export_target_height_px)
                )

            # Scale image for export
            pixmap = self.image_scaler.scale_for_export(
                image, image_path, export_target_width_px, export_target_height_px
            )

            return pixmap

        except Exception as e:
            self.logger.error(f"Error in load_image_for_export for {image_path}: {e}")
            return self.image_scaler.quality_enhancer.create_error_pixmap(
                QSize(export_target_width_px, export_target_height_px)
            )

    def _get_raw_image(self, image_path: str):
        """
        Get raw QImage from cache or load from disk.

        Args:
            image_path: Path to the image file

        Returns:
            QImage if successful, None otherwise
        """
        # Check L1 cache (raw images) first
        cached_image = self.cache_manager.get_raw_image(image_path)
        if cached_image:
            self.logger.debug(f"L1 cache hit for raw image: {image_path}")
            return cached_image

        # Load from disk
        self.logger.debug(f"L1 cache miss. Loading raw image from disk: {image_path}")
        image = self.image_loader.load_image(image_path)

        if image and not image.isNull():
            # Add to L1 cache
            self.cache_manager.put_raw_image(image_path, image)

        return image

    def clear_cache(self) -> None:
        """Clear all image caches."""
        stats = self.cache_manager.clear_all_caches()
        self.logger.info(
            f"All caches cleared: {stats['raw_items_cleared']} raw items, "
            f"{stats['scaled_items_cleared']} scaled items"
        )

    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive performance statistics.

        Returns:
            Dictionary with performance metrics
        """
        return self.cache_manager.get_comprehensive_stats()

    def log_performance_stats(self) -> None:
        """Log current performance statistics."""
        stats = self.get_performance_stats()

        raw_stats = stats.get("raw_cache", {})
        scaled_stats = stats.get("scaled_cache", {})
        perf_stats = stats.get("performance", {})

        self.logger.info(
            f"ImageProcessor Performance: "
            f"Raw Cache: {raw_stats.get('hit_rate_percent', 0)}% hit rate, "
            f"Scaled Cache: {scaled_stats.get('hit_rate_percent', 0)}% hit rate, "
            f"Memory: {perf_stats.get('current_memory_mb', 0)}MB, "
            f"Disk Hit Rate: {perf_stats.get('disk_hit_rate_percent', 0)}%"
        )

    # Backward compatibility method
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
        self.logger.warning(
            "Legacy `load_image` called. Redirecting to `load_image_with_consistent_scaling`."
        )
        return self.load_image_with_consistent_scaling(
            image_path, page_scale_factor, current_page_index
        )
