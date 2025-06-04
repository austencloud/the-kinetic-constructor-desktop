"""
Integration adapter for browse tab v2 with existing application.

This adapter provides compatibility with the existing browse tab interface
while using the new v2 architecture internally.
"""

import logging
from typing import TYPE_CHECKING, Optional, Any
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import pyqtSignal, QTimer

from ..core.interfaces import BrowseTabConfig
from .. import BrowseTabV2Factory
from ..debug.window_resize_tracker import (
    set_phase,
    track_component,
    log_main_window_change,
)

if TYPE_CHECKING:
    from .. import BrowseTabV2

logger = logging.getLogger(__name__)


class BrowseTabV2Adapter(QWidget):
    """
    Adapter that provides compatibility with existing browse tab interface
    while using the new v2 architecture internally.

    This allows the new browse tab to be integrated into the existing
    application with minimal changes to the main application code.
    """

    # Signals for compatibility with existing browse tab
    sequence_selected = pyqtSignal(str)  # sequence_name
    filter_changed = pyqtSignal(dict)  # filter_data
    loading_changed = pyqtSignal(bool)  # is_loading

    def __init__(self, json_manager=None, settings_manager=None, parent=None):
        super().__init__(parent)

        self.json_manager = json_manager
        self.settings_manager = settings_manager
        self.main_widget = parent  # Store the main widget reference for regeneration

        # Internal browse tab v2 instance
        self.browse_tab_v2: Optional["BrowseTabV2"] = None
        self._initialized = False

        # Resize tracking
        self._last_size = (0, 0)

        set_phase("BrowseTabV2Adapter_Creation")
        track_component("BrowseTabV2Adapter_Initial", self, "Constructor start")
        log_main_window_change("BrowseTabV2Adapter constructor start")

        self._setup_ui()
        self._create_browse_tab_v2()

        # Auto-initialize after a short delay
        QTimer.singleShot(100, self._initialize_async)

        track_component("BrowseTabV2Adapter_Created", self, "Constructor complete")
        log_main_window_change("BrowseTabV2Adapter constructor complete")
        logger.info("BrowseTabV2Adapter created")

    def _setup_ui(self):
        """Setup the adapter UI."""
        set_phase("BrowseTabV2Adapter_UI_Setup")
        log_main_window_change("Before adapter UI setup")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # RESPONSIVE FIX: Implement proportional sizing with proper size policies
        from PyQt6.QtWidgets import QSizePolicy

        # Set responsive size policy that allows proportional scaling
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,  # Allow horizontal expansion
            QSizePolicy.Policy.Preferred,  # Prefer natural height, don't force expansion
        )

        # Use default layout constraint for responsive behavior
        layout.setSizeConstraint(QVBoxLayout.SizeConstraint.SetDefaultConstraint)

        track_component(
            "BrowseTabV2Adapter_ResponsiveSizing", self, "Responsive sizing applied"
        )
        log_main_window_change("After BrowseTabV2Adapter responsive sizing applied")

        # Initially show loading message
        self.loading_label = QLabel("Initializing Browse Tab v2...")
        self.loading_label.setStyleSheet(
            """
            QLabel {
                font-size: 14px;
                color: #666;
                padding: 20px;
                text-align: center;
            }
        """
        )
        layout.addWidget(self.loading_label)

        track_component("BrowseTabV2Adapter_UIComplete", self, "UI setup complete")
        log_main_window_change("After adapter UI setup complete")

    def _create_browse_tab_v2(self):
        """Create the internal browse tab v2 instance."""
        try:
            # Create configuration optimized for integration
            config = BrowseTabConfig(
                max_concurrent_image_loads=4,
                image_cache_size=200,
                enable_performance_monitoring=True,
                enable_debug_logging=False,  # Reduce noise in main app
                default_columns=3,
            )

            # Add main_widget to settings_manager for regeneration functionality
            if self.settings_manager and self.main_widget:
                self.settings_manager.main_widget = self.main_widget

            # Create browse tab v2
            self.browse_tab_v2 = BrowseTabV2Factory.create_with_config(
                config=config,
                json_manager=self.json_manager,
                settings_manager=self.settings_manager,
            )

            # Connect internal signals to adapter signals
            self._connect_signals()

            logger.info("Browse tab v2 created for adapter")

        except Exception as e:
            logger.error(f"Failed to create browse tab v2 in adapter: {e}")
            self._show_error(f"Failed to initialize: {e}")

    def _connect_signals(self):
        """Connect internal browse tab signals to adapter signals."""
        if not self.browse_tab_v2:
            return

        try:
            # Connect ViewModel signals
            viewmodel = self.browse_tab_v2.viewmodel

            viewmodel.state_changed.connect(self._on_internal_state_changed)
            viewmodel.loading_started.connect(
                lambda op: self.loading_changed.emit(True)
            )
            viewmodel.loading_finished.connect(
                lambda op, success: self.loading_changed.emit(False)
            )

            logger.debug("Internal signals connected")

        except Exception as e:
            logger.error(f"Failed to connect signals: {e}")

    def _on_internal_state_changed(self, state):
        """Handle internal state changes."""
        try:
            # Emit sequence selection if changed
            if state.selected_sequence_id:
                self.sequence_selected.emit(state.selected_sequence_id)

            # Emit filter changes
            filter_data = {
                "active_filters": len(state.active_filters),
                "search_query": (
                    state.search_criteria.query if state.search_criteria else ""
                ),
                "total_sequences": len(state.sequences),
                "filtered_sequences": len(state.filtered_sequences),
            }
            self.filter_changed.emit(filter_data)

        except Exception as e:
            logger.error(f"Error handling internal state change: {e}")

    def _initialize_async(self):
        """Initialize asynchronously using QTimer (PyQt compatible)."""
        # Use QTimer for PyQt compatibility instead of asyncio
        QTimer.singleShot(100, self._sync_initialize)

    def _sync_initialize(self):
        """Synchronous initialization for PyQt compatibility."""
        try:
            set_phase("BrowseTabV2Adapter_Initialization")
            log_main_window_change("Before adapter initialization")

            if not self.browse_tab_v2:
                self._show_error("Browse tab v2 not created")
                return

            # Initialize browse tab v2 synchronously
            # Note: We'll skip the async initialization for now to avoid event loop issues
            logger.info("Initializing browse tab v2 synchronously...")

            # Replace loading label with actual view
            self.layout().removeWidget(self.loading_label)
            self.loading_label.deleteLater()
            track_component(
                "BrowseTabV2Adapter_LoadingRemoved", self, "Loading label removed"
            )
            log_main_window_change("After loading label removed")

            # Add the actual browse tab view
            view = self.browse_tab_v2.get_view()
            track_component("BrowseTabView_BeforeAdd", view, "Before adding to adapter")
            log_main_window_change("Before adding browse tab view")

            self.layout().addWidget(view)

            track_component(
                "BrowseTabV2Adapter_ViewAdded", self, "Browse tab view added"
            )
            track_component("BrowseTabView_AfterAdd", view, "After adding to adapter")
            log_main_window_change("After adding browse tab view - CRITICAL POINT")

            self._initialized = True
            logger.info("BrowseTabV2Adapter initialized successfully")

            # NOTE: Sequence loading is already triggered by get_view() above
            # No need for additional delayed loading to avoid duplicate processing

        except Exception as e:
            logger.error(f"Failed to initialize adapter: {e}")
            self._show_error(f"Initialization failed: {e}")

    def resizeEvent(self, event):
        """Override resize event to track size changes."""
        old_size = self._last_size
        new_size = (event.size().width(), event.size().height())

        # Log the resize
        from ..debug.window_resize_tracker import get_tracker

        tracker = get_tracker()
        tracker.log_resize(
            "BrowseTabV2Adapter_ResizeEvent",
            old_size[0],
            old_size[1],
            new_size[0],
            new_size[1],
            f"Phase: {tracker.initialization_phase}",
        )

        # Also log main window change
        log_main_window_change(f"BrowseTabV2Adapter resize: {old_size} → {new_size}")

        self._last_size = new_size
        super().resizeEvent(event)

    def sizeHint(self):
        """
        Provide proportional size hint based on parent container dimensions.

        This method calculates the preferred size as a percentage of the parent
        container to enable responsive scaling while preventing unwanted expansion.
        """
        from PyQt6.QtCore import QSize

        # Get parent widget dimensions for proportional sizing
        parent_widget = self.parent()
        if parent_widget and hasattr(parent_widget, "size"):
            parent_size = parent_widget.size()

            # Calculate proportional dimensions (use 100% width, natural height)
            width = parent_size.width()

            # Calculate height based on content requirements
            # For browse tab, we need space for filter panel (120px) + content area
            filter_height = 120
            content_height = max(
                600, parent_size.height() - filter_height - 52
            )  # 52px for menu bar
            total_height = filter_height + content_height

            return QSize(width, total_height)
        else:
            # Fallback to reasonable default proportions
            return QSize(2304, 1200)

    def minimumSizeHint(self):
        """
        Provide minimum size hint to prevent unwanted layout expansion.
        """
        from PyQt6.QtCore import QSize

        return QSize(800, 720)

    def hasHeightForWidth(self):
        """
        Disable height-for-width layout calculations to prevent size propagation.
        """
        return False

    def _load_sequences_delayed(self):
        """Load sequences with a delay to ensure UI is ready - Qt-native approach."""
        try:
            if self.browse_tab_v2 and self._initialized:
                # Get the viewmodel and trigger sequence loading
                viewmodel = self.browse_tab_v2.viewmodel
                if viewmodel:
                    # Use Qt-native synchronous loading instead of asyncio
                    def trigger_load():
                        try:
                            # Call the synchronous load_sequences method
                            viewmodel.load_sequences()
                            logger.info("Sequence loading triggered successfully")
                        except Exception as e:
                            logger.error(f"Failed to trigger sequence loading: {e}")

                    # Trigger loading after a short delay
                    QTimer.singleShot(100, trigger_load)
                    logger.info("Triggered sequence loading via viewmodel")
                else:
                    logger.warning("No viewmodel available for sequence loading")
        except Exception as e:
            logger.error(f"Failed to load sequences: {e}")

    def _show_error(self, message: str):
        """Show error message."""
        try:
            # Clear layout
            layout = self.layout()
            while layout.count():
                child = layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

            # Show error
            error_label = QLabel(f"Error: {message}")
            error_label.setStyleSheet(
                """
                QLabel {
                    color: #f44336;
                    font-size: 14px;
                    padding: 20px;
                    text-align: center;
                    background: #ffebee;
                    border: 1px solid #f44336;
                    border-radius: 4px;
                }
            """
            )
            layout.addWidget(error_label)

        except Exception as e:
            logger.error(f"Failed to show error: {e}")

    # Public API for compatibility with existing browse tab

    def load_sequences(self):
        """Load sequences (compatibility method) - Qt-native approach."""
        if self.browse_tab_v2 and self._initialized:
            # Trigger sequence loading via viewmodel
            viewmodel = self.browse_tab_v2.viewmodel
            if viewmodel:

                def trigger_load():
                    try:
                        # Use synchronous load_sequences method
                        viewmodel.load_sequences()
                        logger.info("Load sequences completed successfully")
                    except Exception as e:
                        logger.error(f"Failed to trigger sequence loading: {e}")

                QTimer.singleShot(50, trigger_load)
                logger.info("Load sequences triggered via viewmodel")
            else:
                logger.warning("No viewmodel available for load_sequences")

    def apply_filter(self, filter_type: str, filter_value: Any):
        """Apply filter (compatibility method)."""
        if self.browse_tab_v2 and self._initialized:
            # For now, defer async operations to avoid event loop issues
            logger.info(
                f"Apply filter called: {filter_type}={filter_value} - deferred to Phase 2"
            )

    def search_sequences(self, query: str):
        """Search sequences (compatibility method)."""
        if self.browse_tab_v2 and self._initialized:
            self.browse_tab_v2.search_sequences(query)

    def select_sequence(self, sequence_id: str):
        """Select sequence (compatibility method)."""
        if self.browse_tab_v2 and self._initialized:
            self.browse_tab_v2.select_sequence(sequence_id)

    def get_current_state(self):
        """Get current state (compatibility method)."""
        if self.browse_tab_v2 and self._initialized:
            return self.browse_tab_v2.get_state()
        return None

    def get_performance_stats(self):
        """Get performance statistics (compatibility method)."""
        if self.browse_tab_v2 and self._initialized:
            # For now, return basic stats without async operations
            logger.info("Get performance stats called - deferred to Phase 2")
            return {"status": "deferred_to_phase_2"}
        return None

    def is_ready(self) -> bool:
        """Check if adapter is ready."""
        return self._initialized and self.browse_tab_v2 is not None

    def cleanup(self):
        """Cleanup resources."""
        try:
            if self.browse_tab_v2:
                self.browse_tab_v2.cleanup()
            logger.info("BrowseTabV2Adapter cleanup completed")
        except Exception as e:
            logger.error(f"BrowseTabV2Adapter cleanup failed: {e}")


def create_browse_tab_v2_adapter(json_manager=None, settings_manager=None, parent=None):
    """
    Convenience function to create a browse tab v2 adapter.

    This can be used as a drop-in replacement for the existing browse tab
    in the main application.

    Args:
        json_manager: The JSON manager instance
        settings_manager: The settings manager instance
        parent: Parent widget

    Returns:
        BrowseTabV2Adapter instance
    """
    return BrowseTabV2Adapter(
        json_manager=json_manager, settings_manager=settings_manager, parent=parent
    )
