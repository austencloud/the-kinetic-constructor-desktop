from typing import TYPE_CHECKING
from Enums.PropTypes import PropType
from base_widgets.pictograph.pictograph import Pictograph
from main_window.main_widget.font_color_updater.font_color_updater import (
    FontColorUpdater,
)
from .prop_type_changer import PropTypeChanger

if TYPE_CHECKING:
    from ..settings_manager import SettingsManager


class GlobalSettings:
    def __init__(self, settings_manager: "SettingsManager") -> None:
        self.settings = settings_manager.settings
        self.settings_manager = settings_manager
        self.prop_type_changer = PropTypeChanger(self.settings_manager)

    def get_grow_sequence(self) -> bool:
        return self.settings.value("global/grow_sequence", True, type=bool)

    def set_grow_sequence(self, grow_sequence: bool) -> None:
        self.settings.setValue("global/grow_sequence", grow_sequence)

    def get_prop_type(self) -> PropType:
        prop_type_key: str = self.settings.value("global/prop_type", "Staff")
        prop_type_key = prop_type_key.capitalize()
        return PropType[prop_type_key]

    def set_prop_type(
        self, prop_type: PropType, pictographs: list["Pictograph"]
    ) -> None:
        self.settings.setValue("global/prop_type", prop_type.name)
        self.prop_type_changer.apply_prop_type(pictographs)

    def get_background_type(self) -> str:
        return self.settings.value("global/background_type", "Snowfall")

    def set_background_type(self, background_type: str) -> None:
        self.settings.setValue("global/background_type", background_type)
        self.settings_manager.background_changed.emit(background_type)

    def get_current_font_color(self) -> str:
        return FontColorUpdater.get_font_color(self.get_background_type())

    def get_current_tab(self) -> str:
        return self.settings.value("global/current_tab", "sequence_builder")

    def set_current_tab(self, tab: str) -> None:
        self.settings.setValue("global/current_tab", tab)

    def get_grid_mode(self) -> str:
        return self.settings.value("global/grid_mode", "diamond")

    def set_grid_mode(self, grid_mode: str) -> None:
        self.settings.setValue("global/grid_mode", grid_mode)

    def get_show_welcome_screen(self) -> bool:
        return self.settings.value("global/show_welcome_screen", True, type=bool)

    def set_show_welcome_screen(self, show_welcome_screen: bool) -> None:
        self.settings.setValue("global/show_welcome_screen", show_welcome_screen)

    def get_enable_fades(self) -> bool:
        return self.settings.value("global/enable_fades", True, type=bool)

    def set_enable_fades(self, enable: bool) -> None:
        self.settings.setValue("global/enable_fades", enable)
