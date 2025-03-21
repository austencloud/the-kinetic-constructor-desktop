from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from settings_manager.settings_manager import SettingsManager


class VisibilitySettings:
    def __init__(self, settings_manager: "SettingsManager") -> None:
        self.settings_manager = settings_manager
        self.settings = self.settings_manager.settings

    def get_glyph_visibility(self, glyph_type: str) -> bool:
        # Set default visibility - only TKA and Reversals visible by default
        default_visibility = glyph_type in ["TKA", "Reversals"]

        return self.settings.value(
            f"visibility/{glyph_type}",
            default_visibility,  # Use appropriate default based on glyph type
            type=bool,
        )

    def set_glyph_visibility(self, glyph_type: str, visible: bool) -> None:
        self.settings.setValue(f"visibility/{glyph_type}", visible)

    def get_non_radial_visibility(self) -> bool:
        return self.settings.value(f"visibility/non_radial_points", False, type=bool)

    def set_non_radial_visibility(self, visible: bool):
        self.settings.setValue(f"visibility/non_radial_points", visible)
