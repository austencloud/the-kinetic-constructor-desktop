"""
Browse Tab v2 Coordinator - Phase 3 Clean Architecture Implementation.

This coordinator replaces the legacy BrowseTabView (1315 lines) with a clean,
maintainable implementation using the five Phase 3 components.

Architecture:
- 3-panel layout: navigation sidebar (200px), main content (2/3), sequence viewer (1/3)
- Component-based design with single responsibility principle
- Signal/slot communication between components
- Performance optimization with 120fps scrolling, <100ms navigation response
- Glassmorphism styling with 2025 best practices

Components Integrated:
- FilterPanel: Search and filtering UI (<200 lines)
- GridView: Thumbnail grid display (<200 lines)
- SequenceViewer: Sequence detail display (<200 lines)
- NavigationSidebar: Alphabet navigation (<200 lines)
- ThumbnailCard: Individual thumbnail widget (<200 lines)
"""

import logging
from typing import List, Optional, Dict, Any
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSizePolicy, QSplitter
from PyQt6.QtCore import pyqtSignal, QTimer, QElapsedTimer, Qt

from ..core.interfaces import SequenceModel, BrowseTabConfig, FilterCriteria
from .filter_panel import FilterPanel
from .grid_view import GridView
from .sequence_viewer import SequenceViewer
from .navigation_sidebar import NavigationSidebar
from ..services.sequence_data_service import SequenceDataService

logger = logging.getLogger(__name__)


