# src/main_window/main_widget/sequence_card_tab/components/display/scroll_view.py
import logging
from typing import TYPE_CHECKING
from PyQt6.QtWidgets import QWidget, QGridLayout, QApplication
from PyQt6.QtCore import Qt


if TYPE_CHECKING:
    from main_window.main_widget.sequence_card_tab.components.display.sequence_display_manager import (
        DisplayConfig,
    )
    from ...tab import SequenceCardTab


class ScrollView:
    """
    Manages the scroll view for sequence card display.

    This class is responsible for:
    1. Creating and managing the multi-column layout for page previews
    2. Clearing existing pages and layouts
    3. Handling UI updates and refreshes
    """

    def __init__(self, sequence_card_tab: "SequenceCardTab", config: "DisplayConfig"):
        self.sequence_card_tab = sequence_card_tab
        self.config = config
        self.preview_grid = None

    def create_multi_column_layout(self) -> QGridLayout:
        """
        Create a multi-column layout for page previews.

        Returns:
            QGridLayout: The created grid layout
        """
        # Clear the scroll layout if it exists
        if (
            hasattr(self.sequence_card_tab.content_area, "scroll_layout")
            and self.sequence_card_tab.content_area.scroll_layout is not None
        ):
            self._clear_scroll_layout()
        else:
            logging.debug("Skipping _clear_scroll_layout - scroll_layout not ready yet")

        # Create a grid layout for the page previews
        self.preview_grid = QGridLayout()
        self.preview_grid.setSpacing(self.config.page_spacing)
        self.preview_grid.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter
        )
        # MINIMAL MARGINS: Set zero content margins for the preview grid
        self.preview_grid.setContentsMargins(0, 0, 0, 0)  # No margins at all

        # Add the grid layout to the scroll layout (AFTER creating it)
        if (
            hasattr(self.sequence_card_tab.content_area, "scroll_layout")
            and self.sequence_card_tab.content_area.scroll_layout is not None
        ):
            self.sequence_card_tab.content_area.scroll_layout.addLayout(
                self.preview_grid
            )

            # MINIMAL MARGINS: Set zero horizontal margins on the parent scroll layout
            self.sequence_card_tab.content_area.scroll_layout.setContentsMargins(
                0, 5, 0, 5
            )

            logging.debug("Added preview_grid to scroll_layout with reduced margins")
        else:
            # Don't log an error, just a debug message
            logging.debug(
                "scroll_layout not available yet - preview_grid created but not added to layout"
            )
            # We'll still return the preview_grid even if we couldn't add it to the layout

        return self.preview_grid

    def clear_existing_pages(self, pages: list[QWidget]) -> None:
        """
        Clear all existing pages and remove them from the layout.

        This method:
        1. Removes all page widgets from the preview grid
        2. Forces a UI update to ensure the layout is properly cleared

        Args:
            pages: list of page widgets to clear
        """
        # First check if there are any pages to clear
        if not pages:
            logging.debug("No pages to clear")
            return

        # Then, remove all widgets from the preview grid if it exists
        if hasattr(self, "preview_grid") and self.preview_grid is not None:
            # Get all widgets from the grid layout
            for i in range(self.preview_grid.count()):
                item = self.preview_grid.itemAt(i)
                if item and item.widget():
                    # Remove the widget from the layout and delete it
                    widget = item.widget()
                    if widget:
                        widget.setParent(None)
                        widget.deleteLater()

            logging.debug(f"Cleared {len(pages)} pages from preview grid")
        else:
            # Don't log an error, just a debug message
            logging.debug("Preview grid not initialized yet, skipping page clearing")

            # Manually clean up the pages to prevent memory leaks
            for page in pages:
                if page and not page.isDestroyed():
                    page.setParent(None)
                    page.deleteLater()

        # Force a UI update to ensure the layout is properly cleared
        QApplication.processEvents()

    def _clear_scroll_layout(self) -> None:
        """Clear the scroll layout completely."""
        # This method should only be called after we've verified scroll_layout exists
        # But we'll add an extra check just to be safe
        if (
            hasattr(self.sequence_card_tab.content_area, "scroll_layout")
            and self.sequence_card_tab.content_area.scroll_layout is not None
        ):
            try:
                # Get the count before we start removing items
                initial_count = (
                    self.sequence_card_tab.content_area.scroll_layout.count()
                )
                logging.debug(f"Clearing scroll layout with {initial_count} items")

                while self.sequence_card_tab.content_area.scroll_layout.count():
                    item = self.sequence_card_tab.content_area.scroll_layout.takeAt(0)
                    if item is None:
                        break

                    if item.widget():
                        widget = item.widget()
                        if widget:
                            widget.setParent(None)
                            widget.deleteLater()
                    elif item.layout():
                        # Get the layout
                        layout = item.layout()

                        # Remove all widgets from the sublayout
                        while layout.count():
                            subitem = layout.takeAt(0)
                            if subitem is None:
                                break

                            if subitem.widget():
                                widget = subitem.widget()
                                if widget:
                                    widget.setParent(None)
                                    widget.deleteLater()

                        # Remove the layout itself
                        self.sequence_card_tab.content_area.scroll_layout.removeItem(
                            item
                        )

                logging.debug(
                    f"Scroll layout cleared, now has {self.sequence_card_tab.content_area.scroll_layout.count()} items"
                )
            except Exception as e:
                logging.debug(f"Error clearing scroll layout: {e}")
        else:
            # Don't log an error, just a debug message
            logging.debug("Scroll layout not available, skipping clear operation")
