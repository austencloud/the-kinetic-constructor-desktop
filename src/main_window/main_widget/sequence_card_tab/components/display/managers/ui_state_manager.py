import logging
from typing import TYPE_CHECKING
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

if TYPE_CHECKING:
    from ....tab import SequenceCardTab


class UIStateManager:
    def __init__(self, sequence_card_tab: "SequenceCardTab"):
        self.sequence_card_tab = sequence_card_tab
        self.logger = logging.getLogger(__name__)

    def set_loading_cursor(self):
        self.sequence_card_tab.setCursor(Qt.CursorShape.WaitCursor)

    def set_normal_cursor(self):
        self.sequence_card_tab.setCursor(Qt.CursorShape.ArrowCursor)

    def update_header_text(self, text: str):
        self.sequence_card_tab.header.description_label.setText(text)

    def show_progress_bar(self, total: int = 0):
        if hasattr(self.sequence_card_tab.header, "progress_bar"):
            self.sequence_card_tab.header.progress_bar.setValue(0)
            if total > 0:
                self.sequence_card_tab.header.progress_bar.setRange(0, total)
            self.sequence_card_tab.header.progress_bar.show()

            if hasattr(self.sequence_card_tab.header, "progress_container"):
                self.sequence_card_tab.header.progress_container.setVisible(True)
            QApplication.processEvents()

    def update_progress(self, current: int):
        if hasattr(self.sequence_card_tab.header, "progress_bar"):
            self.sequence_card_tab.header.progress_bar.setValue(current)

    def hide_progress_bar(self):
        if hasattr(self.sequence_card_tab.header, "progress_bar"):
            self.sequence_card_tab.header.progress_bar.hide()
            if hasattr(self.sequence_card_tab.header, "progress_container"):
                self.sequence_card_tab.header.progress_container.setVisible(False)

    def format_filter_description(self, length: int, levels: list) -> str:
        length_text = f"{length}-step" if length > 0 else "all"

        if levels and len(levels) < 3:
            level_names = {1: "Basic", 2: "Intermediate", 3: "Advanced"}
            level_text = ", ".join([level_names[lvl] for lvl in sorted(levels)])
            return f"{length_text} sequences (Levels: {level_text})"
        else:
            return f"{length_text} sequences"
