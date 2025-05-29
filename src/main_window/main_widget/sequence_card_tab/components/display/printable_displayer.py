# src/main_window/main_widget/sequence_card_tab/components/display/printable_displayer.py
"""
Refactored PrintableDisplayer that uses the new component-based architecture.
This class now delegates most of its functionality to the SequenceDisplayManager.
"""
from typing import TYPE_CHECKING, Optional, List
from PyQt6.QtWidgets import QWidget

from ..pages.printable_layout import PaperSize, PaperOrientation
from .sequence_display_manager import SequenceDisplayManager

if TYPE_CHECKING:
    from ...tab import SequenceCardTab


class PrintableDisplayer:
    """
    Displays sequence cards in a print-friendly layout with multiple page previews side-by-side.

    This class:
    1. Arranges sequence cards in a grid optimized for printing
    2. Shows multiple page previews side-by-side
    3. Implements vertical scrolling for browsing pages
    4. Removes redundant headers from card containers
    5. Ensures the layout matches standard paper sizes

    This is a simplified facade that delegates to the SequenceDisplayManager.
    """

    def __init__(self, sequence_card_tab: "SequenceCardTab"):
        # Create the display manager that orchestrates all components
        self.manager = SequenceDisplayManager(sequence_card_tab)

    @property
    def columns_per_row(self) -> int:
        """Get the number of columns per row."""
        return self.manager.columns_per_row

    @columns_per_row.setter
    def columns_per_row(self, value: int) -> None:
        """Set the number of columns per row."""
        self.manager.columns_per_row = value

    def set_columns_per_row(self, columns: int) -> None:
        """
        Set the number of page previews to display per row.

        Args:
            columns: Number of columns (limited to 1-4)
        """
        self.manager.columns_per_row = columns

    def refresh_layout(self) -> None:
        """
        Refresh the layout with the current settings.

        This method:
        1. Clears existing pages and cache
        2. Completely removes all widgets from the layout
        3. Recreates the layout from scratch
        4. Updates grid dimensions based ONLY on sequence length
        5. Reloads all sequences with the new layout
        """
        self.manager.refresh_layout()

    def set_paper_size(self, paper_size: PaperSize) -> None:
        """
        Set the paper size for page previews.

        Args:
            paper_size: Paper size to use
        """
        self.manager.set_paper_size(paper_size)

    def set_orientation(self, orientation: PaperOrientation) -> None:
        """
        Set the orientation for page previews.

        Args:
            orientation: Paper orientation to use
        """
        self.manager.set_orientation(orientation)

    def display_sequences(
        self,
        selected_length: Optional[int] = None,
        selected_levels: Optional[List[int]] = None,
    ) -> None:
        """
        Display sequence card images in a print-friendly layout.

        Args:
            selected_length: The length of sequences to display. If None, use the sidebar selection.
            selected_levels: The difficulty levels to display. If None, use the sidebar selection.
        """
        # Cancel any in-progress loading operations
        if self.manager.is_loading:
            self.manager.cancel_loading()

        # Display sequences with the new filters
        self.manager.display_sequences(selected_length, selected_levels)

    # For backward compatibility, expose the pages property
    @property
    def pages(self) -> List[QWidget]:
        """Get the list of pages."""
        return self.manager.pages
