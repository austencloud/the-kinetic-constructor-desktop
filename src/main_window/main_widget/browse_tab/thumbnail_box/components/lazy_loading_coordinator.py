"""
Lazy Loading Coordinator - Interface with the lazy loading system.

Responsibilities:
- Lazy loading registration and coordination
- Viewport-based loading decisions
- Loading state synchronization
- Fallback to immediate loading
"""

import logging
from typing import Optional, Callable, TYPE_CHECKING
from PyQt6.QtCore import QObject, QTimer, QSize, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QWidget


if TYPE_CHECKING:
    from lazy_loading.browse_tab_lazy_loader import BrowseTabLazyLoader
    from lazy_loading.loading_indicator import LoadingIndicator


class LazyLoadingCoordinator(QObject):
    """
    Coordinates lazy loading operations for thumbnail images.

    Features:
    - Lazy loader integration
    - Viewport-based loading decisions
    - Loading state management
    - Graceful fallback handling
    """

    # Signals
    lazy_load_requested = pyqtSignal(str, QSize)  # path, size
    lazy_load_completed = pyqtSignal(str, QPixmap)  # path, pixmap
    lazy_load_failed = pyqtSignal(str, str)  # path, error
    fallback_triggered = pyqtSignal(str)  # path

    def __init__(self, widget: QWidget):
        super().__init__()

        self.widget = widget
        self._lazy_loader: Optional["BrowseTabLazyLoader"] = None
        self._loading_indicator: Optional["LoadingIndicator"] = None

        # State tracking
        self._is_lazy_loading_enabled = False
        self._is_registered = False
        self._pending_path: Optional[str] = None
        self._pending_size: Optional[QSize] = None

        # Fallback timer for when lazy loading fails
        self._fallback_timer = QTimer()
        self._fallback_timer.setSingleShot(True)
        self._fallback_timer.timeout.connect(self._trigger_fallback)
        self._fallback_delay_ms = (
            2000  # PERFORMANCE FIX: Reduced to 2 second fallback timeout
        )

        logging.debug("LazyLoadingCoordinator initialized")

    def enable_lazy_loading(self, lazy_loader: "BrowseTabLazyLoader") -> None:
        """
        Enable lazy loading with the provided loader.

        Args:
            lazy_loader: The browse tab lazy loader instance
        """
        self._lazy_loader = lazy_loader
        self._is_lazy_loading_enabled = True

        logging.debug("Lazy loading enabled")

    def disable_lazy_loading(self) -> None:
        """Disable lazy loading and clean up."""
        self._is_lazy_loading_enabled = False
        self._lazy_loader = None
        self._is_registered = False

        # Cancel any pending operations
        self._cancel_pending_operations()

        logging.debug("Lazy loading disabled")

    def request_image_load(
        self,
        image_path: str,
        target_size: QSize,
        load_callback: Callable[[str, QPixmap], None],
    ) -> bool:
        """
        Request image loading through lazy loading system.

        Args:
            image_path: Path to the image file
            target_size: Target size for the image
            load_callback: Callback function when image is loaded

        Returns:
            True if lazy loading was initiated, False if fallback needed
        """
        if not self._is_lazy_loading_enabled or not self._lazy_loader:
            logging.debug("Lazy loading not available, triggering fallback")
            self.fallback_triggered.emit(image_path)
            return False

        try:
            # Store pending request
            self._pending_path = image_path
            self._pending_size = target_size

            # Register with lazy loader
            self._loading_indicator = self._lazy_loader.register_thumbnail(
                image_path,
                self.widget,
                self._on_lazy_image_loaded,
                target_size=target_size,
                callback=load_callback,
            )

            self._is_registered = True

            # Start fallback timer
            self._fallback_timer.start(self._fallback_delay_ms)

            # Emit request signal
            self.lazy_load_requested.emit(image_path, target_size)

            logging.debug(f"Lazy load requested for: {image_path}")
            return True

        except Exception as e:
            logging.warning(f"Error requesting lazy load: {e}")
            self.fallback_triggered.emit(image_path)
            return False

    def _on_lazy_image_loaded(self, image_path: str, pixmap: QPixmap) -> None:
        """
        Callback when lazy loaded image is ready.

        Args:
            image_path: Path to the loaded image
            pixmap: The loaded pixmap
        """
        try:
            # Cancel fallback timer
            if self._fallback_timer.isActive():
                self._fallback_timer.stop()

            # Verify this is the expected image
            if image_path == self._pending_path:
                # Emit completion signal
                self.lazy_load_completed.emit(image_path, pixmap)

                # Clear pending state
                self._clear_pending_state()

                logging.debug(f"Lazy load completed for: {image_path}")
            else:
                logging.warning(f"Unexpected lazy load completion: {image_path}")

        except Exception as e:
            logging.error(f"Error in lazy load callback: {e}")
            self.lazy_load_failed.emit(image_path, str(e))

    def _trigger_fallback(self) -> None:
        """Trigger fallback loading when lazy loading times out."""
        if self._pending_path:
            logging.warning(
                f"Lazy loading timeout, triggering fallback: {self._pending_path}"
            )
            self.fallback_triggered.emit(self._pending_path)
            self._clear_pending_state()

    def _cancel_pending_operations(self) -> None:
        """Cancel any pending lazy loading operations."""
        if self._fallback_timer.isActive():
            self._fallback_timer.stop()

        self._clear_pending_state()

    def _clear_pending_state(self) -> None:
        """Clear pending request state."""
        self._pending_path = None
        self._pending_size = None
        self._is_registered = False

        # Clean up loading indicator
        if self._loading_indicator:
            self._loading_indicator = None

    def is_in_viewport(self) -> bool:
        """
        Check if the widget is currently in the viewport.

        Returns:
            True if widget is visible in viewport
        """
        if not self._lazy_loader:
            return True  # Default to visible if no lazy loader

        try:
            return self._lazy_loader.viewport_manager.is_widget_visible(self.widget)
        except Exception as e:
            logging.debug(f"Error checking viewport: {e}")
            return True  # Default to visible on error

    def is_in_loading_zone(self) -> bool:
        """
        Check if the widget is in the loading zone.

        Returns:
            True if widget is in loading zone
        """
        if not self._lazy_loader:
            return True  # Default to in zone if no lazy loader

        try:
            return self._lazy_loader.viewport_manager.is_widget_in_loading_zone(
                self.widget
            )
        except Exception as e:
            logging.debug(f"Error checking loading zone: {e}")
            return True  # Default to in zone on error

    def force_load(self) -> None:
        """Force immediate loading, bypassing lazy loading."""
        if self._pending_path:
            logging.debug(f"Force loading: {self._pending_path}")
            self.fallback_triggered.emit(self._pending_path)
            self._clear_pending_state()

    def get_loading_stats(self) -> dict:
        """Get loading statistics."""
        return {
            "lazy_loading_enabled": self._is_lazy_loading_enabled,
            "is_registered": self._is_registered,
            "has_pending_request": self._pending_path is not None,
            "pending_path": self._pending_path,
            "fallback_timeout_ms": self._fallback_delay_ms,
            "in_viewport": self.is_in_viewport(),
            "in_loading_zone": self.is_in_loading_zone(),
        }

    def set_fallback_timeout(self, timeout_ms: int) -> None:
        """
        Set the fallback timeout for lazy loading.

        Args:
            timeout_ms: Timeout in milliseconds
        """
        self._fallback_delay_ms = max(1000, timeout_ms)  # Minimum 1 second
        logging.debug(f"Fallback timeout set to: {self._fallback_delay_ms}ms")

    @property
    def is_lazy_loading_enabled(self) -> bool:
        """Check if lazy loading is currently enabled."""
        return self._is_lazy_loading_enabled

    @property
    def has_pending_request(self) -> bool:
        """Check if there's a pending lazy loading request."""
        return self._pending_path is not None

    @property
    def pending_image_path(self) -> Optional[str]:
        """Get the path of the pending image request."""
        return self._pending_path
