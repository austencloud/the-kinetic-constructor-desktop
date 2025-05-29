from typing import TYPE_CHECKING
from PyQt6.QtWidgets import QApplication

if TYPE_CHECKING:
    from main_window.main_widget.browse_tab.thumbnail_box.thumbnail_image_label import (
        ThumbnailImageLabel,
    )
    from main_window.main_widget.browse_tab.browse_tab import BrowseTab


class BrowseTabSelectionHandler:
    current_thumbnail: "ThumbnailImageLabel" = None

    def __init__(self, dictionary_widget: "BrowseTab") -> None:
        self.browse_tab = dictionary_widget
        self.sequence_viewer = self.browse_tab.sequence_viewer
        self.main_widget = self.browse_tab.main_widget

    def on_thumbnail_clicked(self, image_label: "ThumbnailImageLabel") -> None:
        """Handles the event when a thumbnail is clicked."""
        if not image_label.thumbnail_box.state.thumbnails:
            raise ValueError(f"No thumbnails for {image_label.thumbnail_box.word}")

        sequence_dict = self.browse_tab.metadata_extractor.extract_metadata_from_file(
            image_label.thumbnail_box.state.thumbnails[0]
        )

        widgets = self._get_widgets_to_fade()
        self.main_widget.fade_manager.widget_fader.fade_and_update(
            widgets,
            lambda: self.select_box_thumbnail(image_label, sequence_dict),
            300,
        )

    def _get_widgets_to_fade(self):
        """Returns a list of widgets to be faded during thumbnail selection."""
        return [self.sequence_viewer.thumbnail_box]

    def select_box_thumbnail(
        self, image_label: "ThumbnailImageLabel", sequence_dict: dict
    ) -> None:
        """Selects a thumbnail from the box and updates the sequence viewer."""
        self._update_sequence_data(image_label, sequence_dict)
        self._update_selected_thumbnail(image_label)
        self._update_labels_and_settings(image_label)
        QApplication.processEvents()


    def _update_sequence_data(
        self, image_label: "ThumbnailImageLabel", sequence_dict: dict
    ):
        """Updates sequence-related data in the browse tab and sequence viewer."""
        self.browse_tab.sequence_picker.selected_sequence_dict = sequence_dict
        self.sequence_viewer.thumbnail_box.state.thumbnails = (
            image_label.thumbnail_box.state.thumbnails
        )
        self.sequence_viewer.state.matching_thumbnail_box = image_label.thumbnail_box

    def _update_selected_thumbnail(self, image_label: "ThumbnailImageLabel"):
        """Updates the visual state of the selected thumbnail."""
        if self.current_thumbnail:
            self.current_thumbnail.set_selected(False)

        self.current_thumbnail = image_label
        self.current_thumbnail.set_selected(True)

    def _update_labels_and_settings(self, image_label: "ThumbnailImageLabel"):
        """Updates labels and browse settings based on the selected thumbnail."""
        from PyQt6.QtWidgets import QApplication

        thumbnails = image_label.thumbnail_box.state.thumbnails

        self.sequence_viewer.update_thumbnails(thumbnails)
        QApplication.processEvents()

        self.select_viewer_thumbnail(
            image_label.thumbnail_box,
            image_label.thumbnail_box.state.current_index,
            image_label.thumbnail_box.word,
        )

        self.sequence_viewer.thumbnail_box.variation_number_label.update_index(
            image_label.thumbnail_box.state.current_index
        )
        word = image_label.thumbnail_box.word
        var_index = image_label.thumbnail_box.state.current_index
        self.browse_tab.browse_settings.set_selected_sequence(
            {"word": word, "variation_index": var_index}
        )
        self.sequence_viewer.thumbnail_box.nav_buttons_widget.variation_number_label.update_index(
            var_index
        )
        is_favorite = image_label.thumbnail_box.favorites_manager.is_favorite()
        self.sequence_viewer.thumbnail_box.header.favorite_button.update_favorite_icon(
            is_favorite
        )
        self.sequence_viewer.thumbnail_box.word = word



    def select_viewer_thumbnail(self, thumbnail_box, index, word):
        """Selects a thumbnail in the sequence viewer."""
        sequence_viewer = self.sequence_viewer
        sequence_viewer.thumbnail_box.state.current_index = index
        sequence_viewer.state.matching_thumbnail_box = thumbnail_box
        sequence_viewer.thumbnail_box.variation_number_label.update_index(index)
        sequence_viewer.thumbnail_box.header.word_label.setText(word)
        sequence_viewer.update_thumbnails(
            sequence_viewer.thumbnail_box.state.thumbnails
        )
        sequence_viewer.update_nav_buttons()
