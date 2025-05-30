import logging
from typing import List, Optional, TYPE_CHECKING
from PyQt6.QtWidgets import QWidget, QGridLayout
from PyQt6.QtCore import Qt

if TYPE_CHECKING:
    from ..page_renderer import PageRenderer
    from ..scroll_view import ScrollView
    from ....tab import SequenceCardTab


class PageManager:
    def __init__(
        self,
        sequence_card_tab: "SequenceCardTab",
        page_renderer: "PageRenderer",
        scroll_view: "ScrollView",
    ):
        self.sequence_card_tab = sequence_card_tab
        self.page_renderer = page_renderer
        self.scroll_view = scroll_view
        self.pages: List[QWidget] = []
        self.current_page_index = -1
        self.current_position = 0
        self.logger = logging.getLogger(__name__)

    def clear_existing_pages(self):
        self.logger.debug(f"Clearing {len(self.pages)} existing pages")

        self.scroll_view.clear_existing_pages(self.pages)
        self.pages = []
        self.page_renderer.clear_pages()

        self.current_page_index = -1
        self.current_position = 0

        self.logger.debug("All pages cleared and state reset")

    def ensure_first_page_exists(self):
        if self.current_page_index == -1:
            self.logger.debug("Creating first page...")
            new_page = self.page_renderer.create_new_page()

            if new_page.layout() is None:
                self.logger.warning(
                    "First page created without layout. Adding QGridLayout."
                )
                grid_layout = QGridLayout(new_page)
                grid_layout.setContentsMargins(10, 10, 10, 10)
                grid_layout.setSpacing(5)

            self.pages.append(new_page)
            self.current_page_index = 0
            self.current_position = 0
            self.logger.debug(f"Created first page with layout: {new_page.layout()}")

    def add_widget_to_current_page(self, widget: QWidget):
        if self.page_renderer.is_page_full(self.current_position):
            self.logger.debug(
                f"Current page {self.current_page_index} is full at position {self.current_position}. Creating new page."
            )
            self._create_new_page()

        if self.current_page_index < 0 or self.current_page_index >= len(self.pages):
            self.logger.error(
                f"Invalid page index {self.current_page_index}, pages length: {len(self.pages)}"
            )
            return

        page = self.pages[self.current_page_index]
        grid_layout_on_page = page.layout()

        if grid_layout_on_page is None:
            self.logger.warning(
                f"Page {self.current_page_index} has no layout. Adding QGridLayout."
            )
            grid_layout_on_page = QGridLayout(page)
            grid_layout_on_page.setContentsMargins(10, 10, 10, 10)
            grid_layout_on_page.setSpacing(5)

        positions = self.sequence_card_tab.page_factory.get_grid_positions()
        if self.current_position < len(positions):
            row, col = positions[self.current_position]
            try:
                grid_layout_on_page.addWidget(
                    widget, row, col, Qt.AlignmentFlag.AlignCenter
                )
                self.current_position += 1
                self.logger.debug(
                    f"Added widget to page {self.current_page_index} at position ({row}, {col})"
                )
            except Exception as e:
                self.logger.error(
                    f"Error adding widget to page {self.current_page_index}: {e}"
                )
        else:
            self.logger.error(
                f"Invalid position {self.current_position} for page's internal grid, max positions: {len(positions)}"
            )

    def _create_new_page(self):
        new_page = self.page_renderer.create_new_page()

        if new_page.layout() is None:
            self.logger.warning("New page created without layout. Adding QGridLayout.")
            grid_layout = QGridLayout(new_page)
            grid_layout.setContentsMargins(10, 10, 10, 10)
            grid_layout.setSpacing(5)

        self.pages.append(new_page)
        self.current_page_index = len(self.pages) - 1
        self.current_position = 0
        self.logger.debug(
            f"Created new page {self.current_page_index} with layout: {new_page.layout()}"
        )

    def get_current_page_scale_factor(self) -> float:
        if self.current_page_index >= 0 and self.current_page_index < len(self.pages):
            current_page = self.pages[self.current_page_index]
            scale_factor = current_page.property("scale_factor")
            if scale_factor is not None:
                return float(scale_factor)
        return 1.0

    def get_page_count(self) -> int:
        return len(self.pages)
