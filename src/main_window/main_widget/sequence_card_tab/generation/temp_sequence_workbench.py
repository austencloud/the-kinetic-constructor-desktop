from typing import TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from main_window.main_widget.browse_tab.temp_beat_frame.temp_beat_frame import (
        TempBeatFrame,
    )

from .temp_populator import TempPopulator
from .temp_beat_factory import TempBeatFactory


class TempSequenceWorkbench:
    def __init__(self, temp_beat_frame: "TempBeatFrame"):
        self.beat_frame = temp_beat_frame
        self.temp_beat_frame = temp_beat_frame
        self._add_missing_beat_frame_attributes()

    def _add_missing_beat_frame_attributes(self):
        if not hasattr(self.beat_frame, "populator"):
            self.beat_frame.populator = TempPopulator(self.beat_frame)

        if not hasattr(self.beat_frame, "beat_factory"):
            self.beat_frame.beat_factory = TempBeatFactory(self.beat_frame)
            logging.info(
                "Added TempBeatFactory to beat_frame for circular generation compatibility"
            )

        if not hasattr(self.beat_frame, "emit_update_image_export_preview"):

            def emit_update_image_export_preview():
                pass

            self.beat_frame.emit_update_image_export_preview = (
                emit_update_image_export_preview
            )

    def emit_update_image_export_preview(self):
        pass

    def __getattr__(self, name):
        return getattr(self.temp_beat_frame, name)
