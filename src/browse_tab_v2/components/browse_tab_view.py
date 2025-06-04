"""
Main view component for browse tab v2 - Refactored Modular Architecture.

This is the primary coordinator component that composes focused, modular components
following modern software architecture principles. Each component has a single
responsibility and communicates through well-defined interfaces.

Architecture:
- FilterPanelComponent: Search and filtering functionality
- GridViewComponent: Thumbnail grid display and viewport management
- SequenceViewerComponent: Sequence viewer integration
- NavigationComponent: Navigation sidebar coordination
- ImageManagerComponent: Image loading and caching coordination
- PerformanceManagerComponent: Performance tracking and optimization
"""

import logging
from typing import Optional, TYPE_CHECKING
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QApplication
from PyQt6.QtCore import QTimer

# Use TYPE_CHECKING to avoid circular imports
if TYPE_CHECKING:
    from ..viewmodels.browse_tab_viewmodel import BrowseTabViewModel
    from ..core.interfaces import BrowseTabConfig, FilterCriteria, SortOrder
    from ..core.state import SequenceModel

# Runtime imports for essential classes
from ..core.interfaces import (
    SequenceModel,
    FilterCriteria,
    SortOrder,
    SearchCriteria,
    BrowseTabConfig,
)

from ..debug.window_resize_tracker import (
    set_phase,
    track_component,
    log_main_window_change,
)

# Import modular components
from .filter_panel_component import FilterPanelComponent
from .grid_view_component import GridViewComponent
from .sequence_viewer_component import SequenceViewerComponent
from .navigation_component import NavigationComponent
from .image_manager_component import ImageManagerComponent
from .performance_manager_component import PerformanceManagerComponent

logger = logging.getLogger(__name__)


