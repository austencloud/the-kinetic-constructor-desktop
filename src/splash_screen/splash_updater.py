from typing import TYPE_CHECKING
from PyQt6.QtWidgets import QApplication
from .monotonic_progress_coordinator import MonotonicProgressCoordinator

if TYPE_CHECKING:
    from .splash_screen import SplashScreen


class SplashUpdater:
    """Manages progress updates for the splash screen with monotonic progress coordination."""

    def __init__(self, splash_screen: "SplashScreen"):
        self.splash_screen = splash_screen

        # Legacy widget messages for backward compatibility
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
            "OptimizedStartup": "Optimizing startup...",
            "Finalizing": "Finalizing setup...",
        }

        # Initialize monotonic progress coordinator
        self.progress_coordinator = MonotonicProgressCoordinator(
            progress_callback=self._update_splash_display
        )

        # Legacy compatibility
        self.current_progress = 0
        self.widget_progress_increment = 100 // len(self.widget_messages)

    def _update_splash_display(self, progress: int, message: str):
        """Internal callback to update the splash screen display."""
        self.splash_screen.progress_bar.set_value(progress)
        self.splash_screen.currently_loading_label.setText(message)
        QApplication.processEvents()

    def update_progress(self, widget_name: str):
        """Update the progress bar and message based on the widget being initialized (legacy method)."""
        # Legacy incremental progress for backward compatibility
        self.current_progress = min(
            100, self.current_progress + self.widget_progress_increment
        )
        message = self.widget_messages.get(widget_name, "Loading components...")

        # Use monotonic coordinator to ensure progress only moves forward
        self.progress_coordinator.set_absolute_progress(self.current_progress, message)

    def update_detailed_progress(self, message: str, progress_percent: int):
        """Update progress with detailed message and specific percentage."""
        # Use monotonic coordinator to ensure progress only moves forward
        self.progress_coordinator.set_absolute_progress(progress_percent, message)

    # New methods for phase-based progress tracking
    def start_phase(
        self, phase_name: str, total_steps: int = 1, message: str = ""
    ) -> bool:
        """Start a new initialization phase."""
        return self.progress_coordinator.start_phase(phase_name, total_steps, message)

    def update_phase_progress(self, step_increment: int = 1, message: str = "") -> None:
        """Update progress within the current phase."""
        self.progress_coordinator.update_phase_progress(step_increment, message)

    def update_phase_progress_incremental(
        self, progress_within_phase: float, message: str = ""
    ) -> None:
        """Update progress within the current phase using a percentage (0.0-1.0)."""
        self.progress_coordinator.update_phase_progress_incremental(
            progress_within_phase, message
        )

    def complete_phase(self, message: str = "") -> None:
        """Complete the current phase."""
        self.progress_coordinator.complete_phase(message)

    def get_current_progress(self) -> tuple[int, str]:
        """Get current progress and message."""
        return self.progress_coordinator.get_current_progress()
