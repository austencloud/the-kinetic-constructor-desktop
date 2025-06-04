"""
Component Initialization Manager - Handles complex component initialization sequence.

This manager extracts the massive initialization logic from MainWidgetCoordinator
following the Single Responsibility Principle.
"""

import logging
from typing import TYPE_CHECKING, Optional
from PyQt6.QtCore import QTimer

if TYPE_CHECKING:
    from core.application_context import ApplicationContext
    from ..widget_manager import WidgetManager
    from ..tab_manager import TabManager
    from ..main_widget_coordinator import MainWidgetCoordinator


class ComponentInitializationManager:
    """
    Manages the complex component initialization sequence.

    Responsibilities:
    - Handle multi-stage initialization process
    - Manage initialization dependencies/ordering
    - Handle initialization error recovery
    - Load saved sequences
    - Set up menu bar layout
    """

    def __init__(
        self,
        app_context: "ApplicationContext",
        widget_manager: "WidgetManager",
        tab_manager: "TabManager",
        coordinator: "MainWidgetCoordinator",
    ):
        self.app_context = app_context
        self.widget_manager = widget_manager
        self.tab_manager = tab_manager
        self.coordinator = coordinator
        self.logger = logging.getLogger(__name__)

        self._components_initialized = False

        # Initialize AppContextAdapter early to prevent warnings
        self._setup_legacy_compatibility()

    def _setup_legacy_compatibility(self) -> None:
        """Set up legacy compatibility adapter early to prevent warnings."""
        try:
            from core.migration_adapters import setup_legacy_compatibility

            setup_legacy_compatibility(self.app_context)
            self.logger.info("Legacy compatibility adapter initialized")
        except Exception as e:
            self.logger.warning(f"Failed to initialize legacy compatibility: {e}")

    def initialize_all_components(self) -> None:
        """
        Initialize all components in the correct order.

        This method should be called AFTER the dependency injection system
        and legacy compatibility are fully set up to avoid circular dependencies.
        """
        self.logger.info(
            "ComponentInitializationManager.initialize_all_components() called"
        )

        if self._components_initialized:
            self.logger.info("Components already initialized, skipping")
            return

        try:
            # Phase 1: Initialize widgets first
            self._initialize_widgets()

            # Phase 2: Set up essential services
            self._initialize_services()

            # Phase 3: Set up UI layout
            self._setup_menu_bar_layout()

            # Phase 4: Initialize tabs
            self._initialize_tabs()

            # Phase 5: Initialize state
            self._initialize_state()

            # Phase 6: Load saved sequence
            self._load_saved_sequence()

            self._components_initialized = True
            self.logger.info("Component initialization completed successfully")

        except Exception as e:
            self.logger.error(f"Component initialization failed: {e}")
            import traceback

            traceback.print_exc()
            raise

    def _initialize_widgets(self) -> None:
        """Initialize widget manager and core widgets."""
        self.logger.info("Initializing widget manager...")
        self.widget_manager.initialize_widgets()
        self.logger.info("Widget manager initialization completed")

    def _initialize_services(self) -> None:
        """Initialize essential services for backward compatibility."""
        self.logger.info("Initializing essential services...")

        # Set sequence_properties_manager immediately after widgets are initialized
        self._setup_sequence_properties_manager()

        # Set additional services after widgets are initialized
        self._setup_fade_manager()
        self._setup_sequence_workbench()
        self._setup_thumbnail_finder()
        self._setup_sequence_level_evaluator()
        self._setup_letter_determiner()
        self._setup_pictograph_dataset()
        self._setup_pictograph_collector()
        self._setup_tab_widgets()

        self.logger.info("Essential services initialization completed")

    def _setup_sequence_properties_manager(self) -> None:
        """Set up sequence properties manager."""
        try:
            from main_window.main_widget.sequence_properties_manager.sequence_properties_manager_factory import (
                SequencePropertiesManagerFactory,
            )

            self.coordinator.sequence_properties_manager = (
                SequencePropertiesManagerFactory.create(self.app_context)
            )
            self.logger.info(
                "Sequence properties manager injected for backward compatibility"
            )
        except Exception as e:
            self.logger.warning(f"Sequence properties manager not available: {e}")
            self.coordinator.sequence_properties_manager = None

    def _setup_fade_manager(self) -> None:
        """Set up fade manager."""
        self.coordinator.fade_manager = self.widget_manager.get_widget("fade_manager")
        if self.coordinator.fade_manager:
            self.logger.info("Fade manager injected for backward compatibility")
        else:
            self.logger.warning("Fade manager not available")

    def _setup_sequence_workbench(self) -> None:
        """Set up sequence workbench."""
        self.coordinator.sequence_workbench = self.widget_manager.get_widget(
            "sequence_workbench"
        )
        if self.coordinator.sequence_workbench:
            self.logger.info("Sequence workbench injected for backward compatibility")
        else:
            self.logger.warning("Sequence workbench not available")

    def _setup_thumbnail_finder(self) -> None:
        """Set up thumbnail finder."""
        try:
            from main_window.main_widget.thumbnail_finder import ThumbnailFinder

            self.coordinator.thumbnail_finder = ThumbnailFinder()
            self.logger.info("Thumbnail finder created for backward compatibility")
        except Exception as e:
            self.logger.warning(f"Thumbnail finder creation failed: {e}")
            self.coordinator.thumbnail_finder = None

    def _setup_sequence_level_evaluator(self) -> None:
        """Set up sequence level evaluator."""
        try:
            from main_window.main_widget.sequence_level_evaluator import (
                SequenceLevelEvaluator,
            )

            self.coordinator.sequence_level_evaluator = SequenceLevelEvaluator()
            self.logger.info(
                "Sequence level evaluator created for backward compatibility"
            )
        except Exception as e:
            self.logger.warning(f"Sequence level evaluator creation failed: {e}")
            self.coordinator.sequence_level_evaluator = None

    def _setup_letter_determiner(self) -> None:
        """Set up letter determiner."""
        try:
            from letter_determination.core import LetterDeterminer

            self.coordinator.letter_determiner = self.app_context.get_service(
                LetterDeterminer
            )
            self.logger.info("Letter determiner injected for backward compatibility")
        except Exception as e:
            self.logger.warning(f"Letter determiner not available: {e}")
            self.coordinator.letter_determiner = None

    def _setup_pictograph_dataset(self) -> None:
        """Set up pictograph dataset."""
        try:
            from main_window.main_widget.pictograph_data_loader import (
                PictographDataLoader,
            )

            pictograph_data_loader = self.app_context.get_service(PictographDataLoader)
            if pictograph_data_loader and hasattr(
                pictograph_data_loader, "get_pictograph_dataset"
            ):
                self.coordinator.pictograph_dataset = (
                    pictograph_data_loader.get_pictograph_dataset()
                )
                self.logger.info(
                    "Pictograph dataset injected for backward compatibility"
                )

                # Update the letter determiner with the loaded dataset
                if self.coordinator.letter_determiner and hasattr(
                    self.coordinator.letter_determiner, "update_pictograph_dataset"
                ):
                    self.coordinator.letter_determiner.update_pictograph_dataset(
                        self.coordinator.pictograph_dataset
                    )
                    self.logger.info(
                        "Letter determiner dataset updated with loaded data"
                    )
            else:
                self.logger.warning("Pictograph dataset not available from data loader")
                self.coordinator.pictograph_dataset = {}
        except Exception as e:
            self.logger.warning(f"Pictograph dataset not available: {e}")
            self.coordinator.pictograph_dataset = {}

    def _setup_pictograph_collector(self) -> None:
        """Set up pictograph collector."""
        try:
            from main_window.main_widget.pictograph_collector_factory import (
                PictographCollectorFactory,
            )

            self.coordinator.pictograph_collector = PictographCollectorFactory.create(
                parent=self.coordinator, app_context=self.app_context
            )
            self.logger.info("Pictograph collector created for backward compatibility")

        except ImportError as e:
            self.logger.warning(f"Could not import PictographCollectorFactory: {e}")
            # Fallback: create basic pictograph collector
            try:
                from main_window.main_widget.pictograph_collector import (
                    PictographCollector,
                )

                self.coordinator.pictograph_collector = PictographCollector(
                    self.coordinator
                )
                self.logger.info(
                    "Fallback pictograph collector created for backward compatibility"
                )
            except ImportError as e2:
                self.logger.error(f"Could not create pictograph_collector: {e2}")
                self.coordinator.pictograph_collector = None
        except Exception as e:
            self.logger.error(f"Failed to initialize pictograph_collector: {e}")
            self.coordinator.pictograph_collector = None

    def _setup_tab_widgets(self) -> None:
        """Set up tab widgets for backward compatibility."""
        self.coordinator.construct_tab = self.tab_manager.get_tab_widget("construct")
        if self.coordinator.construct_tab:
            self.logger.info("Construct tab injected for backward compatibility")
        else:
            self.logger.warning("Construct tab not available")

        self.coordinator.learn_tab = self.tab_manager.get_tab_widget("learn")
        if self.coordinator.learn_tab:
            self.logger.info("Learn tab injected for backward compatibility")
        else:
            self.logger.warning("Learn tab not available")

        self.coordinator.settings_dialog = self.widget_manager.get_widget(
            "settings_dialog"
        )
        if self.coordinator.settings_dialog:
            self.logger.info("Settings dialog injected for backward compatibility")
        else:
            self.logger.warning("Settings dialog not available")

    def _setup_menu_bar_layout(self) -> None:
        """Set up the menu bar layout after widgets are initialized."""
        self.logger.info("Setting up menu bar layout...")
        try:
            # Get the menu bar widget
            menu_bar = self.widget_manager.get_widget("menu_bar")
            if not menu_bar:
                self.logger.warning("Menu bar widget not available for layout setup")
                return

            # Create top layout for menu bar components
            from PyQt6.QtWidgets import QHBoxLayout

            self.coordinator.top_layout = QHBoxLayout()
            self.coordinator.top_layout.setContentsMargins(0, 0, 0, 0)
            self.coordinator.top_layout.setSpacing(0)

            # Add menu bar components with proper proportions
            if hasattr(menu_bar, "social_media_widget"):
                self.coordinator.top_layout.addWidget(menu_bar.social_media_widget, 1)
            if hasattr(menu_bar, "navigation_widget"):
                self.coordinator.top_layout.addWidget(menu_bar.navigation_widget, 16)
            if hasattr(menu_bar, "settings_button"):
                self.coordinator.top_layout.addWidget(menu_bar.settings_button, 1)

            # Insert the top layout at the beginning of the main layout
            self.coordinator.main_layout.insertLayout(0, self.coordinator.top_layout)

        except Exception as e:
            self.logger.error(f"Failed to set up menu bar layout: {e}")

        self.logger.info("Menu bar layout setup completed")

    def _initialize_tabs(self) -> None:
        """Initialize tab manager."""
        self.logger.info("Initializing tab manager...")
        self.tab_manager.initialize_tabs()
        self.logger.info("Tab manager initialization completed")

    def _initialize_state(self) -> None:
        """Initialize state manager."""
        self.logger.info("Initializing state manager...")
        self.coordinator.state_manager.initialize_state()
        self.logger.info("State manager initialization completed")

    def _load_saved_sequence(self) -> None:
        """Load the saved sequence from current_sequence.json into the beat frame UI."""
        self.logger.info("Loading saved sequence into beat frame...")
        try:
            # Get the sequence workbench
            sequence_workbench = self.widget_manager.get_widget("sequence_workbench")
            if not sequence_workbench or not hasattr(sequence_workbench, "beat_frame"):
                self.logger.warning(
                    "Sequence workbench or beat frame not available for sequence loading"
                )
                return

            beat_frame = sequence_workbench.beat_frame
            if not beat_frame or not hasattr(beat_frame, "populator"):
                self.logger.warning(
                    "Beat frame populator not available for sequence loading"
                )
                return

            # STARTUP OPTIMIZATION: Skip construct tab dependency check during startup
            # The construct tab will be created on-demand when needed
            construct_tab = self.tab_manager.get_tab_widget("construct")
            if not construct_tab or not hasattr(construct_tab, "start_pos_picker"):
                self.logger.info(
                    "Construct tab not available during startup - skipping sequence loading (will load on-demand)"
                )
                # CRITICAL FIX: Don't defer with QTimer - this causes infinite startup loop
                # The sequence will be loaded when the construct tab is actually accessed
                return

            # Load the current sequence from JSON
            json_manager = self.app_context.json_manager
            current_sequence = json_manager.loader_saver.load_current_sequence()

            # Only load if there's actual sequence data (more than just the default entry)
            if len(current_sequence) > 1:
                self.logger.info(
                    f"Loading sequence with {len(current_sequence)} entries into beat frame"
                )

                # Use the beat frame populator to load the sequence
                beat_frame.populator.populate_beat_frame_from_json(
                    current_sequence, initial_state_load=True
                )
                self.logger.info("Sequence loaded successfully into beat frame UI")
            else:
                self.logger.info(
                    "No saved sequence found or sequence is empty, starting with empty beat frame"
                )

        except Exception as e:
            self.logger.error(f"Failed to load saved sequence: {e}")
            # Don't raise - let the application continue with an empty beat frame

        self.logger.info("Saved sequence loading completed")

    def handle_initialization_error(self, error: Exception) -> None:
        """Handle initialization errors with recovery strategies."""
        self.logger.error(f"Initialization error occurred: {error}")

        # Could implement recovery strategies here:
        # - Retry initialization
        # - Skip problematic components
        # - Fallback to minimal initialization
        # - User notification

        # For now, just log and re-raise
        raise error
