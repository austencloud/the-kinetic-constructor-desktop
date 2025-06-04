import logging
from PyQt6.QtWidgets import QApplication
from ..core.mode_manager import SequenceCardMode
from ..ui_manager import SequenceCardUIManager  # Added for type hint
from ..settings_handler import SequenceCardSettingsHandler  # Added for type hint

from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from ..tab import SequenceCardTab
    from ..components.display.printable_displayer import PrintableDisplayer


class SequenceCardDictionaryModeController:
    def __init__(self, tab: "SequenceCardTab"):
        self.tab: "SequenceCardTab" = tab
        self.ui_manager: SequenceCardUIManager = tab.ui_manager
        self.settings_manager_obj: SequenceCardSettingsHandler = (
            tab.settings_manager_obj
        )

    def activate(self) -> None:
        """Activates dictionary mode."""
        self.ui_manager.set_header_description("Browse sequences from the dictionary")
        if self.tab.nav_sidebar.scroll_area:
            self.tab.nav_sidebar.scroll_area.setVisible(True)
        if self.tab.nav_sidebar.level_filter:
            self.tab.nav_sidebar.level_filter.setVisible(True)
        self.load_sequences()

    def deactivate(self) -> None:
        """Deactivates dictionary mode (e.g., when switching to another mode)."""
        # Optionally, add any cleanup specific to dictionary mode when it's deactivated
        pass

    def on_length_selected(self, length: int) -> None:
        """Handles length selection changes."""
        self.tab.currently_displayed_length = length
        self.settings_manager_obj.save_length(length)

        if self.tab.is_initializing:
            return

        self.ui_manager.clear_content_area()
        self.ui_manager.set_header_description(
            f"Loading {length if length > 0 else 'all'}-step sequences..."
        )

        if (
            self.tab.USE_PRINTABLE_LAYOUT
            and hasattr(self.tab, "printable_displayer")
            and self.tab.printable_displayer
        ):
            printable_displayer: "PrintableDisplayer" = self.tab.printable_displayer
            if (
                hasattr(printable_displayer, "manager")
                and printable_displayer.manager.is_loading
            ):
                logging.debug(
                    f"Cancelling in-progress loading operation before loading length {length}"
                )
                printable_displayer.manager.cancel_loading()

            printable_displayer.display_sequences(length)
            self.tab._sync_pages_from_displayer()

    def on_level_filter_changed(
        self, selected_levels: List[int]
    ) -> None:  # Changed to List[int]
        """Handles level filter changes."""
        self.settings_manager_obj.save_levels(selected_levels)

        if self.tab.is_initializing:
            return

        self.ui_manager.clear_content_area()

        length_text = (
            f"{self.tab.currently_displayed_length}-step"
            if self.tab.currently_displayed_length > 0
            else "all"
        )
        if len(selected_levels) < 3:
            level_names = {1: "Basic", 2: "Intermediate", 3: "Advanced"}
            level_text = ", ".join(
                [level_names[lvl] for lvl in sorted(selected_levels)]
            )
            self.ui_manager.set_header_description(
                f"Loading {length_text} sequences (Levels: {level_text})..."
            )
        else:
            self.ui_manager.set_header_description(
                f"Loading {length_text} sequences..."
            )

        if (
            self.tab.USE_PRINTABLE_LAYOUT
            and hasattr(self.tab, "printable_displayer")
            and self.tab.printable_displayer
        ):
            printable_displayer: "PrintableDisplayer" = self.tab.printable_displayer
            if (
                hasattr(printable_displayer, "manager")
                and printable_displayer.manager.is_loading
            ):
                logging.debug(
                    "Cancelling in-progress loading operation before applying level filter"
                )
                printable_displayer.manager.cancel_loading()

            printable_displayer.display_sequences(
                self.tab.currently_displayed_length, selected_levels
            )
            self.tab._sync_pages_from_displayer()

    def load_sequences(self) -> None:
        """Loads sequences based on current filters."""
        selected_length = self.tab.nav_sidebar.selected_length
        length_text = f"{selected_length}-step" if selected_length > 0 else "all"
        self.ui_manager.set_header_description(f"Loading {length_text} sequences...")
        QApplication.processEvents()  # Ensure UI updates before potentially long operation

        if (
            self.tab.USE_PRINTABLE_LAYOUT
            and hasattr(self.tab, "printable_displayer")
            and self.tab.printable_displayer
        ):
            printable_displayer: "PrintableDisplayer" = self.tab.printable_displayer
            printable_displayer.display_sequences(selected_length)
            self.tab._sync_pages_from_displayer()
        else:
            # Handle non-printable layout if necessary, or log a warning
            logging.warning(
                "Printable Displayer not found, cannot load sequences in dictionary mode."
            )
