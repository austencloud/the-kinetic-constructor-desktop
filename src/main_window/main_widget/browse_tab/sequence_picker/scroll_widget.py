from typing import TYPE_CHECKING, Optional
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QGridLayout, QSizePolicy
import logging

from ..thumbnail_box.thumbnail_box import ThumbnailBox

if TYPE_CHECKING:
    from .sequence_picker import SequencePicker
    from ..section_header import BrowseTabSectionHeader
    from ..lazy_loading.browse_tab_lazy_loader import BrowseTabLazyLoader


class SequencePickerScrollWidget(QWidget):
    def __init__(self, sequence_picker: "SequencePicker"):
        super().__init__(sequence_picker)
        self.sequence_picker = sequence_picker
        self.thumbnail_boxes: dict[str, ThumbnailBox] = {}
        self.section_headers: dict[int, "BrowseTabSectionHeader"] = {}

        # Lazy loading support
        self._lazy_loader: Optional["BrowseTabLazyLoader"] = None
        self._lazy_loading_enabled = False

        self.setStyleSheet("background: transparent;")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._setup_scroll_area()
        self._setup_layout()

    def _setup_layout(self):
        self.grid_layout = QGridLayout(self.scroll_content)
        self.grid_layout.setSpacing(0)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.layout: QVBoxLayout = QVBoxLayout(self)
        self.layout.addWidget(self.scroll_area)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)

    def _setup_scroll_area(self):
        self.scroll_content = QWidget()
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.scroll_area.setWidget(self.scroll_content)

    def clear_layout(self):
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Set the scrollbar width to 10% of the main widget's width
        scrollbar_width = self.calculate_scrollbar_width()
        self.scroll_area.verticalScrollBar().setFixedWidth(int(scrollbar_width))

    def calculate_scrollbar_width(self):
        return self.sequence_picker.main_widget.width() * 0.01

    def enable_lazy_loading(self, lazy_loader: "BrowseTabLazyLoader") -> None:
        """Enable lazy loading for all thumbnails in this scroll widget."""
        self._lazy_loader = lazy_loader
        self._lazy_loading_enabled = True

        # Enable lazy loading for existing thumbnails
        for thumbnail_box in self.thumbnail_boxes.values():
            if hasattr(thumbnail_box.image_label, "enable_lazy_loading"):
                thumbnail_box.image_label.enable_lazy_loading(lazy_loader)

        logging.info("Lazy loading enabled for scroll widget")

    def disable_lazy_loading(self) -> None:
        """Disable lazy loading for all thumbnails."""
        self._lazy_loading_enabled = False

        # Disable lazy loading for existing thumbnails
        for thumbnail_box in self.thumbnail_boxes.values():
            if hasattr(thumbnail_box.image_label, "disable_lazy_loading"):
                thumbnail_box.image_label.disable_lazy_loading()

        self._lazy_loader = None
        logging.info("Lazy loading disabled for scroll widget")

    def add_thumbnail_box(self, word: str, thumbnail_box: ThumbnailBox) -> None:
        """Add a thumbnail box and configure lazy loading if enabled."""
        self.thumbnail_boxes[word] = thumbnail_box

        # Configure lazy loading for new thumbnail if enabled
        if self._lazy_loading_enabled and self._lazy_loader:
            if hasattr(thumbnail_box.image_label, "enable_lazy_loading"):
                thumbnail_box.image_label.enable_lazy_loading(self._lazy_loader)

    def get_lazy_loading_stats(self) -> dict:
        """Get lazy loading statistics for this scroll widget."""
        if not self._lazy_loader:
            return {"lazy_loading_enabled": False}

        return {
            "lazy_loading_enabled": self._lazy_loading_enabled,
            "total_thumbnails": len(self.thumbnail_boxes),
            "lazy_loader_stats": (
                self._lazy_loader.get_stats() if self._lazy_loader else {}
            ),
        }
