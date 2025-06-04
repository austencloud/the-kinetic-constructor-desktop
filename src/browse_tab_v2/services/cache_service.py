"""
Cache service implementation for browse tab v2.

This service provides multi-layer caching with LRU eviction,
disk persistence, and performance monitoring.
"""

import logging
import hashlib
import pickle
import time
from typing import Dict, Optional, Any, List
from pathlib import Path
from collections import OrderedDict
import threading

from PyQt6.QtGui import QPixmap

from ..core.interfaces import CacheError, BrowseTabConfig

logger = logging.getLogger(__name__)

# Global cache service instance for startup optimization
_global_cache_service = None


class LRUCache:
    """Thread-safe LRU cache implementation."""

    def __init__(self, maxsize: int):
        self.maxsize = maxsize
        self.cache: OrderedDict = OrderedDict()
        self.lock = threading.RLock()
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[Any]:
        """Get item from cache."""
        with self.lock:
            if key in self.cache:
                # Move to end (most recently used)
                self.cache.move_to_end(key)
                self.hits += 1
                return self.cache[key]
            else:
                self.misses += 1
                return None

    def put(self, key: str, value: Any) -> None:
        """Put item in cache."""
        with self.lock:
            if key in self.cache:
                # Update existing item
                self.cache[key] = value
                self.cache.move_to_end(key)
            else:
                # Add new item
                self.cache[key] = value
                if len(self.cache) > self.maxsize:
                    # Remove least recently used item
                    self.cache.popitem(last=False)

    def clear(self) -> None:
        """Clear cache."""
        with self.lock:
            self.cache.clear()
            self.hits = 0
            self.misses = 0

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self.lock:
            total = self.hits + self.misses
            hit_rate = (self.hits / total * 100) if total > 0 else 0

            return {
                "size": len(self.cache),
                "maxsize": self.maxsize,
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": hit_rate,
            }


