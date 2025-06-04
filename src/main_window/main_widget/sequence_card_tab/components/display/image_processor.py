# src/main_window/main_widget/sequence_card_tab/components/display/image_processor.py
"""
Image Processor - Refactored with coordinator pattern.

This is now a lightweight wrapper around the ImageProcessorCoordinator
that maintains backward compatibility while using the new architecture.
"""

import logging
from typing import TYPE_CHECKING, Dict, Any, List
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import QSize

if TYPE_CHECKING:
    from ..pages.printable_factory import PrintablePageFactory

from .image_core.image_processor_coordinator import ImageProcessorCoordinator

DEFAULT_IMAGE_CACHE_SIZE = 1000

logger = logging.getLogger(__name__)


class ImageProcessor:
    """
    Image processor - now a lightweight wrapper around ImageProcessorCoordinator.

    This maintains backward compatibility while using the new refactored architecture
    with focused components following the Single Responsibility Principle.
    """

    def __init__(
        self,
        page_factory: "PrintablePageFactory",
        columns_per_row: int = 2,
        cache_size: int = DEFAULT_IMAGE_CACHE_SIZE,
    ):
        self.page_factory = page_factory

        # Initialize the coordinator that handles all the complexity
        self.coordinator = ImageProcessorCoordinator(
            page_factory, columns_per_row, cache_size
        )

        # Backward compatibility properties
        self.columns_per_row = columns_per_row
        self.cache_size = cache_size

        logger.info("ImageProcessor initialized with coordinator pattern")

    def set_columns_per_row(self, columns: int) -> None:
        """Set the number of columns per row for screen scaling calculations."""
        self.columns_per_row = columns
        self.coordinator.set_columns_per_row(columns)

    def clear_cache(self) -> None:
        """Clear all image caches."""
        self.coordinator.clear_cache()

    def load_images_batch_if_cached(
        self,
        image_paths: List[str],
        page_scale_factor: float = 1.0,
        current_page_index: int = -1,
    ) -> Dict[str, QPixmap]:
        """Load multiple images instantly if they are cached, bypassing async loading."""
        return self.coordinator.load_images_batch_if_cached(
            image_paths, page_scale_factor, current_page_index
        )

    # Backward compatibility methods - delegate to coordinator
    def load_image_with_consistent_scaling(
        self,
        image_path: str,
        page_scale_factor: float = 1.0,
        current_page_index: int = -1,
    ) -> QPixmap:
        """Load image with consistent scaling for screen display."""
        return self.coordinator.load_image_with_consistent_scaling(
            image_path, page_scale_factor, current_page_index
        )

    def load_image_for_export(
        self, image_path: str, export_target_width_px: int, export_target_height_px: int
    ) -> QPixmap:
        """Load and scale an image specifically for high-quality export."""
        return self.coordinator.load_image_for_export(
            image_path, export_target_width_px, export_target_height_px
        )

    def load_image(
        self,
        image_path: str,
        page_scale_factor: float = 1.0,
        current_page_index: int = -1,
    ) -> QPixmap:
        """Legacy method for backward compatibility."""
        return self.coordinator.load_image(
            image_path, page_scale_factor, current_page_index
        )

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics."""
        return self.coordinator.get_performance_stats()

    def log_performance_stats(self) -> None:
        """Log current performance statistics."""
        self.coordinator.log_performance_stats()

    # Backward compatibility properties
    @property
    def cache_hits(self) -> int:
        """Get cache hits for backward compatibility."""
        stats = self.coordinator.get_performance_stats()
        scaled_stats = stats.get("scaled_cache", {})
        return scaled_stats.get("hits", 0)

    @property
    def cache_misses(self) -> int:
        """Get cache misses for backward compatibility."""
        stats = self.coordinator.get_performance_stats()
        scaled_stats = stats.get("scaled_cache", {})
        return scaled_stats.get("misses", 0)

    @property
    def disk_cache_hits(self) -> int:
        """Get disk cache hits for backward compatibility."""
        stats = self.coordinator.get_performance_stats()
        perf_stats = stats.get("performance", {})
        return perf_stats.get("disk_cache_hits", 0)

    @property
    def disk_cache_misses(self) -> int:
        """Get disk cache misses for backward compatibility."""
        stats = self.coordinator.get_performance_stats()
        perf_stats = stats.get("performance", {})
        return perf_stats.get("disk_cache_misses", 0)

    @property
    def raw_image_cache(self) -> Dict[str, Any]:
        """Get raw image cache for backward compatibility."""

        # Return a dict-like interface that supports 'in' operator
        class CacheInterface:
            def __init__(self, cache_manager):
                self.cache_manager = cache_manager

            def __contains__(self, image_path: str) -> bool:
                """Check if image is in raw cache."""
                return self.cache_manager.get_raw_image(image_path) is not None

            def get(self, image_path: str, default=None):
                """Get image from raw cache."""
                result = self.cache_manager.get_raw_image(image_path)
                return result if result is not None else default

        return CacheInterface(self.coordinator.cache_manager)
