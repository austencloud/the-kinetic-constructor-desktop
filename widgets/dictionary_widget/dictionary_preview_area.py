import os
import shutil
from typing import TYPE_CHECKING
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QMessageBox,
    QApplication,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap

from path_helpers import get_images_and_data_path
from widgets.dictionary_widget.thumbnail_box.base_word_label import BaseWordLabel
from widgets.dictionary_widget.thumbnail_box.preview_area_nav_btns import (
    PreviewAreaNavButtonsWidget,
)
from widgets.dictionary_widget.thumbnail_box.thumbnail_box import ThumbnailBox

from widgets.dictionary_widget.thumbnail_box.variation_number_label import (
    VariationNumberLabel,
)

if TYPE_CHECKING:
    from widgets.dictionary_widget.dictionary_widget import DictionaryWidget


class DictionaryPreviewArea(QWidget):
    def __init__(self, dictionary_widget: "DictionaryWidget"):
        super().__init__(dictionary_widget)
        self.thumbnails = []
        self.current_index = 0
        self.main_widget = dictionary_widget.main_widget
        self.dictionary_widget = dictionary_widget
        self.sequence_json = None
        self.current_thumbnail_box: ThumbnailBox = None
        self.base_word = ""
        self._setup_components()
        self.image_label.setStyleSheet("font: 20pt Arial; font-weight: bold;")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.variation_number_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.update_thumbnails()
        self.layout: QVBoxLayout = QVBoxLayout(self)
        self.layout.addStretch(1)
        self.layout.addWidget(self.base_word_label)
        self.layout.addWidget(self.variation_number_label)
        self.layout.addWidget(self.image_label)
        self.layout.addWidget(self.nav_buttons)
        self.layout.addWidget(self.edit_sequence_button)
        self.layout.addWidget(self.delete_variation_button)
        self.layout.addWidget(self.delete_word_button)
        self.layout.addStretch(1)

    def _setup_components(self):
        self.variation_number_label = VariationNumberLabel(self.current_index)
        self.base_word_label = BaseWordLabel(self.base_word)
        self.image_label = QLabel("Select a sequence to preview it here!", self)
        self.nav_buttons = PreviewAreaNavButtonsWidget(self)
        self.edit_sequence_button = QPushButton("Edit Sequence")
        self.edit_sequence_button.clicked.connect(self.edit_sequence)
        self._setup_deletion_buttons()

    def _setup_deletion_buttons(self):
        self.delete_variation_button = QPushButton("Delete Variation", self)
        self.delete_variation_button.clicked.connect(
            self.dictionary_widget.deletion_manager.confirm_delete_variation
        )
        self.delete_word_button = QPushButton("Delete Base Word", self)
        self.delete_word_button.clicked.connect(
            self.dictionary_widget.deletion_manager.confirm_delete_word
        )

    def update_thumbnails(self, thumbnails=[]):
        self.thumbnails = thumbnails
        if self.thumbnails:
            self.nav_buttons.enable_buttons(True)
        else:
            self.nav_buttons.enable_buttons(False)
            self.update_preview(None)

    def update_preview(self, index):
        if index == None:
            self.image_label.setText("Select a sequence to preview it here!")
            self._adjust_label_for_text()

            self.variation_number_label.setText("")
            return
        if self.thumbnails and index is not None:
            pixmap = QPixmap(self.thumbnails[index])
            self._scale_pixmap_to_label(pixmap)

        if self.current_thumbnail_box:
            self.sequence_json = self.current_thumbnail_box.metadata_extractor.extract_metadata_from_file(
                self.thumbnails[index]
            )

    def _scale_pixmap_to_label(self, pixmap: QPixmap):
        label_width = self.image_label.width()
        aspect_ratio = pixmap.height() / pixmap.width()
        new_height = int(label_width * aspect_ratio)
        scaled_pixmap = pixmap.scaled(
            label_width,
            new_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.image_label.setPixmap(scaled_pixmap)
        self.image_label.setMinimumHeight(new_height)

    def _adjust_label_for_text(self):
        min_height = int(max(self.height() / 5, 50))
        self.image_label.setMinimumHeight(min_height)

    def select_thumbnail(self, thumbnail_box, index, base_word):
        self.current_index = index
        self.base_word = base_word
        self.current_thumbnail_box = thumbnail_box
        self.update_base_word_label()
        self.update_thumbnails(self.thumbnails)
        self.update_preview(index)

    def update_base_word_label(self):
        self.base_word_label.setText(self.base_word)

    def _setup_preview_image_label(self):
        default_text = "Select a sequence to display it here."
        self.image_label = QLabel(default_text)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def edit_sequence(self):
        if not hasattr(self, "sequence_populator"):
            self.sequence_populator = self.dictionary_widget.sequence_populator
        if self.sequence_json:
            self.main_widget.setCurrentIndex(self.main_widget.builder_tab_index)
            self.sequence_populator.load_sequence_from_json(self.sequence_json)

        else:
            QMessageBox.warning(
                self, "No Selection", "Please select a thumbnail first."
            )

    def showEvent(self, event):
        super().showEvent(event)
        if self.thumbnails and self.current_index is not None:
            self.update_preview(self.current_index)
        else:
            self._adjust_label_for_text()

    def reset_preview_area(self):
        self.current_index = None
        self.update_preview(None)
        self.variation_number_label.setText("")
        self.base_word = ""
        self.base_word_label.setText(self.base_word)