import json
from typing import TYPE_CHECKING
from data.constants import DIAMOND
from main_window.main_widget.sequence_level_evaluator import SequenceLevelEvaluator
from main_window.main_widget.sequence_properties_manager.sequence_properties_manager import (
    SequencePropertiesManager,
)
from main_window.settings_manager.global_settings.app_context import AppContext
from utilities.path_helpers import get_user_editable_resource_path
from utilities.word_simplifier import WordSimplifier

if TYPE_CHECKING:
    pass


class SequenceDataLoaderSaver:
    def __init__(self) -> None:
        self.current_sequence_json = get_user_editable_resource_path(
            "current_sequence.json"
        )
        self.sequence_properties_manager = SequencePropertiesManager()

    def load_current_sequence(self) -> list[dict]:
        try:
            with open(self.current_sequence_json, "r", encoding="utf-8") as file:
                content = file.read().strip()
                if not content:
                    return self.get_default_sequence()

                sequence = json.loads(content)
                if not sequence or not isinstance(sequence, list):
                    return self.get_default_sequence()

            return sequence

        except (FileNotFoundError, json.JSONDecodeError):
            return self.get_default_sequence()

    def get_default_sequence(self) -> list[dict]:
        """Return a default sequence if JSON is missing, empty, or invalid."""
        return [
            {
                "word": "",
                "author": AppContext.settings_manager().users.user_manager.get_current_user(),
                "level": 0,
                "prop_type": AppContext.settings_manager()
                .global_settings.get_prop_type()
                .name.lower(),
                "grid_mode": DIAMOND,
                "is_circular": False,
                "is_permutable": False,
                "is_strictly_rotated_permutation": False,
                "is_strictly_mirrored_permutation": False,
                "is_strictly_colorswapped_permutation": False,
                "is_mirrored_color_swapped_permutation": False,
                "is_rotated_colorswapped_permutation": False,
            }
        ]

    def save_current_sequence(self, sequence: list[dict]):
        if not sequence:
            sequence = self.get_default_sequence()
        else:
            sequence[0]["word"] = WordSimplifier.simplify_repeated_word(
                self.sequence_properties_manager.calculate_word(sequence)
            )
            if "author" not in sequence[0]:
                sequence[0][
                    "author"
                ] = AppContext.settings_manager().users.user_manager.get_current_user()
            if "level" not in sequence[0]:
                sequence[0]["level"] = (
                    SequenceLevelEvaluator.get_sequence_difficulty_level(sequence)
                )
            if "prop_type" not in sequence[0]:
                sequence[0]["prop_type"] = (
                    AppContext.settings_manager()
                    .global_settings.get_prop_type()
                    .name.lower()
                )
            if "is_circular" not in sequence[0]:
                sequence[0]["is_circular"] = False
            if "is_permutable" not in sequence[0]:
                sequence[0]["is_permutable"] = False

        # Add beat numbers to each beat at the beginning
        beat_number = 0
        for beat in sequence:
            if "letter" in beat or "sequence_start_position" in beat:
                beat_dict_with_beat_number = {"beat": beat_number}
                beat_dict_with_beat_number.update(beat)
                sequence[sequence.index(beat)] = beat_dict_with_beat_number
                beat_number += 1

        with open(self.current_sequence_json, "w", encoding="utf-8") as file:
            json.dump(sequence, file, indent=4, ensure_ascii=False)

    def clear_current_sequence_file(self):
        self.save_current_sequence([])

    def get_json_prop_rot_dir(self, index: int, color: str) -> int:
        sequence = self.load_current_sequence()
        if sequence:
            return sequence[index][f"{color}_attributes"].get("prop_rot_dir", 0)
        return 0

    def get_json_motion_type(self, index: int, color: str) -> int:
        sequence = self.load_current_sequence()
        if sequence:
            return sequence[index][f"{color}_attributes"].get("motion_type", 0)
        return 0

    def get_json_prefloat_prop_rot_dir(self, index: int, color: str) -> int:
        sequence = self.load_current_sequence()
        if sequence:
            return sequence[index][f"{color}_attributes"].get(
                "prefloat_prop_rot_dir", ""
            )
        return 0

    def get_json_prefloat_motion_type(self, index: int, color: str) -> int:
        sequence = self.load_current_sequence()
        if sequence:
            return sequence[index][f"{color}_attributes"].get(
                "prefloat_motion_type",
                sequence[index][f"{color}_attributes"].get("motion_type", 0),
            )
        return 0

    def get_red_end_ori(self, sequence):
        last_pictograph_data = (
            sequence[-1]
            if sequence[-1].get("is_placeholder", "") != True
            else sequence[-2]
        )

        if sequence:
            return last_pictograph_data["red_attributes"]["end_ori"]
        return 0

    def get_blue_end_ori(self, sequence):
        last_pictograph_data = (
            sequence[-1]
            if sequence[-1].get("is_placeholder", "") != True
            else sequence[-2]
        )

        if sequence:
            return last_pictograph_data["blue_attributes"]["end_ori"]
        return 0

    def load_last_beat_dict(self) -> dict:
        sequence = self.load_current_sequence()
        if sequence:
            return sequence[-1]
        return {}
