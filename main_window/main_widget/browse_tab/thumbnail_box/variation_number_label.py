from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel

from typing import TYPE_CHECKING, Union



if TYPE_CHECKING:
    from main_window.main_widget.browse_tab.thumbnail_box.thumbnail_box import ThumbnailBox
    from main_window.main_widget.browse_tab.browse_tab_preview_area import (
        BrowseTabPreviewArea,
    )


class VariationNumberLabel(QLabel):
    def __init__(self, parent: Union["ThumbnailBox", "BrowseTabPreviewArea"]):
        super().__init__(parent)
        if len(parent.thumbnails) > 1:
            self.setText(f"{parent.current_index + 1}/{len(parent.thumbnails)}")
        else:
            self.hide()
        self.parent: Union["ThumbnailBox", "BrowseTabPreviewArea"] = parent
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def update_index(self, index):
        if len(self.parent.thumbnails) > 1:
            self.setText(f"{index + 1}/{len(self.parent.thumbnails)}")
        else:
            self.hide()

    def clear(self) -> None:
        self.setText("")

    def resizeEvent(self, event):
        font = self.font()
        font.setPointSize(self.parent.browse_tab.main_widget.width() // 100)
        font.setBold(True)
        self.setFont(font)
        super().resizeEvent(event)