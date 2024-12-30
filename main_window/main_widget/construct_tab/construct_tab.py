from PyQt6.QtWidgets import QFrame, QHBoxLayout, QStackedWidget
from PyQt6.QtCore import Qt, pyqtSignal
from typing import TYPE_CHECKING
from Enums.Enums import Letter
from base_widgets.base_pictograph.base_pictograph import BasePictograph
from main_window.main_widget.construct_tab.start_pos_picker.start_pos_picker import (
    StartPosPicker,
)

from .advanced_start_pos_picker.advanced_start_pos_picker import AdvancedStartPosPicker

from .add_to_sequence_manager import AddToSequenceManager
from .option_picker.option_picker import OptionPicker
from .option_picker.option_picker_click_handler import OptionPickerClickHandler

if TYPE_CHECKING:
    from main_window.main_widget.main_widget import MainWidget


class ConstructTab(QFrame):
    start_position_selected = pyqtSignal(object)

    start_pos_picker_index = 0
    advanced_start_pos_picker_index = 1
    option_picker_index = 2

    def __init__(self, main_widget: "MainWidget") -> None:
        super().__init__(main_widget)
        self.main_widget = main_widget
        self.last_beat: "BasePictograph" = None
        self.json_manager = self.main_widget.json_manager
        self.start_position_picked = False
        self.pictograph_cache: dict[Letter, dict[str, BasePictograph]] = {
            letter: {} for letter in Letter
        }

        self.option_click_handler = OptionPickerClickHandler(self)
        self.start_pos_picker = StartPosPicker(self)
        self.advanced_start_pos_picker = AdvancedStartPosPicker(self)
        self.option_picker = OptionPicker(self)
        self.add_to_sequence_manager = AddToSequenceManager(self)

        self.layout: QHBoxLayout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.setLayout(self.layout)
        self.setContentsMargins(0, 0, 0, 0)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background: transparent;")

    def transition_to_option_picker(self):
        """Transition to the option picker for sequence building."""
        self.main_widget.fade_manager.fade_to_tab(
            self.main_widget.right_stack, self.main_widget.right_option_picker_index
        )

        self.option_picker.scroll_area.section_manager.display_sections()
        self.option_picker.update_option_picker()

    def transition_to_advanced_start_pos_picker(self) -> None:
        """Transition to the advanced start position picker."""
        self.main_widget.fade_manager.fade_to_tab(
            self.main_widget.right_stack, self.advanced_start_pos_picker_index
        )
        self.advanced_start_pos_picker.display_variations()

    def reset_to_start_pos_picker(self) -> None:
        """Reset the view back to the start position picker."""
        self.main_widget.fade_manager.fade_to_tab(
            self.main_widget.right_stack, self.start_pos_picker_index
        )
