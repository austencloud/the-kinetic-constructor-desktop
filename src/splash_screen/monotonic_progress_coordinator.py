"""
Monotonic Progress Coordinator for Splash Screen

This module provides a centralized progress tracking system that ensures
progress only moves forward and coordinates between different initialization phases.

Key Features:
- Monotonic progress (never goes backwards)
- Phase-based progress mapping
- Integration with performance pre-initialization
- Fine-grained progress tracking
- Thread-safe progress updates
"""

import logging
import threading
import time
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ProgressPhase:
    """Represents a phase of the initialization process."""

    name: str
    start_percent: int
    end_percent: int
    current_step: int = 0
    total_steps: int = 1

    def get_current_progress(self) -> int:
        """Calculate current progress within this phase."""
        if self.total_steps <= 0:
            return self.start_percent

        phase_range = self.end_percent - self.start_percent
        step_progress = (self.current_step / self.total_steps) * phase_range
        return min(self.end_percent, self.start_percent + int(step_progress))


class MonotonicProgressCoordinator:
    """
    Coordinates progress updates across different initialization phases
    ensuring monotonic progress (never goes backwards).
    """

    def __init__(self, progress_callback: Optional[Callable[[int, str], None]] = None):
        self.progress_callback = progress_callback
        self._lock = threading.Lock()
        self._current_progress = 0
        self._current_phase: Optional[str] = None
        self._current_message = "Initializing..."

        # Progress smoothing for better UX
        self._last_update_time = time.time()
        self._min_update_interval = 0.5  # Minimum 500ms between updates for smoothing

        # Define initialization phases with their progress ranges
        self._phases: Dict[str, ProgressPhase] = {
            "pre_initialization": ProgressPhase("Pre-initialization", 0, 15),
            "performance_systems": ProgressPhase("Performance Systems", 15, 30),
            "optimized_startup": ProgressPhase("Optimized Startup", 30, 50),
            "dependency_injection": ProgressPhase("Dependency Injection", 50, 60),
            "main_window_creation": ProgressPhase("Main Window Creation", 60, 65),
            "widget_initialization": ProgressPhase("Widget Initialization", 65, 85),
            "tab_initialization": ProgressPhase("Tab Initialization", 85, 95),
            "finalization": ProgressPhase("Finalization", 95, 100),
        }

        logger.info("MonotonicProgressCoordinator initialized with phases:")
        for phase_name, phase in self._phases.items():
            logger.info(
                f"  {phase_name}: {phase.start_percent}% - {phase.end_percent}%"
            )

    def start_phase(
        self, phase_name: str, total_steps: int = 1, message: str = ""
    ) -> bool:
        """
        Start a new initialization phase.

        Args:
            phase_name: Name of the phase to start
            total_steps: Total number of steps in this phase
            message: Optional message to display

        Returns:
            True if phase was started successfully, False if phase doesn't exist
        """
        with self._lock:
            if phase_name not in self._phases:
                logger.warning(f"Unknown phase: {phase_name}")
                return False

            phase = self._phases[phase_name]

            # Only allow forward progress
            if phase.start_percent < self._current_progress:
                logger.warning(
                    f"Attempted to start phase {phase_name} ({phase.start_percent}%) "
                    f"but current progress is {self._current_progress}%"
                )
                return False

            self._current_phase = phase_name
            phase.current_step = 0
            phase.total_steps = max(1, total_steps)

            if message:
                self._current_message = message
            else:
                self._current_message = f"Starting {phase.name}..."

            self._update_progress(phase.start_percent)
            logger.info(f"Started phase: {phase_name} ({total_steps} steps)")
            return True

    def update_phase_progress(self, step_increment: int = 1, message: str = "") -> None:
        """
        Update progress within the current phase.

        Args:
            step_increment: Number of steps to increment
            message: Optional message to display
        """
        with self._lock:
            if not self._current_phase:
                logger.warning("No active phase for progress update")
                return

            phase = self._phases[self._current_phase]
            phase.current_step = min(
                phase.total_steps, phase.current_step + step_increment
            )

            if message:
                self._current_message = message

            new_progress = phase.get_current_progress()
            self._update_progress(new_progress)

    def update_phase_progress_incremental(
        self, progress_within_phase: float, message: str = ""
    ) -> None:
        """
        Update progress within the current phase using a percentage (0.0-1.0).
        This allows for smooth progress updates during long-running operations.

        Args:
            progress_within_phase: Progress within current phase (0.0 = start, 1.0 = end)
            message: Optional message to display
        """
        with self._lock:
            if not self._current_phase:
                logger.warning("No active phase for incremental progress update")
                return

            phase = self._phases[self._current_phase]
            progress_within_phase = max(0.0, min(1.0, progress_within_phase))

            # Calculate absolute progress based on phase range
            phase_range = phase.end_percent - phase.start_percent
            absolute_progress = phase.start_percent + (
                progress_within_phase * phase_range
            )

            if message:
                self._current_message = message

            # Only update if progress has increased significantly or enough time has passed
            current_time = time.time()
            progress_diff = absolute_progress - self._current_progress
            time_diff = current_time - self._last_update_time

            if progress_diff >= 1 or time_diff >= self._min_update_interval:
                self._update_progress(int(absolute_progress))
                self._last_update_time = current_time

    def complete_phase(self, message: str = "") -> None:
        """
        Complete the current phase and move to its end progress.

        Args:
            message: Optional completion message
        """
        with self._lock:
            if not self._current_phase:
                logger.warning("No active phase to complete")
                return

            phase = self._phases[self._current_phase]
            phase.current_step = phase.total_steps

            if message:
                self._current_message = message
            else:
                self._current_message = f"{phase.name} completed"

            self._update_progress(phase.end_percent)
            logger.info(f"Completed phase: {self._current_phase}")
            self._current_phase = None

    def set_absolute_progress(self, progress: int, message: str = "") -> None:
        """
        Set absolute progress value (only if it's higher than current).

        Args:
            progress: Progress percentage (0-100)
            message: Optional message to display
        """
        with self._lock:
            progress = max(0, min(100, progress))

            if progress < self._current_progress:
                logger.debug(
                    f"Ignored backwards progress: {progress}% < {self._current_progress}%"
                )
                return

            if message:
                self._current_message = message

            self._update_progress(progress)

    def _update_progress(self, progress: int) -> None:
        """
        Internal method to update progress and notify callback.
        Must be called with lock held.
        """
        if progress > self._current_progress:
            self._current_progress = progress

            if self.progress_callback:
                try:
                    self.progress_callback(progress, self._current_message)
                except Exception as e:
                    logger.error(f"Error in progress callback: {e}")

    def get_current_progress(self) -> tuple[int, str]:
        """
        Get current progress and message.

        Returns:
            Tuple of (progress_percent, message)
        """
        with self._lock:
            return self._current_progress, self._current_message

    def get_phase_info(self, phase_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific phase.

        Args:
            phase_name: Name of the phase

        Returns:
            Dictionary with phase information or None if phase doesn't exist
        """
        with self._lock:
            if phase_name not in self._phases:
                return None

            phase = self._phases[phase_name]
            return {
                "name": phase.name,
                "start_percent": phase.start_percent,
                "end_percent": phase.end_percent,
                "current_step": phase.current_step,
                "total_steps": phase.total_steps,
                "current_progress": phase.get_current_progress(),
                "is_active": self._current_phase == phase_name,
            }

    def get_all_phases_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all phases."""
        return {
            phase_name: self.get_phase_info(phase_name)
            for phase_name in self._phases.keys()
        }
