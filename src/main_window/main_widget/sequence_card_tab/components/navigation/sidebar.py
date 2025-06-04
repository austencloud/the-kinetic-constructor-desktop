# src/main_window/main_widget/sequence_card_tab/components/navigation/sidebar.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QApplication
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from typing import TYPE_CHECKING
from .page_preview_column_selector import PagePreviewColumnSelector
from .length_scroll_area import LengthScrollArea
from .sidebar_header import SidebarHeader
from .sidebar_styler import SidebarStyler
from .transition_overlay import TransitionOverlay
from .level_filter import LevelFilterWidget

if TYPE_CHECKING:
    from ...tab import SequenceCardTab


class SequenceCardNavSidebar(QWidget):
    length_selected = pyqtSignal(int)
    level_filter_changed = pyqtSignal(list)

    def __init__(self, sequence_card_tab: "SequenceCardTab"):
        super().__init__(sequence_card_tab)
        self.sequence_card_tab = sequence_card_tab
        self.settings_manager = sequence_card_tab.settings_manager
        # Initialize with a default length instead of 0
        self.selected_length = int(
            self.settings_manager.get_setting("sequence_card_tab", "last_length", 16)
        )
        self.level_filter = None
        self.setup_ui()
        SidebarStyler.apply_modern_styling(self)

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(12)

        self.header = SidebarHeader()
        main_layout.addWidget(self.header)

        self.scroll_area = LengthScrollArea()
        self.scroll_area.length_selected.connect(self.on_length_selected)
        main_layout.addWidget(self.scroll_area, 1)

        # Add level filter widget
        self.level_filter = LevelFilterWidget()
        self.level_filter.level_filter_changed.connect(self.on_level_filter_changed)
        main_layout.addWidget(self.level_filter)

        self.column_selector = PagePreviewColumnSelector(
            self.settings_manager, self.width()
        )
        self.column_selector.column_count_changed.connect(self.on_column_count_changed)
        main_layout.addWidget(self.column_selector)

        # Initialize the length selection after UI setup
        if self.selected_length and self.selected_length > 0:
            self.scroll_area.update_selection(self.selected_length)

    def on_length_selected(self, length: int):
        self.selected_length = length
        self.scroll_area.update_selection(length)
        self.length_selected.emit(length)

    def on_level_filter_changed(self, selected_levels: list):
        """Handle level filter changes and emit signal."""
        self.level_filter_changed.emit(selected_levels)

    def select_length(self, length: int):
        if length in self.scroll_area.length_frames:
            self.on_length_selected(length)

    def on_column_count_changed(self, column_count: int):
        try:
            scroll_position = (
                self.sequence_card_tab.content_area.scroll_area.verticalScrollBar().value()
            )

            self.sequence_card_tab.setCursor(Qt.CursorShape.WaitCursor)
            self.sequence_card_tab.header.description_label.setText(
                f"Updating display to show {column_count} preview columns..."
            )
            QApplication.processEvents()

            overlay = TransitionOverlay(self.sequence_card_tab)
            overlay.show_with_timer()

            self.settings_manager.set_setting(
                "sequence_card_tab", "column_count", column_count
            )
            self.sequence_card_tab.update_column_count(column_count)

            QTimer.singleShot(
                100, lambda: self._restore_scroll_position(scroll_position)
            )
            self._update_description_label(column_count)
            self.sequence_card_tab.setCursor(Qt.CursorShape.ArrowCursor)

        except Exception as e:
            print(f"Error updating column count: {e}")
            self.sequence_card_tab.header.description_label.setText(f"Error: {str(e)}")
            self.sequence_card_tab.setCursor(Qt.CursorShape.ArrowCursor)

    def _update_description_label(self, column_count: int):
        total_pages = 0
        if hasattr(self.sequence_card_tab, "printable_displayer"):
            total_pages = len(self.sequence_card_tab.printable_displayer.pages)

        length_text = (
            f"{self.selected_length}-step" if self.selected_length > 0 else "all"
        )

        if total_pages > 0:
            self.sequence_card_tab.header.description_label.setText(
                f"Showing {length_text} sequences across {total_pages} pages with {column_count} preview columns"
            )
        else:
            self.sequence_card_tab.header.description_label.setText(
                f"Updated display to show {column_count} preview columns"
            )

    def _restore_scroll_position(self, position):
        if hasattr(self.sequence_card_tab.content_area, "scroll_area"):
            self.sequence_card_tab.content_area.scroll_area.verticalScrollBar().setValue(
                position
            )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "scroll_area"):
            for frame in self.scroll_area.length_frames.values():
                font = frame.label.font()
                font.setPointSize(min(max(12, int(self.width() / 15)), 14))
                frame.label.setFont(font)
