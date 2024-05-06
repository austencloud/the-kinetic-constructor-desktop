from typing import TYPE_CHECKING
from PIL import Image
from PyQt6.QtWidgets import QMessageBox
import json

if TYPE_CHECKING:
    from widgets.dictionary_widget.thumbnail_box.thumbnail_box import ThumbnailBox


class MetaDataExtractor:
    def __init__(self, thumbnail_box: "ThumbnailBox"):
        self.thumbnail_box = thumbnail_box

    def extract_metadata_from_file(self, file_path):
        # check if a file exists at the path we're passing as "file_path"
        if not file_path:
            return

        try:
            with Image.open(file_path) as img:
                metadata = img.info.get("metadata")
                if metadata:
                    return json.loads(metadata)
                else:
                    QMessageBox.warning(
                        self.thumbnail_box.main_widget,
                        "Error",
                        "No sequence metadata found in the thumbnail.",
                    )
        except Exception as e:
            QMessageBox.critical(
                self.thumbnail_box.main_widget,
                "Error",
                f"Error loading sequence from thumbnail: {e}",
            )

    def get_sequence_length(self, file_path):
        metadata = self.extract_metadata_from_file(file_path)
        if metadata:
            return len(metadata) - 1
        return 0
