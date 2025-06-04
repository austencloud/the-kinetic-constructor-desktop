from PIL import Image
import json
from PyQt6.QtCore import Qt, QMimeData, QEvent, QByteArray
from PyQt6.QtGui import QCursor, QMouseEvent, QDrag
from typing import TYPE_CHECKING

# Note: ThumbnailImageLabel import removed due to browse_tab restructure
# Creating a simple replacement for now
from PyQt6.QtWidgets import QLabel


class ThumbnailImageLabel(QLabel):
    """Simple replacement for ThumbnailImageLabel."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(200, 150)


if TYPE_CHECKING:
    from main_window.main_widget.write_tab.act_browser.act_browser import (
        ActThumbnailBox,
    )


class ActThumbnailImageLabel(ThumbnailImageLabel):
    def __init__(self, thumbnail_box: "ActThumbnailBox"):
        super().__init__(thumbnail_box)

    def eventFilter(self, obj, event: QEvent):
        """Override hover behavior for ActBrowser to use an open-hand cursor."""
        if obj == self and event.type() == QEvent.Type.Enter:
            self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
            self.setStyleSheet("border: 3px solid gold;")
            return True
        elif obj == self and event.type() == QEvent.Type.Leave:
            self.setStyleSheet(
                "border: 3px solid black;"
                if not self.is_selected
                else "border: 3px solid blue;"
            )
            return True

        return super().eventFilter(obj, event)

    def extract_metadata(self, image_path):
        """Extract metadata from an image file using PIL."""
        try:
            with Image.open(image_path) as img:
                metadata = img.info.get("metadata")
                return json.loads(metadata) if metadata else {}
        except Exception as e:
            print(f"Error extracting metadata: {e}")
            return {}

    def mousePressEvent(self, event: QMouseEvent):
        """Override click behavior to initiate drag-and-drop."""
        if event.button() == Qt.MouseButton.LeftButton and self.thumbnails:
            # Retrieve metadata for drag
            metadata = self.metadata_extractor.extract_metadata_from_file(
                self.thumbnails[self.thumbnail_box.state.current_index]
            )
            if metadata:
                self.startDrag(metadata)

    def startDrag(self, metadata: dict):
        drag = QDrag(self)
        mime_data = QMimeData()

        try:
            data_str = json.dumps(metadata)
            mime_data.setData(
                "application/sequence-data", QByteArray(data_str.encode("utf-8"))
            )
            drag.setMimeData(mime_data)
            drag.exec(Qt.DropAction.CopyAction)
        except json.JSONDecodeError as e:
            print(f"Error encoding metadata to JSON: {e}")
