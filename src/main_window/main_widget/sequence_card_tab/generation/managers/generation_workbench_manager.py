import logging
from typing import TYPE_CHECKING, Optional


from main_window.main_widget.browse_tab.temp_beat_frame.temp_beat_frame import (
    TempBeatFrame,
)
from ..temp_sequence_workbench import TempSequenceWorkbench

if TYPE_CHECKING:
    from main_window.main_widget.main_widget import MainWidget


class GenerationWorkbenchManager:
    def __init__(self, main_widget: "MainWidget"):
        self.main_widget = main_widget
        self.logger = logging.getLogger(__name__)

    def create_temp_workbench(self) -> Optional[TempSequenceWorkbench]:
        try:
            mock_browse_tab = self._create_mock_browse_tab()
            temp_beat_frame = TempBeatFrame(mock_browse_tab)
            temp_workbench = TempSequenceWorkbench(temp_beat_frame)

            self.logger.info(
                "Created fresh temporary beat frame wrapped for sequence builder compatibility"
            )
            return temp_workbench
        except Exception as e:
            self.logger.error(f"Error creating temporary beat frame: {e}")
            return None

    def _create_mock_browse_tab(self):
        class MockBrowseTab:
            def __init__(self, main_widget):
                self.main_widget = main_widget

        return MockBrowseTab(self.main_widget)

    def extract_sequence_data(
        self, temp_workbench: TempSequenceWorkbench
    ) -> Optional[list]:
        try:
            temp_beat_frame = temp_workbench.beat_frame

            if not hasattr(temp_beat_frame, "json_manager"):
                self.logger.error("Temporary beat frame missing json_manager")
                return None

            current_sequence = (
                temp_beat_frame.json_manager.loader_saver.load_current_sequence()
            )

            if not current_sequence or len(current_sequence) < 3:
                self.logger.error(
                    f"Invalid sequence data: length={len(current_sequence) if current_sequence else 0}"
                )
                return None

            self.logger.info(f"Extracted sequence data: {len(current_sequence)} beats")
            return current_sequence

        except Exception as e:
            self.logger.error(f"Error extracting generated sequence: {e}")
            return None