class BrowseTabV2Coordinator(QWidget):
    """
    Main coordinator for Browse Tab v2 using Phase 3 clean architecture components.

    Replaces the legacy BrowseTabView (1315 lines) with a clean, maintainable
    implementation that orchestrates focused components.

    Responsibilities:
    - Component lifecycle management
    - Signal routing and communication
    - Layout management (3-panel design)
    - Performance coordination
    - State management and error handling
    """

    # Public signals for compatibility with existing Browse Tab v2 interface
    sequence_selected = pyqtSignal(str)  # sequence_id
    sequence_loaded = pyqtSignal(str)  # sequence_id
    error_occurred = pyqtSignal(str)  # error_message
    content_ready = pyqtSignal()  # emitted when content is ready
    loading_changed = pyqtSignal(bool)  # is_loading

    def __init__(
        self,
        viewmodel=None,
        config: BrowseTabConfig = None,
        cache_service=None,
        main_widget=None,
        parent=None,
    ):
        super().__init__(parent)

        # Dependencies
        self.viewmodel = viewmodel
        self.config = config or BrowseTabConfig()
        self.cache_service = cache_service
        self.main_widget = main_widget  # NEW: Store main widget reference

        # Data service
        self.sequence_data_service = SequenceDataService(
            config=self.config, parent=self
        )
        self.sequence_data_service.json_manager = (
            getattr(viewmodel, "json_manager", None) if viewmodel else None
        )
        self.sequence_data_service.settings_manager = (
            getattr(viewmodel, "settings_manager", None) if viewmodel else None
        )

        # Component references
        self.filter_panel: Optional[FilterPanel] = None
        self.grid_view: Optional[GridView] = None
        self.sequence_viewer: Optional[SequenceViewer] = None
        self.navigation_sidebar: Optional[NavigationSidebar] = None

        # State management
        self._sequences: List[SequenceModel] = []
        self._filtered_sequences: List[SequenceModel] = []
        self._current_filter_criteria: List[FilterCriteria] = []
        self._current_sort_criteria = "alphabetical"
        self._selected_sequence: Optional[SequenceModel] = None

        # Performance tracking
        self._performance_timer = QElapsedTimer()
        self._initialization_timer = QElapsedTimer()

        # Layout containers
        self.main_splitter: Optional[QSplitter] = None
        self.left_panel: Optional[QWidget] = None
        self.right_panel: Optional[QWidget] = None

        # Initialize coordinator
        self._initialize_coordinator()

        logger.info("BrowseTabV2Coordinator initialized successfully")

    def _initialize_coordinator(self):
        """Initialize the coordinator with all components and connections."""
        try:
            self._initialization_timer.start()

            # Setup layout structure
            self._setup_layout()

            # Create and initialize components
            self._create_components()

            # Connect component signals
            self._connect_signals()

            # Apply styling
            self._apply_styling()

            # Connect to viewmodel if available
            if self.viewmodel:
                self._connect_viewmodel()

            # Connect sequence data service
            self._connect_sequence_data_service()

            # Load sequence data
            self._load_sequence_data()

            elapsed = self._initialization_timer.elapsed()
            logger.info(f"Coordinator initialization completed in {elapsed}ms")

            # Performance target: <400ms startup
            if elapsed > 400:
                logger.warning(f"Initialization exceeded 400ms target: {elapsed}ms")

        except Exception as e:
            logger.error(f"Failed to initialize coordinator: {e}")
            self.error_occurred.emit(f"Initialization failed: {e}")
            raise

    def _setup_layout(self):
        """Setup the 3-panel layout structure."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(0)

        # Create main splitter for responsive layout
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.setChildrenCollapsible(False)

        # Left panel (2/3 width) - Navigation + Content
        self.left_panel = QWidget()
        left_layout = QHBoxLayout(self.left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        # Navigation sidebar container (200px fixed width)
        self.nav_container = QWidget()
        self.nav_container.setFixedWidth(200)
        left_layout.addWidget(self.nav_container)

        # Content area (filters + grid)
        self.content_container = QWidget()
        content_layout = QVBoxLayout(self.content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(8)

        # Filter panel container
        self.filter_container = QWidget()
        self.filter_container.setFixedHeight(120)
        content_layout.addWidget(self.filter_container)

        # Grid view container
        self.grid_container = QWidget()
        content_layout.addWidget(self.grid_container, 1)

        left_layout.addWidget(self.content_container, 1)

        # Right panel (1/3 width) - Sequence viewer
        self.right_panel = QWidget()
        self.viewer_container = self.right_panel

        # Add panels to splitter
        self.main_splitter.addWidget(self.left_panel)
        self.main_splitter.addWidget(self.right_panel)

        # Set initial splitter sizes (2:1 ratio)
        self.main_splitter.setSizes([800, 400])  # 2/3 : 1/3 ratio

        main_layout.addWidget(self.main_splitter)

        logger.debug("3-panel layout structure created")

    def _create_components(self):
        """Create and initialize all Phase 3 components."""
        try:
            # Create FilterPanel with main_widget reference for regenerate functionality
            self.filter_panel = FilterPanel(
                config=self.config,
                main_widget=self.main_widget,
                parent=self.filter_container,
            )
            filter_layout = QVBoxLayout(self.filter_container)
            filter_layout.setContentsMargins(0, 0, 0, 0)
            filter_layout.addWidget(self.filter_panel)

            # Create GridView
            self.grid_view = GridView(config=self.config, parent=self.grid_container)
            grid_layout = QVBoxLayout(self.grid_container)
            grid_layout.setContentsMargins(0, 0, 0, 0)
            grid_layout.addWidget(self.grid_view)

            # Create SequenceViewer
            self.sequence_viewer = SequenceViewer(
                config=self.config, parent=self.viewer_container
            )
            viewer_layout = QVBoxLayout(self.viewer_container)
            viewer_layout.setContentsMargins(0, 0, 0, 0)
            viewer_layout.addWidget(self.sequence_viewer)

            # Create NavigationSidebar
            self.navigation_sidebar = NavigationSidebar(
                config=self.config, parent=self.nav_container
            )
            nav_layout = QVBoxLayout(self.nav_container)
            nav_layout.setContentsMargins(0, 0, 0, 0)
            nav_layout.addWidget(self.navigation_sidebar)

            logger.debug("All Phase 3 components created successfully")

        except Exception as e:
            logger.error(f"Failed to create components: {e}")
            raise

    def _connect_signals(self):
        """Connect signals between components for coordination."""
        try:
            # FilterPanel signals
            if self.filter_panel:
                self.filter_panel.search_changed.connect(self._on_search_changed)
                self.filter_panel.filter_added.connect(self._on_filter_added)
                self.filter_panel.filter_removed.connect(self._on_filter_removed)
                self.filter_panel.sort_changed.connect(self._on_sort_changed)
                self.filter_panel.regenerate_requested.connect(
                    self._on_regenerate_requested
                )  # NEW

            # GridView signals
            if self.grid_view:
                self.grid_view.item_clicked.connect(self._on_item_clicked)
                self.grid_view.item_double_clicked.connect(self._on_item_double_clicked)
                self.grid_view.content_ready.connect(self._on_content_ready)

            # SequenceViewer signals
            if self.sequence_viewer:
                self.sequence_viewer.edit_requested.connect(self._on_edit_requested)
                self.sequence_viewer.save_requested.connect(self._on_save_requested)
                self.sequence_viewer.delete_requested.connect(self._on_delete_requested)

            # NavigationSidebar signals
            if self.navigation_sidebar:
                self.navigation_sidebar.section_clicked.connect(
                    self._on_section_clicked
                )
                self.navigation_sidebar.active_section_changed.connect(
                    self._on_active_section_changed
                )

            logger.debug("Component signals connected successfully")

        except Exception as e:
            logger.error(f"Failed to connect signals: {e}")

    def _apply_styling(self):
        """Apply glassmorphism styling to the coordinator."""
        try:
            self.setStyleSheet(
                """
                BrowseTabV2Coordinator {
                    background: transparent;
                }
                QSplitter::handle {
                    background: rgba(255, 255, 255, 0.1);
                    width: 2px;
                }
                QSplitter::handle:hover {
                    background: rgba(255, 255, 255, 0.2);
                }
            """
            )

            # Apply glassmorphism to panels
            panel_style = """
                QWidget {
                    background: rgba(255, 255, 255, 0.08);
                    border-radius: 15px;
                    border: 1px solid rgba(255, 255, 255, 0.15);
                }
            """

            if self.left_panel:
                self.left_panel.setStyleSheet(panel_style)

            if self.right_panel:
                self.right_panel.setStyleSheet(panel_style)

            logger.debug("Glassmorphism styling applied")

        except Exception as e:
            logger.warning(f"Failed to apply styling: {e}")

    def _connect_viewmodel(self):
        """Connect to viewmodel for data management."""
        if not self.viewmodel:
            return

        try:
            # Connect viewmodel signals
            if hasattr(self.viewmodel, "state_changed"):
                self.viewmodel.state_changed.connect(self._on_viewmodel_state_changed)

            if hasattr(self.viewmodel, "error_occurred"):
                self.viewmodel.error_occurred.connect(self._on_viewmodel_error)

            if hasattr(self.viewmodel, "loading_started"):
                self.viewmodel.loading_started.connect(
                    lambda: self.loading_changed.emit(True)
                )

            if hasattr(self.viewmodel, "loading_finished"):
                self.viewmodel.loading_finished.connect(
                    lambda: self.loading_changed.emit(False)
                )

            logger.debug("Viewmodel signals connected")

        except Exception as e:
            logger.error(f"Failed to connect viewmodel: {e}")

    def _connect_sequence_data_service(self):
        """Connect sequence data service signals."""
        try:
            self.sequence_data_service.sequences_loaded.connect(
                self._on_sequences_loaded
            )
            self.sequence_data_service.loading_progress.connect(
                self._on_loading_progress
            )
            self.sequence_data_service.loading_error.connect(self._on_loading_error)

            logger.debug("Sequence data service signals connected")

        except Exception as e:
            logger.error(f"Failed to connect sequence data service: {e}")

    def _load_sequence_data(self):
        """Load sequence data using the data service."""
        try:
            logger.info("Starting sequence data loading...")
            self.loading_changed.emit(True)
            self.sequence_data_service.load_sequences()

        except Exception as e:
            logger.error(f"Failed to start sequence data loading: {e}")
            self.error_occurred.emit(f"Failed to load sequences: {e}")

    def _check_immediate_data(self):
        """Check for immediate data availability and display."""
        try:
            # Check viewmodel for existing sequences
            if self.viewmodel and hasattr(self.viewmodel, "current_state"):
                current_state = self.viewmodel.current_state
                if hasattr(current_state, "sequences") and current_state.sequences:
                    self._update_sequences(current_state.sequences)
                    return

            # Check for preloaded data
            try:
                from ..startup.data_preloader import (
                    get_preloaded_data,
                    is_preloading_completed,
                )

                if is_preloading_completed():
                    preloaded_data = get_preloaded_data()
                    if preloaded_data and preloaded_data.get("sequences"):
                        self._update_sequences(preloaded_data["sequences"])
                        return
            except ImportError:
                pass

            logger.debug("No immediate data available")

        except Exception as e:
            logger.error(f"Failed to check immediate data: {e}")

    # Signal handlers for component communication
    def _on_search_changed(self, query: str):
        """Handle search query changes from FilterPanel."""
        self._performance_timer.start()

        # Apply search filter
        self._apply_search_filter(query)

        elapsed = self._performance_timer.elapsed()
        logger.debug(f"Search applied in {elapsed}ms: '{query}'")

        # Performance target: <100ms search response
        if elapsed > 100:
            logger.warning(f"Search exceeded 100ms target: {elapsed}ms")

    def _on_filter_added(self, filter_criteria: FilterCriteria):
        """Handle filter addition from FilterPanel."""
        self._current_filter_criteria.append(filter_criteria)
        self._apply_filters()
        logger.debug(f"Filter added: {filter_criteria}")

    def _on_filter_removed(self, filter_criteria: FilterCriteria):
        """Handle filter removal from FilterPanel."""
        if filter_criteria in self._current_filter_criteria:
            self._current_filter_criteria.remove(filter_criteria)
            self._apply_filters()
            logger.debug(f"Filter removed: {filter_criteria}")

    def _on_sort_changed(self, sort_criteria: str):
        """Handle sort criteria changes from FilterPanel."""
        self._current_sort_criteria = sort_criteria
        self._apply_sort()
        logger.debug(f"Sort changed to: {sort_criteria}")

    def _on_item_clicked(self, sequence_id: str, index: int):
        """Handle thumbnail click from GridView."""
        self._performance_timer.start()

        # Find and select sequence
        sequence = self._find_sequence_by_id(sequence_id)
        if sequence:
            self._selected_sequence = sequence

            # Display in sequence viewer
            if self.sequence_viewer:
                self.sequence_viewer.display_sequence(sequence)

            # Update navigation
            if self.navigation_sidebar:
                self._update_active_section_for_sequence(sequence)

            # Emit public signal
            self.sequence_selected.emit(sequence_id)

        elapsed = self._performance_timer.elapsed()
        logger.debug(f"Item clicked in {elapsed}ms: {sequence_id}")

        # Performance target: <100ms click response
        if elapsed > 100:
            logger.warning(f"Click response exceeded 100ms target: {elapsed}ms")

    def _on_item_double_clicked(self, sequence_id: str, index: int):
        """Handle thumbnail double-click from GridView."""
        # Load sequence for editing
        sequence = self._find_sequence_by_id(sequence_id)
        if sequence:
            self.sequence_loaded.emit(sequence_id)
            logger.debug(f"Sequence loaded for editing: {sequence_id}")

    def _on_section_clicked(self, section: str):
        """Handle navigation section click from NavigationSidebar."""
        self._performance_timer.start()

        # Scroll grid to section
        if self.grid_view:
            self.grid_view.scroll_to_section(section)

        elapsed = self._performance_timer.elapsed()
        logger.debug(f"Navigation to section '{section}' in {elapsed}ms")

        # Performance target: <100ms navigation response
        if elapsed > 100:
            logger.warning(f"Navigation exceeded 100ms target: {elapsed}ms")

    def _on_active_section_changed(self, section: str):
        """Handle active section change from NavigationSidebar."""
        logger.debug(f"Active section changed to: {section}")

    def _on_content_ready(self):
        """Handle content ready signal from GridView."""
        logger.info("GridView content ready - all widgets created")

        # Update navigation sections now that content is ready
        if self.navigation_sidebar and self._filtered_sequences:
            self.navigation_sidebar.update_sections(
                self._filtered_sequences, self._current_sort_criteria
            )

        # Emit content ready signal for external handling
        self.content_ready.emit()

    def _on_edit_requested(self, sequence_id: str):
        """Handle edit request from SequenceViewer."""
        self.sequence_loaded.emit(sequence_id)
        logger.debug(f"Edit requested for sequence: {sequence_id}")

    def _on_save_requested(self, sequence_id: str):
        """Handle save request from SequenceViewer."""
        # TODO: Implement save functionality
        logger.debug(f"Save requested for sequence: {sequence_id}")

    def _on_delete_requested(self, sequence_id: str):
        """Handle delete request from SequenceViewer."""
        # TODO: Implement delete functionality
        logger.debug(f"Delete requested for sequence: {sequence_id}")

    def _on_viewmodel_state_changed(self, state):
        """Handle viewmodel state changes."""
        if hasattr(state, "sequences"):
            self._update_sequences(state.sequences)

    def _on_viewmodel_error(self, error_message: str):
        """Handle viewmodel errors."""
        self.error_occurred.emit(error_message)
        logger.error(f"Viewmodel error: {error_message}")

    def _on_sequences_loaded(self, sequences: List[SequenceModel]):
        """Handle sequences loaded from data service."""
        logger.info(f"Sequences loaded from data service: {len(sequences)}")
        self.loading_changed.emit(False)
        self._update_sequences(sequences)

    def _on_loading_progress(self, current: int, total: int):
        """Handle loading progress from data service."""
        logger.debug(f"Loading progress: {current}/{total}")
        # Could emit progress signal if needed

    def _on_loading_error(self, error_message: str):
        """Handle loading error from data service."""
        logger.error(f"Data service loading error: {error_message}")
        self.loading_changed.emit(False)
        self.error_occurred.emit(error_message)

    # Data management methods
    def _update_sequences(self, sequences: List[SequenceModel]):
        """Update sequences and refresh all components."""
        try:
            self._sequences = sequences
            logger.info(f"Updated sequences: {len(sequences)} total")

            # Apply current filters and sort
            self._apply_filters()

            # Update navigation sections
            if self.navigation_sidebar:
                self.navigation_sidebar.update_sections(
                    self._filtered_sequences, self._current_sort_criteria
                )

            # Emit content ready signal
            self.content_ready.emit()

        except Exception as e:
            logger.error(f"Failed to update sequences: {e}")
            self.error_occurred.emit(f"Failed to update sequences: {e}")

    def _apply_search_filter(self, query: str):
        """Apply search filter to sequences."""
        if not query.strip():
            self._filtered_sequences = self._sequences.copy()
        else:
            self._filtered_sequences = [
                seq for seq in self._sequences if query.lower() in seq.name.lower()
            ]

        self._update_grid_view()

    def _apply_filters(self):
        """Apply all current filters to sequences."""
        self._filtered_sequences = self._sequences.copy()

        # Apply each filter criteria
        for criteria in self._current_filter_criteria:
            self._filtered_sequences = self._filter_sequences(
                self._filtered_sequences, criteria
            )

        # Apply sort
        self._apply_sort()

    def _filter_sequences(
        self, sequences: List[SequenceModel], criteria: FilterCriteria
    ) -> List[SequenceModel]:
        """Filter sequences based on criteria."""
        # TODO: Implement specific filter logic based on criteria type
        return sequences

    def _apply_sort(self):
        """Apply current sort criteria to filtered sequences."""
        if self._current_sort_criteria == "alphabetical":
            self._filtered_sequences.sort(key=lambda seq: seq.name.lower())
        elif self._current_sort_criteria == "difficulty":
            self._filtered_sequences.sort(key=lambda seq: getattr(seq, "difficulty", 0))
        elif self._current_sort_criteria == "length":
            self._filtered_sequences.sort(key=lambda seq: getattr(seq, "length", 0))

        self._update_grid_view()

    def _update_grid_view(self):
        """Update grid view with filtered and sorted sequences."""
        if self.grid_view:
            self.grid_view.set_sequences(self._filtered_sequences)

    # Utility methods
    def _find_sequence_by_id(self, sequence_id: str) -> Optional[SequenceModel]:
        """Find sequence by ID."""
        for sequence in self._sequences:
            if sequence.id == sequence_id:
                return sequence
        return None

    def _get_sequence_at_index(self, index: int) -> Optional[SequenceModel]:
        """Get sequence at specific index."""
        if 0 <= index < len(self._filtered_sequences):
            return self._filtered_sequences[index]
        return None

    def _get_section_for_sequence(self, sequence: SequenceModel) -> Optional[str]:
        """Get navigation section for a sequence."""
        if sequence.name:
            return sequence.name[0].upper()
        return None

    def _update_active_section_for_sequence(self, sequence: SequenceModel):
        """Update active navigation section for a sequence."""
        section = self._get_section_for_sequence(sequence)
        if section and self.navigation_sidebar:
            self.navigation_sidebar.set_active_section(section)

    # Public interface methods for compatibility with legacy BrowseTabView
    def load_sequences(self, sequences: List[SequenceModel] = None):
        """Load sequences into the coordinator."""
        if sequences is not None:
            self._update_sequences(sequences)
        elif self.viewmodel:
            # Trigger viewmodel to load sequences
            if hasattr(self.viewmodel, "load_sequences"):
                self.viewmodel.load_sequences()

    def apply_filter(self, filter_type: str, filter_value: Any):
        """Apply a filter to the sequences."""
        from ..core.interfaces import FilterType, FilterCriteria

        try:
            # Convert string to FilterType enum if needed
            if isinstance(filter_type, str):
                filter_type_enum = FilterType(filter_type)
            else:
                filter_type_enum = filter_type

            # Create filter criteria
            criteria = FilterCriteria(
                filter_type=filter_type_enum, value=filter_value, operator="equals"
            )

            # Add filter
            self._on_filter_added(criteria)

        except Exception as e:
            logger.error(f"Failed to apply filter: {e}")

    def clear_filters(self):
        """Clear all filters."""
        self._current_filter_criteria.clear()
        self._apply_filters()

    def set_sort_criteria(self, sort_criteria: str):
        """Set sort criteria."""
        self._on_sort_changed(sort_criteria)

    def get_selected_sequence(self) -> Optional[SequenceModel]:
        """Get the currently selected sequence."""
        return self._selected_sequence

    def get_sequences(self) -> List[SequenceModel]:
        """Get all sequences."""
        return self._sequences.copy()

    def get_filtered_sequences(self) -> List[SequenceModel]:
        """Get filtered sequences."""
        return self._filtered_sequences.copy()

    def refresh(self):
        """Refresh the coordinator and all components."""
        try:
            # Refresh components
            if self.grid_view:
                self.grid_view.refresh()

            if self.sequence_viewer:
                self.sequence_viewer.refresh()

            if self.navigation_sidebar:
                self.navigation_sidebar.update_sections(
                    self._filtered_sequences, self._current_sort_criteria
                )

            logger.debug("Coordinator refreshed")

        except Exception as e:
            logger.error(f"Failed to refresh coordinator: {e}")

    def cleanup(self):
        """Cleanup resources."""
        try:
            # Cleanup components
            if self.filter_panel and hasattr(self.filter_panel, "cleanup"):
                self.filter_panel.cleanup()

            if self.grid_view and hasattr(self.grid_view, "cleanup"):
                self.grid_view.cleanup()

            if self.sequence_viewer and hasattr(self.sequence_viewer, "cleanup"):
                self.sequence_viewer.cleanup()

            if self.navigation_sidebar and hasattr(self.navigation_sidebar, "cleanup"):
                self.navigation_sidebar.cleanup()

            # Cleanup sequence data service
            if self.sequence_data_service and hasattr(
                self.sequence_data_service, "cleanup"
            ):
                self.sequence_data_service.cleanup()

            logger.debug("Coordinator cleanup completed")

        except Exception as e:
            logger.error(f"Coordinator cleanup failed: {e}")

    # Performance monitoring methods
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        stats = {
            "total_sequences": len(self._sequences),
            "filtered_sequences": len(self._filtered_sequences),
            "current_sort": self._current_sort_criteria,
            "active_filters": len(self._current_filter_criteria),
            "selected_sequence": (
                self._selected_sequence.id if self._selected_sequence else None
            ),
        }

        # Add component-specific stats if available
        if self.grid_view and hasattr(self.grid_view, "get_performance_stats"):
            stats["grid_view"] = self.grid_view.get_performance_stats()

        return stats

    def _on_regenerate_requested(self):
        """Handle regenerate dictionary images request from FilterPanel."""
        try:
            logger.info("🔄 Regenerate dictionary images requested from FilterPanel")

            # The FilterPanel already handles the regeneration directly
            # This signal handler is available for additional coordinator-level actions
            # such as refreshing the grid after regeneration completes

            # Could emit a signal or trigger grid refresh after regeneration
            # For now, just log the event
            logger.info("✅ Regenerate request handled by coordinator")

        except Exception as e:
            logger.error(f"Error handling regenerate request: {e}")
            self.error_occurred.emit(f"Regenerate request failed: {e}")
