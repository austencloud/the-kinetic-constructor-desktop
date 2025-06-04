"""
Qt-native image loader implementation for browse tab v2.

This service provides high-performance Qt-native image loading with
thread pool management and intelligent caching integration.
Replaces AsyncImageLoader to eliminate asyncio/Qt event loop conflicts.
"""

import logging
import time
from typing import Dict, List, Optional, Set
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal, QThread, QTimer, QMutex, QMutexLocker
from PyQt6.QtGui import QPixmap

logger = logging.getLogger(__name__)


class ImageLoadWorker(QThread):
    """Worker thread for loading images without blocking the UI."""
    
    # Signals
    image_loaded = pyqtSignal(str, QPixmap)  # image_path, pixmap
    load_failed = pyqtSignal(str, str)  # image_path, error_message
    
    def __init__(self, image_path: str, target_size: tuple = None):
        super().__init__()
        self.image_path = image_path
        self.target_size = target_size
        self._cancelled = False
        
    def cancel(self):
        """Cancel the loading operation."""
        self._cancelled = True
        
    def run(self):
        """Load image in background thread."""
        try:
            if self._cancelled:
                return
                
            # Check if file exists
            if not Path(self.image_path).exists():
                self.load_failed.emit(self.image_path, f"File not found: {self.image_path}")
                return
                
            # Load the image
            pixmap = QPixmap(self.image_path)
            
            if self._cancelled:
                return
                
            if pixmap.isNull():
                self.load_failed.emit(self.image_path, f"Failed to load image: {self.image_path}")
                return
                
            # Scale if target size specified
            if self.target_size and not self._cancelled:
                width, height = self.target_size
                pixmap = pixmap.scaled(
                    width, height,
                    aspectRatioMode=1,  # KeepAspectRatio
                    transformMode=1     # SmoothTransformation
                )
                
            if not self._cancelled:
                self.image_loaded.emit(self.image_path, pixmap)
                
        except Exception as e:
            if not self._cancelled:
                self.load_failed.emit(self.image_path, str(e))


