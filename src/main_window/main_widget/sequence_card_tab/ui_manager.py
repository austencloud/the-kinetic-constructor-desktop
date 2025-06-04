from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QSizePolicy
from PyQt6.QtCore import Qt

from .content_area import SequenceCardContentArea
from .header import SequenceCardHeader
from .components.navigation.sidebar import SequenceCardNavSidebar
from src.interfaces.settings_manager_interface import (
    ISettingsManager,
)  # Added for type hint

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .tab import SequenceCardTab

    # Add missing type imports for attributes
    from .content_area import SequenceCardContentArea
    from .header import SequenceCardHeader
    from .components.navigation.sidebar import SequenceCardNavSidebar
    from .components.display.printable_displayer import PrintableDisplayer


class SequenceCardUIManager:
    def __init__(self, tab: "SequenceCardTab"):
        self.tab: "SequenceCardTab" = tab
        self.main_widget = tab.main_widget  # Type is MainWidget via tab
        self.settings_manager: ISettingsManager = tab.settings_manager  # Corrected type
        # Ensure attributes that are assigned from tab also have clear types if used
        # For example, if self.tab.printable_displayer is used, its type should be clear

    def init_ui(self) -> None:
        """Initializes the main UI layout and components."""
        self.tab.layout = QVBoxLayout(self.tab)
        self.tab.layout.setContentsMargins(10, 10, 10, 10)
        self.tab.layout.setSpacing(10)

        self.tab.header = SequenceCardHeader(self.tab)
        self.tab.layout.addWidget(self.tab.header)

        self.tab.content_layout = QHBoxLayout()
        self.tab.content_layout.setContentsMargins(0, 0, 0, 0)
        self.tab.content_layout.setSpacing(15)

        self._update_sidebar_width()

        self.tab.content_layout.addWidget(self.tab.nav_sidebar, 0)
        self.tab.content_layout.addWidget(self.tab.content_area.scroll_area, 1)

        self.tab.layout.addLayout(self.tab.content_layout, 1)

    def _update_sidebar_width(self) -> None:
        """Dynamically calculate and set sidebar width based on tab dimensions."""
        try:
            tab_width = (
                self.tab.width() if self.tab.width() > 100 else self.main_widget.width()
            )

            # Calculate sidebar as percentage of available width with bounds
            sidebar_percentage = 0.22  # 22% of total width
            calculated_width = int(tab_width * sidebar_percentage)

            # Apply reasonable bounds: min 200px, max 400px
            sidebar_width = max(200, min(calculated_width, 400))

            self.tab.nav_sidebar.setMinimumWidth(sidebar_width)
            self.tab.nav_sidebar.setMaximumWidth(sidebar_width)
            self.tab.nav_sidebar.setSizePolicy(
                QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding
            )
        except (AttributeError, ZeroDivisionError):
            # Fallback to reasonable default
            self.tab.nav_sidebar.setMinimumWidth(250)
            self.tab.nav_sidebar.setMaximumWidth(250)

    def handle_resize_event(self) -> None:
        """Handle resize events to maintain responsive layout."""
        self._update_sidebar_width()

    def update_column_count(self, column_count: int) -> None:
        """Updates the column count for the printable displayer."""
        if (
            self.tab.USE_PRINTABLE_LAYOUT
            and hasattr(self.tab, "printable_displayer")
            and self.tab.printable_displayer
        ):
            printable_displayer: "PrintableDisplayer" = self.tab.printable_displayer
            printable_displayer.set_columns_per_row(column_count)

    def set_header_description(self, text: str) -> None:
        """Sets the description text in the header."""
        if hasattr(self.tab, "header") and self.tab.header:
            self.tab.header.description_label.setText(text)

    def show_loading_indicator(self, message: str = "Loading...") -> None:
        """Shows a loading indicator, e.g., by setting header text and cursor."""
        self.set_header_description(message)
        self.tab.setCursor(Qt.CursorShape.WaitCursor)

    def hide_loading_indicator(self, original_message: str = "") -> None:
        """Hides the loading indicator."""
        self.tab.setCursor(Qt.CursorShape.ArrowCursor)
        if original_message:
            self.set_header_description(original_message)

    def clear_content_area(self) -> None:
        """Clears the content area."""
        if hasattr(self.tab, "content_area") and self.tab.content_area:
            content_area: "SequenceCardContentArea" = self.tab.content_area
            content_area.clear_layout()
