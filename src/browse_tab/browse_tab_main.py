"""
Browse Tab v2 Main Coordinator - Clean Architecture Implementation.

This is the primary coordinator component that orchestrates focused, modular components
following modern software architecture principles. Each component has a single
responsibility and communicates through well-defined interfaces.

Target Architecture:
- Main coordinator: <300 lines (this file)
- components/filter_panel.py: Filtering UI and logic (<200 lines)
- components/grid_view.py: Thumbnail grid display (<200 lines)
- components/sequence_viewer.py: Sequence detail display (<200 lines)
- components/navigation_sidebar.py: Alphabet navigation (<200 lines)
- components/thumbnail_card.py: Individual thumbnail widget (<200 lines)
- services/: Data management, filtering, caching services

Performance Preservation:
- All QElapsedTimer profiling maintained
- 8ms scroll debouncing preserved
- Pre-computed hash maps for filtering
- Width-first image scaling (4-column 25% layout)
- Progressive loading with staggered animations
- Glassmorphism styling (rgba(255,255,255,0.08))
- Type 3 kinetic alphabet support (W-, X-, Y-)
"""

import logging
from typing import Optional, TYPE_CHECKING
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from PyQt6.QtCore import QTimer, pyqtSignal

# Use TYPE_CHECKING to avoid circular imports
if TYPE_CHECKING:
    from .viewmodels.browse_tab_viewmodel import BrowseTabViewModel
    from .core.interfaces import BrowseTabConfig, FilterCriteria, SortOrder
    from .core.state import SequenceModel

# Runtime imports for essential classes
from .core.interfaces import (
    SequenceModel,
    FilterCriteria,
    SortOrder,
    SearchCriteria,
    BrowseTabConfig,
)

logger = logging.getLogger(__name__)


