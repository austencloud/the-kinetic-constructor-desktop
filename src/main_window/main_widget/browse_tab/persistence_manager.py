from typing import TYPE_CHECKING
from PyQt6.QtCore import QTimer

from src.settings_manager.global_settings.app_context import AppContext

from .thumbnail_box.thumbnail_box import ThumbnailBox

if TYPE_CHECKING:
    from .browse_tab import BrowseTab


class BrowseTabPersistenceManager:
    """
    Manages the persistence and restoration of the browse tab state.
    """

    def __init__(self, browse_tab: "BrowseTab") -> None:
        self.browse_tab = browse_tab
        self.preloading_paused = False
        self.thumbnail_queue = []

    def apply_saved_browse_state(self):
        """Applies the saved browse state on startup."""
        state = self.browse_tab.state
        sequence_picker = self.browse_tab.sequence_picker
        filter_controller = self.browse_tab.filter_controller

        section_name = state.get_current_section()
        if not section_name:
            sequence_picker.filter_stack.show_filter_selection_widget()
        else:
            sequence_picker.filter_stack.show_section(section_name)

        filter_criteria = state.get_current_filter()
        selected_seq = state.get_selected_sequence()

        if selected_seq:
            word = selected_seq.get("word")
            var_index = selected_seq.get("variation_index", 0)
            self.browse_tab.sequence_viewer.reopen_thumbnail(word, var_index)

        if filter_criteria:
            filter_controller.apply_filter(filter_criteria, fade=False)
