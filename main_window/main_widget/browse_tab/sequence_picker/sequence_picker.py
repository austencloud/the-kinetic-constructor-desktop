from typing import TYPE_CHECKING
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout

from main_window.main_widget.browse_tab.sequence_picker.sequence_picker_thumbnail_box_sorter import (
    SequencePickerThumbnailBoxSorter,
)
from .sequence_picker_control_panel import SequencePickerControlPanel
from .filter_selector.sequence_picker_filter_selector import (
    SequencePickerFilterSelector,
)
from .sequence_picker_progress_bar import SequencePickerProgressBar
from .sequence_picker_nav_sidebar import SequencePickerNavSidebar
from .sequence_picker_scroll_widget import SequencePickerScrollWidget

if TYPE_CHECKING:
    from ..browse_tab import BrowseTab


class SequencePicker(QWidget):
    def __init__(self, browse_tab: "BrowseTab"):
        super().__init__(browse_tab)
        self.browse_tab = browse_tab
        self.main_widget = browse_tab.main_widget
        self._setup_ui()

    def _setup_ui(self):
        self.progress_bar = SequencePickerProgressBar(self)
        self.control_panel = SequencePickerControlPanel(self)
        self.scroll_widget = SequencePickerScrollWidget(self)
        self.nav_sidebar = SequencePickerNavSidebar(self)
        self.filter_selector = SequencePickerFilterSelector(self)
        self.thumbnail_box_sorter = SequencePickerThumbnailBoxSorter(self)

        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.addWidget(self.nav_sidebar, 1)
        content_layout.addWidget(self.scroll_widget, 9)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.main_layout.addWidget(self.control_panel)
        self.main_layout.addLayout(content_layout)

        self.setLayout(self.main_layout)
