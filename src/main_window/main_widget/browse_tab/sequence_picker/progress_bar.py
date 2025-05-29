from typing import TYPE_CHECKING

from ...rainbow_progress_bar import RainbowProgressBar

if TYPE_CHECKING:
    from .sequence_picker import SequencePicker


class SequencePickerProgressBar(RainbowProgressBar):
    def __init__(self, sequence_picker: "SequencePicker") -> None:
        super().__init__(sequence_picker)
        self.sequence_picker = sequence_picker
        self.hide()

    def resizeEvent(self, event):
        self.resize_progress_bar()
        super().resizeEvent(event)

    def resize_progress_bar(self):
        """We need this so we"""
        self.setFixedWidth(self.sequence_picker.width() // 3)
        self.setFixedHeight(self.sequence_picker.height() // 6)
        font = self.percentage_label.font()
        font.setFamily("Monotype Corsiva")
        font.setPointSize(self.sequence_picker.main_widget.width() // 80)
        self.percentage_label.setFont(font)
        self.loading_label.setFont(font)
