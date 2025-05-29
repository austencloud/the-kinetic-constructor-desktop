from typing import TYPE_CHECKING



if TYPE_CHECKING:
    from settings_manager.browse_tab_settings import BrowseTabSettings


class BrowseTabState:
    """
    Encapsulates the state of the BrowseTab, including the currently selected
    section, filter criteria, and selected sequence.  Handles persistence
    of this state to settings.
    """

    def __init__(self, browse_settings: "BrowseTabSettings") -> None:
        self.browse_settings = browse_settings
        self._current_section: str = ""
        self._current_filter: str = ""
        self._selected_sequence: dict = {}

        self.load_state()

    def load_state(self):
        """Loads the browse tab state from settings."""
        self._current_section = self.browse_settings.get_current_section() or ""
        self._current_filter = self.browse_settings.get_current_filter() or ""
        self._selected_sequence = self.browse_settings.get_selected_sequence() or {}

    def save_state(self):
        """Saves the browse tab state to settings."""
        self.browse_settings.set_current_section(self._current_section)
        self.browse_settings.set_current_filter(self._current_filter)
        self.browse_settings.set_selected_sequence(self._selected_sequence)

    def clear_state(self):
        """Clears the browse tab state."""
        self._current_section = ""
        self._current_filter = ""
        self._selected_sequence = {}
        self.save_state()

    def set_current_section(self, section_name: str):
        """Sets the current section name."""
        self._current_section = section_name
        self.save_state()

    def get_current_section(self) -> str:
        """Gets the current section name."""
        return self._current_section

    def set_current_filter(self, filter_criteria: str):
        """Sets the current filter criteria."""
        self._current_filter = filter_criteria
        self.save_state()

    def get_current_filter(self) -> str:
        """Gets the current filter criteria."""
        return self._current_filter

    def set_selected_sequence(self, selected_sequence: dict):
        """Sets the selected sequence."""
        self._selected_sequence = selected_sequence
        self.save_state()

    def get_selected_sequence(self) -> dict:
        """Gets the selected sequence."""
        return self._selected_sequence
