"""
Temporary Sequence Workbench for isolated generation operations.

Provides a minimal workbench interface for sequence generation without
affecting the main sequence workbench state.
"""

import logging
from typing import TYPE_CHECKING, Optional
from PyQt6.QtWidgets import QWidget

if TYPE_CHECKING:
    from main_window.main_widget.sequence_workbench.sequence_beat_frame.sequence_beat_frame import (
        SequenceBeatFrame,
    )

logger = logging.getLogger(__name__)


class TempSequenceWorkbench(QWidget):
    """
    Temporary sequence workbench for isolated generation operations.

    This provides a minimal interface compatible with the main sequence workbench
    but operates in isolation for generation purposes.
    """

    def __init__(self, beat_frame: "SequenceBeatFrame"):
        super().__init__()
        self.beat_frame = beat_frame
        self.main_widget = getattr(beat_frame, "main_widget", None)

        # Initialize minimal components needed for generation
        self._setup_minimal_interface()

        logger.info("TempSequenceWorkbench created for isolated generation")

    def _setup_minimal_interface(self):
        """Setup minimal interface components needed for generation."""
        # This workbench is primarily used as a container for the beat_frame
        # during isolated generation operations
        pass

    def get_current_sequence_length(self) -> int:
        """Get the current sequence length from the beat frame."""
        try:
            if hasattr(self.beat_frame, "json_manager"):
                sequence = (
                    self.beat_frame.json_manager.loader_saver.load_current_sequence()
                )
                return len([item for item in sequence if item.get("beat", 0) > 0])
            return 0
        except Exception as e:
            logger.warning(f"Could not get sequence length: {e}")
            return 0

    def get_beat_frame(self) -> "SequenceBeatFrame":
        """Get the associated beat frame."""
        return self.beat_frame

    def cleanup(self):
        """Cleanup resources when done with isolated generation."""
        logger.info("TempSequenceWorkbench cleaned up")
