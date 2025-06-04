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
        print(f"🔧 _SETUP_LAYOUT CALLED")

        # AGGRESSIVE GRID LAYOUT STRATEGY: Force the scroll content to use our layout
        print(f"🔧 SCROLL CONTENT BEFORE: {self.scroll_content}")
        print(f"🔧 SCROLL CONTENT LAYOUT BEFORE: {self.scroll_content.layout()}")

        # FORCE LAYOUT APPROACH: Aggressively force the layout to be set correctly
        print(f"🔧 FORCE LAYOUT APPROACH: Aggressively setting layout")

        # Clear any existing layout completely
        existing_layout = self.scroll_content.layout()
        if existing_layout:
            print(f"🔧 FOUND EXISTING LAYOUT: {existing_layout}")
            # Clear all items first
            while existing_layout.count():
                item = existing_layout.takeAt(0)
                if item.widget():
                    item.widget().setParent(None)
            print(f"🔧 CLEARED ALL LAYOUT ITEMS")

            # Force delete the layout
            existing_layout.setParent(None)
            existing_layout.deleteLater()
            print(f"🔧 FORCE DELETED EXISTING LAYOUT")

        # Force the scroll content to have no layout
        self.scroll_content.setLayout(None)
        print(f"🔧 FORCED SCROLL CONTENT LAYOUT TO NONE")

        # Create a completely fresh grid layout
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(0)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        print(f"🔧 CREATED FRESH GRID LAYOUT: {self.grid_layout}")

        # FORCE set the layout on the scroll content
        result = self.scroll_content.setLayout(self.grid_layout)
        print(f"🔧 FORCE SET LAYOUT RESULT: {result}")

        # Verify multiple times to ensure it stuck
        for i in range(3):
            current_layout = self.scroll_content.layout()
            print(f"🔧 VERIFICATION {i+1}: scroll_content.layout() = {current_layout}")
            print(
                f"🔧 VERIFICATION {i+1}: grid_layout is same = {self.grid_layout is current_layout}"
            )
            if self.grid_layout is current_layout:
                print(f"🔧 SUCCESS: Layout verification passed on attempt {i+1}")
                break
            else:
                print(
                    f"🔧 RETRY: Layout verification failed on attempt {i+1}, retrying..."
                )
                self.scroll_content.setLayout(self.grid_layout)

        # Verify the layout was set correctly
        print(f"🔧 SCROLL CONTENT LAYOUT AFTER: {self.scroll_content.layout()}")
        print(
            f"🔧 GRID LAYOUT IS SAME AS SCROLL CONTENT: {self.grid_layout is self.scroll_content.layout()}"
        )

        print(f"🔧 CHECKING MAIN LAYOUT")
        # Set up main layout if not already done
        try:
            current_layout = self.layout()
            print(f"🔧 CURRENT LAYOUT: {current_layout}")
            if not current_layout:
                print(f"🔧 CREATING MAIN LAYOUT")
                main_layout = QVBoxLayout(self)
                main_layout.addWidget(self.scroll_area)
                main_layout.setSpacing(0)
                main_layout.setContentsMargins(0, 0, 0, 0)
                print(f"🔧 MAIN LAYOUT CREATED: {main_layout}")
            else:
                print(f"🔧 MAIN LAYOUT ALREADY EXISTS: {current_layout}")
        except Exception as layout_error:
            print(f"❌ LAYOUT ERROR: {layout_error}")
            raise layout_error

        print(f"🔧 _SETUP_LAYOUT COMPLETED")

    def _setup_scroll_area(self):
        self.scroll_content = QWidget()
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.scroll_area.setWidget(self.scroll_content)

    def clear_layout(self):
        print(
            f"🧹 CLEAR_LAYOUT CALLED - grid_layout: {getattr(self, 'grid_layout', 'NOT_SET')}"
        )

        # GRID LAYOUT SAFETY: Ensure grid layout exists before clearing
        if not hasattr(self, "grid_layout") or self.grid_layout is None:
            print(f"⚠️ WARNING: grid_layout is None in clear_layout() - reinitializing")
            self._setup_layout()
            return

        print(f"🧹 CLEARING {self.grid_layout.count()} items from grid layout")
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
        print(f"🧹 CLEAR_LAYOUT COMPLETED - grid_layout: {self.grid_layout}")

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