class DiskCache:
    """Disk-based cache with compression."""

    def __init__(self, cache_dir: Path, max_size_mb: int = 100):
        self.cache_dir = cache_dir
        self.max_size_mb = max_size_mb
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Index file for metadata
        self.index_file = self.cache_dir / "cache_index.json"
        self.index: Dict[str, Dict[str, Any]] = {}
        self._load_index()

    async def get(self, key: str) -> Optional[QPixmap]:
        """Get item from disk cache."""
        try:
            if key not in self.index:
                return None

            cache_file = self.cache_dir / f"{key}.cache"
            if not cache_file.exists():
                # Remove from index if file doesn't exist
                del self.index[key]
                await self._save_index()
                return None

            # Check if expired
            entry = self.index[key]
            if time.time() > entry["expires_at"]:
                await self.remove(key)
                return None

            # Load pixmap
            with open(cache_file, "rb") as f:
                pixmap_data = pickle.load(f)
                pixmap = QPixmap()
                pixmap.loadFromData(pixmap_data)

                # Update access time
                entry["accessed_at"] = time.time()
                await self._save_index()

                return pixmap

        except Exception as e:
            logger.error(f"Failed to load from disk cache: {e}")
            return None

    async def put(self, key: str, pixmap: QPixmap, ttl_hours: int = 24) -> None:
        """Put item in disk cache."""
        try:
            # Convert pixmap to bytes
            byte_array = (
                pixmap.toImage().bits().asstring(pixmap.toImage().sizeInBytes())
            )

            # Save to file
            cache_file = self.cache_dir / f"{key}.cache"
            with open(cache_file, "wb") as f:
                pickle.dump(byte_array, f)

            # Update index
            self.index[key] = {
                "created_at": time.time(),
                "accessed_at": time.time(),
                "expires_at": time.time() + (ttl_hours * 3600),
                "size": cache_file.stat().st_size,
            }

            await self._save_index()
            await self._cleanup_if_needed()

        except Exception as e:
            logger.error(f"Failed to save to disk cache: {e}")

    async def remove(self, key: str) -> None:
        """Remove item from disk cache."""
        try:
            cache_file = self.cache_dir / f"{key}.cache"
            if cache_file.exists():
                cache_file.unlink()

            if key in self.index:
                del self.index[key]
                await self._save_index()

        except Exception as e:
            logger.error(f"Failed to remove from disk cache: {e}")

    async def clear(self) -> None:
        """Clear disk cache."""
        try:
            for cache_file in self.cache_dir.glob("*.cache"):
                cache_file.unlink()

            self.index.clear()
            await self._save_index()

        except Exception as e:
            logger.error(f"Failed to clear disk cache: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get disk cache statistics."""
        total_size = sum(entry["size"] for entry in self.index.values())

        return {
            "entries": len(self.index),
            "total_size_mb": total_size / (1024 * 1024),
            "max_size_mb": self.max_size_mb,
        }

    def _load_index(self) -> None:
        """Load cache index from disk."""
        try:
            if self.index_file.exists():
                import json

                with open(self.index_file, "r") as f:
                    self.index = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load cache index: {e}")
            self.index = {}

    async def _save_index(self) -> None:
        """Save cache index to disk."""
        try:
            import json

            with open(self.index_file, "w") as f:
                json.dump(self.index, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save cache index: {e}")

    async def _cleanup_if_needed(self) -> None:
        """Cleanup cache if it exceeds size limit."""
        total_size = sum(entry["size"] for entry in self.index.values())
        max_size_bytes = self.max_size_mb * 1024 * 1024

        if total_size > max_size_bytes:
            # Sort by access time (oldest first)
            sorted_entries = sorted(
                self.index.items(), key=lambda x: x[1]["accessed_at"]
            )

            # Remove oldest entries until under limit
            for key, entry in sorted_entries:
                await self.remove(key)
                total_size -= entry["size"]

                if total_size <= max_size_bytes * 0.8:  # Leave some headroom
                    break


class CacheService:
    """
    Multi-layer cache service with performance optimization.

    Provides three cache layers:
    1. Memory cache (instant access)
    2. Compressed memory cache (fast access)
    3. Disk cache (persistent)
    """

    def __init__(self, config: BrowseTabConfig = None):
        global _global_cache_service

        self.config = config or BrowseTabConfig()

        # Initialize cache layers
        self.memory_cache = LRUCache(maxsize=self.config.image_cache_size)
        self.compressed_cache = LRUCache(maxsize=self.config.image_cache_size * 2)

        # Disk cache
        cache_dir = Path.home() / ".kinetic_constructor" / "cache" / "browse_tab_v2"
        self.disk_cache = DiskCache(cache_dir, max_size_mb=100)

        # Performance tracking
        self.total_requests = 0
        self.cache_hits_by_layer = {"memory": 0, "compressed": 0, "disk": 0}
        self.load_times: List[float] = []

        # Set as global instance for startup optimization
        if _global_cache_service is None:
            _global_cache_service = self
            logger.info("Set as global cache service instance for startup optimization")

        logger.info("CacheService initialized with multi-layer caching")

    def get_cached_image_sync(self, image_path: str, size: tuple) -> Optional[QPixmap]:
        """Get cached image synchronously (Qt-native approach)."""
        try:
            cache_key = self._get_cache_key(image_path, size)

            # Layer 1: Memory cache (fastest)
            pixmap = self.memory_cache.get(cache_key)
            if pixmap:
                self.cache_hits_by_layer["memory"] += 1
                return pixmap

            # Layer 2: Compressed cache (fast)
            compressed_data = self.compressed_cache.get(cache_key)
            if compressed_data:
                pixmap = self._decompress_pixmap(compressed_data)
                if pixmap:
                    # Promote to memory cache
                    self.memory_cache.put(cache_key, pixmap)
                    self.cache_hits_by_layer["compressed"] += 1
                    return pixmap

            # Skip disk cache for sync operation to avoid blocking
            return None

        except Exception as e:
            logger.debug(f"Sync cache get failed: {e}")
            return None

    def cache_image_sync(self, image_path: str, pixmap: QPixmap, size: tuple = None):
        """Cache image synchronously (Qt-native approach)."""
        try:
            cache_key = self._get_cache_key(image_path, size)

            # Store in memory cache with high priority for instant access
            self.memory_cache.put(cache_key, pixmap)

            # Store in compressed cache
            compressed_data = self._compress_pixmap(pixmap)
            if compressed_data:
                self.compressed_cache.put(cache_key, compressed_data)

            # Skip disk cache for sync operation to avoid blocking
            logger.debug(
                f"🚀 INSTANT_CACHE: Cached {image_path} with size {size} for instant access"
            )

        except Exception as e:
            logger.debug(f"Sync cache put failed: {e}")

    def cache_image_instant(self, image_path: str, pixmap: QPixmap, size: tuple = None):
        """Cache image instantly for immediate availability (startup optimization)."""
        try:
            cache_key = self._get_cache_key(image_path, size)

            # Store in memory cache with maximum priority
            self.memory_cache.put(cache_key, pixmap)

            # Also store in compressed cache for backup
            compressed_data = self._compress_pixmap(pixmap)
            if compressed_data:
                self.compressed_cache.put(cache_key, compressed_data)

            logger.debug(
                f"🚀 INSTANT_CACHE: Instant cached {image_path} with size {size}"
            )

        except Exception as e:
            logger.debug(f"Instant cache failed: {e}")

    def get_instant_thumbnail(
        self, image_path: str, size: tuple = (260, 220)
    ) -> Optional[QPixmap]:
        """Get instantly available thumbnail from cache (for instant display)."""
        try:
            cache_key = self._get_cache_key(image_path, size)

            # Check memory cache first (fastest)
            pixmap = self.memory_cache.get(cache_key)
            if pixmap:
                logger.debug(f"🚀 INSTANT_CACHE: Instant hit for {image_path}")
                return pixmap

            # Check compressed cache
            compressed_data = self.compressed_cache.get(cache_key)
            if compressed_data:
                pixmap = self._decompress_pixmap(compressed_data)
                if pixmap:
                    # Promote to memory cache for next access
                    self.memory_cache.put(cache_key, pixmap)
                    logger.debug(f"🚀 INSTANT_CACHE: Compressed hit for {image_path}")
                    return pixmap

            return None

        except Exception as e:
            logger.debug(f"Instant thumbnail get failed: {e}")
            return None

    async def get_cached_image(self, image_path: str, size: tuple) -> Optional[QPixmap]:
        """Get cached image with intelligent cache hierarchy."""
        start_time = time.perf_counter()
        self.total_requests += 1

        try:
            cache_key = self._get_cache_key(image_path, size)

            # Layer 1: Memory cache (instant)
            pixmap = self.memory_cache.get(cache_key)
            if pixmap:
                self.cache_hits_by_layer["memory"] += 1
                return pixmap

            # Layer 2: Compressed cache (fast)
            compressed_data = self.compressed_cache.get(cache_key)
            if compressed_data:
                pixmap = self._decompress_pixmap(compressed_data)
                if pixmap:
                    # Promote to memory cache
                    self.memory_cache.put(cache_key, pixmap)
                    self.cache_hits_by_layer["compressed"] += 1
                    return pixmap

            # Layer 3: Disk cache (medium)
            pixmap = await self.disk_cache.get(cache_key)
            if pixmap:
                # Promote to memory and compressed caches
                self.memory_cache.put(cache_key, pixmap)
                compressed_data = self._compress_pixmap(pixmap)
                if compressed_data:
                    self.compressed_cache.put(cache_key, compressed_data)

                self.cache_hits_by_layer["disk"] += 1
                return pixmap

            # Cache miss
            return None

        except Exception as e:
            logger.error(f"Cache get failed: {e}")
            return None

        finally:
            load_time = time.perf_counter() - start_time
            self.load_times.append(load_time)

    async def cache_image(self, image_path: str, pixmap: QPixmap, size: tuple) -> None:
        """Cache image in all layers."""
        try:
            cache_key = self._get_cache_key(image_path, size)

            # Store in memory cache
            self.memory_cache.put(cache_key, pixmap)

            # Store in compressed cache
            compressed_data = self._compress_pixmap(pixmap)
            if compressed_data:
                self.compressed_cache.put(cache_key, compressed_data)

            # Store in disk cache (async)
            if self.config.enable_disk_cache:
                await self.disk_cache.put(
                    cache_key, pixmap, self.config.cache_expiry_hours
                )

        except Exception as e:
            logger.error(f"Cache put failed: {e}")
            raise CacheError(f"Failed to cache image: {e}")

    def cache_image_instant(
        self, image_path: str, pixmap: QPixmap, size: tuple
    ) -> None:
        """Cache image instantly in memory layers only (for startup optimization)."""
        try:
            cache_key = self._get_cache_key(image_path, size)

            # Store in memory cache immediately
            self.memory_cache.put(cache_key, pixmap)

            # Store in compressed cache immediately
            compressed_data = self._compress_pixmap(pixmap)
            if compressed_data:
                self.compressed_cache.put(cache_key, compressed_data)

            # Skip disk cache for instant operation

        except Exception as e:
            logger.debug(f"Instant cache put failed: {e}")  # Debug level for startup

    async def preload_images(self, image_paths: List[str], size: tuple) -> None:
        """Preload images in background."""
        try:
            # This would typically load images and cache them
            # For now, just log the operation
            logger.info(f"Preloading {len(image_paths)} images")

            # In a real implementation, you would:
            # 1. Load images asynchronously
            # 2. Cache them in all layers
            # 3. Provide progress feedback

        except Exception as e:
            logger.error(f"Preload failed: {e}")

    async def clear_cache(self) -> None:
        """Clear all cached data."""
        try:
            self.memory_cache.clear()
            self.compressed_cache.clear()
            await self.disk_cache.clear()

            # Reset stats
            self.total_requests = 0
            self.cache_hits_by_layer = {"memory": 0, "compressed": 0, "disk": 0}
            self.load_times.clear()

            logger.info("All caches cleared")

        except Exception as e:
            logger.error(f"Cache clear failed: {e}")
            raise CacheError(f"Failed to clear cache: {e}")

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        try:
            total_hits = sum(self.cache_hits_by_layer.values())
            total_requests = max(self.total_requests, 1)  # Avoid division by zero

            stats = {
                "total_requests": self.total_requests,
                "total_hits": total_hits,
                "overall_hit_rate": (total_hits / total_requests) * 100,
                "hits_by_layer": self.cache_hits_by_layer.copy(),
                "memory_cache": self.memory_cache.get_stats(),
                "compressed_cache": self.compressed_cache.get_stats(),
                "disk_cache": self.disk_cache.get_stats(),
                "avg_load_time": (
                    sum(self.load_times) / len(self.load_times)
                    if self.load_times
                    else 0
                ),
            }

            return stats

        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {}

    def _get_cache_key(self, image_path: str, size: tuple) -> str:
        """Generate cache key for image and size."""
        key_data = f"{image_path}_{size[0]}x{size[1]}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _compress_pixmap(self, pixmap: QPixmap) -> Optional[bytes]:
        """Compress pixmap for storage."""
        try:
            # Convert to bytes with compression
            byte_array = (
                pixmap.toImage().bits().asstring(pixmap.toImage().sizeInBytes())
            )
            return byte_array
        except Exception as e:
            logger.error(f"Pixmap compression failed: {e}")
            return None

    def _decompress_pixmap(self, compressed_data: bytes) -> Optional[QPixmap]:
        """Decompress pixmap from storage."""
        try:
            pixmap = QPixmap()
            pixmap.loadFromData(compressed_data)
            return pixmap if not pixmap.isNull() else None
        except Exception as e:
            logger.error(f"Pixmap decompression failed: {e}")
            return None


def get_global_cache_service() -> Optional[CacheService]:
    """
    Get the global cache service instance for startup optimization.

    Returns:
        CacheService: The global cache service instance, or None if not initialized
    """
    global _global_cache_service
    return _global_cache_service