class BrowseTabView(QWidget):
    """
    Main coordinator component for browse tab v2 - Refactored Modular Architecture.

    This component coordinates focused, modular components following modern software
    architecture principles. Each component has a single responsibility and
    communicates through well-defined interfaces.
    """

    def __init__(self, viewmodel, config, cache_service=None):
        super().__init__()

        self.viewmodel = viewmodel
        self.config = config

        # Extract cache service from viewmodel if not provided directly
        self.cache_service = cache_service or getattr(viewmodel, "cache_service", None)

        # Log cache service availability for debugging
        if self.cache_service:
            logger.info("🚀 CACHE_SERVICE: Available for instant thumbnail display")
        else:
            logger.warning(
                "⚠️ CACHE_SERVICE: Not available - thumbnails will use fallback loading"
            )

        # Initialize sequences list to prevent AttributeError
        self._sequences = []

        # Resize tracking
        self._last_size = (0, 0)

        # Modular components
        self.filter_panel_component: Optional[FilterPanelComponent] = None
        self.grid_view_component: Optional[GridViewComponent] = None
        self.sequence_viewer_component: Optional[SequenceViewerComponent] = None
        self.navigation_component: Optional[NavigationComponent] = None
        self.image_manager_component: Optional[ImageManagerComponent] = None
        self.performance_manager_component: Optional[PerformanceManagerComponent] = None

        # Legacy UI components (for compatibility during transition)
        self.left_panel = None
        self.content_area = None
        self.animation_manager = None

        set_phase("BrowseTabView_Creation")
        track_component("BrowseTabView_Initial", self, "Constructor start")
        log_main_window_change("BrowseTabView constructor start")

        self._setup_ui()

        # CRITICAL: Initialize with instant browse tab manager for zero loading delays
        self._initialize_instant_browse_tab()

        # Connect to viewmodel only if instant initialization failed
        if self.viewmodel and not self._sequences:
            self._connect_viewmodel()

        track_component("BrowseTabView_Complete", self, "Constructor complete")
        log_main_window_change("BrowseTabView constructor complete")
        logger.info("BrowseTabView initialized with modular architecture")

    def _load_preloaded_data(self):
        """Load pre-loaded data if available for immediate display using modular components."""
        try:
            from ..startup.data_preloader import (
                get_preloaded_data,
                is_preloading_completed,
            )

            # Check if pre-loading was completed during startup
            if not is_preloading_completed():
                logger.debug("Pre-loading not completed, will use skeleton state")
                return False

            preloaded_data = get_preloaded_data()
            if preloaded_data:
                sequences = preloaded_data.get("sequences", [])

                if sequences:
                    logger.info(
                        f"🚀 BrowseTabView loading {len(sequences)} pre-loaded sequences for instant display"
                    )

                    # Set sequences immediately
                    self._sequences = sequences

                    # CRITICAL: Update all components immediately with pre-loaded data
                    # This ensures instant display without progressive loading

                    # Update grid view component with pre-loaded data
                    if self.grid_view_component:
                        print(
                            f"📋 INSTANT_LOAD: Setting {len(sequences)} sequences in grid view"
                        )
                        self.grid_view_component.set_sequences(sequences)
                        # Force immediate content display (no skeleton state)
                        self.grid_view_component.show_content()

                    # Update navigation component with pre-loaded data
                    if self.navigation_component:
                        print(
                            f"🧭 INSTANT_LOAD: Setting {len(sequences)} sequences in navigation"
                        )
                        self.navigation_component.update_for_sequences(
                            sequences, "alphabetical"
                        )

                    # Preload images using image manager for instant thumbnails
                    if self.image_manager_component:
                        print(
                            f"🖼️ INSTANT_LOAD: Preloading images for {len(sequences)} sequences"
                        )
                        self.image_manager_component.preload_sequence_images(sequences)

                    logger.info(
                        f"✅ BrowseTabView instant initialization completed with {len(sequences)} sequences"
                    )
                    return True

            logger.debug("No pre-loaded data available for BrowseTabView")
            return False

        except Exception as e:
            logger.warning(f"Failed to load pre-loaded data for BrowseTabView: {e}")
            return False

    def _connect_viewmodel(self):
        """Connect view to viewmodel signals and initialize data loading."""
        if not self.viewmodel:
            return

        # Connect signals - but only if we don't have pre-loaded data
        # This prevents false positive "Failed to complete initialization" errors
        if not self._sequences:
            self.viewmodel.state_changed.connect(self._on_viewmodel_state_changed)
            self.viewmodel.loading_started.connect(self._on_loading_started)
            self.viewmodel.loading_finished.connect(self._on_loading_finished)
            self.viewmodel.error_occurred.connect(self._on_error_occurred)
            logger.debug("Connected to viewmodel signals for async fallback")
        else:
            logger.debug(
                "Skipping viewmodel signal connections - using pre-loaded data"
            )

    def _load_initial_data(self):
        """Load initial sequence data with instant content display (no skeleton loaders)."""
        try:
            logger.info("🚀 INSTANT_DISPLAY: Starting instant content loading")

            # Try instant initialization first (highest priority)
            if self._initialize_instant_browse_tab():
                logger.info(
                    "✅ INSTANT_DISPLAY: Instant initialization successful - content displayed immediately"
                )
                return

            # Try synchronous initialization with pre-loaded data
            if self.viewmodel.initialize_sync():
                logger.info(
                    "✅ INSTANT_DISPLAY: Sync initialization successful - displaying content"
                )
                # Data is already available, trigger content display immediately
                QTimer.singleShot(10, self._update_content_from_preloaded_data)
                return

            # Last resort: async fallback but still try to avoid skeleton loaders
            logger.info(
                "⚠️ INSTANT_DISPLAY: Using async fallback - attempting to minimize skeleton display"
            )

            # Try to get any available sequences immediately to avoid empty skeleton state
            sequences = self._get_any_available_sequences()
            if sequences:
                logger.info(
                    f"✅ INSTANT_DISPLAY: Found {len(sequences)} sequences for immediate display"
                )
                self._sequences = sequences

                # Pre-warm widget creation to reduce first-time creation overhead
                self._prewarm_widget_creation()

                self.show_content(sequences)
                # Continue with async loading in background for complete data
                QTimer.singleShot(100, self._trigger_async_fallback)
            else:
                logger.warning(
                    "⚠️ INSTANT_DISPLAY: No sequences available - showing minimal skeleton state"
                )
                # Only show skeleton as absolute last resort
                self.show_skeleton_state()
                QTimer.singleShot(100, self._trigger_async_fallback)

        except Exception as e:
            logger.error(f"Failed to load initial data: {e}")
            self.show_error_state(f"Failed to initialize: {e}")

    def _get_any_available_sequences(self) -> list:
        """Get any available sequences from any source for immediate display."""
        try:
            # Try instant manager first
            from ..startup.instant_browse_tab_manager import get_instant_manager

            instant_manager = get_instant_manager()
            if instant_manager and instant_manager.is_ready():
                sequences = instant_manager.get_sequences()
                if sequences:
                    logger.info(
                        f"🚀 INSTANT_SEQUENCES: Got {len(sequences)} from instant manager"
                    )
                    return sequences

            # Try data preloader
            from ..startup.data_preloader import (
                get_preloaded_data,
                is_preloading_completed,
            )

            if is_preloading_completed():
                preloaded_data = get_preloaded_data()
                if preloaded_data and preloaded_data.get("sequences"):
                    sequences = preloaded_data["sequences"]
                    logger.info(
                        f"🚀 INSTANT_SEQUENCES: Got {len(sequences)} from data preloader"
                    )
                    return sequences

            # Try viewmodel sync loading
            sequences = self.viewmodel._load_sequences_sync()
            if sequences:
                logger.info(
                    f"🚀 INSTANT_SEQUENCES: Got {len(sequences)} from viewmodel sync"
                )
                return sequences

            logger.warning(
                "🚀 INSTANT_SEQUENCES: No sequences available from any source"
            )
            return []

        except Exception as e:
            logger.error(f"Failed to get available sequences: {e}")
            return []

    def _update_content_from_preloaded_data(self):
        """Update content display using pre-loaded data."""
        try:
            # Get current state with pre-loaded sequences
            if self.viewmodel:
                current_state = self.viewmodel.current_state
                sequences = current_state.sequences

                if sequences:
                    self._sequences = sequences
                    logger.info(
                        f"BrowseTabView updated with {len(sequences)} pre-loaded sequences"
                    )

                    # Update components with pre-loaded data
                    if hasattr(self, "thumbnail_grid"):
                        self.thumbnail_grid.set_sequences(sequences)

                    if hasattr(self, "navigation_sidebar"):
                        self.navigation_sidebar.update_for_sequences(
                            sequences, "alphabetical"
                        )

                    # Show content immediately
                    self.show_content(sequences)
                else:
                    logger.warning("No sequences in pre-loaded data")
                    self.show_error_state("No sequences available")

        except Exception as e:
            logger.error(f"Failed to update content from pre-loaded data: {e}")
            self.show_error_state(f"Failed to display content: {e}")

    def _trigger_async_fallback(self):
        """Trigger async fallback using QTimer-based approach."""
        try:
            if self.viewmodel:
                self.viewmodel.initialize_async_fallback()
        except Exception as e:
            logger.error(f"Failed to trigger async fallback: {e}")
            self.show_error_state(f"Failed to load data: {e}")

    def _setup_ui(self):
        """Setup the main view UI with modular components."""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(10)

        # Initialize modular components
        self._setup_modular_components()

        # Left panel (2/3 width) - Navigation + Content area
        self.left_panel = QWidget()
        self.left_panel.setStyleSheet(
            """
            QWidget {
                background: transparent !important;
                border: none !important;
            }
        """
        )

        left_layout = QHBoxLayout(self.left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        # Add navigation component
        if self.navigation_component:
            left_layout.addWidget(self.navigation_component, 0)  # Fixed width

        # Create content area (filters + grid)
        self.content_area = QWidget()
        content_layout = QVBoxLayout(self.content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Add filter panel component
        if self.filter_panel_component:
            content_layout.addWidget(self.filter_panel_component, 0)  # Fixed height

        # Add grid view component
        if self.grid_view_component:
            content_layout.addWidget(self.grid_view_component, 1)  # Expandable

        left_layout.addWidget(self.content_area, 1)  # Expandable content area

        # Add panels to main layout with proper stretch factors
        main_layout.addWidget(self.left_panel, 2)  # 2/3 width for grid
        # Sequence viewer component can be added here if needed (1/3 width)

        # Setup responsive sizing
        self._setup_responsive_sizing()

        # Connect component signals
        self._connect_component_signals()

        # Setup animation manager and coordinate with components
        self._setup_animation_coordination()

        # Setup grid view item creator
        self._setup_grid_item_creator()

    def _setup_grid_item_creator(self):
        """Setup the item creator for the grid view component."""
        if self.grid_view_component:
            self.grid_view_component.set_item_creator(self._create_fast_thumbnail_card)
            print("🚀 BROWSE_TAB_VIEW: Grid item creator set")

    def _create_fast_thumbnail_card(
        self, sequence: SequenceModel, index: int
    ) -> QWidget:
        """Create an instant thumbnail card optimized for immediate display (no progressive loading)."""
        from .instant_thumbnail_card import InstantThumbnailCard

        # Create instant card with cache service integration for immediate display
        card = InstantThumbnailCard(
            sequence,
            cache_service=self.cache_service,
        )

        # Connect card events for interaction
        card.clicked.connect(lambda: self._on_thumbnail_clicked(sequence.id, index))
        card.double_clicked.connect(
            lambda: self._on_thumbnail_double_clicked(sequence.id, index)
        )

        logger.debug(f"🚀 INSTANT_CARD_FACTORY: Created instant card for {sequence.id}")
        return card

    def _on_thumbnail_clicked(self, sequence_id: str, index: int):
        """Handle thumbnail click events."""
        try:
            logger.debug(
                f"🚀 INSTANT_CARD: Thumbnail clicked for sequence {sequence_id} at index {index}"
            )

            # Find the sequence by ID
            sequence = None
            for seq in self._sequences:
                if seq.id == sequence_id:
                    sequence = seq
                    break

            if sequence:
                # Update sequence viewer with clicked sequence
                if self.sequence_viewer_component:
                    self.sequence_viewer_component.display_sequence(sequence)
                    logger.debug(
                        f"🚀 INSTANT_CARD: Sequence viewer updated with {sequence_id}"
                    )
                else:
                    logger.warning(
                        f"🚀 INSTANT_CARD: No sequence viewer component available"
                    )
            else:
                logger.warning(f"🚀 INSTANT_CARD: Sequence {sequence_id} not found")

        except Exception as e:
            logger.error(f"Failed to handle thumbnail click: {e}")

    def _on_thumbnail_double_clicked(self, sequence_id: str, index: int):
        """Handle thumbnail double-click events."""
        try:
            logger.debug(
                f"🚀 INSTANT_CARD: Thumbnail double-clicked for sequence {sequence_id} at index {index}"
            )

            # Find the sequence by ID
            sequence = None
            for seq in self._sequences:
                if seq.id == sequence_id:
                    sequence = seq
                    break

            if sequence:
                # Could trigger additional actions like opening in editor, etc.
                logger.debug(f"🚀 INSTANT_CARD: Double-click action for {sequence_id}")

                # For now, just update sequence viewer (same as single click)
                if self.sequence_viewer_component:
                    self.sequence_viewer_component.display_sequence(sequence)
            else:
                logger.warning(
                    f"🚀 INSTANT_CARD: Sequence {sequence_id} not found for double-click"
                )

        except Exception as e:
            logger.error(f"Failed to handle thumbnail double-click: {e}")

    def _setup_modular_components(self):
        """Initialize all modular components."""
        track_component(
            "BrowseTabView_BeforeComponents", self, "Before creating modular components"
        )
        log_main_window_change("Before creating modular components - CRITICAL POINT")

        # Create performance manager first (for tracking other components)
        self.performance_manager_component = PerformanceManagerComponent(
            self.config, self
        )

        # Create image manager
        self.image_manager_component = ImageManagerComponent(self.config, self)

        # Create filter panel component
        self.filter_panel_component = FilterPanelComponent(self.config, self)

        # Create grid view component
        self.grid_view_component = GridViewComponent(self.config, self)

        # Create navigation component
        self.navigation_component = NavigationComponent(self.config, self)

        # Create sequence viewer component
        self.sequence_viewer_component = SequenceViewerComponent(self.config, self)

        track_component(
            "BrowseTabView_AfterComponents", self, "After creating modular components"
        )
        log_main_window_change("After creating modular components - CRITICAL POINT")
        logger.info("All modular components initialized successfully")

    def _setup_responsive_sizing(self):
        """Setup responsive sizing for the main view."""
        from PyQt6.QtWidgets import QSizePolicy

        # Responsive widget sizing
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,  # Allow horizontal expansion
            QSizePolicy.Policy.Preferred,  # Prefer natural height, don't force expansion
        )

        track_component(
            "BrowseTabView_SizeIsolation", self, "Complete size isolation applied"
        )
        log_main_window_change("After BrowseTabView size isolation applied")

    def _connect_component_signals(self):
        """Connect signals between modular components."""
        # Connect filter panel signals
        if self.filter_panel_component:
            self.filter_panel_component.search_changed.connect(self._on_search_changed)
            self.filter_panel_component.filter_added.connect(self._on_filter_added)
            self.filter_panel_component.filter_removed.connect(self._on_filter_removed)
            self.filter_panel_component.filters_cleared.connect(
                self._on_filters_cleared
            )
            self.filter_panel_component.sort_changed.connect(self._on_sort_changed)

        # Connect grid view signals
        if self.grid_view_component:
            self.grid_view_component.item_clicked.connect(self._on_item_clicked)
            self.grid_view_component.item_double_clicked.connect(
                self._on_item_double_clicked
            )
            self.grid_view_component.viewport_changed.connect(self._on_viewport_changed)

        # Connect navigation signals
        if self.navigation_component:
            self.navigation_component.section_clicked.connect(self._on_section_clicked)

        # Connect sequence viewer signals
        if self.sequence_viewer_component:
            self.sequence_viewer_component.edit_requested.connect(
                self._on_sequence_edit_requested
            )
            self.sequence_viewer_component.save_requested.connect(
                self._on_sequence_save_requested
            )
            self.sequence_viewer_component.delete_requested.connect(
                self._on_sequence_delete_requested
            )

        # Connect image manager signals
        if self.image_manager_component:
            self.image_manager_component.image_ready.connect(self._on_image_ready)

        logger.debug("Component signals connected successfully")

    def _setup_animation_coordination(self):
        """Setup animation manager and coordinate with components."""
        from .animation_system import AnimationManager, AnimationConfig

        # Create animation manager
        animation_config = AnimationConfig()
        animation_config.enable_animations = self.config.enable_animations
        self.animation_manager = AnimationManager(animation_config)

        # Set animation manager for components that need it
        if self.filter_panel_component:
            self.filter_panel_component.set_animation_manager(self.animation_manager)

        if self.grid_view_component:
            self.grid_view_component.set_animation_manager(self.animation_manager)

        # Setup smooth scroll navigation
        if self.navigation_component and self.grid_view_component:
            # Get scroll area from grid component
            scroll_area = getattr(
                self.grid_view_component.thumbnail_grid, "scroll_area", None
            )
            if scroll_area:
                self.navigation_component.setup_smooth_scroll(
                    scroll_area, self.animation_manager
                )

        logger.debug("Animation coordination setup completed")

    def _initialize_instant_browse_tab(self):
        """Initialize browse tab instantly using the instant manager for zero loading delays."""
        try:
            from ..startup.instant_browse_tab_manager import (
                get_instant_manager,
                initialize_instant_browse_tab,
            )

            print(
                "🚀 INSTANT_INITIALIZATION: Starting instant browse tab initialization"
            )
            logger.info("Starting instant browse tab initialization")

            # Initialize instant manager
            instant_success = initialize_instant_browse_tab()

            if instant_success:
                instant_manager = get_instant_manager()

                # Get instantly available data
                sequences = instant_manager.sequences
                if sequences:
                    print(
                        f"⚡ INSTANT_INITIALIZATION: Got {len(sequences)} sequences instantly"
                    )
                    logger.info(
                        f"Instant initialization successful with {len(sequences)} sequences"
                    )

                    # Set sequences immediately for all components
                    self._sequences = sequences

                    # Update all components instantly
                    if self.grid_view_component:
                        print(
                            "⚡ INSTANT_INITIALIZATION: Setting sequences in grid view"
                        )
                        self.grid_view_component.set_sequences(sequences)
                        self.grid_view_component.show_content()

                    if self.navigation_component:
                        print(
                            "⚡ INSTANT_INITIALIZATION: Setting sequences in navigation"
                        )
                        self.navigation_component.update_for_sequences(
                            sequences, "alphabetical"
                        )

                    if self.image_manager_component:
                        print("⚡ INSTANT_INITIALIZATION: Pre-loading images")
                        self.image_manager_component.preload_sequence_images(sequences)

                    print("✅ INSTANT_INITIALIZATION: All components updated instantly")
                    logger.info(
                        "✅ Instant browse tab initialization completed successfully"
                    )

                    # CRITICAL: Immediately show content to bypass skeleton loaders
                    self.show_content(sequences)
                    logger.info(
                        "🚀 INSTANT_DISPLAY: Content displayed immediately - no skeleton loaders"
                    )

                    return True
                else:
                    print(
                        "⚠️ INSTANT_INITIALIZATION: No sequences available from instant manager"
                    )
                    logger.warning(
                        "Instant manager initialized but no sequences available"
                    )
            else:
                print(
                    "⚠️ INSTANT_INITIALIZATION: Instant initialization failed, falling back to preloader"
                )
                logger.warning(
                    "Instant initialization failed, falling back to data preloader"
                )

                # Fallback to data preloader
                return self._load_preloaded_data()

        except Exception as e:
            print(
                f"❌ INSTANT_INITIALIZATION: Error during instant initialization: {e}"
            )
            logger.error(f"Error during instant initialization: {e}")

            # Fallback to data preloader
            return self._load_preloaded_data()

        return False

    def _prewarm_widget_creation(self):
        """Pre-warm widget creation to reduce first-time creation overhead."""
        try:
            if not self._sequences:
                return

            # Create a few dummy widgets to warm up Qt's widget creation system
            from .instant_thumbnail_card import InstantThumbnailCard
            from PyQt6.QtWidgets import QApplication

            dummy_widgets = []
            for i in range(min(3, len(self._sequences))):
                sequence = self._sequences[i]
                dummy_widget = InstantThumbnailCard(
                    sequence,
                    cache_service=self.cache_service,
                )
                dummy_widget.setVisible(False)  # Keep hidden
                dummy_widgets.append(dummy_widget)

            # Process events to complete initialization
            QApplication.processEvents()

            # Clean up dummy widgets
            for widget in dummy_widgets:
                widget.deleteLater()

            logger.debug("🚀 INSTANT_DISPLAY: Widget creation pre-warmed")

        except Exception as e:
            logger.debug(f"Widget pre-warming failed: {e}")  # Non-critical failure

    # Size hint methods for responsive layout
    def sizeHint(self):
        """Provide proportional size hint based on parent container dimensions."""
        from PyQt6.QtCore import QSize

        parent_widget = self.parent()
        if parent_widget and hasattr(parent_widget, "size"):
            parent_size = parent_widget.size()
            width = parent_size.width()
            filter_height = 120
            content_height = max(600, parent_size.height() - filter_height)
            total_height = filter_height + content_height
            return QSize(width, total_height)
        else:
            return QSize(2304, 1126)

    def minimumSizeHint(self):
        """Provide minimum size hint to prevent unwanted layout expansion."""
        from PyQt6.QtCore import QSize

        return QSize(800, 720)

    def hasHeightForWidth(self):
        """Disable height-for-width layout calculations to prevent size propagation."""
        return False

    def _on_viewport_changed(self, start_index: int, end_index: int):
        """Handle viewport changes from grid view component for efficient loading."""
        print(f"📡 ON_VIEWPORT_CHANGED: Received signal {start_index}-{end_index}")
        logger.debug(f"ON_VIEWPORT_CHANGED: Received signal {start_index}-{end_index}")

        # Get visible sequences
        visible_sequences = (
            self._sequences[start_index:end_index] if self._sequences else []
        )

        print(
            f"📡 ON_VIEWPORT_CHANGED: Found {len(visible_sequences)} visible sequences"
        )
        logger.debug(
            f"ON_VIEWPORT_CHANGED: Found {len(visible_sequences)} visible sequences"
        )

        # Trigger staggered entrance animations through animation manager
        if self.animation_manager and self.grid_view_component:
            thumbnail_grid = self.grid_view_component.thumbnail_grid
            if thumbnail_grid and hasattr(thumbnail_grid, "_all_widgets"):
                newly_visible_widgets = []
                for i in range(
                    start_index, min(end_index, len(thumbnail_grid._all_widgets))
                ):
                    if i in thumbnail_grid._all_widgets:
                        widget = thumbnail_grid._all_widgets[i]
                        if hasattr(widget, "trigger_entrance_animation"):
                            newly_visible_widgets.append(widget)

                # Create staggered entrance animation for newly visible cards
                if newly_visible_widgets:
                    print(
                        f"🎬 VIEWPORT_ANIMATION: Triggering staggered entrance for {len(newly_visible_widgets)} cards"
                    )
                    stagger_id = (
                        self.animation_manager.create_staggered_entrance_animation(
                            newly_visible_widgets,
                            delay_between=30,  # 30ms delay between cards
                        )
                    )
                    self.animation_manager.start_animation_group(stagger_id)

        # Queue visible images for high-priority loading through image manager
        visible_paths = []
        for sequence in visible_sequences:
            if hasattr(sequence, "thumbnails") and sequence.thumbnails:
                visible_paths.append(sequence.thumbnails[0])

        logger.debug(f"ON_VIEWPORT_CHANGED: Collected {len(visible_paths)} image paths")

        if visible_paths and self.image_manager_component:
            print(
                f"📡 ON_VIEWPORT_CHANGED: Queueing {len(visible_paths)} images for preload"
            )
            logger.debug(
                f"ON_VIEWPORT_CHANGED: Queueing {len(visible_paths)} images for preload"
            )
            self.image_manager_component.preload_visible_images(visible_paths)

            # Force immediate update of visible cards through image manager
            if self.grid_view_component and hasattr(
                self.grid_view_component.thumbnail_grid, "_all_widgets"
            ):
                print(
                    "📡 ON_VIEWPORT_CHANGED: Calling force_visible_card_image_update()"
                )
                logger.debug(
                    "ON_VIEWPORT_CHANGED: Calling force_visible_card_image_update()"
                )
                self.image_manager_component.force_visible_card_image_update(
                    self.grid_view_component.thumbnail_grid._all_widgets
                )

                # Schedule a delayed update in case widgets weren't ready
                print("📡 ON_VIEWPORT_CHANGED: Scheduling delayed update in 100ms")
                QTimer.singleShot(
                    100,
                    lambda: self.image_manager_component.delayed_force_update(
                        self.grid_view_component.thumbnail_grid._all_widgets
                    ),
                )
        else:
            print("📡 ON_VIEWPORT_CHANGED: No visible paths to queue")
            logger.debug("ON_VIEWPORT_CHANGED: No visible paths to queue")

    def _force_visible_card_image_update(self):
        """Force all visible cards to update their images."""
        print("🔥 FORCE_UPDATE: Starting force visible card image update")
        if not hasattr(self.thumbnail_grid, "_all_widgets"):
            print("❌ FORCE_UPDATE: thumbnail_grid has no _all_widgets attribute")
            logger.warning("FORCE_UPDATE: thumbnail_grid has no _all_widgets attribute")
            return

        visible_count = len(self.thumbnail_grid._all_widgets)
        print(f"🔥 FORCE_UPDATE: Starting update for {visible_count} visible cards")
        logger.debug(f"FORCE_UPDATE: Starting update for {visible_count} visible cards")

        updated_count = 0
        for index, widget in self.thumbnail_grid._all_widgets.items():
            logger.debug(f"FORCE_UPDATE: Processing widget {index}")

            if hasattr(widget, "_load_image_fast"):
                logger.debug(
                    f"FORCE_UPDATE: Calling _load_image_fast() for widget {index}"
                )
                widget._load_image_fast()
                updated_count += 1
            elif hasattr(widget, "sequence") and hasattr(widget.sequence, "thumbnails"):
                # Try to get from image service cache
                if widget.sequence.thumbnails:
                    image_path = widget.sequence.thumbnails[0]
                    logger.debug(
                        f"FORCE_UPDATE: Trying cache for widget {index}, path {image_path}"
                    )
                    cached_pixmap = self.image_service.get_image_sync(image_path)
                    if cached_pixmap and hasattr(widget, "image_label"):
                        logger.debug(
                            f"FORCE_UPDATE: Setting cached image for widget {index}"
                        )
                        widget.image_label.setPixmap(cached_pixmap)
                        widget._image_loaded = True
                        updated_count += 1
                    else:
                        logger.debug(
                            f"FORCE_UPDATE: No cached image for widget {index}"
                        )
                else:
                    logger.debug(f"FORCE_UPDATE: Widget {index} has no thumbnails")
            else:
                logger.warning(
                    f"FORCE_UPDATE: Widget {index} has no image loading capability"
                )

        logger.debug(
            f"FORCE_UPDATE: Completed - updated {updated_count}/{visible_count} widgets"
        )

    def _delayed_force_update(self):
        """Delayed force update to catch widgets that weren't ready initially."""
        print("⏰ DELAYED_FORCE_UPDATE: Starting delayed image update")
        logger.debug("DELAYED_FORCE_UPDATE: Starting delayed image update")
        self._force_visible_card_image_update()

    def _on_search_changed(self, query: str):
        """Handle search query changes from filter panel component."""
        logger.info(f"Search changed: {query}")
        if self.viewmodel:
            try:
                from ..core.interfaces import SearchCriteria

                search_criteria = SearchCriteria(query=query)
                self._execute_search(search_criteria)
            except Exception as e:
                logger.error(f"Failed to handle search: {e}")

    def _execute_search(self, search_criteria):
        """Execute search with viewmodel."""
        try:
            import asyncio

            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self.viewmodel.search_sequences(search_criteria))
            else:
                loop.run_until_complete(
                    self.viewmodel.search_sequences(search_criteria)
                )
        except Exception as e:
            logger.error(f"Failed to execute search: {e}")

    def _on_filter_added(self, filter_criteria: FilterCriteria):
        """Handle filter addition from filter panel component."""
        logger.info(f"Filter added: {filter_criteria}")
        if self.viewmodel:
            try:
                import asyncio

                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self.viewmodel.add_filter(filter_criteria))
                else:
                    loop.run_until_complete(self.viewmodel.add_filter(filter_criteria))
            except Exception as e:
                logger.error(f"Failed to add filter: {e}")

    def _on_filter_removed(self, filter_criteria: FilterCriteria):
        """Handle filter removal from filter panel component."""
        logger.info(f"Filter removed: {filter_criteria}")
        if self.viewmodel:
            try:
                import asyncio

                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self.viewmodel.remove_filter(filter_criteria))
                else:
                    loop.run_until_complete(
                        self.viewmodel.remove_filter(filter_criteria)
                    )
            except Exception as e:
                logger.error(f"Failed to remove filter: {e}")

    def _on_filters_cleared(self):
        """Handle clearing all filters from filter panel component."""
        logger.info("All filters cleared")
        if self.viewmodel:
            try:
                import asyncio

                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self.viewmodel.clear_filters())
                else:
                    loop.run_until_complete(self.viewmodel.clear_filters())
            except Exception as e:
                logger.error(f"Failed to clear filters: {e}")

    def _on_sort_changed(self, sort_by: str, sort_order: SortOrder):
        """Handle sort criteria changes from filter panel component."""
        logger.info(f"Sort changed: {sort_by} {sort_order}")
        if self.viewmodel:
            try:
                self.viewmodel.set_sort_criteria(sort_by, sort_order)
                # Update navigation component with new sort criteria
                if self.navigation_component:
                    self.navigation_component.update_for_sequences(
                        self._sequences, sort_by.lower()
                    )
            except Exception as e:
                logger.error(f"Failed to set sort criteria: {e}")

    def _on_item_clicked(self, sequence_id: str, index: int):
        """Handle item click from grid view component - display sequence in viewer."""
        # Start thumbnail click performance tracking
        interaction_id = None
        if self.performance_manager_component:
            interaction_id = (
                self.performance_manager_component.track_thumbnail_click_performance(
                    sequence_id
                )
            )

        logger.info(f"Item clicked: {sequence_id} at index {index}")

        # Find the sequence and display in viewer
        sequence = self._find_sequence_by_id(sequence_id)
        if sequence and self.sequence_viewer_component:
            self.sequence_viewer_component.display_sequence(
                sequence, 0
            )  # Start with first variation
            logger.info(f"Displayed sequence {sequence_id} in viewer")

            # Complete thumbnail performance tracking
            if self.performance_manager_component and interaction_id:
                QTimer.singleShot(
                    50,
                    lambda: self.performance_manager_component.complete_thumbnail_performance_tracking(
                        interaction_id
                    ),
                )

        # Also trigger viewmodel selection for state management
        if self.viewmodel:
            try:
                self.viewmodel.select_sequence(sequence_id)
            except Exception as e:
                logger.error(f"Failed to select sequence: {e}")
                try:
                    self.viewmodel.error_occurred.emit("select_sequence", str(e))
                except Exception as signal_error:
                    logger.error(f"Failed to emit error signal: {signal_error}")

    def _on_item_double_clicked(self, sequence_id: str, index: int):
        """Handle item double click from grid view component - load into workbench."""
        logger.info(f"Item double clicked: {sequence_id} at index {index}")
        try:
            # Double-click should load sequence into workbench
            if self.sequence_viewer_component:
                self.sequence_viewer_component.load_sequence_to_workbench(
                    sequence_id, self._sequences
                )
        except Exception as e:
            logger.error(f"Failed to load sequence to workbench: {e}")

    def _load_sequence_to_workbench(self, sequence_id: str):
        """Load sequence into the main workbench for editing."""
        try:
            # Get the sequence data from viewmodel
            current_state = self.viewmodel.current_state
            sequence = None

            # Find the sequence in current sequences
            for seq in current_state.filtered_sequences or current_state.sequences:
                # Use 'id' attribute instead of 'sequence_id'
                if seq.id == sequence_id:
                    sequence = seq
                    break

            if sequence:
                # Get main widget reference to load sequence
                from src.settings_manager.global_settings.app_context import AppContext

                try:
                    main_window = AppContext.main_window()
                except Exception as e:
                    logger.error(f"Failed to get main window: {e}")
                    main_window = None

                if main_window:
                    if hasattr(main_window, "main_widget"):
                        main_widget = main_window.main_widget

                        # Load sequence into workbench
                        if hasattr(main_widget, "sequence_workbench"):
                            workbench = main_widget.sequence_workbench
                            # Convert sequence model to workbench format
                            sequence_data = self._convert_sequence_for_workbench(
                                sequence
                            )
                            workbench.load_sequence(sequence_data)

                            logger.info(f"Loaded sequence {sequence_id} into workbench")
                        else:
                            logger.warning("Sequence workbench not found")
                    else:
                        logger.warning("Main widget not found")
                else:
                    logger.warning("Main window not available")
            else:
                logger.warning(f"Sequence {sequence_id} not found")

        except Exception as e:
            logger.error(f"Failed to load sequence to workbench: {e}")

    def _find_sequence_by_id(self, sequence_id: str) -> Optional["SequenceModel"]:
        """Find sequence by ID in current sequences."""
        if not self._sequences:
            return None

        for sequence in self._sequences:
            if hasattr(sequence, "id") and sequence.id == sequence_id:
                return sequence
        return None

    def _on_sequence_edit_requested(self, sequence_id: str):
        """Handle edit request from sequence viewer."""
        logger.info(f"Edit requested for sequence: {sequence_id}")
        self._load_sequence_to_workbench(sequence_id)

    def _on_sequence_save_requested(self, sequence_id: str):
        """Handle save request from sequence viewer."""
        logger.info(f"Save requested for sequence: {sequence_id}")
        # TODO: Implement save functionality
        # This would typically open a save dialog or export the sequence

    def _on_sequence_delete_requested(self):
        """Handle delete request from sequence viewer."""
        if self.sequence_viewer and self.sequence_viewer.current_sequence:
            sequence_id = self.sequence_viewer.current_sequence.id
            variation_index = self.sequence_viewer.current_variation_index
            logger.info(
                f"Delete requested for sequence: {sequence_id}, variation: {variation_index}"
            )
            # TODO: Implement delete functionality with confirmation dialog

    def _on_sequence_fullscreen_requested(self, image_path: str):
        """Handle fullscreen request from sequence viewer."""
        logger.info(f"Fullscreen requested for image: {image_path}")
        # TODO: Implement fullscreen image viewer

    def _convert_sequence_for_workbench(self, sequence: "SequenceModel") -> list:
        """Convert SequenceModel to workbench format."""
        try:
            # Try to get sequence data from metadata first
            if hasattr(sequence, "metadata") and sequence.metadata:
                if "sequence_data" in sequence.metadata:
                    return sequence.metadata["sequence_data"]
                elif "beats" in sequence.metadata:
                    return sequence.metadata["beats"]

            # Try direct attributes
            if hasattr(sequence, "beats") and getattr(sequence, "beats", None):
                return sequence.beats
            elif hasattr(sequence, "sequence_data") and getattr(
                sequence, "sequence_data", None
            ):
                return getattr(sequence, "sequence_data")
            else:
                logger.warning(f"No sequence data found for {sequence.name}")
                return []

        except Exception as e:
            logger.error(f"Failed to convert sequence for workbench: {e}")
            return []

    def _on_selection_changed(self, selected_ids: list):
        """Handle selection changes."""
        logger.info(f"Selection changed: {len(selected_ids)} items selected")
        if self.viewmodel:
            try:
                # Update viewmodel with selection
                import asyncio

                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self.viewmodel.set_selection(selected_ids))
                else:
                    loop.run_until_complete(self.viewmodel.set_selection(selected_ids))

            except Exception as e:
                logger.error(f"Failed to update selection: {e}")

    def _on_viewport_changed(self, start_index: int, end_index: int):
        """Handle viewport changes for virtual scrolling - Qt-native approach."""
        logger.debug(f"Viewport changed: {start_index}-{end_index}")
        if self.viewmodel:
            try:
                # Use QTimer for delayed viewport loading to avoid blocking UI
                def load_viewport():
                    try:
                        # For now, viewport loading is handled by the grid component directly
                        # This avoids async complications while maintaining performance
                        logger.debug(
                            f"Viewport data loading handled by grid component: {start_index}-{end_index}"
                        )
                    except Exception as e:
                        logger.error(f"Failed to load viewport data: {e}")

                # Schedule viewport loading with minimal delay
                QTimer.singleShot(10, load_viewport)

            except Exception as e:
                logger.error(f"Failed to schedule viewport data loading: {e}")

    def _on_card_clicked(self, sequence_id: str, index: int):
        """Handle card click events."""
        self._on_item_clicked(sequence_id, index)

    def _on_card_double_clicked(self, sequence_id: str, index: int):
        """Handle card double click events."""
        self._on_item_double_clicked(sequence_id, index)

    def _on_favorite_toggled(self, sequence_id: str, is_favorite: bool):
        """Handle favorite toggle."""
        logger.info(f"Favorite toggled: {sequence_id} -> {is_favorite}")
        # TODO: Update sequence favorite status

    def _on_retry_requested(self):
        """Handle retry requests from grid view component."""
        logger.info("Retry requested")

        if self.grid_view_component:
            self.grid_view_component.show_loading_state()

        # Retry loading data
        if self.viewmodel:
            try:
                self.viewmodel.load_sequences()
            except Exception as e:
                logger.error(f"Failed to retry loading: {e}")
                self.show_error_state(f"Retry failed: {e}")

    def _on_viewmodel_state_changed(self, state):
        """Handle viewmodel state changes."""
        try:
            logger.debug(f"Viewmodel state changed: {state.loading_state}")

            # Update UI based on state
            if state.loading_state.value == "loading":
                # SKIP loading overlay - maintain skeleton placeholders for smooth transitions
                logger.debug(
                    "Skipping loading overlay to maintain skeleton placeholders"
                )
            elif state.loading_state.value == "error":
                error_msg = getattr(state, "error_message", "Unknown error")
                self.show_error_state(error_msg)
            elif state.loading_state.value == "loaded":
                # Show sequences
                sequences = state.filtered_sequences or state.sequences
                self.show_content(sequences)

        except Exception as e:
            logger.error(f"Failed to handle state change: {e}")

    def _on_loading_started(self, operation: str):
        """Handle loading started signal."""
        logger.debug(f"Loading started: {operation}")
        # SKIP loading overlay - keep skeleton placeholders visible
        # This prevents jarring visual transitions
        logger.debug("Skipping loading overlay to maintain skeleton placeholders")

    def _on_loading_finished(self, operation: str, success: bool):
        """Handle loading finished signal - improved error handling to prevent false positives."""
        logger.debug(
            f"🔍 ERROR_TRACE: _on_loading_finished called: {operation}, success: {success}"
        )

        # Enhanced logic to prevent false positive "Failed to complete initialization" errors
        if not success:
            logger.debug(f"🔍 ERROR_TRACE: Loading failed for operation: {operation}")
            # Check if we have working data from any source
            has_working_data = (
                self._sequences and len(self._sequences) > 0
            ) or self._has_instant_data_available()

            logger.debug(f"🔍 ERROR_TRACE: has_working_data = {has_working_data}")
            logger.debug(
                f"🔍 ERROR_TRACE: self._sequences count = {len(self._sequences) if self._sequences else 0}"
            )

            if has_working_data:
                logger.debug(
                    f"🔍 ERROR_TRACE: Loading failed for {operation} but working data is available - ignoring error"
                )
                logger.debug(
                    f"🔍 ERROR_TRACE: Available sequences: {len(self._sequences) if self._sequences else 0}"
                )
            else:
                # Only show error if we truly have no data available
                logger.warning(
                    f"🔍 ERROR_TRACE: Loading failed for {operation} and no working data available"
                )
                # Only show error for critical operations, not initialization fallbacks
                if operation not in ["initialization", "async_load_sequences"]:
                    logger.warning(
                        f"🔍 ERROR_TRACE: Showing error state for operation: {operation}"
                    )
                    self.show_error_state(f"Failed to complete {operation}")
                else:
                    logger.info(
                        f"🔍 ERROR_TRACE: Initialization fallback failed for {operation} - this is expected behavior"
                    )
        else:
            logger.debug(f"Loading completed successfully: {operation}")

    def _has_instant_data_available(self) -> bool:
        """Check if instant data is available from any source."""
        try:
            # Check instant manager
            from ..startup.instant_browse_tab_manager import get_instant_manager

            instant_manager = get_instant_manager()
            if instant_manager and instant_manager.is_ready():
                return len(instant_manager.get_sequences()) > 0

            # Check data preloader
            from ..startup.data_preloader import get_preloaded_data

            preloaded_data = get_preloaded_data()
            if preloaded_data and preloaded_data.get("sequences"):
                return len(preloaded_data["sequences"]) > 0

            return False
        except Exception as e:
            logger.debug(f"Error checking instant data availability: {e}")
            return False

    def _on_error_occurred(self, operation: str, error_message: str):
        """Handle error signal - only show errors if we don't have pre-loaded data."""
        logger.error(f"Viewmodel error - {operation}: {error_message}")

        # Don't show error if we already have pre-loaded data working
        if not self._sequences:
            logger.warning(
                f"Error occurred for {operation} and no pre-loaded data available"
            )
            self.show_error_state(f"{operation}: {error_message}")
        else:
            logger.debug(
                f"Error occurred for {operation} but pre-loaded data is working - ignoring error"
            )

    def show_loading_state(self):
        """Show loading state through grid view component."""
        if self.grid_view_component:
            self.grid_view_component.show_loading_state()

    def show_skeleton_state(self):
        """Show skeleton state through grid view component."""
        if self.grid_view_component:
            self.grid_view_component.show_skeleton_state()

    def show_error_state(self, error_message: Optional[str] = None):
        """Show error state through grid view component."""
        if self.grid_view_component:
            self.grid_view_component.show_error_state(error_message or "Unknown error")

    def show_content(self, sequences: Optional[list] = None):
        """Show main content with sequences using modular components."""
        print(
            f"📋 SHOW_CONTENT: Called with {len(sequences) if sequences else 0} sequences"
        )

        if sequences:
            # Store sequences for later reference
            self._sequences = sequences

            # Update grid view component with sequences
            if self.grid_view_component:
                print(
                    f"📋 SHOW_CONTENT: Calling grid_view_component.set_sequences with {len(sequences)} sequences"
                )
                self.grid_view_component.set_sequences(sequences)
                print("📋 SHOW_CONTENT: grid_view_component.set_sequences completed")

            # Update navigation component with sequences
            if self.navigation_component:
                self.navigation_component.update_for_sequences(
                    sequences, "alphabetical"
                )

            # Preload images through image manager
            if self.image_manager_component:
                self.image_manager_component.preload_sequence_images(sequences)

        # Show content through grid view component
        if self.grid_view_component:
            self.grid_view_component.show_content()
            print("📋 SHOW_CONTENT: Grid view component showing content")

    def cleanup(self):
        """Cleanup resources using modular components."""
        try:
            # Cleanup modular components
            if self.grid_view_component:
                self.grid_view_component.cleanup()

            if self.image_manager_component:
                self.image_manager_component.cleanup()

            # Stop animations
            if self.animation_manager:
                self.animation_manager.stop_all_animations()

            logger.info("BrowseTabView cleanup completed")
        except Exception as e:
            logger.error(f"BrowseTabView cleanup failed: {e}")

    # Helper methods for compatibility

    def _on_image_ready(self, image_path: str, scaled_pixmap):
        """Handle image ready from image manager component."""
        # Find cards that need this image and update them
        if (
            self.grid_view_component
            and self.grid_view_component.thumbnail_grid
            and hasattr(self.grid_view_component.thumbnail_grid, "_all_widgets")
        ):
            for widget in self.grid_view_component.thumbnail_grid._all_widgets.values():
                if (
                    hasattr(widget, "sequence")
                    and hasattr(widget.sequence, "thumbnails")
                    and widget.sequence.thumbnails
                    and widget.sequence.thumbnails[0] == image_path
                ):
                    if hasattr(widget, "image_label"):
                        widget.image_label.setPixmap(scaled_pixmap)
                        widget._image_loaded = True

    def _on_section_clicked(self, section_id: str):
        """Handle section click from navigation component."""
        logger.debug(f"Section clicked: {section_id}")
        # Navigation component handles the actual scrolling
        # This is just for coordination if needed
