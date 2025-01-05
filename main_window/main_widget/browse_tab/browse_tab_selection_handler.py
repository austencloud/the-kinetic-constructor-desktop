from typing import TYPE_CHECKING
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt


if TYPE_CHECKING:
    from main_window.main_widget.browse_tab.thumbnail_box.thumbnail_image_label import (
        ThumbnailImageLabel,
    )
    from main_window.main_widget.browse_tab.browse_tab import (
        BrowseTab,
    )


class BrowseTabSelectionManager:
    current_thumbnail: "ThumbnailImageLabel" = None

    def __init__(self, dictionary_widget: "BrowseTab") -> None:
        self.browse_tab = dictionary_widget
        self.sequence_viewer = self.browse_tab.sequence_viewer
        self.main_widget = self.browse_tab.main_widget

    def on_thumbnail_clicked(
        self, image_label: "ThumbnailImageLabel", sequence_dict: dict
    ) -> None:
        sequence_viewer = self.sequence_viewer
        widgets = [
            sequence_viewer.image_label,
            sequence_viewer.placeholder_label,
            sequence_viewer.word_label,
            sequence_viewer.variation_number_label,
            sequence_viewer.nav_buttons_widget,
            sequence_viewer.action_button_panel,
        ]

        self.main_widget.fade_manager.widget_fader.fade_and_update(
            widgets,
            lambda: self.select_thumbnail(image_label, sequence_dict),
            300,
        )

    def select_thumbnail(
        self,
        image_label: "ThumbnailImageLabel",
        sequence_dict: dict,
    ) -> None:
        self.browse_tab.sequence_picker.selected_sequence_dict = sequence_dict
        self.sequence_viewer.thumbnails = image_label.thumbnails
        thumbnail_pixmap = QPixmap(
            image_label.thumbnails[image_label.thumbnail_box.current_index]
        )
        self.sequence_viewer.image_label.setPixmap(
            thumbnail_pixmap.scaled(
                self.sequence_viewer.image_label.size() * 0.9,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
        if self.current_thumbnail:
            self.current_thumbnail.set_selected(False)

        self.current_thumbnail = image_label
        self.current_thumbnail.set_selected(True)
        self.current_thumbnail.is_selected = True

        self.sequence_viewer.select_thumbnail(
            image_label.thumbnail_box,
            image_label.thumbnail_box.current_index,
            image_label.thumbnail_box.word,
        )
        self.sequence_viewer.variation_number_label.update_index(
            image_label.thumbnail_box.current_index
        )
