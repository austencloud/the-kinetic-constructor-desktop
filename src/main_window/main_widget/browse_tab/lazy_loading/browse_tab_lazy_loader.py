"""
Browse Tab Lazy Loader - Optimized lazy loading for thumbnail grid.

This loader is specifically designed for the browse tab's grid layout with:
- Viewport-based loading (5-10 rows ahead)
- Smooth scrolling preservation
- Glassmorphism loading indicators
- Memory-efficient image management
"""

import logging
from typing import Dict, Set, Optional, Callable, Any
from PyQt6.QtCore import QObject, QTimer, pyqtSignal, QRect
from PyQt6.QtWidgets import QWidget, QScrollArea
from PyQt6.QtGui import QPixmap

from .loading_indicator import LoadingIndicator
from .viewport_manager import ViewportManager


class BrowseTabLazyLoader(QObject):
    """
    Lazy loading system optimized for browse tab thumbnail grid.

    Features:
    - Grid-aware viewport calculation
    - 5-10 row loading buffer
    - Smooth scrolling preservation
    - Modern loading indicators
    - Memory-efficient unloading
    """

    # Signals
    image_loaded = pyqtSignal(str, QPixmap)  # path, pixmap
    loading_started = pyqtSignal(str)  # path
    loading_completed = pyqtSignal()
    loading_progress = pyqtSignal(int, int)  # loaded, total

    def __init__(
        self, scroll_area: QScrollArea, grid_columns: int = 3, buffer_rows: int = 7
    ):
        """
        Initialize the browse tab lazy loader.

        Args:
            scroll_area: The scroll area to monitor
            grid_columns: Number of columns in the grid
            buffer_rows: Number of rows to load ahead/behind viewport
        """
        super().__init__()

        self.scroll_area = scroll_area
        self.grid_columns = grid_columns
        self.buffer_rows = buffer_rows

        # Viewport manager for grid-aware calculations
        self.viewport_manager = ViewportManager(scroll_area, grid_columns, buffer_rows)

        # Track image states
        self.pending_images: Dict[str, Dict[str, Any]] = {}  # path -> load_params
        self.loaded_images: Set[str] = set()
        self.loading_images: Set[str] = set()
        self.visible_images: Set[str] = set()

        # Loading indicators
        self.loading_indicators: Dict[str, LoadingIndicator] = {}

        # Timer for debounced loading
        self.load_timer = QTimer()
        self.load_timer.setSingleShot(True)
        self.load_timer.timeout.connect(self._process_visible_images)
        self.load_delay_ms = 50  # PERFORMANCE FIX: Reduced delay for faster loading

        # Connect scroll events
        if self.scroll_area and self.scroll_area.verticalScrollBar():
            self.scroll_area.verticalScrollBar().valueChanged.connect(self._on_scroll)

        # Statistics
        self.images_loaded_lazily = 0
        self.images_unloaded = 0
        self.loading_indicator_requests = 0

        logging.info("Browse tab lazy loader initialized")

    def register_thumbnail(
        self, image_path: str, widget: QWidget, load_callback: Callable, **load_params
    ) -> LoadingIndicator:
        """
        Register a thumbnail for lazy loading.

        Args:
            image_path: Path to the image file
            widget: Widget that will display the image
            load_callback: Function to call when image is loaded
            **load_params: Parameters to pass to the image processor

        Returns:
            Loading indicator to display immediately
        """
        # Store loading parameters
        self.pending_images[image_path] = {
            "widget": widget,
            "callback": load_callback,
            "load_params": load_params,
        }

        # Create loading indicator
        indicator = LoadingIndicator(widget)
        self.loading_indicators[image_path] = indicator
        self.loading_indicator_requests += 1

        # Check if image should be loaded immediately (if visible)
        if self.viewport_manager.is_widget_in_loading_zone(widget):
            self._schedule_loading()

        return indicator

    def _on_scroll(self) -> None:
        """Handle scroll events with debouncing for smooth scrolling."""
        if self.load_timer.isActive():
            self.load_timer.stop()
        self.load_timer.start(self.load_delay_ms)

    def _schedule_loading(self) -> None:
        """Schedule loading of visible images."""
        if self.load_timer.isActive():
            self.load_timer.stop()
        self.load_timer.start(self.load_delay_ms)

    def _process_visible_images(self) -> None:
        """Process and load images in the loading zone."""
        try:
            newly_visible = set()
            total_in_zone = 0

            # Check which images are now in the loading zone
            for image_path, params in self.pending_images.items():
                widget = params["widget"]

                if self.viewport_manager.is_widget_in_loading_zone(widget):
                    total_in_zone += 1
                    newly_visible.add(image_path)
                    if image_path not in self.visible_images:
                        self.visible_images.add(image_path)

            # Load newly visible images
            loaded_count = 0
            for image_path in newly_visible:
                if (
                    image_path not in self.loaded_images
                    and image_path not in self.loading_images
                ):
                    self._load_image(image_path)
                    loaded_count += 1

            # Emit progress signal
            if total_in_zone > 0:
                self.loading_progress.emit(len(self.loaded_images), total_in_zone)

            # Unload images that are far from viewport
            self._unload_distant_images()

        except Exception as e:
            logging.warning(f"Error processing visible images: {e}")

    def _load_image(self, image_path: str) -> None:
        """Load a specific image with loading indicator management."""
        if image_path not in self.pending_images:
            return

        # PERFORMANCE FIX: Quick file existence check to prevent timeouts
        import os

        if not os.path.exists(image_path):
            logging.warning(f"Image file not found, skipping lazy load: {image_path}")
            # Remove from pending and create error placeholder
            if image_path in self.pending_images:
                params = self.pending_images[image_path]
                callback = params.get("callback")
                if callback:
                    error_pixmap = self._create_error_pixmap(
                        params.get("load_params", {}).get("target_size")
                    )
                    callback(image_path, error_pixmap)
                del self.pending_images[image_path]
            return

        try:
            self.loading_images.add(image_path)
            self.loading_started.emit(image_path)

            # Show loading indicator
            if image_path in self.loading_indicators:
                self.loading_indicators[image_path].show_loading()

            params = self.pending_images[image_path]
            load_params = params["load_params"]
            callback = params["callback"]

            # PERFORMANCE FIX: Robust image loading with proper fallbacks
            widget = params["widget"]
            target_size = load_params.get("target_size")

            # Try multiple loading strategies
            pixmap = self._load_image_with_fallbacks(image_path, target_size, widget)

            if pixmap and not pixmap.isNull():
                self.loaded_images.add(image_path)
                self.images_loaded_lazily += 1

                # Hide loading indicator and show image
                if image_path in self.loading_indicators:
                    self.loading_indicators[image_path].show_image(pixmap)

                # Call the callback to update the UI
                if callback:
                    callback(image_path, pixmap)

                # Emit signal
                self.image_loaded.emit(image_path, pixmap)

                logging.debug(f"Lazy loaded thumbnail: {image_path}")

            # Remove from pending
            if image_path in self.pending_images:
                del self.pending_images[image_path]

        except Exception as e:
            logging.warning(f"Error loading image {image_path}: {e}")
            # Show error state in indicator
            if image_path in self.loading_indicators:
                self.loading_indicators[image_path].show_error()

        finally:
            self.loading_images.discard(image_path)

            # Check if all loading is complete
            if not self.loading_images:
                self.loading_completed.emit()

    def _load_image_with_fallbacks(
        self, image_path: str, target_size, widget
    ) -> Optional[QPixmap]:
        """
        PERFORMANCE FIX: Load image with multiple fallback strategies to prevent timeouts.

        Args:
            image_path: Path to the image file
            target_size: Target size for the image
            widget: Widget requesting the image

        Returns:
            QPixmap if successful, None otherwise
        """
        import os
        from PyQt6.QtCore import QSize
        from PyQt6.QtGui import QPixmap

        try:
            # Strategy 1: Try widget's image processor if available
            if hasattr(widget, "image_processor") and widget.image_processor:
                try:
                    pixmap = widget.image_processor.process_image(
                        image_path, target_size
                    )
                    if pixmap and not pixmap.isNull():
                        logging.debug(
                            f"Loaded via widget image processor: {os.path.basename(image_path)}"
                        )
                        return pixmap
                except Exception as e:
                    logging.debug(f"Widget image processor failed: {e}")

            # Strategy 2: Try widget's image loading manager if available
            if (
                hasattr(widget, "image_loading_manager")
                and widget.image_loading_manager
            ):
                try:
                    if target_size and isinstance(target_size, QSize):
                        pixmap = widget.image_loading_manager.load_image_sync(
                            image_path, target_size
                        )
                    else:
                        pixmap = widget.image_loading_manager.load_image_sync(
                            image_path, QSize(200, 200)
                        )

                    if pixmap and not pixmap.isNull():
                        logging.debug(
                            f"Loaded via image loading manager: {os.path.basename(image_path)}"
                        )
                        return pixmap
                except Exception as e:
                    logging.debug(f"Image loading manager failed: {e}")

            # Strategy 3: Direct QPixmap loading with scaling
            if os.path.exists(image_path):
                try:
                    pixmap = QPixmap(image_path)
                    if pixmap and not pixmap.isNull():
                        # Scale if target size is provided
                        if (
                            target_size
                            and isinstance(target_size, QSize)
                            and target_size.isValid()
                        ):
                            from PyQt6.QtCore import Qt

                            pixmap = pixmap.scaled(
                                target_size,
                                Qt.AspectRatioMode.KeepAspectRatio,
                                Qt.TransformationMode.SmoothTransformation,
                            )

                        logging.debug(
                            f"Loaded via direct QPixmap: {os.path.basename(image_path)}"
                        )
                        return pixmap
                except Exception as e:
                    logging.debug(f"Direct QPixmap loading failed: {e}")

            # Strategy 4: Create error placeholder
            logging.warning(f"All loading strategies failed for: {image_path}")
            return self._create_error_pixmap(target_size)

        except Exception as e:
            logging.error(f"Error in image loading fallbacks: {e}")
            return self._create_error_pixmap(target_size)

    def _create_error_pixmap(self, target_size) -> QPixmap:
        """Create an error placeholder pixmap."""
        from PyQt6.QtCore import QSize, Qt
        from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont

        try:
            # Use target size or default
            if target_size and isinstance(target_size, QSize) and target_size.isValid():
                size = target_size
            else:
                size = QSize(200, 200)

            # Create error pixmap
            pixmap = QPixmap(size)
            pixmap.fill(QColor(240, 240, 240))  # Light gray background

            painter = QPainter(pixmap)
            painter.setPen(QColor(150, 150, 150))  # Gray text
            painter.setFont(QFont("Arial", 10))
            painter.drawText(
                pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "Image\nNot Available"
            )
            painter.end()

            return pixmap

        except Exception as e:
            logging.error(f"Error creating error pixmap: {e}")
            # Return minimal pixmap as last resort
            pixmap = QPixmap(200, 200)
            pixmap.fill(QColor(200, 200, 200))
            return pixmap

    def _unload_distant_images(self) -> None:
        """Unload images that are far from the viewport to save memory."""
        try:
            distant_images = set()

            for image_path in self.visible_images.copy():
                if image_path in self.pending_images:
                    widget = self.pending_images[image_path]["widget"]
                    if not self.viewport_manager.is_widget_in_unload_zone(widget):
                        distant_images.add(image_path)

            # Remove from visible set and clean up
            for image_path in distant_images:
                self.visible_images.discard(image_path)
                self.loaded_images.discard(image_path)

                # Clean up loading indicator
                if image_path in self.loading_indicators:
                    self.loading_indicators[image_path].reset()

                self.images_unloaded += 1
                logging.debug(f"Unloaded distant image: {image_path}")

        except Exception as e:
            logging.debug(f"Error unloading distant images: {e}")

    def force_load_visible(self) -> None:
        """Force load all currently visible images."""
        try:
            for image_path in list(self.pending_images.keys()):
                widget = self.pending_images[image_path]["widget"]
                if (
                    self.viewport_manager.is_widget_visible(widget)
                    and image_path not in self.loaded_images
                    and image_path not in self.loading_images
                ):
                    self._load_image(image_path)

        except Exception as e:
            logging.warning(f"Error force loading visible images: {e}")

    def clear(self) -> None:
        """Clear all pending and loaded images."""
        self.pending_images.clear()
        self.loaded_images.clear()
        self.loading_images.clear()
        self.visible_images.clear()

        # Clean up loading indicators
        for indicator in self.loading_indicators.values():
            indicator.reset()
        self.loading_indicators.clear()

        if self.load_timer.isActive():
            self.load_timer.stop()

    def get_stats(self) -> Dict[str, Any]:
        """Get lazy loading statistics."""
        return {
            "pending_images": len(self.pending_images),
            "loaded_images": len(self.loaded_images),
            "loading_images": len(self.loading_images),
            "visible_images": len(self.visible_images),
            "images_loaded_lazily": self.images_loaded_lazily,
            "images_unloaded": self.images_unloaded,
            "loading_indicator_requests": self.loading_indicator_requests,
            "buffer_rows": self.buffer_rows,
            "grid_columns": self.grid_columns,
        }
