"""
Image Loading Manager - Handles async image loading, caching, and processing.

Responsibilities:
- Asynchronous image loading with quality processing
- Cache management and metadata handling
- Image processing coordination
- Loading state tracking
"""

import logging
import os
import hashlib
import json
from pathlib import Path
from typing import Optional, Callable
from PyQt6.QtCore import QObject, QTimer, QSize, pyqtSignal
from PyQt6.QtGui import QPixmap, QPainter, QColor
from PyQt6.QtCore import Qt


class ImageLoadingManager(QObject):
    """
    Manages image loading operations with caching and quality processing.
    
    Features:
    - Asynchronous loading with timers
    - High-quality image processing
    - Disk-based caching system
    - Loading state management
    """
    
    # Signals
    image_loaded = pyqtSignal(str, QPixmap)  # path, pixmap
    loading_started = pyqtSignal(str)  # path
    loading_failed = pyqtSignal(str, str)  # path, error
    
    # Cache configuration
    CACHE_DIR = Path("browse_thumbnails")
    CACHE_METADATA_FILE = "cache_metadata.json"
    
    def __init__(self, image_processor):
        super().__init__()
        
        self.image_processor = image_processor
        self.current_path: Optional[str] = None
        self._original_pixmap: Optional[QPixmap] = None
        
        # Loading state
        self._pending_path: Optional[str] = None
        self._pending_index: Optional[int] = None
        self._is_loading = False
        
        # Deferred loading timer
        self._load_timer = QTimer()
        self._load_timer.setSingleShot(True)
        self._load_timer.timeout.connect(self._load_pending_image)
        
        # Cache system
        self._cache_metadata = {}
        self._ensure_cache_directory()
        self._load_cache_metadata()
        
        logging.debug("ImageLoadingManager initialized")
    
    def load_image_async(self, image_path: str, target_size: QSize, index: Optional[int] = None) -> None:
        """
        Load image asynchronously with quality processing.
        
        Args:
            image_path: Path to the image file
            target_size: Target size for processing
            index: Optional index for tracking
        """
        if image_path == self.current_path and self._original_pixmap:
            # Image already loaded, just emit signal
            self.image_loaded.emit(image_path, self._original_pixmap)
            return
        
        # Set pending load
        self._pending_path = image_path
        self._pending_index = index
        self._is_loading = True
        
        # Emit loading started signal
        self.loading_started.emit(image_path)
        
        # Start deferred loading
        self._load_timer.start(1)
    
    def load_image_sync(self, image_path: str, target_size: QSize) -> Optional[QPixmap]:
        """
        Load image synchronously with caching.
        
        Args:
            image_path: Path to the image file
            target_size: Target size for processing
            
        Returns:
            Processed QPixmap or None if failed
        """
        try:
            # Check cache first
            cached_pixmap = self._get_cached_thumbnail(image_path, target_size)
            if cached_pixmap and not cached_pixmap.isNull():
                logging.debug(f"Cache hit for: {os.path.basename(image_path)}")
                return cached_pixmap
            
            # Process image with high quality
            if not os.path.exists(image_path):
                logging.warning(f"Image file not found: {image_path}")
                return self._create_error_pixmap(target_size)
            
            processed_pixmap = self.image_processor.process_image(image_path, target_size)
            
            if processed_pixmap and not processed_pixmap.isNull():
                # Cache the result
                self._cache_thumbnail(processed_pixmap, image_path, target_size)
                logging.debug(f"Processed and cached: {os.path.basename(image_path)}")
                return processed_pixmap
            else:
                logging.warning(f"Failed to process image: {image_path}")
                return self._create_error_pixmap(target_size)
                
        except Exception as e:
            logging.error(f"Error loading image {image_path}: {e}")
            return self._create_error_pixmap(target_size)
    
    def _load_pending_image(self) -> None:
        """Load pending image with error handling."""
        if not self._pending_path:
            return
        
        try:
            # Calculate target size (this should be provided by the caller)
            target_size = QSize(200, 150)  # Default size, should be overridden
            
            # Load the image
            pixmap = self.load_image_sync(self._pending_path, target_size)
            
            if pixmap and not pixmap.isNull():
                self.current_path = self._pending_path
                self._original_pixmap = pixmap
                
                # Emit success signal
                self.image_loaded.emit(self._pending_path, pixmap)
            else:
                # Emit failure signal
                self.loading_failed.emit(self._pending_path, "Failed to load image")
                
        except Exception as e:
            logging.error(f"Error in pending image load: {e}")
            self.loading_failed.emit(self._pending_path or "", str(e))
        
        finally:
            # Clear pending state
            self._pending_path = None
            self._pending_index = None
            self._is_loading = False
    
    def _create_error_pixmap(self, size: QSize) -> QPixmap:
        """Create error pixmap when image loading fails."""
        pixmap = QPixmap(size)
        pixmap.fill(QColor(220, 220, 220))
        
        painter = QPainter(pixmap)
        painter.setPen(QColor(100, 100, 100))
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "Error\nLoading")
        painter.end()
        
        return pixmap
    
    # Cache management methods
    def _ensure_cache_directory(self) -> None:
        """Ensure cache directory exists."""
        try:
            self.CACHE_DIR.mkdir(exist_ok=True)
        except Exception as e:
            logging.warning(f"Failed to create cache directory: {e}")
    
    def _load_cache_metadata(self) -> None:
        """Load cache metadata from disk."""
        metadata_path = self.CACHE_DIR / self.CACHE_METADATA_FILE
        try:
            if metadata_path.exists():
                with open(metadata_path, "r") as f:
                    self._cache_metadata = json.load(f)
            else:
                self._cache_metadata = {}
        except Exception as e:
            logging.warning(f"Failed to load cache metadata: {e}")
            self._cache_metadata = {}
    
    def _save_cache_metadata(self) -> None:
        """Save cache metadata to disk."""
        metadata_path = self.CACHE_DIR / self.CACHE_METADATA_FILE
        try:
            with open(metadata_path, "w") as f:
                json.dump(self._cache_metadata, f, indent=2)
        except Exception as e:
            logging.warning(f"Failed to save cache metadata: {e}")
    
    def _generate_cache_key(self, image_path: str, target_size: QSize) -> str:
        """Generate cache key based on image path, modification time, and size."""
        try:
            mtime = os.path.getmtime(image_path)
            cache_string = f"{image_path}_{mtime}_{target_size.width()}x{target_size.height()}"
            return hashlib.md5(cache_string.encode()).hexdigest()
        except Exception as e:
            logging.warning(f"Error generating cache key: {e}")
            return hashlib.md5(image_path.encode()).hexdigest()
    
    def _get_cached_thumbnail(self, image_path: str, target_size: QSize) -> Optional[QPixmap]:
        """Get cached thumbnail if available and valid."""
        cache_key = self._generate_cache_key(image_path, target_size)
        cache_file = self.CACHE_DIR / f"{cache_key}.png"
        
        try:
            if cache_file.exists() and cache_key in self._cache_metadata:
                metadata = self._cache_metadata[cache_key]
                
                # Validate cache entry
                if (metadata.get("source_path") == image_path and
                    metadata.get("target_width") == target_size.width() and
                    metadata.get("target_height") == target_size.height()):
                    
                    pixmap = QPixmap(str(cache_file))
                    if not pixmap.isNull():
                        return pixmap
            
            return None
            
        except Exception as e:
            logging.debug(f"Error reading cache: {e}")
            return None
    
    def _cache_thumbnail(self, pixmap: QPixmap, image_path: str, target_size: QSize) -> None:
        """Cache thumbnail to disk."""
        cache_key = self._generate_cache_key(image_path, target_size)
        cache_file = self.CACHE_DIR / f"{cache_key}.png"
        
        try:
            if pixmap.save(str(cache_file), "PNG"):
                # Update metadata
                self._cache_metadata[cache_key] = {
                    "source_path": image_path,
                    "target_width": target_size.width(),
                    "target_height": target_size.height(),
                    "cached_at": os.path.getmtime(image_path),
                    "cache_file": str(cache_file),
                }
                
                # Save metadata asynchronously
                QTimer.singleShot(100, self._save_cache_metadata)
                logging.debug(f"Cached thumbnail: {os.path.basename(image_path)}")
            else:
                logging.warning(f"Failed to save thumbnail cache: {cache_file}")
                
        except Exception as e:
            logging.warning(f"Error caching thumbnail: {e}")
    
    def clear_cache(self) -> None:
        """Clear all cached thumbnails."""
        try:
            if self.CACHE_DIR.exists():
                for cache_file in self.CACHE_DIR.glob("*.png"):
                    cache_file.unlink()
                
                metadata_file = self.CACHE_DIR / self.CACHE_METADATA_FILE
                if metadata_file.exists():
                    metadata_file.unlink()
                
                self._cache_metadata.clear()
                logging.info("Cache cleared successfully")
        except Exception as e:
            logging.warning(f"Error clearing cache: {e}")
    
    def get_cache_stats(self) -> dict:
        """Get cache statistics."""
        try:
            cache_files = list(self.CACHE_DIR.glob("*.png")) if self.CACHE_DIR.exists() else []
            total_size = sum(f.stat().st_size for f in cache_files)
            
            return {
                "cached_items": len(self._cache_metadata),
                "cache_files": len(cache_files),
                "total_size_mb": total_size / (1024 * 1024),
                "cache_directory": str(self.CACHE_DIR)
            }
        except Exception as e:
            logging.warning(f"Error getting cache stats: {e}")
            return {"error": str(e)}
    
    @property
    def is_loading(self) -> bool:
        """Check if currently loading an image."""
        return self._is_loading
    
    def cancel_loading(self) -> None:
        """Cancel any pending loading operation."""
        if self._load_timer.isActive():
            self._load_timer.stop()
        
        self._pending_path = None
        self._pending_index = None
        self._is_loading = False
