"""
Tab manager responsible for managing all application tabs.

This component follows SRP by focusing solely on tab-related functionality.
"""

from typing import TYPE_CHECKING, Dict, Optional
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QObject, pyqtSignal
import logging

from core.application_context import ApplicationContext

if TYPE_CHECKING:
    from .main_widget_coordinator import MainWidgetCoordinator

logger = logging.getLogger(__name__)


class TabManager(QObject):
    """
    Manages all application tabs with clear separation of concerns.

    Responsibilities:
    - Create and manage tab instances
    - Handle tab switching logic
    - Maintain tab state
    - Provide tab access interface
    """

    tab_changed = pyqtSignal(str)  # tab_name
    tab_ready = pyqtSignal(str)  # tab_name

    def __init__(
        self, coordinator: "MainWidgetCoordinator", app_context: ApplicationContext
    ):
        super().__init__(coordinator)

        self.coordinator = coordinator
        self.app_context = app_context
        self._tabs: Dict[str, QWidget] = {}
        self._current_tab: Optional[str] = None
        self._tab_factories = {}

        # Define which tabs use full-widget layout vs stack-based layout
        self._full_widget_tabs = {"browse", "sequence_card"}
        self._stack_based_tabs = {"construct", "generate", "learn", "write"}

        # Register tab factories
        print("DEBUG: TabManager.__init__() - About to register tab factories")
        self._register_tab_factories()
        print(
            f"DEBUG: TabManager.__init__() - Registered factories: {list(self._tab_factories.keys())}"
        )

    def _register_tab_factories(self) -> None:
        """Register factories for creating different tab types."""
        # Import tab factories individually to handle failures gracefully
        self._tab_factories = {}

        # Define tab factory imports with their names
        tab_imports = [
            (
                "construct",
                "main_window.main_widget.construct_tab.construct_tab_factory",
                "ConstructTabFactory",
            ),
            (
                "generate",
                "main_window.main_widget.generate_tab.generate_tab_factory",
                "GenerateTabFactory",
            ),
            (
                "browse",
                "browse_tab.integration.browse_tab_factory",
                "BrowseTabFactory",
            ),
            (
                "learn",
                "main_window.main_widget.learn_tab.learn_tab_factory",
                "LearnTabFactory",
            ),
            (
                "write",
                "main_window.main_widget.write_tab.write_tab_factory",
                "WriteTabFactory",
            ),
            (
                "sequence_card",
                "main_window.main_widget.sequence_card_tab.utils.tab_factory",
                "SequenceCardTabFactory",
            ),
        ]

        # Import each factory individually
        for tab_name, module_path, factory_class_name in tab_imports:
            try:
                print(
                    f"DEBUG: Attempting to import {tab_name} factory from {module_path}"
                )
                module = __import__(module_path, fromlist=[factory_class_name])
                factory_class = getattr(module, factory_class_name)
                self._tab_factories[tab_name] = factory_class
                print(f"DEBUG: ✅ Registered tab factory: {tab_name}")
                logger.debug(f"✅ Registered tab factory: {tab_name}")
            except ImportError as e:
                print(f"DEBUG: ⚠️ Failed to import {tab_name} tab factory: {e}")
                logger.warning(f"⚠️ Failed to import {tab_name} tab factory: {e}")
                # Continue with other factories
            except AttributeError as e:
                print(
                    f"DEBUG: ⚠️ Failed to get {factory_class_name} from {module_path}: {e}"
                )
                logger.warning(
                    f"⚠️ Failed to get {factory_class_name} from {module_path}: {e}"
                )
                # Continue with other factories
            except Exception as e:
                print(f"DEBUG: ❌ Unexpected error importing {tab_name} factory: {e}")
                logger.error(f"❌ Unexpected error importing {tab_name} factory: {e}")
                import traceback

                traceback.print_exc()

        print(
            f"DEBUG: Registered {len(self._tab_factories)} tab factories: {list(self._tab_factories.keys())}"
        )
        logger.info(
            f"Registered {len(self._tab_factories)} tab factories: {list(self._tab_factories.keys())}"
        )

    def initialize_tabs(self) -> None:
        """Initialize all tabs lazily."""
        logger.info("TabManager.initialize_tabs() called")

        try:
            # First populate the stacks with essential widgets
            logger.info("Populating stacks with essential widgets...")
            self._populate_stacks_with_essential_widgets()

            # Get the default tab from settings
            settings_manager = self.app_context.settings_manager
            try:
                default_tab = settings_manager.global_settings.get_current_tab()
                logger.info(f"Default tab from settings: {default_tab}")
            except Exception as e:
                logger.warning(f"Failed to get current tab from settings: {e}")
                default_tab = "construct"  # Fallback to construct tab
                logger.info(f"Using fallback default tab: {default_tab}")

            # Create the default tab first
            logger.info(f"Creating default tab: {default_tab}")
            tab_widget = self._create_tab(default_tab)
            if tab_widget:
                logger.info(
                    f"Default tab created successfully: {type(tab_widget).__name__}"
                )
            else:
                logger.error(f"Failed to create default tab: {default_tab}")

            # Switch to the default tab
            logger.info(f"Switching to default tab: {default_tab}")
            success = self.switch_to_tab(default_tab)
            if success:
                logger.info(f"Successfully switched to tab: {default_tab}")
            else:
                logger.error(f"Failed to switch to tab: {default_tab}")

            logger.info(
                f"TabManager initialization completed with default: {default_tab}"
            )

        except Exception as e:
            logger.error(f"TabManager initialization failed: {e}")
            import traceback

            traceback.print_exc()

    def _populate_stacks_with_essential_widgets(self) -> None:
        """Populate the stacks with essential widgets that should always be available."""
        try:
            print("DEBUG: Getting essential widgets from widget manager...")
            logger.info("Getting essential widgets from widget manager...")

            # Get essential widgets from widget manager
            sequence_workbench = self.coordinator.widget_manager.get_widget(
                "sequence_workbench"
            )
            codex = self.coordinator.widget_manager.get_widget("codex")

            print(f"DEBUG: sequence_workbench widget: {sequence_workbench}")
            print(f"DEBUG: codex widget: {codex}")
            logger.info(f"sequence_workbench widget: {sequence_workbench}")
            logger.info(f"codex widget: {codex}")

            # Add to left stack (index 0 and 1 are reserved for these)
            if sequence_workbench:
                self.coordinator.left_stack.addWidget(sequence_workbench)  # Index 0
                print("DEBUG: ✅ Added sequence_workbench to left stack")
                logger.info("✅ Added sequence_workbench to left stack")
            else:
                print(
                    "DEBUG: ❌ sequence_workbench widget is None - not added to stack"
                )
                logger.warning(
                    "❌ sequence_workbench widget is None - not added to stack"
                )

            if codex:
                self.coordinator.left_stack.addWidget(codex)  # Index 1
                print("DEBUG: ✅ Added codex to left stack")
                logger.info("✅ Added codex to left stack")
            else:
                print("DEBUG: ❌ codex widget is None - not added to stack")
                logger.warning("❌ codex widget is None - not added to stack")

            print(
                f"DEBUG: Left stack now has {self.coordinator.left_stack.count()} widgets"
            )
            print(
                f"DEBUG: Right stack now has {self.coordinator.right_stack.count()} widgets"
            )
            logger.info(
                f"Left stack now has {self.coordinator.left_stack.count()} widgets"
            )
            logger.info(
                f"Right stack now has {self.coordinator.right_stack.count()} widgets"
            )

        except Exception as e:
            print(f"DEBUG: Failed to populate stacks with essential widgets: {e}")
            logger.error(f"Failed to populate stacks with essential widgets: {e}")
            import traceback

            traceback.print_exc()

    def _create_tab(self, tab_name: str) -> Optional[QWidget]:
        """
        Create a tab instance if it doesn't exist.

        Args:
            tab_name: Name of the tab to create

        Returns:
            The tab widget or None if creation failed
        """
        print(f"DEBUG: _create_tab called for: {tab_name}")

        if tab_name in self._tabs:
            print(f"DEBUG: Tab {tab_name} already exists, returning existing")
            return self._tabs[tab_name]

        if tab_name not in self._tab_factories:
            print(f"DEBUG: ❌ No factory registered for tab: {tab_name}")
            logger.error(f"No factory registered for tab: {tab_name}")
            return None

        try:
            factory = self._tab_factories[tab_name]
            print(f"DEBUG: Creating tab {tab_name} using factory {factory.__name__}")

            # Debug app_context services
            print(f"DEBUG: app_context: {self.app_context}")
            print(
                f"DEBUG: app_context.settings_manager: {self.app_context.settings_manager}"
            )
            print(f"DEBUG: app_context.json_manager: {self.app_context.json_manager}")

            # Create tab with dependency injection
            tab_widget = factory.create(
                parent=self.coordinator, app_context=self.app_context
            )

            print(
                f"DEBUG: ✅ Tab {tab_name} created successfully: {type(tab_widget).__name__}"
            )

            self._tabs[tab_name] = tab_widget

            # Add to appropriate stack
            print(f"DEBUG: Adding tab {tab_name} to stack...")
            self._add_tab_to_stack(tab_name, tab_widget)

            self.tab_ready.emit(tab_name)
            logger.info(f"Created tab: {tab_name}")

            return tab_widget

        except Exception as e:
            print(f"DEBUG: ❌ Failed to create tab {tab_name}: {e}")
            logger.error(f"Failed to create tab {tab_name}: {e}")
            return None

    def _add_tab_to_stack(self, tab_name: str, tab_widget: QWidget) -> None:
        """Add tab to the appropriate stack widget or main content stack."""
        # Full-widget tabs don't get added to left/right stacks
        # They will be added to main_content_stack when first switched to
        if tab_name in self._full_widget_tabs:
            logger.info(
                f"Tab {tab_name} is a full-widget tab, will be added to main content stack when switched to"
            )
            return

        # Stack-based tabs get added to left/right stacks
        # Note: Left stack indices 0 and 1 are reserved for sequence_workbench and codex
        # Tab-specific widgets start from index 2 onwards

        if tab_name == "construct":
            # Construct tab components go to right stack
            if hasattr(tab_widget, "start_pos_picker"):
                self.coordinator.right_stack.addWidget(
                    tab_widget.start_pos_picker
                )  # Index 0
            if hasattr(tab_widget, "advanced_start_pos_picker"):
                self.coordinator.right_stack.addWidget(
                    tab_widget.advanced_start_pos_picker
                )  # Index 1
            if hasattr(tab_widget, "option_picker"):
                self.coordinator.right_stack.addWidget(
                    tab_widget.option_picker
                )  # Index 2
        elif tab_name == "generate":
            self.coordinator.right_stack.addWidget(tab_widget)  # Index 3
        elif tab_name == "learn":
            self.coordinator.right_stack.addWidget(tab_widget)  # Index 4
        else:
            # Default: add to right stack
            self.coordinator.right_stack.addWidget(tab_widget)

    def switch_to_tab(self, tab_name: str) -> bool:
        """
        Switch to a specific tab with instant visual feedback.

        Args:
            tab_name: Name of the tab to switch to

        Returns:
            True if successful, False otherwise
        """
        from PyQt6.QtCore import QTimer
        from PyQt6.QtWidgets import QApplication

        # CRITICAL: Instant visual switching for browse tab
        if tab_name == "browse":
            return self._switch_to_browse_instantly(tab_name)

        # For other tabs, use normal switching
        return self._switch_to_tab_normal(tab_name)

    def _switch_to_browse_instantly(self, tab_name: str) -> bool:
        """Switch to browse tab with instant visual feedback."""
        from PyQt6.QtCore import QTimer
        from PyQt6.QtWidgets import QApplication

        # Create tab if it doesn't exist (lightweight creation)
        tab_widget = self._ensure_tab_exists(tab_name)
        if not tab_widget:
            return False

        # INSTANT: Update UI state immediately
        old_tab = self._current_tab
        self._current_tab = tab_name

        # INSTANT: Switch layout immediately without any animations
        self._switch_layout_instantly(tab_name, tab_widget)

        # INSTANT: Process events to ensure immediate visual update
        QApplication.processEvents()

        # INSTANT: Emit signal for immediate UI updates
        self.tab_changed.emit(tab_name)

        # BACKGROUND: Defer heavy operations
        QTimer.singleShot(
            1, lambda: self._complete_browse_switch_background(tab_name, old_tab)
        )

        logger.info(f"Instantly switched to browse tab (background loading)")
        return True

    def _switch_layout_instantly(self, tab_name: str, tab_widget: QWidget) -> None:
        """Switch layout instantly without animations or fade effects."""
        # Disable any animations temporarily
        fade_manager = getattr(self.coordinator, "fade_manager", None)
        original_fade_state = None

        if fade_manager and hasattr(fade_manager, "set_fades_enabled"):
            original_fade_state = fade_manager.fades_enabled()
            fade_manager.set_fades_enabled(False)

        try:
            # Use full-widget layout for browse tab
            self.coordinator.switch_to_full_widget_layout(tab_widget)
        finally:
            # Restore original fade state
            if fade_manager and original_fade_state is not None:
                fade_manager.set_fades_enabled(original_fade_state)

    def _complete_browse_switch_background(self, tab_name: str, old_tab: str) -> None:
        """Complete browse tab switch operations in background."""
        try:
            # Save to settings
            if hasattr(self.app_context, "settings_manager") and hasattr(
                self.app_context.settings_manager, "global_settings"
            ):
                self.app_context.settings_manager.global_settings.set_current_tab(
                    tab_name
                )
                logger.debug(f"Saved current tab '{tab_name}' to global settings")

            # Initialize browse tab content if needed
            tab_widget = self._tabs.get(tab_name)
            if tab_widget and hasattr(tab_widget, "initialize_content_async"):
                tab_widget.initialize_content_async()

            logger.info(f"Completed background switch from {old_tab} to {tab_name}")

        except Exception as e:
            logger.warning(f"Error in background browse switch completion: {e}")

    def _switch_to_tab_normal(self, tab_name: str) -> bool:
        """Normal tab switching for non-browse tabs."""
        # Create tab if it doesn't exist
        tab_widget = self._create_tab(tab_name)
        if not tab_widget:
            return False

        # Update current tab
        old_tab = self._current_tab
        self._current_tab = tab_name

        # Save current tab to global settings for persistence
        try:
            if hasattr(self.app_context, "settings_manager") and hasattr(
                self.app_context.settings_manager, "global_settings"
            ):
                self.app_context.settings_manager.global_settings.set_current_tab(
                    tab_name
                )
                logger.debug(f"Saved current tab '{tab_name}' to global settings")
        except Exception as e:
            logger.warning(f"Failed to save current tab to settings: {e}")

        # ALWAYS switch stack widgets, even if tab already existed
        print(f"DEBUG: About to call _switch_stack_widgets for {tab_name}")
        self._switch_stack_widgets(tab_name, tab_widget)

        # Emit signal
        self.tab_changed.emit(tab_name)

        logger.info(f"Switched from {old_tab} to {tab_name}")
        return True

    def _switch_stack_widgets(self, tab_name: str, tab_widget: QWidget) -> None:
        """Switch stack widgets based on tab type."""
        if tab_name in self._full_widget_tabs:
            # Full-widget tabs use the main content area
            self.coordinator.switch_to_full_widget_layout(tab_widget)
        else:
            # Stack-based tabs use the left/right stack layout
            self.coordinator.switch_to_stack_layout()

            # Set the appropriate stack indices for the tab
            if tab_name == "construct":
                # Construct tab: show sequence_workbench (index 0) and determine right panel based on sequence state
                self.coordinator.left_stack.setCurrentIndex(0)  # sequence_workbench
                print(
                    f"DEBUG: Construct tab - setting left stack to index 0 (sequence_workbench)"
                )

                # Determine right panel based on sequence length (like the old tab switcher)
                try:
                    json_manager = self.app_context.json_manager
                    current_sequence = json_manager.loader_saver.load_current_sequence()
                    sequence_length = len(current_sequence)
                    print(f"DEBUG: Current sequence length: {sequence_length}")

                    # Show option picker if sequence has beats (length > 1), otherwise show start pos picker
                    if sequence_length > 1:
                        # Option picker should be at index 2 based on _add_tab_to_stack logic
                        target_index = 2
                        print(
                            f"DEBUG: Sequence has beats, setting right stack to index {target_index} (option_picker)"
                        )
                        self.coordinator.right_stack.setCurrentIndex(target_index)
                    else:
                        # Start position picker should be at index 0
                        target_index = 0
                        print(
                            f"DEBUG: Sequence is empty/start-only, setting right stack to index {target_index} (start_pos_picker)"
                        )
                        self.coordinator.right_stack.setCurrentIndex(target_index)

                    # Verify the switch worked
                    actual_index = self.coordinator.right_stack.currentIndex()
                    actual_widget = self.coordinator.right_stack.currentWidget()
                    print(
                        f"DEBUG: Right stack now at index {actual_index}, widget: {type(actual_widget).__name__ if actual_widget else 'None'}"
                    )

                except Exception as e:
                    logger.warning(
                        f"Failed to determine construct tab right panel from sequence: {e}"
                    )
                    print(f"DEBUG: Exception determining right panel: {e}")
                    # Fallback to start position picker
                    self.coordinator.right_stack.setCurrentIndex(0)  # start_pos_picker
                    print(
                        "DEBUG: Fallback - setting right stack to index 0 (start_pos_picker)"
                    )

            elif tab_name == "generate":
                # Generate tab: show sequence_workbench (index 0) and generate widget
                self.coordinator.left_stack.setCurrentIndex(0)  # sequence_workbench
                # Find generate tab index in right stack
                for i in range(self.coordinator.right_stack.count()):
                    widget = self.coordinator.right_stack.widget(i)
                    if widget == tab_widget:
                        self.coordinator.right_stack.setCurrentIndex(i)
                        break
            elif tab_name == "learn":
                # Learn tab: show codex (index 1) and learn widget
                self.coordinator.left_stack.setCurrentIndex(1)  # codex
                # Find learn tab index in right stack
                for i in range(self.coordinator.right_stack.count()):
                    widget = self.coordinator.right_stack.widget(i)
                    if widget == tab_widget:
                        self.coordinator.right_stack.setCurrentIndex(i)
                        break
            else:
                # Default: show sequence_workbench and find tab widget
                self.coordinator.left_stack.setCurrentIndex(0)  # sequence_workbench
                for i in range(self.coordinator.right_stack.count()):
                    widget = self.coordinator.right_stack.widget(i)
                    if widget == tab_widget:
                        self.coordinator.right_stack.setCurrentIndex(i)
                        break

    def _ensure_tab_exists(self, tab_name: str) -> Optional[QWidget]:
        """Ensure tab exists with minimal overhead."""
        if tab_name in self._tabs:
            return self._tabs[tab_name]

        # Create tab with minimal initialization for instant switching
        return self._create_tab(tab_name)

    def get_tab_widget(self, tab_name: str) -> Optional[QWidget]:
        """
        Get a tab widget by name.

        Args:
            tab_name: Name of the tab

        Returns:
            The tab widget or None if not found
        """
        return self._tabs.get(tab_name)

    def get_current_tab(self) -> Optional[str]:
        """Get the name of the currently active tab."""
        return self._current_tab

    def is_tab_created(self, tab_name: str) -> bool:
        """Check if a tab has been created."""
        return tab_name in self._tabs

    def get_available_tabs(self) -> list[str]:
        """Get list of available tab names."""
        return list(self._tab_factories.keys())

    def on_widget_ready(self, widget_name: str) -> None:
        """Handle widget ready events that might affect tabs."""
        # Update tabs that depend on specific widgets
        if widget_name == "sequence_workbench":
            # Some tabs might need the sequence workbench
            for tab_widget in self._tabs.values():
                if hasattr(tab_widget, "on_sequence_workbench_ready"):
                    tab_widget.on_sequence_workbench_ready()

    def cleanup(self) -> None:
        """Cleanup tab resources."""
        for tab_name, tab_widget in self._tabs.items():
            if hasattr(tab_widget, "cleanup"):
                try:
                    tab_widget.cleanup()
                except Exception as e:
                    logger.error(f"Error cleaning up tab {tab_name}: {e}")

        self._tabs.clear()
        self._current_tab = None
        logger.info("Tab manager cleaned up")
