# src/main_window/main_widget/sequence_card_tab/components/display/disk_cache_manager.py
import os
import json
import hashlib
import logging
import time
from pathlib import Path
from typing import Optional, Dict, Any
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import QSize


class DiskCacheManager:
    """
    Manages disk-based caching of processed images for ultra-fast loading.

    Features:
    - Persistent cache across application sessions
    - Automatic cache invalidation based on source file modification
    - Size-based cache cleanup to prevent disk bloat
    - Metadata tracking for cache management
    - Safe fallback if cache operations fail
    """

    def __init__(self, cache_dir: str = None, max_cache_size_mb: int = 1000):
        """
        Initialize the disk cache manager.

        Args:
            cache_dir: Directory for cache files. If None, uses default location.
            max_cache_size_mb: Maximum cache size in MB before cleanup
        """
        self.max_cache_size_mb = max_cache_size_mb
        self.cache_enabled = True

        # Set up cache directory
        if cache_dir is None:
            from utils.path_helpers import get_user_editable_resource_path

            try:
                cache_dir = os.path.join(
                    get_user_editable_resource_path(""), "image_cache"
                )
            except:
                # Fallback to temp directory
                import tempfile

                cache_dir = os.path.join(
                    tempfile.gettempdir(), "kinetic_constructor_cache"
                )

        self.cache_dir = Path(cache_dir)
        self.metadata_file = self.cache_dir / "cache_metadata.json"

        # Initialize cache directory and metadata
        self._initialize_cache()

        # Cache statistics
        self.cache_hits = 0
        self.cache_misses = 0
        self.cache_writes = 0
        self.cache_cleanups = 0

    def _initialize_cache(self) -> None:
        """Initialize cache directory and load metadata."""
        try:
            # Create cache directory if it doesn't exist
            self.cache_dir.mkdir(parents=True, exist_ok=True)

            # Load or create metadata
            if self.metadata_file.exists():
                try:
                    with open(self.metadata_file, "r") as f:
                        self.metadata = json.load(f)
                except (json.JSONDecodeError, IOError):
                    logging.warning("Cache metadata corrupted, creating new metadata")
                    self.metadata = {}
            else:
                self.metadata = {}

            logging.info(f"Disk cache initialized: {self.cache_dir}")

        except Exception as e:
            logging.warning(f"Failed to initialize disk cache: {e}")
            self.cache_enabled = False

    def _get_cache_key(
        self, image_path: str, target_size: QSize, scale_factor: float = 1.0
    ) -> str:
        """
        Generate an optimized cache key for an image with specific parameters.

        This method creates cache keys based on image content and display size
        rather than file path, allowing the same image at the same size to be
        reused across different sequence length filters.

        Args:
            image_path: Path to the source image
            target_size: Target size for the processed image
            scale_factor: Scale factor applied

        Returns:
            Optimized cache key string for size-based reuse
        """
        # Create content-based identifier for the image
        image_content_id = self._create_image_content_id(image_path)

        # Create cache key based on content + display size (not path)
        key_data = f"{image_content_id}_{target_size.width()}x{target_size.height()}_{scale_factor:.4f}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _create_image_content_id(self, image_path: str) -> str:
        """
        Create a content-based identifier for an image.

        This uses file size and modification time to create a unique identifier
        that's independent of the file path, allowing the same image content
        to be recognized regardless of how it's accessed.

        Args:
            image_path: Path to the image file

        Returns:
            Content-based identifier string
        """
        try:
            # Get file stats for content identification
            stat = os.stat(image_path)
            file_size = stat.st_size
            mtime = stat.st_mtime

            # Use filename (without path) + size + mtime for content ID
            filename = os.path.basename(image_path)
            content_data = f"{filename}_{file_size}_{mtime}"

            # Create a short hash for the cache key
            return hashlib.md5(content_data.encode()).hexdigest()[:12]

        except OSError:
            # Fallback to path-based hash if file stats unavailable
            return hashlib.md5(image_path.encode()).hexdigest()[:12]

    def _get_cache_file_path(self, cache_key: str) -> Path:
        """Get the file path for a cache key."""
        return self.cache_dir / f"{cache_key}.png"

    def get_cached_image(
        self, image_path: str, target_size: QSize, scale_factor: float = 1.0
    ) -> Optional[QPixmap]:
        """
        Retrieve a cached image if available and valid.

        Args:
            image_path: Path to the source image
            target_size: Target size for the processed image
            scale_factor: Scale factor applied

        Returns:
            Cached QPixmap if available, None otherwise
        """
        if not self.cache_enabled:
            return None

        try:
            cache_key = self._get_cache_key(image_path, target_size, scale_factor)
            cache_file = self._get_cache_file_path(cache_key)

            # Check if cache file exists and is valid
            if cache_file.exists() and cache_key in self.metadata:
                # Verify source file hasn't changed
                try:
                    current_mtime = os.path.getmtime(image_path)
                    cached_mtime = self.metadata[cache_key].get("source_mtime", 0)

                    if current_mtime <= cached_mtime:
                        # Load cached image
                        pixmap = QPixmap(str(cache_file))
                        if not pixmap.isNull():
                            self.cache_hits += 1
                            logging.debug(
                                f"Disk cache hit: {os.path.basename(image_path)}"
                            )

                            # Update access time in metadata
                            self.metadata[cache_key]["last_access"] = time.time()
                            return pixmap
                    else:
                        # Source file has been modified, remove stale cache
                        self._remove_cache_entry(cache_key)

                except OSError:
                    # Can't check modification time, assume cache is stale
                    self._remove_cache_entry(cache_key)

            self.cache_misses += 1
            return None

        except Exception as e:
            logging.debug(f"Error retrieving cached image: {e}")
            return None

    def cache_image(
        self,
        image_path: str,
        pixmap: QPixmap,
        target_size: QSize,
        scale_factor: float = 1.0,
    ) -> bool:
        """
        Cache a processed image to disk.

        Args:
            image_path: Path to the source image
            pixmap: Processed QPixmap to cache
            target_size: Target size for the processed image
            scale_factor: Scale factor applied

        Returns:
            True if caching succeeded, False otherwise
        """
        if not self.cache_enabled or pixmap.isNull():
            return False

        try:
            cache_key = self._get_cache_key(image_path, target_size, scale_factor)
            cache_file = self._get_cache_file_path(cache_key)

            # Save the pixmap to cache
            if pixmap.save(str(cache_file), "PNG"):
                # Update metadata
                try:
                    source_mtime = os.path.getmtime(image_path)
                except OSError:
                    source_mtime = time.time()

                self.metadata[cache_key] = {
                    "source_path": image_path,
                    "source_mtime": source_mtime,
                    "cache_time": time.time(),
                    "last_access": time.time(),
                    "target_width": target_size.width(),
                    "target_height": target_size.height(),
                    "scale_factor": scale_factor,
                    "file_size": cache_file.stat().st_size,
                }

                self.cache_writes += 1
                logging.debug(f"Cached image: {os.path.basename(image_path)}")

                # Periodically save metadata and check cache size
                if self.cache_writes % 10 == 0:
                    self._save_metadata()
                    self._check_cache_size()

                return True

        except Exception as e:
            logging.debug(f"Error caching image: {e}")

        return False

    def _remove_cache_entry(self, cache_key: str) -> None:
        """Remove a cache entry and its file."""
        try:
            cache_file = self._get_cache_file_path(cache_key)
            if cache_file.exists():
                cache_file.unlink()

            if cache_key in self.metadata:
                del self.metadata[cache_key]

        except Exception as e:
            logging.debug(f"Error removing cache entry: {e}")

    def _save_metadata(self) -> None:
        """Save metadata to disk."""
        try:
            with open(self.metadata_file, "w") as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            logging.warning(f"Failed to save cache metadata: {e}")

    def _check_cache_size(self) -> None:
        """Check cache size and cleanup if necessary."""
        try:
            total_size = sum(
                entry.get("file_size", 0) for entry in self.metadata.values()
            )
            max_size_bytes = self.max_cache_size_mb * 1024 * 1024

            if total_size > max_size_bytes:
                self._cleanup_cache()

        except Exception as e:
            logging.warning(f"Error checking cache size: {e}")

    def _cleanup_cache(self) -> None:
        """Clean up old cache entries to free space."""
        try:
            logging.info("Cleaning up disk cache...")

            # Sort entries by last access time (oldest first)
            sorted_entries = sorted(
                self.metadata.items(), key=lambda x: x[1].get("last_access", 0)
            )

            # Remove oldest 25% of entries
            entries_to_remove = len(sorted_entries) // 4
            for cache_key, _ in sorted_entries[:entries_to_remove]:
                self._remove_cache_entry(cache_key)

            self._save_metadata()
            self.cache_cleanups += 1

            logging.info(
                f"Cache cleanup completed: removed {entries_to_remove} entries"
            )

        except Exception as e:
            logging.warning(f"Error during cache cleanup: {e}")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            total_size = sum(
                entry.get("file_size", 0) for entry in self.metadata.values()
            )
            total_size_mb = total_size / (1024 * 1024)
        except:
            total_size_mb = 0

        hit_rate = 0
        if self.cache_hits + self.cache_misses > 0:
            hit_rate = (self.cache_hits / (self.cache_hits + self.cache_misses)) * 100

        return {
            "enabled": self.cache_enabled,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "hit_rate_percent": round(hit_rate, 1),
            "cache_writes": self.cache_writes,
            "cache_cleanups": self.cache_cleanups,
            "total_entries": len(self.metadata),
            "total_size_mb": round(total_size_mb, 1),
            "cache_dir": str(self.cache_dir),
        }

    def clear_cache(self) -> None:
        """Clear all cache entries."""
        try:
            for cache_key in list(self.metadata.keys()):
                self._remove_cache_entry(cache_key)

            self.metadata.clear()
            self._save_metadata()

            logging.info("Disk cache cleared")

        except Exception as e:
            logging.warning(f"Error clearing cache: {e}")

    def shutdown(self) -> None:
        """Clean shutdown of cache manager."""
        try:
            self._save_metadata()
            logging.info("Disk cache manager shutdown completed")
        except Exception as e:
            logging.warning(f"Error during cache shutdown: {e}")
