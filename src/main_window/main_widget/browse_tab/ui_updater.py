from typing import TYPE_CHECKING
from PyQt6.QtWidgets import QApplication
from .thumbnail_box.thumbnail_box import ThumbnailBox
from src.settings_manager.global_settings.app_context import AppContext
from .sequence_picker.nav_sidebar.button.button_ui_updater import (
    SidebarButtonUIUpdater,
)
from .thumbnail_box.ui_updater import ThumbnailBoxUIUpdater

if TYPE_CHECKING:
    from main_window.main_widget.browse_tab.browse_tab import BrowseTab


class BrowseTabUIUpdater:
    """Updates the Browse Tab UI, managing thumbnails and navigation."""

    def __init__(self, browse_tab: "BrowseTab"):
        self.browse_tab = browse_tab
        self.settings_manager = AppContext.settings_manager()
        self.thumbnail_updater = ThumbnailBoxUIUpdater(browse_tab)
        self.sidebar_button_updater = SidebarButtonUIUpdater(browse_tab)
        self._resize_job_id = 0
        self._last_window_width = None

    def update_and_display_ui(self, total_sequences: int, skip_scaling: bool = True):
        """Updates and displays the UI based on the total number of sequences."""
        QApplication.restoreOverrideCursor()

        if total_sequences == 0:
            return

        self._sort_sequences()
        self._create_and_show_thumbnails(skip_scaling)

    def _sort_sequences(self):
        """Sorts the sequences in the sequence picker."""
        sort_method = self.settings_manager.browse_settings.get_sort_method()
        self.browse_tab.sequence_picker.sorter._sort_only(sort_method)

    def _create_and_show_thumbnails(self, skip_scaling: bool = True):
        """Creates and displays thumbnails, applying styling."""
        self.browse_tab.sequence_picker.sorter.display_sorted_sections(skip_scaling)
        background_type = self.settings_manager.global_settings.get_background_type()
        self.thumbnail_updater.apply_thumbnail_styling(background_type)

    def resize_thumbnails_top_to_bottom(self):
        """Resizes thumbnails from top to bottom, enabling navigation buttons."""

        sections_copy = dict(self.browse_tab.sequence_picker.sections)
        sort_method = self.settings_manager.browse_settings.get_sort_method()
        sorted_sections = (
            self.browse_tab.sequence_picker.section_manager.get_sorted_sections(
                sort_method, sections_copy.keys()
            )
        )

        self.sidebar_button_updater.disable_all_buttons()

        scroll_widget = self.browse_tab.sequence_picker.scroll_widget
        for section in sorted_sections:
            if section not in sections_copy:
                return
            for word, _ in self.browse_tab.sequence_picker.sections.get(section, []):
                if word not in scroll_widget.thumbnail_boxes:
                    return

                # CRITICAL FIX: Remove tab check that was preventing thumbnail loading during startup
                # The tab check was causing thumbnails to not load when the app starts in browse tab
                # because the tab state might not be properly set during initialization

                thumbnail_box = scroll_widget.thumbnail_boxes[word]

                # Use asynchronous thumbnail loading to prevent UI blocking
                self.thumbnail_updater.update_thumbnail_image_async(thumbnail_box)
            if sort_method == "date_added":
                month, day, _ = section.split("-")
                day = day.lstrip("0")
                month = month.lstrip("0")
                section = f"{month}-{day}"

            self._enable_button_for_section(section)

    def _enable_button_for_section(self, section_key: str):
        """Enables a specific navigation button by section key."""
        self.sidebar_button_updater.enable_button_for_section(section_key)
