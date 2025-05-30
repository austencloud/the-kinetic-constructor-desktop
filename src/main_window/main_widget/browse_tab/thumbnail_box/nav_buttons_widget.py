from typing import TYPE_CHECKING
from PyQt6.QtWidgets import QPushButton, QWidget, QHBoxLayout

from main_window.main_widget.browse_tab.thumbnail_box.nav_button import (
    ThumbnailBoxNavButton,
)

if TYPE_CHECKING:
    from main_window.main_widget.browse_tab.thumbnail_box.thumbnail_box import (
        ThumbnailBox,
    )


class ThumbnailBoxNavButtonsWidget(QWidget):
    def __init__(self, thumbnail_box: "ThumbnailBox"):
        super().__init__(thumbnail_box)
        self.thumbnail_box = thumbnail_box
        self.state = thumbnail_box.state
        self.thumbnail_label = thumbnail_box.image_label
        self.variation_number_label = thumbnail_box.variation_number_label

        self._setup_layout()

        self.has_multiple_thumbnails = len(self.state.thumbnails) > 1
        if not self.has_multiple_thumbnails:
            self.hide()

    def _setup_layout(self):
        layout = QHBoxLayout(self)
        layout.setSpacing(10)  # Moderate spacing
        layout.setContentsMargins(5, 0, 5, 0)

        self.left_button = ThumbnailBoxNavButton("⮜", self)
        self.right_button = ThumbnailBoxNavButton("⮞", self)

        layout.addStretch(1)
        layout.addWidget(self.left_button)
        layout.addWidget(self.variation_number_label)  # Centered label
        layout.addWidget(self.right_button)
        layout.addStretch(1)

        self.setLayout(layout)

    def handle_button_click(self):
        sender: QPushButton = self.sender()
        if sender.text() in ("⮜", "←"):
            self.state.current_index = (self.state.current_index - 1) % len(
                self.state.thumbnails
            )
        else:
            self.state.current_index = (self.state.current_index + 1) % len(
                self.state.thumbnails
            )

        self.update_thumbnail(self.state.current_index)
        sequence_viewer = self.thumbnail_box.browse_tab.sequence_viewer
        if self.thumbnail_box.in_sequence_viewer:
            sequence_viewer.state.matching_thumbnail_box.image_label.update_thumbnail(
                self.state.current_index
            )
        else:
            sequence_viewer.thumbnail_box.state.current_index = self.state.current_index
            sequence_viewer.update_preview(self.state.current_index)

    def update_thumbnail(self, index):
        self.thumbnail_label.update_thumbnail(index)
        self.variation_number_label.update_index(index)

    def refresh(self):
        self.update_thumbnail(self.state.current_index)
        if len(self.state.thumbnails) == 1:
            self.hide()
        else:
            self.show()

    def resizeEvent(self, event):
        button_size = self.thumbnail_box.main_widget.height() // 35  # Smaller height
        for btn in (self.left_button, self.right_button):
            font = btn.font()
            font_size = min(
                button_size - 4, self.thumbnail_box.main_widget.width() // 120
            )
            font.setPointSize(font_size)
            btn.setFont(font)
            btn.setFixedSize(int(button_size * 1.5), int(button_size))  # Wider buttons
        # self.refresh()
        super().resizeEvent(event)
