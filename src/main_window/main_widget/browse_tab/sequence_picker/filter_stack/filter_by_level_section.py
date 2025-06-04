from typing import TYPE_CHECKING

from PyQt6.QtCore import QEvent
from main_window.main_widget.browse_tab.sequence_picker.filter_stack.level_resize_handler import (
    LevelResizeHandler,
)
from utils.path_helpers import get_image_path

from .filter_section_base import FilterSectionBase
from .level_data_manager import LevelDataManager
from .level_image_handler import LevelImageHandler
from .level_ui_manager import LevelUIManager

if TYPE_CHECKING:
    from .sequence_picker_filter_stack import SequencePickerFilterStack


class FilterByLevelSection(FilterSectionBase):
    def __init__(self, filter_selector: "SequencePickerFilterStack"):
        super().__init__(filter_selector, "Select by Difficulty Level:")
        self.main_widget = filter_selector.browse_tab.main_widget

        self.data_manager = LevelDataManager()
        self.image_handler = LevelImageHandler(
            get_image_path("level_images"), self.main_widget, self.handle_level_click
        )
        self.ui = LevelUIManager(self, self.data_manager, self.image_handler)
        self.resize_handler = LevelResizeHandler(self, self.ui, self.image_handler)

        self.ui.setup_ui()

    def handle_level_click(self, level: int) -> None:
        # INSTANT SWITCHING: Create instant handler for level clicks
        instant_handler = self.create_instant_button_handler(
            lambda: self.browse_tab.filter_controller.apply_filter({"level": level}),
            f"Level: {level}",
        )
        instant_handler()

    def resizeEvent(self, event: QEvent) -> None:
        self.resize_handler.handle_resize()
        super().resizeEvent(event)
