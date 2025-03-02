import json
from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from settings_manager.settings_manager import SettingsManager


class BrowseTabSettings:
    DEFAULT_BROWSE_SETTINGS = {
        "sort_method": "sequence_length",
        "current_section": "starting_letter",
        "current_filter": {},
    }

    def __init__(self, settings_manager: "SettingsManager") -> None:
        self.settings_manager = settings_manager
        self.settings = self.settings_manager.settings

    def get_sort_method(self) -> str:
        return self.settings.value(
            "browse/sort_method", self.DEFAULT_BROWSE_SETTINGS["sort_method"]
        )

    def set_sort_method(self, sort_method: str) -> None:
        self.settings.setValue("browse/sort_method", sort_method)

    def get_current_filter(self) -> Union[str, dict]:
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
        return data

    def set_current_filter(self, filter_criteria: Union[str, dict]) -> None:
        if isinstance(filter_criteria, str):
            data = {"__string__": filter_criteria}
        else:
            data = filter_criteria
        json_string = json.dumps(data)
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
        json_string = json.dumps(data, ensure_ascii=False).encode('utf8').decode()
        self.settings.setValue("browse/selected_sequence", json_string)

    def get_browse_ratio(self) -> float:
        return self.settings.value("browse/browse_ratio", 0.6667, type=float)

    def set_browse_ratio(self, ratio: float) -> None:
        self.settings.setValue("browse/browse_ratio", ratio)
