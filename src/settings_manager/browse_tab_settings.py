from datetime import datetime
import json
from typing import TYPE_CHECKING, Union


if TYPE_CHECKING:
    from settings_manager.settings_manager import SettingsManager


class BrowseTabSettings:
    DEFAULT_BROWSE_SETTINGS = {
        "sort_method": "sequence_length",
        "current_section": "starting_letter",
        "current_filter": {},
        # Simplified settings - always high quality, no cache
    }

    def __init__(self, settings_manager: "SettingsManager") -> None:
        self.settings_manager = settings_manager
        self.settings = self.settings_manager.settings

    def get_sort_method(self) -> str:
        return self.settings.value(
            "browse/sort_method", self.DEFAULT_BROWSE_SETTINGS["sort_method"]
        )

    def get_date_sub_sort_method(self) -> str:
        """Returns 'year', 'month', 'day', or 'full'."""
        return self.settings.value("browse/date_sub_sort_method", "full")

    def set_date_sub_sort_method(self, sub_method: str) -> None:
        """Stores the user's sub-sorting choice for date-based sorts."""
        # sub_method should be one of: 'year', 'month', 'day', 'full'
        self.settings.setValue("browse/date_sub_sort_method", sub_method)

    def set_sort_method(self, sort_method: str) -> None:
        self.settings.setValue("browse/sort_method", sort_method)

    def get_current_filter(self) -> Union[str, dict, datetime]:
        json_string = self.settings.value("browse/current_filter", "")
        if not json_string:
            return {}
        try:
            data = json.loads(json_string)
        except (ValueError, TypeError):
            return {}

        if (
            isinstance(data, dict)
            and "__string__" in data
            and isinstance(data["__string__"], str)
        ):
            return data["__string__"]
        elif (
            isinstance(data, dict)
            and "__datetime__" in data
            and isinstance(data["__datetime__"], str)
        ):
            try:
                return datetime.fromisoformat(data["__datetime__"])
            except ValueError:
                return data
        return data

    def set_current_filter(self, filter_criteria: Union[str, dict, datetime]) -> None:
        def default_serializer(obj):
            if isinstance(obj, datetime):
                return {"__datetime__": obj.isoformat()}
            raise TypeError(f"Type {type(obj)} not serializable")

        if isinstance(filter_criteria, str):
            data = {"__string__": filter_criteria}
        elif isinstance(filter_criteria, datetime):
            data = {"__datetime__": filter_criteria.isoformat()}
        else:
            data = filter_criteria
        json_string = json.dumps(data, default=default_serializer)
        self.settings.setValue("browse/current_filter", json_string)

    def get_current_section(self) -> str:
        return self.settings.value(
            "browse/current_section",
            self.DEFAULT_BROWSE_SETTINGS["current_section"],
        )

    def set_current_section(self, section: str) -> None:
        self.settings.setValue("browse/current_section", section)

    def get_browse_left_stack_index(self) -> int:
        return self.settings.value("browse/browse_left_stack_index", 4, type=int)

    def set_browse_left_stack_index(self, index: int) -> None:
        self.settings.setValue("browse/browse_left_stack_index", index)

    def get_browse_right_stack_index(self) -> int:
        return self.settings.value("browse/browse_right_stack_index", 6, type=int)

    def set_browse_right_stack_index(self, index: int) -> None:
        self.settings.setValue("browse/browse_right_stack_index", index)

    def get_selected_sequence(self) -> dict:
        json_string = self.settings.value("browse/selected_sequence", "{}")
        try:
            data = json.loads(json_string)
        except (ValueError, TypeError):
            return {}
        return data

    def set_selected_sequence(self, data: dict) -> None:
        json_string = json.dumps(data, ensure_ascii=False).encode("utf8").decode()
        self.settings.setValue("browse/selected_sequence", json_string)

    def get_browse_ratio(self) -> float:
        return self.settings.value("browse/browse_ratio", 0.6667, type=float)

    def set_browse_ratio(self, ratio: float) -> None:
        self.settings.setValue("browse/browse_ratio", ratio)

    # Removed all cache settings - now using simplified high-quality only approach

    def get_thumbnail_processing_settings(self) -> dict:
        """Get thumbnail processing settings - always high quality, no cache."""
        return {
            "scaling_algorithm": "smooth",  # Always use smooth scaling
            "multi_step_scaling": True,  # Always use multi-step for best quality
            "intermediate_scale_factor": 0.7,
            "sharpening_enabled": True,  # Always enable sharpening
            "enhancement_enabled": True,  # Always enable enhancement
            "ultra_quality_enabled": True,  # Always enable ultra quality
            "quality_priority": "high",  # Always high quality
            "max_source_resolution": 4096,  # Maximum source image resolution
            "target_dpi": 96,  # Target DPI for display
        }

    # Removed individual quality settings - now always high quality
