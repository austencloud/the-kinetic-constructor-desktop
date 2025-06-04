"""
Performance Cache Service - Clean Architecture Implementation.

Handles caching and optimization with single responsibility.
Provides cache management, performance monitoring, and optimization strategies.

Features:
- Multi-layer caching (memory, compressed, disk)
- Cache key optimization based on display size
- Performance monitoring and metrics
- Memory management and cleanup
- Cache hit rate optimization

Performance Targets:
- >90% cache hit rate for images
- <10ms cache access time
- Efficient memory usage
- Automatic cache cleanup
"""

import logging
from typing import Dict, Any, Optional, Tuple, List
from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QElapsedTimer, QSize
from PyQt6.QtGui import QPixmap
import hashlib
import time
import gc

from ..core.interfaces import BrowseTabConfig

logger = logging.getLogger(__name__)


class PerformanceCacheService(QObject):
    """
    Service for performance caching and optimization.
    
    Single Responsibility: Manage caching and performance optimization
    
    Features:
    - Multi-layer caching with different strategies
    - Cache key optimization for maximum reuse
    - Performance monitoring and metrics
    - Memory management and automatic cleanup
    - Cache hit rate optimization
    """
    
    # Signals for service communication
    cache_hit = pyqtSignal(str, float)  # cache_key, access_time
    cache_miss = pyqtSignal(str, float)  # cache_key, access_time
    cache_cleaned = pyqtSignal(int, int)  # items_removed, memory_freed
    performance_alert = pyqtSignal(str, float)  # metric_name, value
    
    def __init__(self, config: BrowseTabConfig = None, parent: QObject = None):
        super().__init__(parent)
        
        self.config = config or BrowseTabConfig()
        
        # Cache layers
        self._memory_cache: Dict[str, QPixmap] = {}
        self._compressed_cache: Dict[str, bytes] = {}
        self._metadata_cache: Dict[str, Dict[str, Any]] = {}
        
        # Cache configuration
        self._max_memory_items = self.config.image_cache_size or 200
        self._max_compressed_items = self._max_memory_items * 2
        self._max_metadata_items = self._max_memory_items * 3
        
        # Performance tracking
        self._performance_timer = QElapsedTimer()
        self._cache_hits = 0
        self._cache_misses = 0
        self._access_times = []
        self._max_access_history = 1000
        
        # Memory management
        self._memory_usage = 0
        self._max_memory_mb = 100  # 100MB limit
        self._cleanup_timer = QTimer()
        self._cleanup_timer.timeout.connect(self._periodic_cleanup)
        self._cleanup_timer.start(30000)  # Cleanup every 30 seconds
        
        # Cache statistics
        self._cache_stats = {
            "total_requests": 0,
            "memory_hits": 0,
            "compressed_hits": 0,
            "total_misses": 0,
            "cleanup_count": 0,
            "memory_freed_mb": 0.0
        }
        
        logger.debug("PerformanceCacheService initialized")
    
    def get_cached_pixmap(self, cache_key: str) -> Optional[QPixmap]:
        """Get cached pixmap with performance tracking."""
        self._performance_timer.start()
        self._cache_stats["total_requests"] += 1
        
        try:
            # Try memory cache first (fastest)
            if cache_key in self._memory_cache:
                pixmap = self._memory_cache[cache_key]
                access_time = self._performance_timer.elapsed()
                
                self._record_cache_hit("memory", access_time)
                self._cache_stats["memory_hits"] += 1
                
                # Move to front (LRU)
                self._promote_cache_item(cache_key)
                
                return pixmap
            
            # Try compressed cache (slower but still fast)
            if cache_key in self._compressed_cache:
                compressed_data = self._compressed_cache[cache_key]
                pixmap = self._decompress_pixmap(compressed_data)
                
                if pixmap and not pixmap.isNull():
                    # Store in memory cache for next access
                    self._store_in_memory_cache(cache_key, pixmap)
                    
                    access_time = self._performance_timer.elapsed()
                    self._record_cache_hit("compressed", access_time)
                    self._cache_stats["compressed_hits"] += 1
                    
                    return pixmap
            
            # Cache miss
            access_time = self._performance_timer.elapsed()
            self._record_cache_miss(cache_key, access_time)
            self._cache_stats["total_misses"] += 1
            
            return None
            
        except Exception as e:
            logger.error(f"Cache access failed for {cache_key}: {e}")
            return None
    
    def store_pixmap(self, cache_key: str, pixmap: QPixmap, metadata: Dict[str, Any] = None):
        """Store pixmap in cache with optimization."""
        if not pixmap or pixmap.isNull():
            return
        
        try:
            # Store in memory cache
            self._store_in_memory_cache(cache_key, pixmap)
            
            # Store compressed version for backup
            compressed_data = self._compress_pixmap(pixmap)
            if compressed_data:
                self._store_in_compressed_cache(cache_key, compressed_data)
            
            # Store metadata if provided
            if metadata:
                self._metadata_cache[cache_key] = metadata
                self._cleanup_metadata_cache()
            
            logger.debug(f"Pixmap stored in cache: {cache_key}")
            
        except Exception as e:
            logger.error(f"Failed to store pixmap in cache: {e}")
    
    def _store_in_memory_cache(self, cache_key: str, pixmap: QPixmap):
        """Store pixmap in memory cache with size management."""
        # Calculate pixmap size
        pixmap_size = self._calculate_pixmap_size(pixmap)
        
        # Check if we need to make room
        while (len(self._memory_cache) >= self._max_memory_items or 
               self._memory_usage + pixmap_size > self._max_memory_mb * 1024 * 1024):
            self._evict_oldest_memory_item()
        
        # Store pixmap
        self._memory_cache[cache_key] = pixmap
        self._memory_usage += pixmap_size
        
        logger.debug(f"Memory cache: {len(self._memory_cache)}/{self._max_memory_items} items, "
                    f"{self._memory_usage / (1024*1024):.1f}MB")
    
    def _store_in_compressed_cache(self, cache_key: str, compressed_data: bytes):
        """Store compressed data in cache."""
        # Check if we need to make room
        while len(self._compressed_cache) >= self._max_compressed_items:
            self._evict_oldest_compressed_item()
        
        self._compressed_cache[cache_key] = compressed_data
    
    def _compress_pixmap(self, pixmap: QPixmap) -> Optional[bytes]:
        """Compress pixmap to bytes for storage."""
        try:
            from PyQt6.QtCore import QByteArray, QBuffer, QIODevice
            
            byte_array = QByteArray()
            buffer = QBuffer(byte_array)
            buffer.open(QIODevice.OpenModeFlag.WriteOnly)
            
            # Save as PNG with compression
            success = pixmap.save(buffer, "PNG", 50)  # 50% quality for compression
            
            if success:
                return byte_array.data()
            else:
                return None
                
        except Exception as e:
            logger.warning(f"Failed to compress pixmap: {e}")
            return None
    
    def _decompress_pixmap(self, compressed_data: bytes) -> Optional[QPixmap]:
        """Decompress bytes to pixmap."""
        try:
            pixmap = QPixmap()
            success = pixmap.loadFromData(compressed_data)
            
            if success and not pixmap.isNull():
                return pixmap
            else:
                return None
                
        except Exception as e:
            logger.warning(f"Failed to decompress pixmap: {e}")
            return None
    
    def _calculate_pixmap_size(self, pixmap: QPixmap) -> int:
        """Calculate approximate memory size of pixmap in bytes."""
        if pixmap.isNull():
            return 0
        
        # Approximate: width * height * 4 bytes per pixel (RGBA)
        return pixmap.width() * pixmap.height() * 4
    
    def _promote_cache_item(self, cache_key: str):
        """Promote cache item to front (LRU implementation)."""
        # For dict in Python 3.7+, moving to end simulates LRU
        if cache_key in self._memory_cache:
            pixmap = self._memory_cache.pop(cache_key)
            self._memory_cache[cache_key] = pixmap
    
    def _evict_oldest_memory_item(self):
        """Evict oldest item from memory cache."""
        if not self._memory_cache:
            return
        
        # Get oldest item (first in dict)
        oldest_key = next(iter(self._memory_cache))
        oldest_pixmap = self._memory_cache.pop(oldest_key)
        
        # Update memory usage
        pixmap_size = self._calculate_pixmap_size(oldest_pixmap)
        self._memory_usage -= pixmap_size
        
        logger.debug(f"Evicted from memory cache: {oldest_key}")
    
    def _evict_oldest_compressed_item(self):
        """Evict oldest item from compressed cache."""
        if not self._compressed_cache:
            return
        
        oldest_key = next(iter(self._compressed_cache))
        self._compressed_cache.pop(oldest_key)
        
        logger.debug(f"Evicted from compressed cache: {oldest_key}")
    
    def _cleanup_metadata_cache(self):
        """Cleanup metadata cache if it gets too large."""
        while len(self._metadata_cache) > self._max_metadata_items:
            oldest_key = next(iter(self._metadata_cache))
            self._metadata_cache.pop(oldest_key)
    
    def _record_cache_hit(self, cache_type: str, access_time: float):
        """Record cache hit for performance tracking."""
        self._cache_hits += 1
        self._access_times.append(access_time)
        
        # Limit access time history
        if len(self._access_times) > self._max_access_history:
            self._access_times.pop(0)
        
        self.cache_hit.emit(cache_type, access_time)
        
        # Performance target: <10ms cache access time
        if access_time > 10:
            logger.warning(f"Slow cache access: {access_time:.2f}ms > 10ms target")
            self.performance_alert.emit("slow_cache_access", access_time)
    
    def _record_cache_miss(self, cache_key: str, access_time: float):
        """Record cache miss for performance tracking."""
        self._cache_misses += 1
        self.cache_miss.emit(cache_key, access_time)
    
    def _periodic_cleanup(self):
        """Perform periodic cache cleanup."""
        try:
            initial_memory_items = len(self._memory_cache)
            initial_compressed_items = len(self._compressed_cache)
            initial_memory_usage = self._memory_usage
            
            # Force garbage collection
            gc.collect()
            
            # Check cache hit rate and adjust if needed
            hit_rate = self.get_cache_hit_rate()
            if hit_rate < 0.8:  # Less than 80% hit rate
                logger.info(f"Low cache hit rate: {hit_rate:.2%}, considering cache size increase")
            
            # Clean up invalid pixmaps
            invalid_keys = []
            for key, pixmap in self._memory_cache.items():
                if pixmap.isNull():
                    invalid_keys.append(key)
            
            for key in invalid_keys:
                pixmap = self._memory_cache.pop(key)
                self._memory_usage -= self._calculate_pixmap_size(pixmap)
            
            # Update statistics
            items_cleaned = (initial_memory_items - len(self._memory_cache) + 
                           initial_compressed_items - len(self._compressed_cache))
            memory_freed = (initial_memory_usage - self._memory_usage) / (1024 * 1024)
            
            if items_cleaned > 0:
                self._cache_stats["cleanup_count"] += 1
                self._cache_stats["memory_freed_mb"] += memory_freed
                self.cache_cleaned.emit(items_cleaned, int(memory_freed))
                
                logger.debug(f"Cache cleanup: {items_cleaned} items removed, "
                           f"{memory_freed:.1f}MB freed")
            
        except Exception as e:
            logger.error(f"Cache cleanup failed: {e}")
    
    def generate_cache_key(self, image_path: str, target_size: QSize, 
                          additional_params: Dict[str, Any] = None) -> str:
        """Generate optimized cache key based on display size."""
        try:
            # Base key components
            key_components = [
                image_path,
                f"{target_size.width()}x{target_size.height()}"
            ]
            
            # Add additional parameters if provided
            if additional_params:
                for key, value in sorted(additional_params.items()):
                    key_components.append(f"{key}:{value}")
            
            # Create hash for consistent key length
            key_string = "|".join(key_components)
            cache_key = hashlib.md5(key_string.encode()).hexdigest()
            
            return cache_key
            
        except Exception as e:
            logger.error(f"Failed to generate cache key: {e}")
            return f"fallback_{hash(image_path)}_{target_size.width()}x{target_size.height()}"
    
    # Public interface methods
    def get_cache_hit_rate(self) -> float:
        """Get current cache hit rate."""
        total_requests = self._cache_hits + self._cache_misses
        if total_requests == 0:
            return 0.0
        return self._cache_hits / total_requests
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        hit_rate = self.get_cache_hit_rate()
        avg_access_time = (sum(self._access_times) / len(self._access_times) 
                          if self._access_times else 0.0)
        
        stats = self._cache_stats.copy()
        stats.update({
            "cache_hit_rate": hit_rate,
            "memory_cache_size": len(self._memory_cache),
            "compressed_cache_size": len(self._compressed_cache),
            "metadata_cache_size": len(self._metadata_cache),
            "memory_usage_mb": self._memory_usage / (1024 * 1024),
            "average_access_time_ms": avg_access_time,
            "max_access_time_ms": max(self._access_times) if self._access_times else 0.0,
            "cache_efficiency": hit_rate * 100,  # Percentage
        })
        
        return stats
    
    def clear_cache(self, cache_type: str = "all"):
        """Clear specified cache type."""
        try:
            if cache_type in ["all", "memory"]:
                self._memory_cache.clear()
                self._memory_usage = 0
                logger.debug("Memory cache cleared")
            
            if cache_type in ["all", "compressed"]:
                self._compressed_cache.clear()
                logger.debug("Compressed cache cleared")
            
            if cache_type in ["all", "metadata"]:
                self._metadata_cache.clear()
                logger.debug("Metadata cache cleared")
            
            # Reset statistics if clearing all
            if cache_type == "all":
                self._cache_hits = 0
                self._cache_misses = 0
                self._access_times.clear()
                self._cache_stats = {key: 0 if isinstance(value, (int, float)) else value 
                                   for key, value in self._cache_stats.items()}
            
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
    
    def optimize_cache_size(self, target_hit_rate: float = 0.9):
        """Optimize cache size based on hit rate target."""
        try:
            current_hit_rate = self.get_cache_hit_rate()
            
            if current_hit_rate < target_hit_rate:
                # Increase cache size
                new_size = min(self._max_memory_items * 1.2, 500)  # Max 500 items
                self._max_memory_items = int(new_size)
                self._max_compressed_items = self._max_memory_items * 2
                
                logger.info(f"Cache size increased to {self._max_memory_items} items "
                           f"(hit rate: {current_hit_rate:.2%})")
            
            elif current_hit_rate > 0.95 and self._max_memory_items > 50:
                # Decrease cache size if hit rate is very high
                new_size = max(self._max_memory_items * 0.9, 50)  # Min 50 items
                self._max_memory_items = int(new_size)
                self._max_compressed_items = self._max_memory_items * 2
                
                logger.info(f"Cache size decreased to {self._max_memory_items} items "
                           f"(hit rate: {current_hit_rate:.2%})")
            
        except Exception as e:
            logger.error(f"Cache optimization failed: {e}")
    
    def preload_images(self, image_paths: List[str], target_size: QSize):
        """Preload images into cache for better performance."""
        try:
            preloaded_count = 0
            
            for image_path in image_paths:
                cache_key = self.generate_cache_key(image_path, target_size)
                
                # Skip if already cached
                if cache_key in self._memory_cache or cache_key in self._compressed_cache:
                    continue
                
                # Load and cache image
                pixmap = QPixmap(image_path)
                if not pixmap.isNull():
                    # Scale to target size
                    scaled_pixmap = pixmap.scaled(
                        target_size,
                        1,  # KeepAspectRatio
                        1   # SmoothTransformation
                    )
                    
                    self.store_pixmap(cache_key, scaled_pixmap)
                    preloaded_count += 1
            
            logger.debug(f"Preloaded {preloaded_count} images into cache")
            
        except Exception as e:
            logger.error(f"Image preloading failed: {e}")
    
    def cleanup(self):
        """Cleanup resources."""
        try:
            self._cleanup_timer.stop()
            self.clear_cache("all")
            logger.debug("PerformanceCacheService cleanup completed")
        except Exception as e:
            logger.error(f"PerformanceCacheService cleanup failed: {e}")
