from typing import TYPE_CHECKING, Union
from PyQt6.QtWidgets import QWidget

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
        beat_frame_class: Union["SequenceBeatFrame", TempBeatFrame],
    ):
        self.export_manager = export_manager
        self.beat_frame_class = beat_frame_class

    def process_sequence_to_beats(self, sequence: list[dict]) -> list[BeatView]:
        if self.beat_frame_class.__name__ == "SequenceBeatFrame":
            temp_beat_frame = self.beat_frame_class(
                self.export_manager.main_widget.sequence_workbench
            )
        else:
            # For TempBeatFrame, we need to create a proper instance with main_widget
            # The issue is that TempBeatFrame needs proper infrastructure to create BeatViews
            class MockParent:
                def __init__(self, main_widget):
                    self.main_widget = main_widget

            actual_main_widget = self._get_actual_main_widget()
            mock_parent = MockParent(actual_main_widget)
            temp_beat_frame = self.beat_frame_class(mock_parent)

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

    def _get_actual_main_widget(self):
        try:
            main_widget = self.export_manager.main_widget
            if hasattr(main_widget, "main_widget"):
                return main_widget.main_widget
            if hasattr(main_widget, "widget_manager") or hasattr(
                main_widget, "tab_manager"
            ):
                return main_widget
            current = main_widget
            while current and hasattr(current, "parent"):
                parent = current.parent()
                if parent and (
                    hasattr(parent, "widget_manager") or hasattr(parent, "tab_manager")
                ):
                    return parent
                current = parent
            return main_widget
        except Exception:
            return self.export_manager.main_widget

    def create_beat_view_from_data(self, beat_data, number, temp_beat_frame):
        new_beat_view = BeatView(temp_beat_frame)
        beat = Beat(temp_beat_frame)
        beat.state.pictograph_data = beat_data
        beat.managers.updater.update_pictograph(beat_data)
        new_beat_view.set_beat(beat, number)
        return new_beat_view
