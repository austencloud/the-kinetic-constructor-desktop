from typing import TYPE_CHECKING
from PyQt6.QtWidgets import QVBoxLayout, QWidget, QApplication
from PyQt6.QtGui import QPixmap

from main_window.main_widget.browse_tab.thumbnail_box.favorites_manager import (
    FavoritesManager,
)
from main_window.main_widget.browse_tab.thumbnail_box.word_label import WordLabel
from main_window.main_widget.write_tab.act_browser.act_thumbnail_image_label import (
    ActThumbnailImageLabel,
)


if TYPE_CHECKING:
    from main_window.main_widget.write_tab.act_browser.act_browser import ActBrowser


class ActThumbnailBox(QWidget):
    def __init__(self, browser: "ActBrowser", word: str, thumbnails) -> None:
        super().__init__(browser)
        self.browser = browser
        self.word = word
        self.thumbnails = thumbnails
        self.main_widget = browser.act_tab.main_widget
        self.current_index = 0
        self.margin = 10

        self.favorites_manager = FavoritesManager(self)

        self.word_label = WordLabel(self)
        self.image_label = ActThumbnailImageLabel(self)

        self._setup_layout()

    def _setup_layout(self):
        self.setContentsMargins(0, 0, 0, 0)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # No margins in the layout
        layout.addWidget(self.word_label)
        layout.addWidget(self.image_label)
        self.setLayout(layout)

    def toggle_favorite_status(self):
        self.favorite_status = not self.favorite_status
        self.word_label.update_favorite_icon(self.favorite_status)
        QApplication.processEvents()
        self.save_favorite_status()

    def load_favorite_status(self):
        if self.thumbnails:
            first_thumbnail = self.thumbnails[0]
            self.favorite_status = (
                self.main_widget.metadata_extractor.get_favorite_status(first_thumbnail)
            )

    def save_favorite_status(self):
        for thumbnail in self.thumbnails:
            self.main_widget.metadata_extractor.set_favorite_status(
                thumbnail, self.favorite_status
            )

    def resizeEvent(self, event):
        """Dynamically adjust the size of the thumbnail box."""

        scroll_bar_width = self.browser.verticalScrollBar().width()
        browser_width = self.browser.width() - scroll_bar_width
        thumbnail_width = int(browser_width * 0.45)
        self.setFixedWidth(thumbnail_width)

        image = QPixmap(self.thumbnails[0])
        image = image.scaledToWidth(thumbnail_width)
        self.image_label.setPixmap(image)
