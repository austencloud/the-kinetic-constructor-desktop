"""
Grid View Component - Modular Architecture

Extracted from browse_tab_view.py to provide focused thumbnail grid functionality.
Handles all grid-related operations including virtual scrolling, viewport management,
and thumbnail card creation.

Responsibilities:
- Thumbnail grid display and management
- Virtual scrolling and viewport optimization
- Thumbnail card creation and lifecycle
- Performance monitoring and optimization
- Integration with EfficientVirtualGrid
"""

import logging
from typing import Optional, List, Callable
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget, QSizePolicy
from PyQt6.QtCore import pyqtSignal, QElapsedTimer

from ..core.interfaces import SequenceModel, BrowseTabConfig
from ..debug.window_resize_tracker import track_component, log_main_window_change
from .efficient_virtual_grid import EfficientVirtualGrid
from .loading_states import LoadingIndicator, SkeletonScreen, ErrorState
from .animation_system import AnimationManager

logger = logging.getLogger(__name__)


class GridViewComponent(QWidget):
    """
    Modular grid view component handling thumbnail display and virtual scrolling.

    This component encapsulates all grid-related operations and provides
    a clean interface for the main view to interact with thumbnail display.
    """

    # Signals for parent coordination
    item_clicked = pyqtSignal(str, int)  # sequence_id, index
    item_double_clicked = pyqtSignal(str, int)  # sequence_id, index
    viewport_changed = pyqtSignal(int, int)  # start_index, end_index

    def __init__(self, config: BrowseTabConfig = None, parent: QWidget = None):
        super().__init__(parent)

        self.config = config or BrowseTabConfig()

        # State management
        self._sequences: List[SequenceModel] = []
        self._item_creator: Optional[Callable] = None

        # UI components
        self.content_stack: Optional[QStackedWidget] = None
        self.thumbnail_grid: Optional[EfficientVirtualGrid] = None
        self.loading_indicator: Optional[LoadingIndicator] = None
        self.skeleton_screen: Optional[SkeletonScreen] = None
        self.error_state: Optional[ErrorState] = None

        # Animation and performance
        self.animation_manager: Optional[AnimationManager] = None
        self.hover_manager = None

        # Performance tracking
        self._performance_timer = QElapsedTimer()
        self._last_size = (0, 0)

        track_component("GridViewComponent_Initial", self, "Constructor start")
        log_main_window_change("GridViewComponent constructor start")

        self._setup_ui()
        self._setup_hover_system()

        track_component("GridViewComponent_Complete", self, "Constructor complete")
        log_main_window_change("GridViewComponent constructor complete")
        logger.info("GridViewComponent initialized")

    def _setup_ui(self):
        """Setup the grid view UI with content stack."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Content stack with responsive sizing
        self.content_stack = QStackedWidget()
        self.content_stack.setSizePolicy(
            QSizePolicy.Policy.Expanding,  # Allow horizontal expansion
            QSizePolicy.Policy.Expanding,  # Allow vertical expansion for content
        )

        # Create ultra-efficient virtual grid for maximum performance
        track_component(
            "GridViewComponent_BeforeGrid", self, "Before creating EfficientVirtualGrid"
        )

        print("🚀 GRID_VIEW_COMPONENT: Creating EfficientVirtualGrid")
        self.thumbnail_grid = EfficientVirtualGrid(self.config)
        print("🚀 GRID_VIEW_COMPONENT: EfficientVirtualGrid created")

        # Connect grid signals
        self.thumbnail_grid.item_clicked.connect(self._on_item_clicked)
        self.thumbnail_grid.item_double_clicked.connect(self._on_item_double_clicked)
        self.thumbnail_grid.viewport_changed.connect(self._on_viewport_changed)

        track_component(
            "GridViewComponent_AfterGrid", self, "After creating EfficientVirtualGrid"
        )

        # Create loading states
        self.loading_indicator = LoadingIndicator(size=64, show_text=True)
        self.skeleton_screen = SkeletonScreen(pattern="grid", item_count=9)
        self.error_state = ErrorState("Failed to load sequences")
        self.error_state.retry_requested.connect(self._on_retry_requested)

        # Add to stack
        self.content_stack.addWidget(self.thumbnail_grid)
        self.content_stack.addWidget(self.loading_indicator)
        self.content_stack.addWidget(self.skeleton_screen)
        self.content_stack.addWidget(self.error_state)

        layout.addWidget(self.content_stack)

        # Set responsive size policy
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,  # Allow horizontal expansion
            QSizePolicy.Policy.Expanding,  # Allow vertical expansion
        )

        # Check for pre-loaded data to determine initial state
        self._check_for_preloaded_data()

        track_component(
            "GridViewComponent_SizeIsolation", self, "Complete size isolation applied"
        )
        log_main_window_change("After GridViewComponent size isolation applied")

    def _check_for_preloaded_data(self):
        """Check for pre-loaded data and set appropriate initial state."""
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
                        f"🚀 GRID_VIEW_COMPONENT: Found {len(sequences)} pre-loaded sequences - starting with content"
                    )

                    # Set sequences immediately and show content
                    self.set_sequences(sequences)
                    self.show_content()
                    logger.info(
                        f"GridViewComponent initialized with {len(sequences)} pre-loaded sequences"
                    )
                    return

            # No pre-loaded data - start with skeleton
            print("🚀 GRID_VIEW_COMPONENT: No pre-loaded data - starting with skeleton")
            self.content_stack.setCurrentWidget(self.skeleton_screen)

        except Exception as e:
            logger.warning(f"Failed to check for pre-loaded data: {e}")
            # Fallback to skeleton state
            self.content_stack.setCurrentWidget(self.skeleton_screen)

    def _setup_hover_system(self):
        """Initialize optimized hover animation system."""
        try:
            from .optimized_hover_manager import get_global_hover_manager

            self.hover_manager = get_global_hover_manager()
            logger.info("GridViewComponent initialized with optimized hover system")
        except ImportError:
            logger.warning("Optimized hover manager not available")
            self.hover_manager = None

    def set_item_creator(self, creator: Callable):
        """Set the item creator function for thumbnail cards."""
        self._item_creator = creator
        if self.thumbnail_grid:
            self.thumbnail_grid.set_item_creator(creator)
        print("🚀 GRID_VIEW_COMPONENT: Item creator set")

    def set_animation_manager(self, animation_manager: AnimationManager):
        """Set animation manager for grid animations."""
        self.animation_manager = animation_manager

    def set_sequences(self, sequences: List[SequenceModel]):
        """Set sequences for display with instant content prioritization (no skeleton loaders)."""
        print(f"🚀 INSTANT_GRID: set_sequences called with {len(sequences)} sequences")

        self._sequences = sequences

        if self.thumbnail_grid:
            print(
                f"🚀 INSTANT_GRID: Calling thumbnail_grid.set_sequences with {len(sequences)} sequences"
            )
            self.thumbnail_grid.set_sequences(sequences)
            print("🚀 INSTANT_GRID: thumbnail_grid.set_sequences completed")

        # CRITICAL: Show content immediately - bypass all skeleton states
        self.show_content()
        print(
            "🚀 INSTANT_GRID: Content displayed immediately - no skeleton loaders shown"
        )

    def _on_item_clicked(self, sequence_id: str, index: int):
        """Handle item click events."""
        logger.debug(f"Grid item clicked: {sequence_id} at index {index}")
        self.item_clicked.emit(sequence_id, index)

    def _on_item_double_clicked(self, sequence_id: str, index: int):
        """Handle item double click events."""
        logger.debug(f"Grid item double clicked: {sequence_id} at index {index}")
        self.item_double_clicked.emit(sequence_id, index)

    def _on_viewport_changed(self, start_index: int, end_index: int):
        """Handle viewport changes for efficient loading."""
        print(f"📡 GRID_VIEW_COMPONENT: Viewport changed {start_index}-{end_index}")
        logger.debug(f"Grid viewport changed: {start_index}-{end_index}")
        self.viewport_changed.emit(start_index, end_index)

    def _on_retry_requested(self):
        """Handle retry requests from error state."""
        logger.info("Grid retry requested")
        self.show_loading_state()

    # State management methods
    def show_loading_state(self):
        """Show loading indicator."""
        if self.content_stack:
            self.content_stack.setCurrentWidget(self.loading_indicator)

    def show_skeleton_state(self):
        """Show skeleton screen."""
        if self.content_stack:
            self.content_stack.setCurrentWidget(self.skeleton_screen)

    def show_error_state(self, error_message: str = None):
        """Show error state."""
        if self.error_state and error_message:
            self.error_state.set_error_message(error_message)
        if self.content_stack:
            self.content_stack.setCurrentWidget(self.error_state)

    def show_content(self):
        """Show main grid content."""
        if self.content_stack:
            self.content_stack.setCurrentWidget(self.thumbnail_grid)
            print("📋 GRID_VIEW_COMPONENT: Set thumbnail_grid as current widget")

    # Public interface methods
    def get_sequences(self) -> List[SequenceModel]:
        """Get current sequences."""
        return self._sequences.copy()

    def get_visible_range(self) -> tuple:
        """Get current visible range."""
        if self.thumbnail_grid:
            return (
                self.thumbnail_grid._viewport_start,
                self.thumbnail_grid._viewport_end,
            )
        return (0, 0)

    def force_refresh(self):
        """Force refresh of the grid display."""
        if self.thumbnail_grid and self._sequences:
            self.thumbnail_grid.set_sequences(self._sequences)

    def cleanup(self):
        """Cleanup grid resources."""
        try:
            if self.loading_indicator:
                self.loading_indicator.stop_animation()
            if self.skeleton_screen:
                self.skeleton_screen.stop_animation()
            logger.info("GridViewComponent cleanup completed")
        except Exception as e:
            logger.error(f"GridViewComponent cleanup failed: {e}")

    def sizeHint(self):
        """Provide size hint for responsive layout."""
        from PyQt6.QtCore import QSize

        return QSize(1600, 800)  # Expandable dimensions

    def minimumSizeHint(self):
        """Provide minimum size hint."""
        from PyQt6.QtCore import QSize

        return QSize(600, 400)

    def hasHeightForWidth(self):
        """Disable height-for-width calculations."""
        return False
