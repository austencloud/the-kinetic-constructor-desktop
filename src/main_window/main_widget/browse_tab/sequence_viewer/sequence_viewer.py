from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from typing import TYPE_CHECKING, Optional

from main_window.main_widget.metadata_extractor import MetaDataExtractor

from .state import SequenceViewerState
from .action_button_panel import SequenceViewerActionButtonPanel
from ..thumbnail_box.factory import ThumbnailBoxFactory


if TYPE_CHECKING:
    from ..browse_tab import BrowseTab


class SequenceViewer(QWidget):
    def __init__(self, browse_tab: "BrowseTab"):
        super().__init__(browse_tab)
        self.main_widget = browse_tab.main_widget
        self.browse_tab = browse_tab
        self.state = SequenceViewerState()

        # Set size policy to respect the layout stretch ratios and prevent expansion
        from PyQt6.QtWidgets import QSizePolicy

        size_policy = QSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Preferred,
        )
        size_policy.setHorizontalStretch(
            1
        )  # This should match the stretch factor in TabManager (1 for right stack)
        self.setSizePolicy(size_policy)

        # Embed a modern integrated thumbnail box for enhanced display
        self.thumbnail_box = ThumbnailBoxFactory.create_integrated_thumbnail_box(
            browse_tab, word="", thumbnails=[], in_sequence_viewer=True
        )

        # Now SequenceViewer just holds the action panel and delegates everything else
        self.action_button_panel = SequenceViewerActionButtonPanel(self)
        self.thumbnail_box.header.hide_favorite_button()

        self._setup_layout()

    def _setup_layout(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addStretch(1)

        layout.addWidget(self.thumbnail_box)
        layout.addWidget(self.action_button_panel)

        layout.addStretch(1)
        self.setLayout(layout)

    def update_thumbnails(self, thumbnails: list[str]):
        from PyQt6.QtWidgets import QApplication

        self.thumbnail_box.state.update_thumbnails(thumbnails)
        QApplication.processEvents()

        current_thumbnail = self.thumbnail_box.state.get_current_thumbnail()
        self.thumbnail_box.header.difficulty_label.update_difficulty_label()  # 🆕 Update difficulty!

        if current_thumbnail:
            self.update_preview(self.thumbnail_box.state.current_index)
            QApplication.processEvents()
        else:
            self.clear()

    def update_preview(self, index: int):
        self.thumbnail_box.state.set_current_index(index)
        current_thumbnail = self.thumbnail_box.state.get_current_thumbnail()

        if current_thumbnail:
            pixmap = QPixmap(current_thumbnail)
            if not pixmap.isNull():
                self.thumbnail_box.image_label.update_thumbnail(index)
                self.thumbnail_box.header.show_favorite_button()
                self.thumbnail_box.header.difficulty_label.show()

                if self.state.matching_thumbnail_box:
                    metadata_extractor = MetaDataExtractor()
                    self.state.sequence_json = (
                        metadata_extractor.extract_metadata_from_file(current_thumbnail)
                    )
        else:
            self.thumbnail_box.variation_number_label.clear()
            self.thumbnail_box.header.hide_favorite_button()
            self.thumbnail_box.header.difficulty_label.hide()

        self.thumbnail_box.variation_number_label.update_index(index)

        # Width constraint now handled by parent container layout

    def update_nav_buttons(self):
        self.thumbnail_box.nav_buttons_widget.refresh()

    def clear(self):
        self.thumbnail_box.state.clear()
        self.thumbnail_box.variation_number_label.clear()
        self.thumbnail_box.header.word_label.clear()
        self.thumbnail_box.nav_buttons_widget.hide()
        self.thumbnail_box.variation_number_label.hide()
        self.thumbnail_box.header.hide_favorite_button()
        self.thumbnail_box.header.difficulty_label.hide()
        self.state.matching_thumbnail_box = None

    def get_thumbnail_at_current_index(self) -> Optional[str]:
        return self.thumbnail_box.state.get_current_thumbnail()

    def reopen_thumbnail(self, word: str, var_index: int):
        """Reopens a thumbnail based on word and variation index."""
        if word in self.browse_tab.sequence_picker.scroll_widget.thumbnail_boxes:
            box = self.browse_tab.sequence_picker.scroll_widget.thumbnail_boxes[word]
            if 0 <= var_index < len(box.state.thumbnails):
                box.state.current_index = var_index
                selected_thumbnail = box.state.thumbnails[var_index]
                metadata = (
                    self.browse_tab.metadata_extractor.extract_metadata_from_file(
                        selected_thumbnail
                    )
                )
                self.browse_tab.selection_handler.on_thumbnail_clicked(
                    box.image_label, metadata
                )
                return

        print(
            f"[INFO] '{word}' not found in the current filter. Searching full dictionary..."
        )

        dictionary_words = self.browse_tab.get.base_words()
        matching_entry = next(
            (entry for entry in dictionary_words if entry[0] == word), None
        )
        if matching_entry:
            thumbnails = matching_entry[1]

            if thumbnails:
                var_index = max(0, min(var_index, len(thumbnails) - 1))
                selected_thumbnail = thumbnails[var_index]

                self.update_thumbnails(thumbnails)
                self.update_preview(var_index)
                self.update_nav_buttons()
                self.thumbnail_box.header.word_label.setText(word)
                self.thumbnail_box.variation_number_label.update_index(var_index)
                self.set_current_thumbnail_box(word)

                print(
                    f"[SUCCESS] Loaded missing sequence: {word} (variation {var_index})"
                )
                return

        print(f"[ERROR] Could not find sequence '{word}' in the dictionary.")

    def set_current_thumbnail_box(self, word):
        """Sets the current thumbnail box and updates the sequence viewer."""
        self.thumbnail_box.word = word
        thumbnail_boxes = self.browse_tab.sequence_picker.scroll_widget.thumbnail_boxes
        if not thumbnail_boxes:
            return
        for box in thumbnail_boxes.values():
            if box.word == word:
                self.state.matching_thumbnail_box = box
                index = self.thumbnail_box.state.current_index
                box.nav_buttons_widget.update_thumbnail(index)
                self.browse_tab.selection_handler.current_thumbnail = (
                    self.state.matching_thumbnail_box.image_label
                )
                self.favorites_manager = box.favorites_manager
                return

    def resizeEvent(self, event):
        # Width constraint now handled by parent container layout

        # Update thumbnail if needed
        if hasattr(self.thumbnail_box, "image_label") and hasattr(
            self.thumbnail_box.state, "current_index"
        ):
            self.thumbnail_box.image_label.update_thumbnail(
                self.thumbnail_box.state.current_index
            )
        super().resizeEvent(event)
