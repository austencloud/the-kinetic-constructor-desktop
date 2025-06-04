import os
from typing import TYPE_CHECKING
from PyQt6.QtWidgets import QMainWindow, QApplication
from PyQt6.QtCore import Qt
import logging

from main_window.palette_manager import PaletteManager
from main_window.main_window_geometry_manager import MainWindowGeometryManager
from main_window.main_widget.core.main_widget_coordinator import MainWidgetFactory

if TYPE_CHECKING:
    from profiler import Profiler
    from splash_screen.splash_screen import SplashScreen
    from core.application_context import ApplicationContext

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(
        self,
        profiler: "Profiler",
        splash_screen: "SplashScreen",
        app_context: "ApplicationContext",
    ) -> None:
        super().__init__()
        self.profiler = profiler
        self.app_context = app_context
        # PERFORMANCE FIX: Handle None splash screen for instant startup
        self.splash_screen = splash_screen
        self.main_widget = None  # Initialize main_widget to None

        # IMPORTANT: Set the MainWindow reference in AppContext immediately
        # This prevents timing issues during widget initialization
        try:
            from src.settings_manager.global_settings.app_context import AppContext

            AppContext.set_main_window(self)
            logger.info("MainWindow reference set in AppContext")
        except Exception as e:
            logger.warning(f"Failed to set MainWindow reference in AppContext: {e}")

        # Initialize managers
        self.palette_manager = PaletteManager(self)
        self.geometry_manager = MainWindowGeometryManager(self)

        # Configure window (but don't create widgets yet)
        self.setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents, True)
        self.setWindowTitle("The Kinetic Constructor")
        self.geometry_manager.set_dimensions()

        logger.info("MainWindow initialized (widgets will be created separately)")

    def initialize_widgets(self) -> None:
        """
        Initialize the main widget and all child widgets.

        This method should be called AFTER the dependency injection system
        and legacy compatibility are fully set up to avoid circular dependencies.
        """
        if self.main_widget is not None:
            logger.warning("Widgets already initialized, skipping re-initialization")
            return

        logger.info("Initializing MainWindow widgets...")

        # Create main widget using dependency injection (this creates the coordinator but doesn't initialize components)
        self.main_widget = MainWidgetFactory.create(
            self, self.splash_screen, self.app_context
        )

        # Set the central widget
        self.setCentralWidget(self.main_widget)

        # Now initialize the components (this is where the circular dependency was occurring)
        logger.info("Initializing MainWidget components...")
        self.main_widget.initialize_components()

        logger.info("MainWindow widgets initialized successfully")

    def exec(self, app: QApplication) -> int:
        self.profiler.enable()
        result = app.exec()
        self.profiler.disable()
        self.profiler.write_profiling_stats_to_file("profiling_output.txt", os.getcwd())
        return result

    def closeEvent(self, event):
        super().closeEvent(event)
        QApplication.instance().installEventFilter(self)
