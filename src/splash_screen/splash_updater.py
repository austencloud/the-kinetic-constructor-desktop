from typing import TYPE_CHECKING
from PyQt6.QtWidgets import QApplication

if TYPE_CHECKING:
    from .splash_screen import SplashScreen


class SplashUpdater:
    """Manages progress updates for the splash screen."""

    def __init__(self, splash_screen: "SplashScreen"):
        self.splash_screen = splash_screen
        self.widget_messages = {
            "MenuBarWidget": "Initializing menu...",
            "NavigationWidget": "Setting up navigation...",
            "SequenceWorkbench": "Loading sequences...",
            "BrowseTabPreloading": "Pre-loading browse tab data...",
            "BrowseTab": "Building dictionary...",
            "LearnTab": "Preparing lessons...",
            "WriteTab": "Setting up Act Tab...",
            "ConstructTab": "Loading construct tab...",
            "GenerateTab": "Setting up generate tab...",
            "Finalizing": "Finalizing setup...",
        }
        self.current_progress = 0
        self.widget_progress_increment = 100 // len(self.widget_messages)

    def update_progress(self, widget_name: str):
        """Update the progress bar and message based on the widget being initialized."""
        self.current_progress = min(
            100, self.current_progress + self.widget_progress_increment
        )
        self.splash_screen.progress_bar.set_value(self.current_progress)
        message = self.widget_messages.get(widget_name, "Loading components...")
        self.splash_screen.currently_loading_label.setText(message)
        # Process events to keep splash screen responsive
        from PyQt6.QtWidgets import QApplication

        QApplication.processEvents()

    def update_detailed_progress(self, message: str, progress_percent: int):
        """Update progress with detailed message and specific percentage."""
        self.splash_screen.progress_bar.set_value(progress_percent)
        self.splash_screen.currently_loading_label.setText(message)
        # Process events to keep splash screen responsive
        from PyQt6.QtWidgets import QApplication

        QApplication.processEvents()
