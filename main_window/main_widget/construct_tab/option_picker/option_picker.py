from typing import TYPE_CHECKING, Callable
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import pyqtSignal, QSize

from main_window.main_widget.construct_tab.add_to_sequence_manager import (
    AddToSequenceManager,
)
from main_window.main_widget.construct_tab.option_picker.option_view import OptionView
from main_window.main_widget.fade_manager.fade_manager import FadeManager
from main_window.settings_manager.global_settings.app_context import AppContext
from .option_scroll.option_scroll import OptionScroll
from .option_factory import OptionFactory
from .option_picker_layout_manager import OptionPickerLayoutManager
from .option_updater import OptionUpdater
from .option_click_handler import OptionClickHandler
from .reversal_filter.option_picker_reversal_filter import OptionPickerReversalFilter
from .option_getter import OptionGetter
from .choose_your_next_pictograph_label import ChooseYourNextPictographLabel
from base_widgets.pictograph.pictograph_scene import PictographScene

if TYPE_CHECKING:
    from ..construct_tab import ConstructTab


class OptionPicker(QWidget):
    COLUMN_COUNT = 8
    option_selected = pyqtSignal(str)
    layout: QVBoxLayout
    option_pool: list["PictographScene"]

    def __init__(
        self,
        add_to_sequence_manager: "AddToSequenceManager",
        pictograph_dataset: dict,
        beat_frame,
        mw_size_provider: Callable[[], QSize],
        fade_manager: "FadeManager",
    ):
        super().__init__()
        self.add_to_sequence_manager = add_to_sequence_manager
        # Components
        self.choose_next_label = ChooseYourNextPictographLabel(mw_size_provider)
        self.reversal_filter = OptionPickerReversalFilter(mw_size_provider)

        self.option_scroll = OptionScroll(self, mw_size_provider)

        # Managers
        self.option_getter = OptionGetter(pictograph_dataset)
        self.click_handler = OptionClickHandler(self, beat_frame)
        self.updater = OptionUpdater(self, fade_manager)
        self.option_factory = OptionFactory(self, mw_size_provider)
        self.layout_manager = OptionPickerLayoutManager(self)

    def resizeEvent(self, event):
        for option in self.option_pool:
            option.view.resize_option_view()
