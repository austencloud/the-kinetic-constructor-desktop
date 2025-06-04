"""
Browse Tab Image Cache - Efficient caching system for browse tab images.

Based on the sequence card tab's successful caching implementation,
this provides memory and disk caching for browse tab thumbnail images
to eliminate redundant loading after first program run.
"""

import logging
import os
import time
from typing import Dict, Optional
from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QPixmap, QImage

from src.main_window.main_widget.sequence_card_tab.utils.cache_utils import (
    ThumbnailCache,
)


class BrowseImageCache:
    """
    Image cache manager for browse tab thumbnails.

    Features:
    - Memory caching with LRU eviction
    - Size-based cache keys for reuse across filters
    - Automatic cache cleanup
    - Performance monitoring
    """

    def __init__(self, cache_size: int = 500):
        self.logger = logging.getLogger(__name__)

        # Initialize thumbnail cache (reuses sequence card tab's implementation)
        self.thumbnail_cache = ThumbnailCache(cache_size)

        # Performance tracking
        self.cache_hits = 0
        self.cache_misses = 0
        self.total_requests = 0

        self.logger.info(f"Browse image cache initialized with size: {cache_size}")

    def get_cached_image(self, image_path: str, size: QSize) -> Optional[QPixmap]:
        """
        Get a cached thumbnail image.

        Args:
            image_path: Path to the original image
            size: Desired thumbnail size

        Returns:
            QPixmap if cached, None if not in cache
        """
        self.total_requests += 1

        try:
            # Check if file exists
            if not os.path.exists(image_path):
                self.cache_misses += 1
                return None

            # Try to get from cache
            cached_pixmap = self.thumbnail_cache.get(image_path, size)

            if cached_pixmap:
                self.cache_hits += 1
                self.logger.debug(f"Cache hit for {os.path.basename(image_path)}")
                return cached_pixmap
            else:
                self.cache_misses += 1
                self.logger.debug(f"Cache miss for {os.path.basename(image_path)}")
                return None

        except Exception as e:
            self.logger.warning(f"Error accessing cache for {image_path}: {e}")
            self.cache_misses += 1
            return None

    def cache_image(self, image_path: str, pixmap: QPixmap, size: QSize) -> bool:
        """
        Cache a thumbnail image.

        Args:
            image_path: Path to the original image
            pixmap: Thumbnail pixmap to cache
            size: Size of the thumbnail

        Returns:
            True if caching succeeded
        """
        try:
            if pixmap.isNull():
                return False

            # Store in cache
            self.thumbnail_cache.put(image_path, pixmap, size)
            self.logger.debug(f"Cached thumbnail for {os.path.basename(image_path)}")
            return True

        except Exception as e:
            self.logger.warning(f"Error caching image {image_path}: {e}")
            return False

    def load_and_cache_image(self, image_path: str, size: QSize) -> Optional[QPixmap]:
        """
        Load an image from disk and cache it.

        Args:
            image_path: Path to the image file
            size: Desired thumbnail size

        Returns:
            QPixmap if successful, None otherwise
        """
        try:
            # Check cache first
            cached = self.get_cached_image(image_path, size)
            if cached:
                return cached

            # Load from disk
            if not os.path.exists(image_path):
                return None

            # Load original image
            image = QImage(image_path)
            if image.isNull():
                self.logger.warning(f"Failed to load image: {image_path}")
                return None

            # Scale to desired size
            scaled_image = image.scaled(
                size,
                aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio,
                transformMode=Qt.TransformationMode.SmoothTransformation,
            )

            # Convert to pixmap
            pixmap = QPixmap.fromImage(scaled_image)

            # Cache the result
            self.cache_image(image_path, pixmap, size)

            return pixmap

        except Exception as e:
            self.logger.error(f"Error loading and caching image {image_path}: {e}")
            return None

    def get_batch_cached_images(
        self, image_paths: list[str], size: QSize
    ) -> Dict[str, QPixmap]:
        """
        Get multiple cached images in a single operation.

        Args:
            image_paths: List of image paths
            size: Desired thumbnail size

        Returns:
            Dictionary mapping paths to cached pixmaps
        """
        cached_images = {}

        for path in image_paths:
            cached = self.get_cached_image(path, size)
            if cached:
                cached_images[path] = cached

        return cached_images

    def clear_cache(self):
        """Clear the entire cache."""
        self.thumbnail_cache.clear()
        self.cache_hits = 0
        self.cache_misses = 0
        self.total_requests = 0
        self.logger.info("Browse image cache cleared")

    def get_cache_stats(self) -> dict:
        """Get cache performance statistics."""
        hit_rate = (
            (self.cache_hits / self.total_requests * 100)
            if self.total_requests > 0
            else 0
        )

        return {
            "total_requests": self.total_requests,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "hit_rate_percent": round(hit_rate, 2),
            "cache_size": len(self.thumbnail_cache.cache),
        }

    def log_cache_performance(self):
        """Log cache performance statistics."""
        stats = self.get_cache_stats()
        self.logger.info(
            f"Browse cache stats - Requests: {stats['total_requests']}, "
            f"Hits: {stats['cache_hits']}, "
            f"Hit rate: {stats['hit_rate_percent']}%, "
            f"Cache size: {stats['cache_size']}"
        )


# Global cache instance
_browse_cache_instance: Optional[BrowseImageCache] = None


def get_browse_cache() -> BrowseImageCache:
    """Get the global browse image cache instance."""
    global _browse_cache_instance

    if _browse_cache_instance is None:
        _browse_cache_instance = BrowseImageCache()

    return _browse_cache_instance


def clear_browse_cache():
    """Clear the global browse image cache."""
    global _browse_cache_instance

    if _browse_cache_instance:
        _browse_cache_instance.clear_cache()
