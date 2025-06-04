"""
Image Cache Manager - Coordinates between memory and disk caches.

Extracted from the monolithic ImageProcessor class to follow SRP.
"""

import logging
from typing import Optional, Dict, Any, List
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import QSize


from ..cache.memory_cache_manager import MemoryCacheManager
from ..cache.cache_performance_monitor import CachePerformanceMonitor
from ..disk_cache_manager import DiskCacheManager


class ImageCacheManager:
    """
    Coordinates between memory and disk caches for optimal performance.

    Responsibilities:
    - Coordinate memory and disk caches
    - Manage cache hierarchies
    - Handle cache statistics
    - Optimize cache performance
    """

    def __init__(self, cache_size: int = 1000):
        self.logger = logging.getLogger(__name__)

        # Initialize cache components
        self.raw_cache = MemoryCacheManager[QImage](cache_size // 2, "raw_image")
        self.scaled_cache = MemoryCacheManager[QPixmap](cache_size, "scaled_image")
        self.performance_monitor = CachePerformanceMonitor()

        # Initialize disk cache
        try:
            self.disk_cache = DiskCacheManager(max_cache_size_mb=1000)
            self.logger.info("Disk cache manager initialized successfully")
        except Exception as e:
            self.logger.warning(f"Failed to initialize disk cache: {e}")
            self.disk_cache = None

    def get_raw_image(self, image_path: str) -> Optional[QImage]:
        """
        Get raw image from cache using content-based key.

        Args:
            image_path: Path to image

        Returns:
            Cached QImage if found, None otherwise
        """
        self.performance_monitor.record_cache_operation()
        # Use content-based key for raw image cache
        content_key = self._create_content_based_key(image_path)
        return self.raw_cache.get(content_key)

    def get_raw_images_batch(self, image_paths: List[str]) -> Dict[str, QImage]:
        """
        Get multiple raw images from cache in a single operation.

        This method enables instant batch retrieval of cached raw images,
        optimizing performance for scenarios where multiple images need
        to be retrieved simultaneously.

        Args:
            image_paths: List of image paths to retrieve

        Returns:
            Dictionary mapping paths to cached QImages (only includes cache hits)
        """
        cached_images = {}
        for image_path in image_paths:
            self.performance_monitor.record_cache_operation()
            content_key = self._create_content_based_key(image_path)
            cached_image = self.raw_cache.get(content_key)
            if cached_image is not None:
                cached_images[image_path] = cached_image
        return cached_images

    def put_raw_image(self, image_path: str, image: QImage) -> None:
        """
        Put raw image in cache using content-based key.

        Args:
            image_path: Path to image
            image: QImage to cache
        """
        # Use content-based key for raw image cache
        content_key = self._create_content_based_key(image_path)
        self.raw_cache.put(content_key, image)

    def _create_content_based_key(self, image_path: str) -> str:
        """
        Create a content-based cache key for raw images.

        This ensures the same image content gets the same cache key
        regardless of how it's accessed (Show All vs specific sequence length).

        Args:
            image_path: Path to the image file

        Returns:
            Content-based cache key
        """
        import os
        import hashlib

        try:
            # Get file stats for content identification
            stat = os.stat(image_path)
            file_size = stat.st_size
            mtime = stat.st_mtime

            # Use filename (without path) + size + mtime for content ID
            filename = os.path.basename(image_path)
            content_data = f"raw_{filename}_{file_size}_{mtime}"

            # Create a hash for the cache key
            return hashlib.md5(content_data.encode()).hexdigest()[:16]

        except OSError:
            # Fallback to path-based hash if file stats unavailable
            return hashlib.md5(f"raw_{image_path}".encode()).hexdigest()[:16]

    def get_scaled_image(self, cache_key: str) -> Optional[QPixmap]:
        """
        Get scaled image from memory cache.

        Args:
            cache_key: Cache key for scaled image

        Returns:
            Cached QPixmap if found, None otherwise
        """
        return self.scaled_cache.get(cache_key)

    def put_scaled_image(self, cache_key: str, pixmap: QPixmap) -> None:
        """
        Put scaled image in memory cache.

        Args:
            cache_key: Cache key for scaled image
            pixmap: QPixmap to cache
        """
        self.scaled_cache.put(cache_key, pixmap)

    def get_disk_cached_image(
        self, image_path: str, cell_size: QSize, page_scale_factor: float
    ) -> Optional[QPixmap]:
        """
        Get image from disk cache.

        Args:
            image_path: Path to image
            cell_size: Cell size
            page_scale_factor: Scale factor

        Returns:
            Cached QPixmap if found, None otherwise
        """
        if not self.disk_cache:
            return None

        try:
            pixmap = self.disk_cache.get_cached_image(
                image_path, cell_size, page_scale_factor
            )
            if pixmap:
                self.performance_monitor.record_disk_cache_hit()
                return pixmap
            else:
                self.performance_monitor.record_disk_cache_miss()
                return None
        except Exception as e:
            self.logger.debug(f"Error accessing disk cache: {e}")
            self.performance_monitor.record_disk_cache_miss()
            return None

    def cache_to_disk(
        self,
        image_path: str,
        pixmap: QPixmap,
        cell_size: QSize,
        page_scale_factor: float,
    ) -> None:
        """
        Cache image to disk.

        Args:
            image_path: Path to image
            pixmap: QPixmap to cache
            cell_size: Cell size
            page_scale_factor: Scale factor
        """
        if not self.disk_cache:
            return

        try:
            self.disk_cache.cache_image(
                image_path, pixmap, cell_size, page_scale_factor
            )
        except Exception as e:
            self.logger.debug(f"Failed to cache image to disk: {e}")

    def clear_all_caches(self) -> Dict[str, int]:
        """
        Clear all caches.

        Returns:
            Dictionary with counts of cleared items
        """
        raw_count = self.raw_cache.clear()
        scaled_count = self.scaled_cache.clear()

        self.logger.info(
            f"All caches cleared: {raw_count} raw items, {scaled_count} scaled items"
        )

        return {
            "raw_items_cleared": raw_count,
            "scaled_items_cleared": scaled_count,
        }

    def cleanup_memory(self, cleanup_ratio: float = 0.5) -> Dict[str, int]:
        """
        Cleanup memory caches by removing oldest items.

        Args:
            cleanup_ratio: Ratio of cache to clean (0.0 to 1.0)

        Returns:
            Dictionary with counts of removed items
        """
        raw_to_remove = int(len(self.raw_cache) * cleanup_ratio)
        scaled_to_remove = int(len(self.scaled_cache) * cleanup_ratio)

        raw_removed = self.raw_cache.remove_oldest(raw_to_remove)
        scaled_removed = self.scaled_cache.remove_oldest(scaled_to_remove)

        self.logger.info(
            f"Memory cleanup: removed {raw_removed} raw, {scaled_removed} scaled items"
        )

        return {
            "raw_items_removed": raw_removed,
            "scaled_items_removed": scaled_removed,
        }

    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive cache statistics.

        Returns:
            Dictionary with all cache statistics
        """
        raw_stats = self.raw_cache.get_stats()
        scaled_stats = self.scaled_cache.get_stats()

        # Get disk cache stats if available
        disk_stats = {}
        if self.disk_cache:
            try:
                disk_stats = self.disk_cache.get_cache_stats()
            except Exception:
                pass

        performance_stats = self.performance_monitor.get_performance_stats(disk_stats)

        return {
            "raw_cache": raw_stats,
            "scaled_cache": scaled_stats,
            "performance": performance_stats,
            "disk_cache": disk_stats,
        }

    def optimize_cache(self, dry_run: bool = True) -> Dict[str, Any]:
        """
        Optimize the cache by removing redundant entries.

        This method uses the new content-based cache key strategy to identify
        and remove redundant cache entries that store the same image at the
        same size but were cached with different path-based keys.

        Args:
            dry_run: If True, only analyze what would be optimized without making changes

        Returns:
            Dictionary with optimization results
        """
        if not self.disk_cache or not hasattr(self.disk_cache, "cache_dir"):
            return {"error": "Disk cache not available for optimization"}

        try:
            from ....utils.cache_optimizer import CacheOptimizer

            optimizer = CacheOptimizer(self.disk_cache.cache_dir)
            return optimizer.optimize_cache(dry_run=dry_run)

        except Exception as e:
            self.logger.error(f"Error optimizing cache: {e}")
            return {"error": str(e)}

    def analyze_cache_redundancy(self) -> Dict[str, Any]:
        """
        Analyze the current cache for redundant entries.

        Returns:
            Dictionary with analysis results showing potential storage savings
        """
        if not self.disk_cache or not hasattr(self.disk_cache, "cache_dir"):
            return {"error": "Disk cache not available for analysis"}

        try:
            from main_window.main_widget.sequence_card_tab.utils.cache_optimizer import (
                CacheOptimizer,
            )

            optimizer = CacheOptimizer(self.disk_cache.cache_dir)
            return optimizer.analyze_cache_redundancy()

        except Exception as e:
            self.logger.error(f"Error analyzing cache: {e}")
            return {"error": str(e)}
