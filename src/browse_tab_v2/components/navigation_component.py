"""
Navigation Component - Modular Architecture

Extracted from browse_tab_view.py to provide focused navigation functionality.
Handles navigation sidebar integration, smooth scrolling, and section management.

Responsibilities:
- Navigation sidebar integration and management
- Smooth scroll navigation coordination
- Section-based navigation and highlighting
- Performance tracking for navigation clicks
- Scroll position persistence
"""

import logging
from typing import Optional, List, Dict
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
from PyQt6.QtCore import QTimer, QElapsedTimer, pyqtSignal

from ..core.interfaces import SequenceModel, BrowseTabConfig
from ..debug.window_resize_tracker import track_component, log_main_window_change
from .modern_navigation_sidebar import ModernNavigationSidebar
from .smooth_scroll_navigation import SmoothScrollNavigation
from .dynamic_section_headers import SectionType

logger = logging.getLogger(__name__)


class NavigationComponent(QWidget):
    """
    Modular navigation component handling sidebar and scroll navigation.

    This component encapsulates all navigation-related operations and provides
    a clean interface for the main view to interact with navigation features.
    """

    # Signals for parent coordination
    section_clicked = pyqtSignal(str)  # section_id
    active_section_changed = pyqtSignal(str)  # section_id
    scroll_finished = pyqtSignal(str)  # target_section

    def __init__(self, config: BrowseTabConfig = None, parent: QWidget = None):
        super().__init__(parent)

        self.config = config or BrowseTabConfig()

        # State management
        self._current_sequences: List[SequenceModel] = []
        self._current_sort_criteria = "alphabetical"
        self._active_section: Optional[str] = None

        # UI components
        self.navigation_sidebar: Optional[ModernNavigationSidebar] = None
        self.smooth_scroll: Optional[SmoothScrollNavigation] = None

        # Performance tracking for <16ms navigation response
        self._performance_timer = QElapsedTimer()
        self._interaction_timers: Dict[str, Dict] = {}
        self._click_times = []
        self._max_click_history = 50
        self._target_response_time = 16.0  # 16ms target

        # Section management
        self.current_section_type = SectionType.ALPHABETICAL

        # Performance tracking
        self._last_size = (0, 0)

        track_component("NavigationComponent_Initial", self, "Constructor start")
        log_main_window_change("NavigationComponent constructor start")

        self._setup_ui()
        self._connect_signals()
        self._load_preloaded_data()

        track_component("NavigationComponent_Complete", self, "Constructor complete")
        log_main_window_change("NavigationComponent constructor complete")
        logger.info("NavigationComponent initialized")

    def _setup_ui(self):
        """Setup the navigation UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create navigation sidebar
        track_component(
            "NavigationComponent_BeforeSidebar",
            self,
            "Before creating ModernNavigationSidebar",
        )

        self.navigation_sidebar = ModernNavigationSidebar(self.config, self)

        track_component(
            "NavigationComponent_AfterSidebar",
            self,
            "After creating ModernNavigationSidebar",
        )

        layout.addWidget(self.navigation_sidebar)

        # Set fixed width for navigation
        self.setFixedWidth(200)

        # Set responsive size policy
        self.setSizePolicy(
            QSizePolicy.Policy.Fixed,  # Fixed width sidebar
            QSizePolicy.Policy.Expanding,  # Allow vertical expansion
        )

        # CRITICAL: Pre-calculate and render sections in final expanded state
        self._initialize_with_preloaded_data()

        track_component(
            "NavigationComponent_SizeIsolation", self, "Complete size isolation applied"
        )
        log_main_window_change("After NavigationComponent size isolation applied")

    def _initialize_with_preloaded_data(self):
        """Initialize navigation with pre-loaded data to prevent progressive expansion."""
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
                        f"🧭 NAVIGATION_COMPONENT: Pre-calculating sections for {len(sequences)} sequences"
                    )

                    # Immediately update with pre-loaded data to establish final layout
                    self._current_sequences = sequences
                    self.update_for_sequences(sequences, "alphabetical")

                    logger.info(
                        f"NavigationComponent pre-initialized with {len(sequences)} sequences"
                    )
                    return

            print(
                "🧭 NAVIGATION_COMPONENT: No pre-loaded data - will expand when data arrives"
            )

        except Exception as e:
            logger.warning(f"Failed to initialize navigation with pre-loaded data: {e}")

    def _connect_signals(self):
        """Connect navigation sidebar signals to component signals."""
        if self.navigation_sidebar:
            self.navigation_sidebar.section_clicked.connect(self._on_section_clicked)

    def _load_preloaded_data(self):
        """Load pre-loaded data if available for immediate display."""
        try:
            from ..startup.data_preloader import get_preloaded_data

            preloaded_data = get_preloaded_data()
            if preloaded_data:
                sequences = preloaded_data.get("sequences", [])
                if sequences:
                    self._current_sequences = sequences
                    if self.navigation_sidebar:
                        self.navigation_sidebar.update_for_sequences(
                            sequences, "alphabetical"
                        )
                    logger.info(
                        f"Navigation component loaded with {len(sequences)} pre-loaded sequences"
                    )

        except Exception as e:
            logger.warning(
                f"Failed to load pre-loaded data for navigation component: {e}"
            )

    def setup_smooth_scroll(self, scroll_area, animation_manager):
        """Setup smooth scroll navigation with the provided scroll area."""
        try:
            if not scroll_area:
                logger.warning("No scroll area provided for smooth scroll navigation")
                return

            # Initialize smooth scroll navigation
            self.smooth_scroll = SmoothScrollNavigation(scroll_area, self.config, self)
            self.smooth_scroll.set_animation_manager(animation_manager)

            # Connect signals
            self.smooth_scroll.active_section_changed.connect(
                self._on_active_section_changed
            )
            self.smooth_scroll.scroll_finished.connect(self._on_scroll_finished)

            logger.debug("Smooth scroll navigation initialized successfully")

        except Exception as e:
            logger.error(f"Failed to setup smooth scroll navigation: {e}")

    def _on_section_clicked(self, section_id: str):
        """Handle navigation sidebar section click with performance tracking."""
        # Start user-perceived performance tracking
        interaction_id = f"nav_click_{section_id}_{self._performance_timer.elapsed()}"
        self._performance_timer.start()
        self._interaction_timers[interaction_id] = {
            "start_time": self._performance_timer.elapsed(),
            "section_id": section_id,
            "phase": "click_received",
        }

        logger.debug(f"Section clicked: {section_id} - Performance tracking started")

        if self.smooth_scroll:
            # Update performance tracking phase
            self._interaction_timers[interaction_id]["phase"] = "scroll_calculation"

            # Save current scroll position
            current_filter = self._get_current_filter_key()
            self.smooth_scroll.save_scroll_position(current_filter)

            # Update performance tracking phase
            self._interaction_timers[interaction_id]["phase"] = "scroll_initiated"

            # Scroll to section
            self.smooth_scroll.scroll_to_section(section_id, animated=True)

            # Schedule performance completion check
            QTimer.singleShot(
                50,
                lambda: self._complete_navigation_performance_tracking(interaction_id),
            )

        # Emit signal for parent coordination
        self.section_clicked.emit(section_id)

    def _on_active_section_changed(self, section_id: str):
        """Handle active section change from viewport tracking."""
        self._active_section = section_id
        if self.navigation_sidebar:
            self.navigation_sidebar.set_active_section(section_id)
        self.active_section_changed.emit(section_id)

    def _on_scroll_finished(self, target_section: str):
        """Handle scroll animation completion with performance tracking."""
        logger.debug(f"Scroll finished to section: {target_section}")

        # Find and complete any pending navigation performance tracking
        for interaction_id, timer_data in list(self._interaction_timers.items()):
            if timer_data.get("section_id") == target_section and timer_data.get(
                "phase"
            ) in ["scroll_initiated", "scroll_calculation"]:
                self._complete_navigation_performance_tracking(interaction_id)

        self.scroll_finished.emit(target_section)

    def _complete_navigation_performance_tracking(self, interaction_id: str):
        """Complete navigation performance tracking and record metrics."""
        if interaction_id not in self._interaction_timers:
            return

        timer_data = self._interaction_timers[interaction_id]
        end_time = self._performance_timer.elapsed()
        total_time = end_time - timer_data["start_time"]

        # Record click time
        self._click_times.append(total_time)
        if len(self._click_times) > self._max_click_history:
            self._click_times.pop(0)

        # Log performance
        if total_time > self._target_response_time:
            logger.warning(
                f"Slow navigation click: {total_time:.1f}ms (target: {self._target_response_time:.1f}ms) "
                f"for section {timer_data['section_id']}"
            )
        else:
            logger.debug(
                f"Navigation click performance: {total_time:.1f}ms for section {timer_data['section_id']}"
            )

        # Clean up
        del self._interaction_timers[interaction_id]

    def _get_current_filter_key(self) -> str:
        """Get current filter state as a key for scroll position persistence."""
        # Create a key based on current sort criteria
        return f"sort_{self._current_sort_criteria}"

    # Public interface methods
    def update_for_sequences(
        self, sequences: List[SequenceModel], sort_criteria: str = "alphabetical"
    ):
        """Update navigation with new sequences and sort criteria."""
        self._current_sequences = sequences
        self._current_sort_criteria = sort_criteria

        if self.navigation_sidebar:
            self.navigation_sidebar.update_for_sequences(sequences, sort_criteria)

        logger.debug(
            f"Navigation updated for {len(sequences)} sequences with {sort_criteria} sort"
        )

    def set_active_section(self, section_id: str):
        """Set the active section programmatically."""
        self._active_section = section_id
        if self.navigation_sidebar:
            self.navigation_sidebar.set_active_section(section_id)

    def get_active_section(self) -> Optional[str]:
        """Get the currently active section."""
        return self._active_section

    def get_navigation_performance_metrics(self) -> Dict:
        """Get navigation performance metrics."""
        if not self._click_times:
            return {"avg_response_time": 0, "max_response_time": 0, "click_count": 0}

        return {
            "avg_response_time": sum(self._click_times) / len(self._click_times),
            "max_response_time": max(self._click_times),
            "click_count": len(self._click_times),
            "target_response_time": self._target_response_time,
        }

    def sizeHint(self):
        """Provide size hint for responsive layout."""
        from PyQt6.QtCore import QSize

        return QSize(200, 600)  # Fixed width, expandable height

    def minimumSizeHint(self):
        """Provide minimum size hint."""
        from PyQt6.QtCore import QSize

        return QSize(200, 400)

    def hasHeightForWidth(self):
        """Disable height-for-width calculations."""
        return False
