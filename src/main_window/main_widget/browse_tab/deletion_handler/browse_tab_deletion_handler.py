import os
import shutil
from typing import TYPE_CHECKING
from .variation_number_fixer import VariationNumberFixer
from ..delete_confirmation_dialog import BrowseTabDeleteConfirmationDialog
from utils.path_helpers import get_data_path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QDialog

if TYPE_CHECKING:
    from ..thumbnail_box.thumbnail_box import ThumbnailBox
    from ..browse_tab import BrowseTab

DICTIONARY_PATH = "dictionary"


class BrowseTabDeletionHandler:
    def __init__(self, browse_tab: "BrowseTab"):
        self.browse_tab = browse_tab
        self.sequence_picker = browse_tab.sequence_picker
        self.variation_number_fixer = VariationNumberFixer()

    def is_folder_empty(self, folder_path):
        return not any(os.scandir(folder_path))

    def delete_variation(self, thumbnail_box: "ThumbnailBox", index):
        dialog = BrowseTabDeleteConfirmationDialog(self.browse_tab)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            current_scroll_position = (
                self.browse_tab.sequence_picker.scroll_widget.scroll_area.verticalScrollBar().value()
            )
            file_path = thumbnail_box.state.thumbnails.pop(index)
            os.remove(file_path)
            if len(thumbnail_box.state.thumbnails) == 0:
                self.delete_word(thumbnail_box.word)
                self.browse_tab.sequence_viewer.update_thumbnails(
                    self.browse_tab.sequence_viewer.thumbnail_box.state.thumbnails
                )

            else:
                self.delete_empty_folders(get_data_path(DICTIONARY_PATH))
                self.browse_tab.sequence_viewer.update_thumbnails(
                    thumbnail_box.state.thumbnails
                )
                thumbnail_box.update_thumbnails(thumbnail_box.state.thumbnails)

            def restore_scroll_position():
                self.browse_tab.sequence_picker.scroll_widget.scroll_area.verticalScrollBar().setValue(
                    current_scroll_position
                )
                QApplication.restoreOverrideCursor()

            QApplication.processEvents()
            QTimer.singleShot(0, restore_scroll_position)

        QApplication.restoreOverrideCursor()

    def delete_word(self, base_word):
        base_path = os.path.join(get_data_path(DICTIONARY_PATH), base_word)
        for root, dirs, files in os.walk(base_path):
            for name in files:
                file_path = os.path.join(root, name)
                os.chmod(file_path, 0o777)
            for name in dirs:
                dir_path = os.path.join(root, name)
                os.chmod(dir_path, 0o777)
        os.chmod(base_path, 0o777)
        shutil.rmtree(base_path)
        self.delete_empty_folders(get_data_path(DICTIONARY_PATH))
        self.variation_number_fixer.ensure_sequential_versions()
        self.browse_tab.sequence_picker.scroll_widget.thumbnail_boxes.pop(base_word)
        self.browse_tab.sequence_viewer.update_thumbnails(
            self.browse_tab.sequence_viewer.thumbnail_box.state.thumbnails
        )
        self.sequence_picker.sorter.reload_currently_displayed_filtered_sequences()

    def delete_empty_folders(self, root_folder):
        for root, dirs, files in os.walk(root_folder, topdown=False):
            for dir_name in dirs:
                dir_path = os.path.join(root, dir_name)
                if self.is_folder_empty(dir_path):
                    os.chmod(dir_path, 0o777)
                    shutil.rmtree(dir_path)
