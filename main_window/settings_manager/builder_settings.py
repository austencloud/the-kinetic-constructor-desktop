from typing import TYPE_CHECKING
from main_window.settings_manager.generate_tab_settings import (
    GenerateTabSettings,
)
from main_window.settings_manager.construct_tab_settings import ConstructTabSettings

if TYPE_CHECKING:
    from main_window.settings_manager.settings_manager import SettingsManager


class BuilderSettings:
    DEFAULT_BUILDER_SETTINGS = {
        "construct_tab": {},
    }

    def __init__(self, settings_manager: "SettingsManager") -> None:
        self.settings_manager = settings_manager
        self.settings = self.settings_manager.settings  # QSettings instance


