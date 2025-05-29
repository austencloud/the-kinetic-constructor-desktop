from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtWidgets import QWidget, QHBoxLayout
from typing import TYPE_CHECKING

from main_window.main_widget.browse_tab.thumbnail_box.favorite_button import (
    FavoriteButton,
)
from main_window.main_widget.browse_tab.thumbnail_box.word_label import (
    ThumbnailBoxWordLabel,
)
from src.settings_manager.global_settings.app_context import AppContext
from .difficulty_label import ThumbnailBoxDifficultyLabel

if TYPE_CHECKING:
    from .thumbnail_box import ThumbnailBox


class ThumbnailBoxHeader(QWidget):
    def __init__(self, thumbnail_box: "ThumbnailBox"):
        super().__init__(thumbnail_box)
        self.thumbnail_box = thumbnail_box
        self.setContentsMargins(0, 0, 0, 0)
        self.setFixedHeight(60)
        self.settings_manager = AppContext.settings_manager()

        self.difficulty_label = ThumbnailBoxDifficultyLabel(thumbnail_box)
        self.word_label = ThumbnailBoxWordLabel(
            thumbnail_box.word, self, self.settings_manager
        )
        self.favorite_button = FavoriteButton(thumbnail_box)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 0, 5, 0)

        layout.addWidget(self.difficulty_label, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addStretch(1)
        layout.addWidget(self.word_label)
        layout.addStretch(1)
        layout.addWidget(self.favorite_button, alignment=Qt.AlignmentFlag.AlignRight)

        self.setLayout(layout)

    def resizeEvent(self, event: QEvent) -> None:
        self.difficulty_label.setFixedSize(self.favorite_button.size())
        super().resizeEvent(event)

    def hide_favorite_button(self):
        """Hide the favorite button when no thumbnail is shown."""
        self.favorite_button.hide()

    def show_favorite_button(self):
        """Show the favorite button when a thumbnail is shown."""
        self.favorite_button.show()
