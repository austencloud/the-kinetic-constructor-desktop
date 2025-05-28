from typing import TYPE_CHECKING, Union

from main_window.main_widget.sequence_workbench.sequence_beat_frame.beat import Beat
from base_widgets.pictograph.elements.views.beat_view import (
    BeatView,
)

if TYPE_CHECKING:
    from main_window.main_widget.sequence_workbench.sequence_beat_frame.sequence_beat_frame import (
        SequenceBeatFrame,
    )
    from .image_export_manager import ImageExportManager

    from main_window.main_widget.browse_tab.temp_beat_frame.temp_beat_frame import (
        TempBeatFrame,
    )


class ImageExportBeatFactory:
    def __init__(
        self,
        export_manager: "ImageExportManager",
        beat_frame_class: Union["SequenceBeatFrame", "TempBeatFrame"],
    ):
        self.export_manager = export_manager
        self.beat_frame_class = beat_frame_class

    def process_sequence_to_beats(self, sequence: list[dict]) -> list[BeatView]:

        if self.beat_frame_class.__name__ == "SequenceBeatFrame":
            temp_beat_frame = self.beat_frame_class(
                self.export_manager.main_widget.sequence_workbench
            )
        elif self.beat_frame_class.__name__ == "TempBeatFrame":
            temp_beat_frame = self.beat_frame_class(
                self.export_manager.main_widget.browse_tab
            )

        filled_beats = []
        current_beat_number = 1

        for beat_data in sequence[2:]:

            if beat_data.get("is_placeholder"):
                continue

            duration = beat_data.get("duration", 1)

            beat_view = self.create_beat_view_from_data(
                beat_data, current_beat_number, temp_beat_frame
            )

            filled_beats.append(beat_view)

            current_beat_number += duration

        return filled_beats

    def create_beat_view_from_data(self, beat_data, number, temp_beat_frame):
        new_beat_view = BeatView(temp_beat_frame)
        beat = Beat(temp_beat_frame)
        beat.state.pictograph_data = beat_data
        beat.managers.updater.update_pictograph(beat_data)
        new_beat_view.set_beat(beat, number)
        return new_beat_view
