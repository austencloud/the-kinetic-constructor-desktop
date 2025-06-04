"""
Async image loader implementation for browse tab v2.

This service provides high-performance async image loading with
thread pool management and intelligent caching integration.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Set
from pathlib import Path
from concurrent.futures import Future

from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import QObject, pyqtSignal, QMetaObject, Qt, Q_ARG
from PyQt6.QtCore import QRunnable, QThreadPool

from ..core.interfaces import BrowseTabConfig

logger = logging.getLogger(__name__)


class ImageLoadWorker(QRunnable):
    """Worker for loading images in background thread."""

    def __init__(
        self,
        image_path: str,
        target_size: tuple,
        future: asyncio.Future,
        result_callback,
    ):
        super().__init__()
        self.image_path = image_path
        self.target_size = target_size
        self.future = future
        self.result_callback = result_callback
        self.setAutoDelete(True)

    def run(self):
        """Load image in background thread."""
        try:
            # Load pixmap
            pixmap = QPixmap(self.image_path)

            if pixmap.isNull():
                self.result_callback(
                    self.future, None, f"Failed to load image: {self.image_path}"
                )
                return

            # Scale if needed
            if self.target_size:
                pixmap = pixmap.scaled(
                    *self.target_size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )

            # Set result
            self.result_callback(self.future, pixmap, None)

        except Exception as e:
            self.result_callback(self.future, None, str(e))


class AsyncImageLoader(QObject):
    """
    High-performance async image loading with caching.

    Features:
    - Thread pool for parallel loading
    - Intelligent cache integration
    - Batch loading optimization
    - Load cancellation support
    - Performance monitoring
    """

    # Signals
    image_loaded = pyqtSignal(str, QPixmap)  # path, pixmap
    batch_loaded = pyqtSignal(dict)  # {path: pixmap}
    loading_progress = pyqtSignal(int, int)  # current, total

    def __init__(self, cache_service, config: BrowseTabConfig = None):
        super().__init__()

        self.cache_service = cache_service
        self.config = config or BrowseTabConfig()

        # Thread pool for I/O operations
        self.thread_pool = QThreadPool()
        self.thread_pool.setMaxThreadCount(self.config.max_concurrent_image_loads)

        # Active loading operations
        self.active_loads: Dict[str, Future] = {}
        self.cancelled_loads: Set[str] = set()

        # Performance tracking
        self.load_times: List[float] = []
        self.cache_hits = 0
        self.cache_misses = 0

        logger.info(
            f"AsyncImageLoader initialized with {self.config.max_concurrent_image_loads} threads"
        )

    async def load_image_async(
        self, image_path: str, target_size: tuple = None
    ) -> Optional[QPixmap]:
        """Load single image asynchronously with caching."""
        start_time = time.perf_counter()

        try:
            # Check if already loading
            if image_path in self.active_loads:
                logger.debug(f"Image already loading: {image_path}")
                return await self.active_loads[image_path]

            # Check if cancelled
            if image_path in self.cancelled_loads:
                logger.debug(f"Image load was cancelled: {image_path}")
                return None

            # 1. Check cache first (instant)
            cached_pixmap = await self.cache_service.get_cached_image(
                image_path, target_size
            )
            if cached_pixmap:
                self.cache_hits += 1
                logger.debug(f"Cache hit for: {image_path}")
                return cached_pixmap

            self.cache_misses += 1

            # 2. Load from disk (async)
            pixmap = await self._load_from_disk_async(image_path, target_size)

            if pixmap and image_path not in self.cancelled_loads:
                # Cache the loaded image
                await self.cache_service.cache_image(image_path, pixmap, target_size)

                # Emit signal
                self.image_loaded.emit(image_path, pixmap)

            load_time = time.perf_counter() - start_time
            self.load_times.append(load_time)

            return pixmap

        except Exception as e:
            logger.error(f"Failed to load image {image_path}: {e}")
            return None

        finally:
            # Clean up active loads
            if image_path in self.active_loads:
                del self.active_loads[image_path]

    async def load_batch_async(
        self, image_paths: List[str], target_size: tuple = None
    ) -> Dict[str, QPixmap]:
        """Load multiple images in parallel with progress tracking."""
        start_time = time.perf_counter()

        try:
            if not image_paths:
                return {}

            logger.info(f"Loading batch of {len(image_paths)} images")

            # Create tasks for all images
            tasks = []
            for i, path in enumerate(image_paths):
                if path not in self.cancelled_loads:
                    task = self.load_image_async(path, target_size)
                    tasks.append((path, task))

                    # Emit progress
                    self.loading_progress.emit(i + 1, len(image_paths))

            # Wait for all tasks to complete
            results = {}
            completed = 0

            for path, task in tasks:
                try:
                    pixmap = await task
                    if pixmap:
                        results[path] = pixmap

                    completed += 1
                    self.loading_progress.emit(completed, len(image_paths))

                except Exception as e:
                    logger.error(f"Failed to load {path}: {e}")

            # Emit batch completion signal
            self.batch_loaded.emit(results)

            load_time = time.perf_counter() - start_time
            logger.info(
                f"Batch loaded {len(results)}/{len(image_paths)} images in {load_time:.3f}s"
            )

            return results

        except Exception as e:
            logger.error(f"Batch loading failed: {e}")
            return {}

    def cancel_loading(self, image_path: str = None) -> None:
        """Cancel loading operations."""
        if image_path:
            # Cancel specific image
            self.cancelled_loads.add(image_path)
            if image_path in self.active_loads:
                future = self.active_loads[image_path]
                future.cancel()
                del self.active_loads[image_path]

            logger.debug(f"Cancelled loading: {image_path}")
        else:
            # Cancel all loading operations
            for path, future in self.active_loads.items():
                future.cancel()
                self.cancelled_loads.add(path)

            self.active_loads.clear()
            logger.info("Cancelled all loading operations")

    def clear_cancelled(self) -> None:
        """Clear cancelled loads list."""
        self.cancelled_loads.clear()

    def get_performance_stats(self) -> Dict[str, any]:
        """Get performance statistics."""
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total_requests * 100) if total_requests > 0 else 0

        stats = {
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": hit_rate,
            "active_loads": len(self.active_loads),
            "cancelled_loads": len(self.cancelled_loads),
            "avg_load_time": (
                sum(self.load_times) / len(self.load_times) if self.load_times else 0
            ),
            "thread_pool_active": self.thread_pool.activeThreadCount(),
            "thread_pool_max": self.thread_pool.maxThreadCount(),
        }

        return stats

    async def _load_from_disk_async(
        self, image_path: str, target_size: tuple
    ) -> Optional[QPixmap]:
        """Load image from disk using thread pool."""
        try:
            # Check if file exists
            if not Path(image_path).exists():
                logger.warning(f"Image file not found: {image_path}")
                return None

            # Create future for async operation
            loop = asyncio.get_event_loop()
            future = loop.create_future()

            # Track active load
            self.active_loads[image_path] = future

            # Create worker and submit to thread pool
            worker = ImageLoadWorker(
                image_path, target_size, future, self._handle_worker_result
            )

            self.thread_pool.start(worker)

            # Wait for result
            return await future

        except Exception as e:
            logger.error(f"Disk loading failed for {image_path}: {e}")
            return None

    def _handle_worker_result(
        self, future: asyncio.Future, pixmap: Optional[QPixmap], error: Optional[str]
    ) -> None:
        """Handle worker result in thread-safe way."""
        try:
            # Use QTimer for thread-safe main thread execution
            from PyQt6.QtCore import QTimer

            def set_result():
                try:
                    if not future.done():
                        if error:
                            future.set_exception(Exception(error))
                        else:
                            future.set_result(pixmap)
                except Exception as e:
                    logger.error(f"Failed to set future result: {e}")

            QTimer.singleShot(0, set_result)

        except Exception as e:
            logger.error(f"Failed to handle worker result: {e}")

    def _set_future_result(
        self, future: asyncio.Future, pixmap: Optional[QPixmap], error: Optional[str]
    ) -> None:
        """Set future result in main thread."""
        try:
            if not future.done():
                if error:
                    future.set_exception(Exception(error))
                else:
                    future.set_result(pixmap)
        except Exception as e:
            logger.error(f"Failed to set future result: {e}")

    def cleanup(self) -> None:
        """Cleanup resources."""
        try:
            # Cancel all operations
            self.cancel_loading()

            # Wait for thread pool to finish
            self.thread_pool.waitForDone(5000)  # 5 second timeout

            # Clear tracking data
            self.active_loads.clear()
            self.cancelled_loads.clear()
            self.load_times.clear()

            logger.info("AsyncImageLoader cleanup completed")

        except Exception as e:
            logger.error(f"Cleanup failed: {e}")


class ImagePreloader(QObject):
    """
    Intelligent image preloader for browse tab.

    Preloads images based on viewport and user behavior patterns.
    """

    def __init__(self, image_loader: AsyncImageLoader, config: BrowseTabConfig = None):
        super().__init__()

        self.image_loader = image_loader
        self.config = config or BrowseTabConfig()

        # Preload queue
        self.preload_queue: List[str] = []
        self.preloading = False

        logger.info("ImagePreloader initialized")

    async def preload_viewport_images(
        self, visible_sequences: List[str], all_sequences: List[str], target_size: tuple
    ) -> None:
        """Preload images for viewport and surrounding area."""
        try:
            if self.preloading:
                return

            self.preloading = True

            # Calculate preload range
            buffer_size = (
                self.config.virtual_scroll_buffer_rows * self.config.default_columns
            )

            # Find visible range
            if visible_sequences and all_sequences:
                start_idx = 0
                for i, seq in enumerate(all_sequences):
                    if seq in visible_sequences:
                        start_idx = i
                        break

                # Preload range
                preload_start = max(0, start_idx - buffer_size)
                preload_end = min(
                    len(all_sequences), start_idx + len(visible_sequences) + buffer_size
                )

                preload_sequences = all_sequences[preload_start:preload_end]

                # Preload in background
                await self.image_loader.load_batch_async(preload_sequences, target_size)

        except Exception as e:
            logger.error(f"Viewport preloading failed: {e}")

        finally:
            self.preloading = False

    def add_to_preload_queue(self, image_paths: List[str]) -> None:
        """Add images to preload queue."""
        for path in image_paths:
            if path not in self.preload_queue:
                self.preload_queue.append(path)

    async def process_preload_queue(self, target_size: tuple) -> None:
        """Process preload queue in background."""
        if not self.preload_queue or self.preloading:
            return

        try:
            self.preloading = True

            # Process in batches
            batch_size = 10
            while self.preload_queue:
                batch = self.preload_queue[:batch_size]
                self.preload_queue = self.preload_queue[batch_size:]

                await self.image_loader.load_batch_async(batch, target_size)

                # Small delay to prevent overwhelming the system
                await asyncio.sleep(0.1)

        except Exception as e:
            logger.error(f"Preload queue processing failed: {e}")

        finally:
            self.preloading = False
