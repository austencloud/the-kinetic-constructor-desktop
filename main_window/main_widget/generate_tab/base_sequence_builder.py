# base_classes/base_sequence_builder.py

import random
from typing import TYPE_CHECKING, Any

from Enums.letters import Letter, LetterConditions
from data.constants import (
    ANTI,
    BLUE,
    END_ORI,
    FLOAT,
    MOTION_TYPE,
    PRO,
    PROP_ROT_DIR,
    RED,
    DASH,
    START_ORI,
    STATIC,
    NO_ROT,
    CLOCKWISE,
    COUNTER_CLOCKWISE,
    TURNS,
)

from main_window.main_widget.generate_tab.sequence_builder_start_position_manager import (
    SequenceBuilderStartPosManager,
)
from main_window.main_widget.sequence_workbench.sequence_workbench import (
    SequenceWorkbench,
)
from main_window.settings_manager.global_settings.app_context import AppContext

if TYPE_CHECKING:
    from main_window.main_widget.generate_tab.generate_tab import GenerateTab


class BaseSequenceBuilder:
    """
    BaseSequenceBuilder is responsible for initializing and updating the
    sequence for the generator. It loads the current sequence from storage,
    adds a starting position if necessary, and updates orientations and beat numbers.
    """

    def __init__(self, generate_tab: "GenerateTab"):
        self.generate_tab = generate_tab
        self.sequence_workbench: SequenceWorkbench = None

        self.main_widget = generate_tab.main_widget
        self.validation_engine = self.main_widget.json_manager.ori_validation_engine
        self.json_manager = AppContext.json_manager()
        self.ori_calculator = self.main_widget.json_manager.ori_calculator
        self.start_pos_manager = SequenceBuilderStartPosManager(self.main_widget)

    def initialize_sequence(self, length: int) -> None:
        if not self.sequence_workbench:
            self.sequence_workbench = self.main_widget.sequence_workbench
        self.sequence = self.json_manager.loader_saver.load_current_sequence()

        if len(self.sequence) == 1:
            self.start_pos_manager.add_start_position()
            self.sequence = self.json_manager.loader_saver.load_current_sequence()

        try:
            self.sequence_workbench.sequence_beat_frame.populator.modify_layout_for_chosen_number_of_beats(
                int(length)
            )
        except Exception as e:
            print(f"Error updating layout for {length} beats: {e}")
            raise

    def update_start_orientations(
        self, next_data: dict[str, Any], last_data: dict[str, Any]
    ) -> None:
        """
        Updates the start orientations of the next beat based on the end orientations of the last beat.
        """
        blue_end_ori = last_data["blue_attributes"][END_ORI]
        red_end_ori = last_data["red_attributes"][END_ORI]

        if blue_end_ori is None or red_end_ori is None:
            raise ValueError(
                "End orientations cannot be None. Please ensure the previous beat has valid orientations."
            )

        next_data["blue_attributes"][START_ORI] = blue_end_ori
        next_data["red_attributes"][START_ORI] = red_end_ori


    def update_end_orientations(self, next_data: dict[str, Any]) -> None:
        """
        Updates the end orientations of the next beat using the orientation calculator.
        """
        next_data["blue_attributes"][END_ORI] = self.ori_calculator.calculate_end_ori(
            next_data, BLUE
        )
        blue_end_ori = self.ori_calculator.calculate_end_ori(next_data, BLUE)
        red_end_ori = self.ori_calculator.calculate_end_ori(next_data, RED)

        if blue_end_ori is None or red_end_ori is None:
            raise ValueError(
                "Calculated end orientations cannot be None. Please check the input data and orientation calculator."
            )

        next_data["blue_attributes"][END_ORI] = blue_end_ori
        next_data["red_attributes"][END_ORI] = red_end_ori

    def update_dash_static_prop_rot_dirs(
        self,
        next_beat: dict[str, Any],
        prop_continuity: str,
        blue_rot_dir: str,
        red_rot_dir: str,
    ) -> None:
        """
        Updates the prop rotation directions for dash/static motion types.
        """

        def update_attr(color: str, rot_dir: str):
            motion_data = next_beat[f"{color}_attributes"]
            if motion_data.get(MOTION_TYPE) in [DASH, STATIC]:
                turns = motion_data.get(TURNS, 0)
                if prop_continuity == "continuous":
                    motion_data[PROP_ROT_DIR] = rot_dir if turns > 0 else NO_ROT
                else:
                    if turns > 0:
                        self._set_random_prop_rot_dir(next_beat, color)
                    else:
                        motion_data[PROP_ROT_DIR] = NO_ROT

                if motion_data[PROP_ROT_DIR] == NO_ROT and turns > 0:
                    raise ValueError(
                        f"{color.capitalize()} prop rotation direction cannot be {NO_ROT} when turns are greater than 0."
                    )

        update_attr(BLUE, blue_rot_dir)
        update_attr(RED, red_rot_dir)

    def _set_random_prop_rot_dir(self, next_data: dict[str, Any], color: str) -> None:
        """Randomly sets the prop rotation direction for the specified color."""
        next_data[f"{color}_attributes"][PROP_ROT_DIR] = random.choice(
            [CLOCKWISE, COUNTER_CLOCKWISE]
        )

    def update_beat_number(
        self, next_data: dict[str, Any], sequence: list
    ) -> dict[str, Any]:
        """Sets the beat number based on the sequence length."""
        next_data["beat"] = len(sequence) - 1
        return next_data

    def filter_options_by_rotation(
        self, options: list[dict[str, Any]], blue_rot: str, red_rot: str
    ) -> list[dict[str, Any]]:
        """Filters options to match the given rotation directions."""
        filtered = [
            opt
            for opt in options
            if opt["blue_attributes"].get(PROP_ROT_DIR) in [blue_rot, NO_ROT]
            and opt["red_attributes"].get(PROP_ROT_DIR) in [red_rot, NO_ROT]
        ]
        return filtered if filtered else options

    def set_turns(
        self, next_beat: dict[str, Any], turn_blue: float, turn_red: float
    ) -> dict[str, Any]:
        """
        Sets the number of turns for both blue and red attributes.
        Adjusts motion types if special flag 'fl' is present.
        """
        # Blue turns
        if turn_blue == "fl" or turn_red == "fl":
            if Letter.get_letter(
                next_beat["letter"]
            ) in Letter.get_letters_by_condition(LetterConditions.TYPE1_HYBRID):
                return next_beat
        if turn_blue == "fl":
            if next_beat["blue_attributes"].get(MOTION_TYPE) in [PRO, ANTI]:
                next_beat["blue_attributes"][TURNS] = "fl"
                next_beat["blue_attributes"]["prefloat_motion_type"] = next_beat[
                    "blue_attributes"
                ][MOTION_TYPE]
                next_beat["blue_attributes"]["prefloat_prop_rot_dir"] = next_beat[
                    "blue_attributes"
                ][PROP_ROT_DIR]
                next_beat["blue_attributes"][MOTION_TYPE] = FLOAT
                next_beat["blue_attributes"][PROP_ROT_DIR] = NO_ROT
            elif next_beat["blue_attributes"].get(MOTION_TYPE) not in [PRO, ANTI]:
                next_beat["blue_attributes"][TURNS] = 0
        else:
            next_beat["blue_attributes"][TURNS] = turn_blue

        # Red turns
        if turn_red == "fl":
            if next_beat["red_attributes"].get(MOTION_TYPE) in [PRO, ANTI]:
                next_beat["red_attributes"][TURNS] = "fl"
                next_beat["red_attributes"]["prefloat_motion_type"] = next_beat[
                    "red_attributes"
                ][MOTION_TYPE]
                next_beat["red_attributes"]["prefloat_prop_rot_dir"] = next_beat[
                    "red_attributes"
                ][PROP_ROT_DIR]
                next_beat["red_attributes"][MOTION_TYPE] = FLOAT
                next_beat["red_attributes"][PROP_ROT_DIR] = NO_ROT
            elif next_beat["red_attributes"].get(MOTION_TYPE) not in [PRO, ANTI]:
                next_beat["red_attributes"][TURNS] = 0
        else:
            next_beat["red_attributes"][TURNS] = turn_red

        return next_beat
