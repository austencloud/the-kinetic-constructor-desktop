# src/main_window/main_widget/sequence_card_tab/tab.py

from interfaces.settings_manager_interface import ISettingsManager


from typing import TYPE_CHECKING


class SequenceCardSettingsHandler:
    def __init__(self, settings_manager: ISettingsManager):
        self.settings_manager = settings_manager
        self.saved_column_count = 3
        self.saved_length = 16
        self.saved_levels = [1, 2, 3]
        self._load_settings()

    def _load_settings(self):
        if self.settings_manager:
            self.saved_column_count = int(
                self.settings_manager.get_setting(
                    "sequence_card_tab", "column_count", 3
                )
            )
            self.saved_length = int(
                self.settings_manager.get_setting(
                    "sequence_card_tab", "last_length", 16
                )
            )

            # Load selected levels using the sequence card tab settings
            if hasattr(self.settings_manager, "sequence_card_tab"):
                self.saved_levels = (
                    self.settings_manager.sequence_card_tab.get_selected_levels()
                )
            else:
                # Fallback for older settings format
                levels_str = self.settings_manager.get_setting(
                    "sequence_card_tab", "selected_levels", "1,2,3"
                )
                try:
                    self.saved_levels = [
                        int(x.strip()) for x in levels_str.split(",") if x.strip()
                    ]
                    self.saved_levels = [
                        lvl for lvl in self.saved_levels if 1 <= lvl <= 3
                    ]
                    if not self.saved_levels:
                        self.saved_levels = [1, 2, 3]
                except (ValueError, AttributeError):
                    self.saved_levels = [1, 2, 3]

        self.saved_column_count = int(self.saved_column_count)
        self.saved_length = int(self.saved_length)

    def save_length(self, length: int):
        if self.settings_manager:
            self.settings_manager.set_setting(
                "sequence_card_tab", "last_length", length
            )
        self.saved_length = length

    def save_levels(self, levels: list):
        """Save the selected difficulty levels."""
        if self.settings_manager:
            if hasattr(self.settings_manager, "sequence_card_tab"):
                self.settings_manager.sequence_card_tab.set_selected_levels(levels)
            else:
                # Fallback for older settings format
                levels_str = ",".join(map(str, sorted(levels)))
                self.settings_manager.set_setting(
                    "sequence_card_tab", "selected_levels", levels_str
                )
        self.saved_levels = levels

    def save_column_count(self, column_count: int):
        if self.settings_manager:
            self.settings_manager.set_setting(
                "sequence_card_tab", "column_count", column_count
            )
        self.saved_column_count = column_count
