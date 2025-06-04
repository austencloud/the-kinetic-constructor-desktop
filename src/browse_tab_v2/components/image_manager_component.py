"""
Image Manager Component - Modular Architecture

Extracted from browse_tab_view.py to provide focused image loading and caching functionality.
Handles all image-related operations including background loading, caching, and coordination
with thumbnail cards.

Responsibilities:
- Image service integration and management
- Background image loading coordination
- Image caching and optimization
- Viewport-based image preloading
- Image ready event handling and distribution
"""

import logging
from typing import List, Dict, Set
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import pyqtSignal

from ..core.interfaces import SequenceModel, BrowseTabConfig
from ..debug.window_resize_tracker import track_component, log_main_window_change

logger = logging.getLogger(__name__)


class ImageManagerComponent(QWidget):
    """
    Modular image manager component handling image loading and caching.

    This component encapsulates all image-related operations and provides
    a clean interface for coordinating image loading across the application.
    """

    # Signals for parent coordination
    image_ready = pyqtSignal(str, object)  # image_path, scaled_pixmap
    images_preloaded = pyqtSignal(int)  # count

    def __init__(self, config: BrowseTabConfig = None, parent: QWidget = None):
        super().__init__(parent)

        self.config = config or BrowseTabConfig()

        # State management
        self._loaded_images: Set[str] = set()
        self._pending_images: Set[str] = set()
        self._priority_queue: List[str] = []

        # Image service
        self.image_service = None

        # Performance tracking
        self._image_load_times: List[float] = []
        self._max_load_history = 100

        track_component("ImageManagerComponent_Initial", self, "Constructor start")
        log_main_window_change("ImageManagerComponent constructor start")

        self._setup_image_service()

        track_component("ImageManagerComponent_Complete", self, "Constructor complete")
        log_main_window_change("ImageManagerComponent constructor complete")

        # Initialize with pre-loaded images for instant display
        self._initialize_with_preloaded_images()

        logger.info("ImageManagerComponent initialized")

    def _setup_image_service(self):
        """Initialize fast image service."""
        try:
            from ..services.fast_image_service import get_image_service

            print("🚀 IMAGE_MANAGER_COMPONENT: Creating image service")
            self.image_service = get_image_service()
            self.image_service.image_ready.connect(self._on_image_ready)
            print("🚀 IMAGE_MANAGER_COMPONENT: image_ready signal connected")

            logger.info("Image service initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize image service: {e}")
            self.image_service = None

    def _initialize_with_preloaded_images(self):
        """Initialize with pre-loaded images for instant display."""
        try:
            from ..startup.data_preloader import (
                get_preloaded_data,
                is_preloading_completed,
            )

            if is_preloading_completed():
                preloaded_data = get_preloaded_data()
                if preloaded_data and preloaded_data.get("sequences"):
                    sequences = preloaded_data["sequences"]
                    print(
                        f"🖼️ IMAGE_MANAGER_COMPONENT: Pre-loading images for {len(sequences)} sequences"
                    )

                    # Pre-load critical images for instant display
                    self.preload_sequence_images(sequences)

                    logger.info(
                        f"ImageManagerComponent pre-initialized with images for {len(sequences)} sequences"
                    )
                    return

            print(
                "🖼️ IMAGE_MANAGER_COMPONENT: No pre-loaded data - will load images on demand"
            )

        except Exception as e:
            logger.warning(f"Failed to initialize with pre-loaded images: {e}")

    def _on_image_ready(self, image_path: str, scaled_pixmap):
        """Handle image ready from background service."""
        self._loaded_images.add(image_path)
        if image_path in self._pending_images:
            self._pending_images.remove(image_path)

        logger.debug(f"Image ready: {image_path}")

        # Emit signal for parent coordination
        self.image_ready.emit(image_path, scaled_pixmap)

    # Public interface methods
    def queue_image_load(self, image_path: str, priority: int = 3):
        """Queue an image for background loading."""
        if not self.image_service or not image_path:
            return

        if (
            image_path not in self._loaded_images
            and image_path not in self._pending_images
        ):
            self._pending_images.add(image_path)
            self.image_service.queue_image_load(image_path, priority=priority)
            logger.debug(
                f"Queued image for loading: {image_path} (priority: {priority})"
            )

    def preload_visible_images(self, image_paths: List[str]):
        """Preload visible images with high priority."""
        if not self.image_service or not image_paths:
            return

        visible_paths = []
        for path in image_paths:
            if path not in self._loaded_images and path not in self._pending_images:
                self._pending_images.add(path)
                visible_paths.append(path)

        if visible_paths:
            print(
                f"📡 IMAGE_MANAGER_COMPONENT: Preloading {len(visible_paths)} visible images"
            )
            self.image_service.preload_visible_images(visible_paths)
            logger.debug(f"Preloading {len(visible_paths)} visible images")

    def get_image_sync(self, image_path: str):
        """Get image synchronously from cache."""
        if not self.image_service or not image_path:
            return None

        try:
            cached_pixmap = self.image_service.get_image_sync(image_path)
            if cached_pixmap:
                self._loaded_images.add(image_path)
                logger.debug(f"Retrieved cached image: {image_path}")
            return cached_pixmap

        except Exception as e:
            logger.error(f"Failed to get cached image {image_path}: {e}")
            return None

    def force_visible_card_image_update(self, all_widgets: Dict[int, QWidget]):
        """Force all visible cards to update their images."""
        print("🔥 IMAGE_MANAGER_COMPONENT: Starting force visible card image update")

        if not all_widgets:
            print("❌ IMAGE_MANAGER_COMPONENT: No widgets provided")
            logger.warning("No widgets provided for image update")
            return

        visible_count = len(all_widgets)
        print(
            f"🔥 IMAGE_MANAGER_COMPONENT: Starting update for {visible_count} visible cards"
        )
        logger.debug(f"Starting image update for {visible_count} visible cards")

        updated_count = 0
        for index, widget in all_widgets.items():
            logger.debug(f"Processing widget {index} for image update")

            if hasattr(widget, "_load_image_fast"):
                logger.debug(f"Calling _load_image_fast() for widget {index}")
                widget._load_image_fast()
                updated_count += 1
            elif hasattr(widget, "sequence") and hasattr(widget.sequence, "thumbnails"):
                # Try to get from image service cache
                if widget.sequence.thumbnails:
                    image_path = widget.sequence.thumbnails[0]
                    logger.debug(f"Trying cache for widget {index}, path {image_path}")
                    cached_pixmap = self.get_image_sync(image_path)
                    if cached_pixmap and hasattr(widget, "image_label"):
                        logger.debug(f"Setting cached image for widget {index}")
                        widget.image_label.setPixmap(cached_pixmap)
                        widget._image_loaded = True
                        updated_count += 1
                    else:
                        logger.debug(f"No cached image for widget {index}")
                else:
                    logger.debug(f"Widget {index} has no thumbnails")
            else:
                logger.warning(f"Widget {index} has no image loading capability")

        logger.debug(
            f"Image update completed - updated {updated_count}/{visible_count} widgets"
        )
        print(
            f"🔥 IMAGE_MANAGER_COMPONENT: Completed - updated {updated_count}/{visible_count} widgets"
        )

    def delayed_force_update(self, all_widgets: Dict[int, QWidget]):
        """Delayed force update to catch widgets that weren't ready initially."""
        print("⏰ IMAGE_MANAGER_COMPONENT: Starting delayed image update")
        logger.debug("Starting delayed image update")
        self.force_visible_card_image_update(all_widgets)

    def preload_sequence_images(self, sequences: List[SequenceModel]):
        """Preload images for a list of sequences."""
        if not sequences:
            return

        image_paths = []
        for sequence in sequences:
            if hasattr(sequence, "thumbnails") and sequence.thumbnails:
                image_paths.append(sequence.thumbnails[0])

        if image_paths:
            print(
                f"📡 IMAGE_MANAGER_COMPONENT: Preloading {len(image_paths)} sequence images"
            )
            self.preload_visible_images(image_paths)

    def clear_cache(self):
        """Clear image cache and reset state."""
        self._loaded_images.clear()
        self._pending_images.clear()
        self._priority_queue.clear()

        if self.image_service and hasattr(self.image_service, "clear_cache"):
            self.image_service.clear_cache()

        logger.info("Image cache cleared")

    def get_cache_stats(self) -> Dict:
        """Get image cache statistics."""
        return {
            "loaded_images": len(self._loaded_images),
            "pending_images": len(self._pending_images),
            "priority_queue": len(self._priority_queue),
            "avg_load_time": (
                sum(self._image_load_times) / len(self._image_load_times)
                if self._image_load_times
                else 0
            ),
            "total_loads": len(self._image_load_times),
        }

    def is_image_loaded(self, image_path: str) -> bool:
        """Check if an image is already loaded."""
        return image_path in self._loaded_images

    def is_image_pending(self, image_path: str) -> bool:
        """Check if an image is pending load."""
        return image_path in self._pending_images

    def get_loaded_image_count(self) -> int:
        """Get count of loaded images."""
        return len(self._loaded_images)

    def get_pending_image_count(self) -> int:
        """Get count of pending images."""
        return len(self._pending_images)

    def cleanup(self):
        """Cleanup image manager resources."""
        try:
            self.clear_cache()
            if self.image_service and hasattr(self.image_service, "cleanup"):
                self.image_service.cleanup()
            logger.info("ImageManagerComponent cleanup completed")
        except Exception as e:
            logger.error(f"ImageManagerComponent cleanup failed: {e}")

    def sizeHint(self):
        """Provide size hint (not visible component)."""
        from PyQt6.QtCore import QSize

        return QSize(0, 0)

    def minimumSizeHint(self):
        """Provide minimum size hint (not visible component)."""
        from PyQt6.QtCore import QSize

        return QSize(0, 0)
