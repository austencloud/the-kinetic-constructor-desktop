"""
Main widget coordinator that orchestrates the different components of the main widget.

This replaces the monolithic MainWidget class with a coordinator that manages
smaller, focused components following the Single Responsibility Principle.
"""

from typing import TYPE_CHECKING, Optional
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import pyqtSignal

from core.application_context import ApplicationContext
from .tab_manager import TabManager
from .widget_manager import WidgetManager
from .state_manager import StateManager
from .image_drag_drop_handler import ImageDragDropHandler
from .image_drop_processor import ImageDropProcessor
from .initialization.component_initialization_manager import (
    ComponentInitializationManager,
)
from .layout.layout_coordinator import LayoutCoordinator
from .events.event_coordinator import EventCoordinator
from .compatibility.legacy_compatibility_provider import LegacyCompatibilityProvider
from .access.widget_access_facade import WidgetAccessFacade

if TYPE_CHECKING:
    from main_window.main_window import MainWindow
    from splash_screen.splash_screen import SplashScreen


class MainWidgetCoordinator(QWidget):
    """
    Coordinates the main widget components without violating SRP.

    Responsibilities:
    - Orchestrate tab and widget managers
    - Handle high-level layout
    - Coordinate between different managers
    - Provide clean interface to MainWindow
    """

    # Signals for communication between components
    tab_changed = pyqtSignal(str)  # tab_name
    state_changed = pyqtSignal(dict)  # state_data

    def __init__(
        self,
        main_window: "MainWindow",
        splash_screen: "SplashScreen",
        app_context: ApplicationContext,
    ):
        super().__init__(main_window)

        self.main_window = main_window
        self.splash_screen = splash_screen
        self.app_context = app_context
        self._components_initialized = False

        # Initialize managers with clear responsibilities
        self.tab_manager = TabManager(self, app_context)
        self.widget_manager = WidgetManager(self, app_context)
        self.state_manager = StateManager(self, app_context)

        # Initialize specialized initialization manager
        self.initialization_manager = ComponentInitializationManager(
            app_context, self.widget_manager, self.tab_manager, self
        )

        # Initialize layout coordinator
        self.layout_coordinator = LayoutCoordinator(self, self.tab_manager)

        # Initialize image drag and drop functionality
        self.image_drop_processor = ImageDropProcessor(app_context)
        self.image_drag_drop_handler = ImageDragDropHandler(self, app_context)

        # Initialize event coordinator
        self.event_coordinator = EventCoordinator(
            self,
            self.tab_manager,
            self.widget_manager,
            self.state_manager,
            self.image_drag_drop_handler,
        )

        # Initialize legacy compatibility provider
        self.legacy_compatibility_provider = LegacyCompatibilityProvider(
            self, app_context
        )

        # Initialize widget access facade
        self.widget_access_facade = WidgetAccessFacade(
            self.widget_manager, self.tab_manager
        )

        # Inject essential services for backward compatibility
        self.legacy_compatibility_provider.inject_all_legacy_services()

        # Setup layout and connections
        self._setup_layout()
        self.event_coordinator.connect_all_signals()
        self._setup_image_drag_drop()

        # NOTE: Components will be initialized separately to avoid circular dependencies
        # Call initialize_components() after dependency injection is fully set up

    def _setup_layout(self) -> None:
        """Setup the main layout structure with hybrid tab support."""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Delegate layout setup to the layout coordinator
        self.layout_coordinator.setup_initial_layout()
        self.setLayout(self.main_layout)

    def initialize_components(self) -> None:
        """
        Initialize all components using the ComponentInitializationManager.

        This method delegates to the specialized initialization manager
        following the Single Responsibility Principle.
        """
        if self._components_initialized:
            return

        # Delegate to the specialized initialization manager
        self.initialization_manager.initialize_all_components()
        self._components_initialized = True

    def _setup_image_drag_drop(self) -> None:
        """Set up image drag and drop functionality."""
        # Set up callbacks for the drag and drop handler
        self.image_drag_drop_handler.set_single_image_callback(
            self.image_drop_processor.process_single_image
        )
        self.image_drag_drop_handler.set_multiple_images_callback(
            self.image_drop_processor.process_multiple_images
        )

    # Public interface methods
    def get_current_tab(self) -> Optional[str]:
        """Get the currently active tab."""
        return self.state_manager.current_tab

    def switch_to_tab(self, tab_name: str) -> None:
        """Switch to a specific tab."""
        self.tab_manager.switch_to_tab(tab_name)

    def get_tab_widget(self, tab_name: str) -> Optional[QWidget]:
        """Get a specific tab widget."""
        return self.widget_access_facade.get_tab_widget(tab_name)

    def switch_to_stack_layout(
        self, left_stretch: int = 1, right_stretch: int = 1
    ) -> None:
        """
        Switch to stack-based layout mode for construct/generate/learn tabs.

        Args:
            left_stretch: Stretch factor for left stack
            right_stretch: Stretch factor for right stack
        """
        self.layout_coordinator.switch_to_stack_layout(left_stretch, right_stretch)

    def switch_to_full_widget_layout(self, tab_widget: QWidget) -> None:
        """
        Switch to full-widget layout mode for browse/sequence_card tabs.

        Args:
            tab_widget: The tab widget that should take full control of the layout
        """
        self.layout_coordinator.switch_to_full_widget_layout(tab_widget)

    def get_current_layout_mode(self) -> str:
        """Get the current layout mode ('stack' or 'full_widget')."""
        return self.layout_coordinator.get_current_layout_mode().value

    def get_widget(self, widget_name: str) -> Optional[QWidget]:
        """Get a specific widget."""
        return self.widget_access_facade.get_widget(widget_name)

    def show_settings_dialog(self) -> None:
        """Show the settings dialog."""
        self.widget_access_facade.show_settings_dialog()

    def show_full_screen_overlay(self, image_data) -> None:
        """Show the full screen image overlay."""
        self.widget_access_facade.show_full_screen_overlay(image_data)

    def enable_image_drag_drop(self) -> None:
        """Enable image drag and drop functionality."""
        if hasattr(self, "image_drag_drop_handler"):
            self.image_drag_drop_handler.enable()

    def disable_image_drag_drop(self) -> None:
        """Disable image drag and drop functionality."""
        if hasattr(self, "image_drag_drop_handler"):
            self.image_drag_drop_handler.disable()

    # Cleanup methods
    def cleanup(self) -> None:
        """Cleanup resources when shutting down."""
        # Cleanup event coordinator first
        if hasattr(self, "event_coordinator"):
            self.event_coordinator.disconnect_all_signals()

        self.tab_manager.cleanup()
        self.widget_manager.cleanup()
        self.state_manager.cleanup()

        # Cleanup image drag and drop
        if hasattr(self, "image_drag_drop_handler"):
            self.image_drag_drop_handler.cleanup()


class MainWidgetFactory:
    """Factory for creating MainWidget instances with proper dependency injection."""

    @staticmethod
    def create(
        main_window: "MainWindow",
        splash_screen: "SplashScreen",
        app_context: ApplicationContext,
    ) -> MainWidgetCoordinator:
        """
        Create a new MainWidget instance.

        Args:
            main_window: The parent main window
            splash_screen: The splash screen instance
            app_context: The application context with dependencies

        Returns:
            A new MainWidgetCoordinator instance
        """
        return MainWidgetCoordinator(main_window, splash_screen, app_context)
