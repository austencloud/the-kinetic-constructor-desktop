"""
Fast Image Service - Pre-scaling and Caching

This service pre-scales images to display size to eliminate runtime scaling bottlenecks.

Key optimizations:
1. Pre-scale images to exact display dimensions
2. Aggressive caching with LRU eviction
3. Background loading with priority queue
4. Memory-efficient storage
5. Fast synchronous access for UI

Performance targets:
- <1ms image retrieval from cache
- <50MB memory usage for 200+ cached images
- Background scaling without UI blocking
"""

import logging
import os
import threading
import time
import queue
from typing import Dict, Optional, Tuple, List
from queue import Queue, PriorityQueue
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import QSize, Qt, QObject, pyqtSignal

logger = logging.getLogger(__name__)


class ImageCacheEntry:
    """Cached image entry with metadata."""

    def __init__(self, pixmap: QPixmap, file_size: int, access_time: float):
        self.pixmap = pixmap
        self.file_size = file_size
        self.access_time = access_time
        self.access_count = 1

    def update_access(self):
        """Update access time and count."""
        self.access_time = time.time()
        self.access_count += 1


class FastImageService(QObject):
    """
    High-performance image service with pre-scaling and caching.
    """

    # Signals
    image_ready = pyqtSignal(str, QPixmap)  # path, scaled_pixmap
    cache_stats_updated = pyqtSignal(int, int, int)  # cached_count, memory_mb, hit_rate

    # Global instance for progressive loading
    _global_instance = None

    def __init__(self, target_width: int = 260, target_height: int = 220):
        super().__init__()

        self.target_width = target_width
        self.target_height = target_height
        self.target_size = QSize(target_width, target_height)

        # Set as global instance for progressive loading
        FastImageService._global_instance = self

        # Cache configuration
        self.max_cache_size_mb = 50  # Maximum cache size in MB
        self.max_cache_entries = 200  # Maximum number of cached images

        # Cache storage
        self._cache: Dict[str, ImageCacheEntry] = {}
        self._cache_lock = threading.RLock()

        # Statistics
        self._cache_hits = 0
        self._cache_misses = 0
        self._total_memory_bytes = 0

        # Background loading
        self._loading_queue = PriorityQueue()
        self._loading_thread = None
        self._stop_loading = False

        # Currently loading paths to prevent duplicates
        self._loading_paths = set()
        self._loading_lock = threading.Lock()

        self._start_background_loader()

        logger.info(
            f"FastImageService initialized: {target_width}x{target_height} target size"
        )

    def get_image_sync(self, image_path: str) -> Optional[QPixmap]:
        """
        Get image synchronously from cache with performance monitoring.

        Returns None if not cached - use queue_image_load() to load it.
        """
        cache_start_time = time.time()

        with self._cache_lock:
            if image_path in self._cache:
                entry = self._cache[image_path]
                entry.update_access()
                self._cache_hits += 1

                cache_time = (time.time() - cache_start_time) * 1000

                # Monitor cache access performance
                if cache_time > 1.0:  # Warn if cache access takes >1ms
                    logger.warning(
                        f"Slow cache access: {cache_time:.2f}ms for {os.path.basename(image_path)}"
                    )

                # Periodic cache performance reporting
                if (self._cache_hits + self._cache_misses) % 100 == 0:
                    self._report_cache_performance()

                return entry.pixmap
            else:
                self._cache_misses += 1

                # Log cache miss for analysis
                logger.debug(f"Cache miss for {os.path.basename(image_path)}")

                return None

    def _report_cache_performance(self):
        """Report comprehensive cache performance metrics."""
        total_requests = self._cache_hits + self._cache_misses
        if total_requests == 0:
            return

        hit_rate = (self._cache_hits / total_requests) * 100
        memory_mb = self._total_memory_bytes / (1024 * 1024)

        # Performance grade based on hit rate
        if hit_rate >= 80:
            grade = "EXCELLENT"
        elif hit_rate >= 60:
            grade = "GOOD"
        elif hit_rate >= 40:
            grade = "ACCEPTABLE"
        else:
            grade = "POOR"

        logger.info(
            f"IMAGE CACHE PERFORMANCE [{grade}]: "
            f"hit_rate={hit_rate:.1f}% ({self._cache_hits}/{total_requests}), "
            f"cached_images={len(self._cache)}, "
            f"memory={memory_mb:.1f}MB/{self.max_cache_size_mb}MB"
        )

        # Emit cache stats signal
        self.cache_stats_updated.emit(len(self._cache), int(memory_mb), int(hit_rate))

    def queue_image_load(self, image_path: str, priority: int = 5):
        """
        Queue image for background loading.

        Priority: 1 = highest, 10 = lowest
        """
        logger.debug(
            f"🖼️ QUEUE_IMAGE: Requested path='{image_path}', priority={priority}"
        )

        if not os.path.exists(image_path):
            logger.warning(f"🖼️ IMAGE_NOT_FOUND: File does not exist - '{image_path}'")
            return

        with self._loading_lock:
            if image_path in self._loading_paths:
                logger.debug(f"🖼️ ALREADY_QUEUED: '{image_path}'")
                return  # Already queued

            if image_path in self._cache:
                logger.debug(f"🖼️ ALREADY_CACHED: '{image_path}'")
                return  # Already cached

            self._loading_paths.add(image_path)

        # Add to priority queue
        self._loading_queue.put((priority, time.time(), image_path))

    def queue_multiple_images(self, image_paths: List[str], priority: int = 5):
        """Queue multiple images for loading."""
        for path in image_paths:
            self.queue_image_load(path, priority)

    def preload_visible_images(self, image_paths: List[str]):
        """Preload images that are currently visible (high priority)."""
        for path in image_paths:
            self.queue_image_load(path, priority=1)  # Highest priority

    def _start_background_loader(self):
        """Start background loading thread."""
        self._loading_thread = threading.Thread(
            target=self._background_loader, daemon=True, name="FastImageLoader"
        )
        self._loading_thread.start()

    def _background_loader(self):
        """Background thread for image loading and scaling."""
        logger.info("Background image loader started")

        while not self._stop_loading:
            try:
                # Get next item from queue (blocks if empty)
                priority, queued_time, image_path = self._loading_queue.get(timeout=1.0)
                logger.debug(
                    f"🖼️ BACKGROUND_LOADER: Processing '{image_path}' (priority={priority})"
                )

                # Remove from loading set
                with self._loading_lock:
                    self._loading_paths.discard(image_path)

                # Check if still needed (not cached)
                with self._cache_lock:
                    if image_path in self._cache:
                        logger.debug(
                            f"🖼️ BACKGROUND_LOADER: Already cached, skipping '{image_path}'"
                        )
                        continue

                # Load and scale image
                scaled_pixmap = self._load_and_scale_image(image_path)

                if scaled_pixmap and not scaled_pixmap.isNull():
                    logger.debug(
                        f"🖼️ BACKGROUND_LOADER: Successfully loaded '{image_path}', size={scaled_pixmap.size()}"
                    )
                    # Add to cache
                    self._add_to_cache(image_path, scaled_pixmap)

                    # Emit signal
                    self.image_ready.emit(image_path, scaled_pixmap)
                    logger.debug(
                        f"🖼️ BACKGROUND_LOADER: Emitted image_ready signal for '{image_path}'"
                    )

                    # Update stats
                    self._update_cache_stats()
                else:
                    logger.error(f"🖼️ BACKGROUND_LOADER: Failed to load '{image_path}'")

                # Mark task as done
                self._loading_queue.task_done()

            except queue.Empty:
                # This is normal when queue is empty - no need to log as error
                continue
            except Exception as e:
                if not self._stop_loading:  # Don't log errors during shutdown
                    logger.error(
                        f"Background loading error for {image_path if 'image_path' in locals() else 'unknown'}: {e}"
                    )
                    import traceback

                    logger.error(f"Traceback: {traceback.format_exc()}")

        logger.info("Background image loader stopped")

    def _load_and_scale_image(self, image_path: str) -> Optional[QPixmap]:
        """Load and scale image using width-first scaling for optimal cache performance."""
        try:
            logger.debug(f"🖼️ LOAD_AND_SCALE: Starting to load '{image_path}'")
            start_time = time.time()

            # Load original image
            original_pixmap = QPixmap(image_path)

            if original_pixmap.isNull():
                logger.error(
                    f"🖼️ LOAD_AND_SCALE: Failed to load image (QPixmap.isNull): {image_path}"
                )
                return None

            logger.debug(
                f"🖼️ LOAD_AND_SCALE: Original image loaded, size={original_pixmap.size()}"
            )

            # Width-first scaling for consistent cache keys
            original_size = original_pixmap.size()
            target_width = self.target_width
            target_height = self.target_height

            # Calculate scaling based on width-first approach
            width_scale = target_width / original_size.width()
            height_scale = target_height / original_size.height()

            # Use the smaller scale to ensure image fits within bounds
            scale_factor = min(width_scale, height_scale)

            # Calculate final dimensions (width-first)
            final_width = int(original_size.width() * scale_factor)
            final_height = int(original_size.height() * scale_factor)

            # Create target size with width-first dimensions
            final_size = QSize(final_width, final_height)

            # Scale to calculated size with high quality
            scaled_pixmap = original_pixmap.scaled(
                final_size,
                Qt.AspectRatioMode.IgnoreAspectRatio,  # We calculated aspect ratio manually
                Qt.TransformationMode.SmoothTransformation,
            )

            load_time = (time.time() - start_time) * 1000

            # Performance monitoring
            if load_time > 100:  # Warn if scaling takes >100ms
                logger.warning(
                    f"Slow image scaling: {load_time:.1f}ms for {os.path.basename(image_path)}"
                )

            logger.debug(
                f"Width-first scaled image {os.path.basename(image_path)} in {load_time:.1f}ms: "
                f"{original_size.width()}x{original_size.height()} -> "
                f"{final_width}x{final_height} (scale={scale_factor:.3f})"
            )

            return scaled_pixmap

        except Exception as e:
            logger.error(f"Error loading/scaling image {image_path}: {e}")
            return None

    def _add_to_cache(self, image_path: str, pixmap: QPixmap):
        """Add image to cache with size management."""
        with self._cache_lock:
            # Calculate memory usage
            pixmap_bytes = pixmap.width() * pixmap.height() * 4  # Assume 32-bit RGBA

            # Check if we need to evict entries
            self._ensure_cache_space(pixmap_bytes)

            # Add new entry
            entry = ImageCacheEntry(pixmap, pixmap_bytes, time.time())
            self._cache[image_path] = entry
            self._total_memory_bytes += pixmap_bytes

            logger.debug(
                f"Cached image: {os.path.basename(image_path)} "
                f"({pixmap_bytes // 1024}KB, {len(self._cache)} total)"
            )

    def _ensure_cache_space(self, new_entry_bytes: int):
        """Ensure cache has space for new entry."""
        # Check entry count limit
        while len(self._cache) >= self.max_cache_entries:
            self._evict_lru_entry()

        # Check memory limit
        max_bytes = self.max_cache_size_mb * 1024 * 1024
        while (self._total_memory_bytes + new_entry_bytes) > max_bytes:
            if not self._evict_lru_entry():
                break  # No more entries to evict

    def _evict_lru_entry(self) -> bool:
        """Evict least recently used entry."""
        if not self._cache:
            return False

        # Find LRU entry
        lru_path = min(
            self._cache.keys(), key=lambda path: self._cache[path].access_time
        )

        # Remove entry
        entry = self._cache.pop(lru_path)
        self._total_memory_bytes -= entry.file_size

        logger.debug(f"Evicted LRU entry: {os.path.basename(lru_path)}")
        return True

    def _update_cache_stats(self):
        """Update and emit cache statistics."""
        with self._cache_lock:
            cached_count = len(self._cache)
            memory_mb = self._total_memory_bytes // (1024 * 1024)

            total_requests = self._cache_hits + self._cache_misses
            hit_rate = int(
                (self._cache_hits / total_requests * 100) if total_requests > 0 else 0
            )

        self.cache_stats_updated.emit(cached_count, memory_mb, hit_rate)

    def get_cache_stats(self) -> Dict[str, int]:
        """Get current cache statistics."""
        with self._cache_lock:
            total_requests = self._cache_hits + self._cache_misses
            hit_rate = int(
                (self._cache_hits / total_requests * 100) if total_requests > 0 else 0
            )

            return {
                "cached_count": len(self._cache),
                "memory_mb": self._total_memory_bytes // (1024 * 1024),
                "hit_rate": hit_rate,
                "cache_hits": self._cache_hits,
                "cache_misses": self._cache_misses,
                "queue_size": self._loading_queue.qsize(),
            }

    def clear_cache(self):
        """Clear all cached images."""
        with self._cache_lock:
            self._cache.clear()
            self._total_memory_bytes = 0
            self._cache_hits = 0
            self._cache_misses = 0

        logger.info("Image cache cleared")

    def shutdown(self):
        """Shutdown the service and cleanup resources."""
        logger.info("Shutting down FastImageService")

        # Stop background loader
        self._stop_loading = True

        if self._loading_thread and self._loading_thread.is_alive():
            self._loading_thread.join(timeout=2.0)

        # Clear cache
        self.clear_cache()

        logger.info("FastImageService shutdown complete")


# Global service instance
_global_image_service: Optional[FastImageService] = None


def get_image_service() -> FastImageService:
    """Get global image service instance."""
    global _global_image_service

    if _global_image_service is None:
        _global_image_service = FastImageService()

    return _global_image_service


def shutdown_image_service():
    """Shutdown global image service."""
    global _global_image_service

    if _global_image_service:
        _global_image_service.shutdown()
        _global_image_service = None