class BrowseTabMain(QWidget):
    """
    Main coordinator for Browse Tab v2 - Clean Architecture Implementation.

    This coordinator orchestrates focused components following the single responsibility
    principle. Each component is <200 lines and handles one specific concern.

    Responsibilities (Coordinator Pattern):
    - Component initialization and lifecycle management
    - Signal routing between components
    - Layout management and responsive sizing
    - Performance coordination and monitoring
    - Error handling and state management
    """

    # Signals for external communication
    sequence_selected = pyqtSignal(str)  # sequence_id
    sequence_loaded = pyqtSignal(str)  # sequence_id
    error_occurred = pyqtSignal(str)  # error_message
    content_ready = pyqtSignal()  # emitted when content is ready for display

    def __init__(self, viewmodel, config, cache_service=None):
        super().__init__()

        logger.info("BrowseTabV2Main coordinator starting initialization...")

        self.viewmodel = viewmodel
        self.config = config
        self.cache_service = cache_service or getattr(viewmodel, "cache_service", None)

        # Component references (will be created in _setup_components)
        self.filter_panel = None
        self.grid_view = None
        self.sequence_viewer = None
        self.navigation_sidebar = None

        # Service references (will be injected)
        self.sequence_data_service = None
        self.filter_service = None
        self.performance_cache_service = None

        # State management
        self._sequences = []
        self._current_filter_criteria = []
        self._current_sort_criteria = "alphabetical"

        # Performance tracking
        self._performance_timer = None
        self._initialization_start_time = None

        # Initialize the coordinator
        try:
            self._initialize_coordinator()
            logger.info(
                "BrowseTabV2Main coordinator initialization completed successfully!"
            )
        except Exception as e:
            logger.error(f"❌ COORDINATOR_INIT: Failed to initialize coordinator: {e}")
            import traceback

            traceback.print_exc()
            raise

        logger.info("✅ NEW ARCHITECTURE: BrowseTabV2Main coordinator created")

    def _initialize_coordinator(self):
        """Initialize the coordinator with all components and services."""
        try:
            # Start performance tracking
            self._start_performance_tracking()

            # Setup services first (dependency injection)
            self._setup_services()

            # Setup UI layout
            self._setup_layout()

            # Create and initialize components
            self._setup_components()

            # Connect component signals
            self._connect_component_signals()

            # Apply styling and effects
            self._apply_styling()

            # Connect to viewmodel
            self._connect_viewmodel()

            # CRITICAL: Check for immediate data availability and trigger content display
            self._check_immediate_data_availability()

            # Complete performance tracking
            self._complete_performance_tracking()

        except Exception as e:
            logger.error(f"Failed to initialize coordinator: {e}")
            self.error_occurred.emit(f"Initialization failed: {e}")

    def _start_performance_tracking(self):
        """Start performance tracking for initialization."""
        from PyQt6.QtCore import QElapsedTimer

        self._performance_timer = QElapsedTimer()
        self._performance_timer.start()
        self._initialization_start_time = self._performance_timer.elapsed()
        logger.debug("Performance tracking started for coordinator initialization")

    def _setup_services(self):
        """Setup service layer with dependency injection - REAL INTEGRATION."""
        try:
            # Import services
            from .services.sequence_data_service import SequenceDataService
            from .services.filter_service import FilterService
            from .services.performance_cache_service import PerformanceCacheService

            # Get JSON manager from viewmodel for real data integration
            json_manager = getattr(self.viewmodel, "json_manager", None)
            if not json_manager:
                # Try to get from sequence service
                sequence_service = getattr(self.viewmodel, "sequence_service", None)
                if sequence_service:
                    json_manager = getattr(sequence_service, "json_manager", None)

            # Create service instances with real dependencies
            self.sequence_data_service = SequenceDataService(self.config, parent=self)

            # Inject JSON manager into sequence data service
            if json_manager:
                self.sequence_data_service.json_manager = json_manager
                logger.info(
                    "✅ REAL INTEGRATION: JSON manager injected into SequenceDataService"
                )

            self.filter_service = FilterService(self.config)
            self.performance_cache_service = PerformanceCacheService(self.config)

            logger.debug(
                "✅ REAL INTEGRATION: Services initialized with real dependencies"
            )

        except ImportError as e:
            logger.warning(f"Service import failed: {e}")
            # Create placeholder services for now
            self.sequence_data_service = None
            self.filter_service = None
            self.performance_cache_service = None

    def _setup_layout(self):
        """Setup the main layout structure (3-panel design)."""
        # Main horizontal layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(10)

        # Left panel (2/3 width) - Navigation + Content area
        self.left_panel = QWidget()
        left_layout = QHBoxLayout(self.left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        # Navigation sidebar placeholder (200px fixed width)
        self.navigation_container = QWidget()
        self.navigation_container.setFixedWidth(200)
        left_layout.addWidget(self.navigation_container, 0)

        # Content area (filters + grid)
        self.content_area = QWidget()
        content_layout = QVBoxLayout(self.content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Filter panel placeholder (fixed height)
        self.filter_container = QWidget()
        self.filter_container.setFixedHeight(120)
        content_layout.addWidget(self.filter_container, 0)

        # Grid view placeholder (expandable)
        self.grid_container = QWidget()
        content_layout.addWidget(self.grid_container, 1)

        left_layout.addWidget(self.content_area, 1)

        # Right panel (1/3 width) - Sequence viewer
        self.sequence_viewer_container = QWidget()

        # Add panels to main layout with proper stretch factors
        main_layout.addWidget(self.left_panel, 2)  # 2/3 width
        main_layout.addWidget(self.sequence_viewer_container, 1)  # 1/3 width

        logger.debug("Layout structure created successfully")

    def _setup_components(self):
        """Create and initialize all components."""
        try:
            # Import new components (will be created in Phase 3)
            from .components.filter_panel import FilterPanel
            from .components.grid_view import GridView
            from .components.sequence_viewer import SequenceViewer
            from .components.navigation_sidebar import NavigationSidebar

            # Create components with service injection
            self.filter_panel = FilterPanel(
                config=self.config,
                filter_service=self.filter_service,
                parent=self.filter_container,
            )

            self.grid_view = GridView(
                config=self.config,
                sequence_data_service=self.sequence_data_service,
                performance_cache_service=self.performance_cache_service,
                parent=self.grid_container,
            )

            self.sequence_viewer = SequenceViewer(
                config=self.config, parent=self.sequence_viewer_container
            )

            self.navigation_sidebar = NavigationSidebar(
                config=self.config, parent=self.navigation_container
            )

            # Add components to their containers
            self._add_components_to_containers()

            logger.debug("Components created successfully")

        except ImportError as e:
            logger.warning(f"Component import failed (will be created in Phase 3): {e}")
            # Create placeholder components for now
            self._create_placeholder_components()

    def _add_components_to_containers(self):
        """Add components to their respective containers."""
        # Add filter panel to filter container
        filter_layout = QVBoxLayout(self.filter_container)
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_layout.addWidget(self.filter_panel)

        # Add grid view to grid container
        grid_layout = QVBoxLayout(self.grid_container)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout.addWidget(self.grid_view)

        # Add sequence viewer to sequence viewer container
        viewer_layout = QVBoxLayout(self.sequence_viewer_container)
        viewer_layout.setContentsMargins(0, 0, 0, 0)
        viewer_layout.addWidget(self.sequence_viewer)

        # Add navigation sidebar to navigation container
        nav_layout = QVBoxLayout(self.navigation_container)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.addWidget(self.navigation_sidebar)

    def _create_placeholder_components(self):
        """Create placeholder components until new ones are implemented."""
        from PyQt6.QtWidgets import QLabel

        # Placeholder labels
        self.filter_panel = QLabel("Filter Panel (To be refactored)")
        self.grid_view = QLabel("Grid View (To be refactored)")
        self.sequence_viewer = QLabel("Sequence Viewer (To be refactored)")
        self.navigation_sidebar = QLabel("Navigation Sidebar (To be refactored)")

        # Add to containers
        self._add_components_to_containers()

    def _connect_component_signals(self):
        """Connect signals between components for coordination."""
        if hasattr(self.filter_panel, "filter_changed"):
            self.filter_panel.filter_changed.connect(self._on_filter_changed)

        if hasattr(self.grid_view, "item_clicked"):
            self.grid_view.item_clicked.connect(self._on_item_clicked)

        if hasattr(self.navigation_sidebar, "section_clicked"):
            self.navigation_sidebar.section_clicked.connect(self._on_section_clicked)

        logger.debug("Component signals connected")

    def _apply_styling(self):
        """Apply glassmorphism styling to panels."""
        try:
            from styles.glassmorphism_coordinator import GlassmorphismCoordinator

            coordinator = GlassmorphismCoordinator()

            # Apply glassmorphism to left panel (CSS only, no blur effects)
            self.left_panel.setStyleSheet(
                """
                QWidget {
                    background: rgba(255, 255, 255, 0.08);
                    border-radius: 20px;
                    border: 1px solid rgba(255, 255, 255, 0.2);
                }
            """
            )

            # CRITICAL FIX: Remove blur effect that causes crashes and content to appear fuzzy
            # coordinator.add_blur_effect(self.left_panel, 10)  # DISABLED - causes segfault

            # Apply shadow effect only (safer than blur)
            coordinator.add_shadow_effect(
                self.left_panel,
                offset_x=0,
                offset_y=4,
                blur_radius=12,
                color="rgba(0, 0, 0, 0.1)",
            )

            logger.debug(
                "Glassmorphism styling applied (blur effects disabled for stability)"
            )

        except Exception as e:
            logger.warning(f"Failed to apply glassmorphism: {e}")
            # Fallback to basic transparent styling
            self.left_panel.setStyleSheet(
                """
                QWidget {
                    background: transparent;
                    border: none;
                }
            """
            )

    def _connect_viewmodel(self):
        """Connect to viewmodel for data management - CRITICAL LOADING STATE HANDLING."""
        if self.viewmodel:
            # CRITICAL: Connect state_changed signal for loading->content transition
            self.viewmodel.state_changed.connect(self._on_viewmodel_state_changed)
            self.viewmodel.error_occurred.connect(self._on_viewmodel_error)

            # Connect additional signals for comprehensive state management
            if hasattr(self.viewmodel, "loading_started"):
                self.viewmodel.loading_started.connect(self._on_loading_started)
            if hasattr(self.viewmodel, "loading_finished"):
                self.viewmodel.loading_finished.connect(self._on_loading_finished)

            # CRITICAL FIX: Connect to state manager for sequence updates
            if hasattr(self.viewmodel, "state_manager"):
                logger.info(
                    f"✅ CRITICAL: Found state manager: {self.viewmodel.state_manager}"
                )
                if hasattr(self.viewmodel.state_manager, "state_changed"):
                    self.viewmodel.state_manager.state_changed.connect(
                        self._on_state_changed
                    )
                    logger.info(
                        "✅ CRITICAL: State manager connected for sequence updates"
                    )

                    # Check current state immediately
                    current_state = self.viewmodel.state_manager.get_current_state()
                    logger.info(
                        f"✅ CRITICAL: Current state has {len(current_state.sequences)} sequences"
                    )
                    if current_state.sequences:
                        logger.info(
                            "✅ CRITICAL: Sequences already available - updating UI immediately"
                        )
                        self._on_state_changed(current_state)
                else:
                    logger.warning(
                        "❌ CRITICAL: State manager has no state_changed signal"
                    )
            else:
                logger.warning("❌ CRITICAL: No state manager found in viewmodel")

            logger.info(
                "✅ CRITICAL: Viewmodel signals connected for loading state management"
            )
        else:
            logger.warning(
                "❌ CRITICAL: No viewmodel available - loading state transitions will not work"
            )

    def _check_immediate_data_availability(self):
        """Check for immediate data availability and trigger content display - CRITICAL FIX."""
        try:
            logger.info("🔍 IMMEDIATE_DATA: Checking for available data to display")

            # Check if viewmodel already has sequences loaded
            if self.viewmodel and hasattr(self.viewmodel, "current_state"):
                current_state = self.viewmodel.current_state
                if hasattr(current_state, "sequences") and current_state.sequences:
                    sequences = current_state.sequences
                    logger.info(
                        f"🔍 IMMEDIATE_DATA: Found {len(sequences)} sequences in viewmodel state"
                    )
                    self._handle_loaded_state(sequences)
                    return

            # Check if viewmodel has sequences directly
            if self.viewmodel and hasattr(self.viewmodel, "sequences"):
                sequences = self.viewmodel.sequences
                if sequences:
                    logger.info(
                        f"🔍 IMMEDIATE_DATA: Found {len(sequences)} sequences in viewmodel"
                    )
                    self._handle_loaded_state(sequences)
                    return

            # Check for preloaded data
            try:
                from .startup.data_preloader import (
                    get_preloaded_data,
                    is_preloading_completed,
                )

                if is_preloading_completed():
                    preloaded_data = get_preloaded_data()
                    if preloaded_data and preloaded_data.get("sequences"):
                        sequences = preloaded_data["sequences"]
                        logger.info(
                            f"🔍 IMMEDIATE_DATA: Found {len(sequences)} preloaded sequences"
                        )
                        self._handle_loaded_state(sequences)
                        return
            except ImportError:
                logger.debug("Preloader not available")

            # Check for instant data
            try:
                from .startup.instant_browse_tab_manager import get_instant_manager

                instant_manager = get_instant_manager()
                if instant_manager and instant_manager.is_ready():
                    sequences = instant_manager.get_sequences()
                    if sequences:
                        logger.info(
                            f"🔍 IMMEDIATE_DATA: Found {len(sequences)} instant sequences"
                        )
                        self._handle_loaded_state(sequences)
                        return
            except ImportError:
                logger.debug("Instant manager not available")

            logger.info(
                "🔍 IMMEDIATE_DATA: No immediate data available - will wait for viewmodel signals"
            )

        except Exception as e:
            logger.error(f"Failed to check immediate data availability: {e}")
            import traceback

            traceback.print_exc()

    def _complete_performance_tracking(self):
        """Complete performance tracking and log results."""
        if self._performance_timer:
            elapsed = self._performance_timer.elapsed()
            logger.info(f"Coordinator initialization completed in {elapsed}ms")

            # Target: <400ms Browse Tab v2 startup
            if elapsed > 400:
                logger.warning(f"Initialization exceeded 400ms target: {elapsed}ms")

    # Event handlers for component coordination
    def _on_filter_changed(self, filter_criteria):
        """Handle filter changes from filter panel."""
        self._current_filter_criteria = filter_criteria
        if self.grid_view and hasattr(self.grid_view, "apply_filters"):
            self.grid_view.apply_filters(filter_criteria)

    def _on_item_clicked(self, sequence_id: str, index: int):
        """Handle item clicks from grid view."""
        if self.sequence_viewer and hasattr(self.sequence_viewer, "display_sequence"):
            sequence = self._find_sequence_by_id(sequence_id)
            if sequence:
                self.sequence_viewer.display_sequence(sequence)
                self.sequence_selected.emit(sequence_id)

    def _on_section_clicked(self, section_id: str):
        """Handle section clicks from navigation sidebar."""
        if self.grid_view and hasattr(self.grid_view, "scroll_to_section"):
            self.grid_view.scroll_to_section(section_id)

    def _on_viewmodel_state_changed(self, state):
        """Handle viewmodel state changes - CRITICAL LOADING STATE MANAGEMENT."""
        try:
            logger.info(
                f"🔄 STATE_CHANGE: Viewmodel state changed: {getattr(state, 'loading_state', 'unknown')}"
            )

            # Check loading state and handle transitions
            if hasattr(state, "loading_state"):
                if hasattr(state.loading_state, "value"):
                    loading_state = state.loading_state.value
                else:
                    loading_state = str(state.loading_state)

                logger.info(f"🔄 STATE_CHANGE: Loading state: {loading_state}")

                # Handle different loading states
                if loading_state == "loading":
                    logger.debug(
                        "🔄 STATE_CHANGE: Maintaining skeleton placeholders during loading"
                    )
                    # Keep skeleton placeholders visible during loading

                elif loading_state == "error":
                    error_msg = getattr(state, "error_message", "Unknown error")
                    logger.error(f"🔄 STATE_CHANGE: Error state: {error_msg}")
                    self._show_error_state(error_msg)

                elif loading_state == "loaded":
                    # CRITICAL: This is where we transition from loading to content
                    sequences = state.filtered_sequences or state.sequences
                    logger.info(
                        f"🔄 STATE_CHANGE: Loaded state with {len(sequences)} sequences"
                    )
                    self._handle_loaded_state(sequences)
                    return  # Early return to avoid duplicate processing

            # Fallback: Handle sequences regardless of loading state
            sequences = state.filtered_sequences or state.sequences
            if sequences:
                logger.info(
                    f"🔄 STATE_CHANGE: Fallback processing {len(sequences)} sequences"
                )
                self._handle_loaded_state(sequences)

        except Exception as e:
            logger.error(f"Failed to handle viewmodel state change: {e}")
            import traceback

            traceback.print_exc()

    def _handle_loaded_state(self, sequences):
        """Handle the loaded state with sequences - CRITICAL CONTENT TRANSITION."""
        try:
            logger.info(f"✅ LOADED_STATE: Processing {len(sequences)} sequences")

            # Store sequences
            self._sequences = sequences

            # Update components with new data
            if self.grid_view and hasattr(self.grid_view, "set_sequences"):
                logger.info(
                    f"✅ LOADED_STATE: Updating grid view with {len(sequences)} sequences"
                )
                self.grid_view.set_sequences(sequences)

            if self.navigation_sidebar and hasattr(
                self.navigation_sidebar, "update_sections"
            ):
                logger.info(
                    f"✅ LOADED_STATE: Updating navigation with {len(sequences)} sequences"
                )
                self.navigation_sidebar.update_sections(
                    sequences, self._current_sort_criteria
                )

            # CRITICAL: Transition from loading to content display
            logger.info(f"✅ LOADED_STATE: Transitioning to content display")
            self._show_content_state(sequences)

        except Exception as e:
            logger.error(f"Failed to handle loaded state: {e}")
            import traceback

            traceback.print_exc()

    def _show_content_state(self, sequences):
        """Transition from loading/skeleton state to content display."""
        try:
            logger.info(
                f"✅ CONTENT_TRANSITION: Showing content with {len(sequences)} sequences"
            )

            # Hide any loading states and show content
            if self.grid_view and hasattr(self.grid_view, "show_content"):
                self.grid_view.show_content()

            if self.filter_panel and hasattr(self.filter_panel, "show_content"):
                self.filter_panel.show_content()

            if self.navigation_sidebar and hasattr(
                self.navigation_sidebar, "show_content"
            ):
                self.navigation_sidebar.show_content()

            # Emit content ready signal
            self.content_ready.emit()
            logger.info(
                "✅ CONTENT_READY: All components transitioned to content display"
            )

        except Exception as e:
            logger.error(f"Failed to transition to content state: {e}")

    def _show_error_state(self, error_message: str):
        """Show error state in components."""
        try:
            logger.error(f"🚨 ERROR_STATE: {error_message}")

            # Show error in grid view
            if self.grid_view and hasattr(self.grid_view, "show_error_state"):
                self.grid_view.show_error_state(error_message)

            # Emit error signal
            self.error_occurred.emit(error_message)

        except Exception as e:
            logger.error(f"Failed to show error state: {e}")

    def show_content(self, sequences=None):
        """Public method to show content (for external calls)."""
        if sequences is None:
            sequences = self._sequences
        self._show_content_state(sequences)

    def _on_loading_started(self, operation: str):
        """Handle loading started signal."""
        logger.debug(f"🔄 LOADING_STARTED: {operation}")
        # Keep skeleton placeholders visible during loading
        # This prevents jarring visual transitions

    def _on_loading_finished(self, operation: str, success: bool):
        """Handle loading finished signal."""
        logger.debug(f"🔄 LOADING_FINISHED: {operation}, success: {success}")

        if not success:
            # Check if we have working data despite the failure
            has_working_data = self._sequences and len(self._sequences) > 0

            if has_working_data:
                logger.debug(
                    f"Loading failed for {operation} but working data is available - ignoring error"
                )
            else:
                # Only show error for critical operations
                if operation not in ["initialization", "async_load_sequences"]:
                    logger.warning(f"Showing error state for operation: {operation}")
                    self._show_error_state(f"Failed to complete {operation}")
                else:
                    logger.info(
                        f"Initialization fallback failed for {operation} - this is expected behavior"
                    )
        else:
            logger.debug(f"Loading completed successfully: {operation}")

    def _on_state_changed(self, state):
        """Handle state changes from the state manager - CRITICAL for sequence display."""
        try:
            logger.info(
                f"✅ STATE_CHANGED: Received state with {len(state.sequences)} sequences"
            )

            # Check if we have sequences to display
            if state.sequences:
                logger.info(
                    f"✅ STATE_CHANGED: Updating UI with {len(state.sequences)} sequences"
                )
                self._handle_loaded_state(state.sequences)
            else:
                logger.warning("STATE_CHANGED: No sequences in state")

        except Exception as e:
            logger.error(f"Failed to handle state change: {e}")
            import traceback

            traceback.print_exc()

    def _on_viewmodel_error(self, operation: str, error_message: str):
        """Handle viewmodel errors."""
        logger.error(f"Viewmodel error - {operation}: {error_message}")

        # Don't show error if we already have working data
        if not self._sequences:
            logger.warning("Error occurred and no working data available")
            self.error_occurred.emit(f"{operation}: {error_message}")
        else:
            logger.debug(
                "Error occurred but working data is available - ignoring error"
            )

    def _find_sequence_by_id(self, sequence_id: str):
        """Find sequence by ID in current sequences."""
        for sequence in self._sequences:
            if hasattr(sequence, "id") and sequence.id == sequence_id:
                return sequence
        return None

    # Public interface methods
    def set_sequences(self, sequences):
        """Set sequences for display."""
        self._sequences = sequences
        if self.grid_view and hasattr(self.grid_view, "set_sequences"):
            self.grid_view.set_sequences(sequences)

    def cleanup(self):
        """Cleanup resources."""
        try:
            # Cleanup components
            for component in [
                self.filter_panel,
                self.grid_view,
                self.sequence_viewer,
                self.navigation_sidebar,
            ]:
                if component and hasattr(component, "cleanup"):
                    component.cleanup()

            logger.info("BrowseTabV2Main cleanup completed")
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
