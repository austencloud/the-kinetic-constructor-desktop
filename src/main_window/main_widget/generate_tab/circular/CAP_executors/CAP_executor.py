from typing import TYPE_CHECKING
from data.constants import *
from main_window.main_widget.generate_tab.circular.CAP_executors.CAP_type import CAPType
from PyQt6.QtWidgets import QApplication

if TYPE_CHECKING:
    from ..circular_sequence_builder import CircularSequenceBuilder


class CAPExecutor:
    """Base class for all CAP executors, handling shared logic."""

    CAP_TYPE: CAPType | None = None

    def __init__(self, circular_sequence_generator: "CircularSequenceBuilder"):
        self.circular_sequence_generator = circular_sequence_generator

    def create_CAPs(self, sequence: list[dict], **kwargs):
        """Handles generic CAP creation, using specialized logic from subclasses."""
        if not self.can_perform_CAP(sequence):
            return

        sequence_length = len(sequence) - 2
        last_entry = sequence[-1]
        next_beat_number = last_entry[BEAT] + 1
        final_intended_sequence_length = (
            sequence_length + self.determine_how_many_entries_to_add(sequence_length)
        )

        for i in range(2, sequence_length + 2):  # Skip first two beats
            next_pictograph = self.create_new_CAP_entry(
                sequence,
                last_entry,
                next_beat_number + i - 2,
                final_intended_sequence_length,
                **kwargs
            )
            sequence.append(next_pictograph)
            last_entry = next_pictograph

            # Add to UI
            sequence_workbench = self.circular_sequence_generator.sequence_workbench
            sequence_workbench.beat_frame.beat_factory.create_new_beat_and_add_to_sequence(
                next_pictograph,
                override_grow_sequence=True,
                update_word=False,
                update_image_export_preview=False,
            )
            QApplication.processEvents()

    def determine_how_many_entries_to_add(self, sequence_length: int) -> int:
        """Determines how many entries need to be added for full circularity. Can be overridden."""
        return sequence_length  # Default behavior

    def can_perform_CAP(self, sequence: list[dict]) -> bool:
        """Subclasses should define their own validation logic."""
        return True

    def create_new_CAP_entry(
        self,
        sequence,
        previous_entry,
        beat_number: int,
        final_intended_sequence_length: int,
        **kwargs
    ) -> dict:
        """Subclasses must implement logic for CAP transformation."""
        raise NotImplementedError("Subclasses must implement create_new_CAP_entry.")

    def get_previous_matching_beat(
        self, sequence: list[dict], beat_number: int, final_length: int
    ) -> dict:
        """Fetch the previous matching beat using an index map."""
        index_map = self.get_index_map(final_length)
        return sequence[index_map[beat_number]]

    def get_index_map(self, length: int) -> dict[int, int]:
        """Generate index mapping for retrieving mirrored/rotated beats."""
        return {i: i - (length // 2) + 1 for i in range((length // 2) + 1, length + 1)}

    def swap_colors(self, beat: dict) -> dict:
        """Swaps blue and red attributes if needed."""
        beat[BLUE_ATTRS], beat[RED_ATTRS] = beat[RED_ATTRS], beat[BLUE_ATTRS]
        return beat
