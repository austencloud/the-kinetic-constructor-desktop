from typing import Callable
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import pyqtSignal, QSize

from base_widgets.pictograph.pictograph import Pictograph
from main_window.main_widget.construct_tab.add_to_sequence_manager.add_to_sequence_manager import (
    AddToSequenceManager,
)
from main_window.main_widget.construct_tab.option_picker.widgets.scroll.option_scroll import (
    OptionScroll,
)
from main_window.main_widget.fade_manager.fade_manager import FadeManager
from .choose_your_next_pictograph_label import ChooseYourNextPictographLabel
from ..core.option_factory import OptionFactory
from ..core.option_getter import OptionGetter
from ..handlers.click_handler import OptionClickHandler
from ..core.option_updater import OptionUpdater
from .reversal_filter_widget import OptionPickerReversalFilter
from ..layout.layout_manager import OptionPickerLayoutManager
from main_window.main_widget.sequence_workbench.sequence_beat_frame.sequence_beat_frame import (
    SequenceBeatFrame,
)


class OptionPicker(QWidget):
    option_selected = pyqtSignal(str)
    COLUMN_COUNT = 8

    def __init__(
        self,
        add_to_sequence_manager: "AddToSequenceManager",
        pictograph_dataset: dict,
        beat_frame: "SequenceBeatFrame",
        mw_size_provider: Callable[[], QSize],
        fade_manager: "FadeManager",
    ):
        super().__init__()
        self.add_to_sequence_manager = add_to_sequence_manager
        self.option_pool: list[Pictograph] = []
        self.choose_next_label = ChooseYourNextPictographLabel(mw_size_provider)
        self.option_scroll = OptionScroll(self, mw_size_provider)
        self.option_getter = OptionGetter(pictograph_dataset)
        self.option_click_handler = OptionClickHandler(self, beat_frame)
        self.updater = OptionUpdater(self, fade_manager)
        self.reversal_filter = OptionPickerReversalFilter(
            mw_size_provider, self.updater.update_options
        )
        self.option_factory = OptionFactory(self, mw_size_provider)
        self.layout_manager = OptionPickerLayoutManager(self)
        self.option_pool = self.option_factory.create_options()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        for section in self.option_scroll.sections.values():
            for pictograph in section.pictographs.values():
                if pictograph.elements.view.isVisible():
                    pictograph.elements.view.resize_option_view()
                    
        self.option_scroll.setFixedWidth(self.parent().parent().width() // 2)
