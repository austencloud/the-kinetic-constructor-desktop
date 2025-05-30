import logging
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from src.interfaces.settings_manager_interface import ISettingsManager


class SettingsPersistenceManager:
    def __init__(self, settings_manager: Optional["ISettingsManager"] = None):
        self.settings_manager = settings_manager
        self.logger = logging.getLogger(__name__)

        if self.settings_manager:
            self.logger.info("Generation controls settings persistence enabled")
        else:
            self.logger.warning(
                "Settings manager not provided to GenerationControlsPanel"
            )

    def load_saved_settings(self) -> dict:
        if not self.settings_manager:
            return self._get_default_settings()

        try:
            return {
                "start_position": self.settings_manager.get_setting(
                    "generation_controls", "start_position", "Any"
                ),
                "length": self.settings_manager.get_setting(
                    "generation_controls", "length", "16"
                ),
                "level": self.settings_manager.get_setting(
                    "generation_controls", "level", "1 - Basic (No turns)"
                ),
                "turn_intensity": self.settings_manager.get_setting(
                    "generation_controls", "turn_intensity", "1"
                ),
                "generation_mode": self.settings_manager.get_setting(
                    "generation_controls", "generation_mode", "Freeform"
                ),
                "prop_continuity": self.settings_manager.get_setting(
                    "generation_controls", "prop_continuity", "Continuous"
                ),
                "batch_size": self.settings_manager.get_setting(
                    "generation_controls", "batch_size", "5"
                ),
            }
        except Exception as e:
            self.logger.error(f"Error loading saved settings: {e}")
            return self._get_default_settings()

    def save_settings(self, values: dict):
        if not self.settings_manager:
            return

        try:
            for key, value in values.items():
                self.settings_manager.set_setting("generation_controls", key, value)
            self.logger.debug("Saved generation controls settings")
        except Exception as e:
            self.logger.error(f"Error saving settings: {e}")

    def _get_default_settings(self) -> dict:
        return {
            "start_position": "Any",
            "length": "16",
            "level": "1 - Basic (No turns)",
            "turn_intensity": "1",
            "generation_mode": "Freeform",
            "prop_continuity": "Continuous",
            "batch_size": "5",
        }