class QtNativeImageLoader(QObject):
    """
    High-performance Qt-native image loading with caching.
    
    Features:
    - QThread-based parallel loading
    - Intelligent cache integration
    - Batch loading optimization
    - No asyncio dependencies
    """
    
    # Signals
    image_loaded = pyqtSignal(str, QPixmap)  # image_path, pixmap
    loading_progress = pyqtSignal(int, int)  # current, total
    batch_completed = pyqtSignal(dict)  # results dict
    
    def __init__(self, cache_service=None, config=None):
        super().__init__()
        
        from ..core.interfaces import BrowseTabConfig
        
        self.cache_service = cache_service
        self.config = config or BrowseTabConfig()
        
        # Thread management
        self.active_workers: Dict[str, ImageLoadWorker] = {}
        self.max_concurrent = getattr(self.config, 'max_concurrent_image_loads', 4)
        self.worker_queue: List[str] = []
        
        # Thread safety
        self.mutex = QMutex()
        
        # Performance tracking
        self.load_times: List[float] = []
        self.cache_hits = 0
        self.cache_misses = 0
        
        # Cancelled loads tracking
        self.cancelled_loads: Set[str] = set()
        
        logger.info(f"QtNativeImageLoader initialized with {self.max_concurrent} max concurrent loads")
        
    def load_image(self, image_path: str, target_size: tuple = None) -> None:
        """Load single image using Qt-native approach."""
        start_time = time.perf_counter()
        
        try:
            # Check if cancelled
            if image_path in self.cancelled_loads:
                logger.debug(f"Image load was cancelled: {image_path}")
                return
                
            # Check if already loading
            with QMutexLocker(self.mutex):
                if image_path in self.active_workers:
                    logger.debug(f"Image already loading: {image_path}")
                    return
                    
            # Check cache first (instant)
            if self.cache_service:
                try:
                    # Use synchronous cache check to avoid async complications
                    cached_pixmap = self._get_cached_image_sync(image_path, target_size)
                    if cached_pixmap:
                        self.cache_hits += 1
                        logger.debug(f"Cache hit for: {image_path}")
                        self.image_loaded.emit(image_path, cached_pixmap)
                        return
                except Exception as e:
                    logger.debug(f"Cache check failed for {image_path}: {e}")
                    
            self.cache_misses += 1
            
            # Load from disk using worker thread
            self._start_worker_load(image_path, target_size)
            
        except Exception as e:
            logger.error(f"Failed to start image load for {image_path}: {e}")
            
    def _get_cached_image_sync(self, image_path: str, target_size: tuple) -> Optional[QPixmap]:
        """Get cached image synchronously."""
        try:
            # Try to get from cache without async calls
            if hasattr(self.cache_service, 'get_cached_image_sync'):
                return self.cache_service.get_cached_image_sync(image_path, target_size)
            else:
                # Fallback - no cache available
                return None
        except Exception as e:
            logger.debug(f"Sync cache access failed: {e}")
            return None
            
    def _start_worker_load(self, image_path: str, target_size: tuple):
        """Start worker thread to load image."""
        try:
            with QMutexLocker(self.mutex):
                # Check if we can start immediately
                if len(self.active_workers) < self.max_concurrent:
                    self._create_and_start_worker(image_path, target_size)
                else:
                    # Add to queue
                    if image_path not in self.worker_queue:
                        self.worker_queue.append(image_path)
                        logger.debug(f"Added {image_path} to worker queue")
                        
        except Exception as e:
            logger.error(f"Failed to start worker load: {e}")
            
    def _create_and_start_worker(self, image_path: str, target_size: tuple):
        """Create and start a worker thread."""
        try:
            worker = ImageLoadWorker(image_path, target_size)
            
            # Connect signals
            worker.image_loaded.connect(self._on_image_loaded)
            worker.load_failed.connect(self._on_load_failed)
            worker.finished.connect(lambda: self._on_worker_finished(image_path))
            
            # Track worker
            self.active_workers[image_path] = worker
            
            # Start worker
            worker.start()
            logger.debug(f"Started worker for: {image_path}")
            
        except Exception as e:
            logger.error(f"Failed to create worker for {image_path}: {e}")
            
    def _on_image_loaded(self, image_path: str, pixmap: QPixmap):
        """Handle successful image load."""
        try:
            # Cache the loaded image
            if self.cache_service and hasattr(self.cache_service, 'cache_image_sync'):
                try:
                    self.cache_service.cache_image_sync(image_path, pixmap)
                except Exception as e:
                    logger.debug(f"Failed to cache image {image_path}: {e}")
                    
            # Emit signal
            self.image_loaded.emit(image_path, pixmap)
            
        except Exception as e:
            logger.error(f"Failed to handle loaded image {image_path}: {e}")
            
    def _on_load_failed(self, image_path: str, error_message: str):
        """Handle failed image load."""
        logger.warning(f"Image load failed for {image_path}: {error_message}")
        
    def _on_worker_finished(self, image_path: str):
        """Handle worker thread completion."""
        try:
            with QMutexLocker(self.mutex):
                # Remove from active workers
                if image_path in self.active_workers:
                    worker = self.active_workers[image_path]
                    worker.deleteLater()
                    del self.active_workers[image_path]
                    
                # Start next worker from queue
                if self.worker_queue and len(self.active_workers) < self.max_concurrent:
                    next_path = self.worker_queue.pop(0)
                    if next_path not in self.cancelled_loads:
                        # Use QTimer to avoid recursive calls
                        QTimer.singleShot(10, lambda: self._create_and_start_worker(next_path, None))
                        
        except Exception as e:
            logger.error(f"Failed to handle worker finished for {image_path}: {e}")
            
    def load_batch(self, image_paths: List[str], target_size: tuple = None) -> None:
        """Load multiple images in parallel with progress tracking."""
        try:
            logger.debug(f"Starting batch load of {len(image_paths)} images")
            
            # Filter out cancelled loads
            valid_paths = [path for path in image_paths if path not in self.cancelled_loads]
            
            if not valid_paths:
                self.batch_completed.emit({})
                return
                
            # Track batch progress
            self._batch_total = len(valid_paths)
            self._batch_completed = 0
            self._batch_results = {}
            
            # Connect to track completion
            self.image_loaded.connect(self._on_batch_image_loaded)
            
            # Start loading all images
            for path in valid_paths:
                self.load_image(path, target_size)
                
        except Exception as e:
            logger.error(f"Batch loading failed: {e}")
            self.batch_completed.emit({})
            
    def _on_batch_image_loaded(self, image_path: str, pixmap: QPixmap):
        """Handle batch image completion."""
        try:
            self._batch_results[image_path] = pixmap
            self._batch_completed += 1
            
            # Emit progress
            self.loading_progress.emit(self._batch_completed, self._batch_total)
            
            # Check if batch complete
            if self._batch_completed >= self._batch_total:
                self.batch_completed.emit(self._batch_results.copy())
                # Disconnect to avoid memory leaks
                self.image_loaded.disconnect(self._on_batch_image_loaded)
                
        except Exception as e:
            logger.error(f"Failed to handle batch image completion: {e}")
            
    def cancel_load(self, image_path: str):
        """Cancel image loading."""
        try:
            self.cancelled_loads.add(image_path)
            
            with QMutexLocker(self.mutex):
                # Cancel active worker
                if image_path in self.active_workers:
                    worker = self.active_workers[image_path]
                    worker.cancel()
                    
                # Remove from queue
                if image_path in self.worker_queue:
                    self.worker_queue.remove(image_path)
                    
        except Exception as e:
            logger.error(f"Failed to cancel load for {image_path}: {e}")
            
    def cleanup(self):
        """Cleanup resources."""
        try:
            with QMutexLocker(self.mutex):
                # Cancel all active workers
                for worker in self.active_workers.values():
                    worker.cancel()
                    worker.wait(1000)  # Wait up to 1 second
                    worker.deleteLater()
                    
                self.active_workers.clear()
                self.worker_queue.clear()
                self.cancelled_loads.clear()
                
            logger.info("QtNativeImageLoader cleanup completed")
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
