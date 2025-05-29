from typing import TYPE_CHECKING
from PyQt6.QtWidgets import QApplication
from ....thumbnail_box.thumbnail_box import ThumbnailBox
from src.settings_manager.global_settings.app_context import AppContext

if TYPE_CHECKING:
    from main_window.main_widget.browse_tab.browse_tab import BrowseTab


class SidebarButtonUIUpdater:
    """Handles enabling/disabling navigation buttons."""

    def __init__(self, browse_tab: "BrowseTab"):
        self.browse_tab = browse_tab

    def enable_button_for_section(self, section_key: str):
        """Enables the navigation button associated with the given section key."""
        for btn in self.browse_tab.sequence_picker.nav_sidebar.manager.buttons:
            if getattr(btn, "section_key", None) == section_key:
                btn.setEnabled(True)
                break

    def disable_all_buttons(self):
        """Disables all navigation buttons."""
        for button in self.browse_tab.sequence_picker.nav_sidebar.manager.buttons:
            button.setEnabled(False)
