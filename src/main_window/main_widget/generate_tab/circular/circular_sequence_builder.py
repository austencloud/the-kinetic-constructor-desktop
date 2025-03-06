from typing import TYPE_CHECKING
from PyQt6.QtWidgets import QApplication
import random
from copy import deepcopy
from PyQt6.QtCore import Qt
from data.constants import (
    BLUE_ATTRS,
    CLOCKWISE,
    COUNTER_CLOCKWISE,
    DASH,
    END_POS,
    MOTION_TYPE,
    RED_ATTRS,
    STATIC,
)
from data.position_maps import (
    half_position_map,
    quarter_position_map_cw,
    quarter_position_map_ccw, position_swap_mapping
)
from data.quartered_CAPs import quartered_CAPs
from data.halved_CAPs import halved_CAPs
from .CAP_executors.CAP_executor import CAPExecutor
from .CAP_executors.CAP_executor_factory import CAPExecutorFactory
from .CAP_executors.CAP_type import CAPType
from ..base_sequence_builder import BaseSequenceBuilder
from ..turn_intensity_manager import TurnIntensityManager


if TYPE_CHECKING:
    from main_window.main_widget.generate_tab.generate_tab import GenerateTab


class CircularSequenceBuilder(BaseSequenceBuilder):
    def __init__(self, generate_tab: "GenerateTab"):
        super().__init__(generate_tab)
        self.executors: dict[CAPType, CAPExecutor] = {
            CAPType.STRICT_ROTATED: CAPExecutorFactory.create_executor(
                CAPType.STRICT_ROTATED, self
            ),
            CAPType.STRICT_MIRRORED: CAPExecutorFactory.create_executor(
                CAPType.STRICT_MIRRORED, self
            ),
            CAPType.STRICT_SWAPPED: CAPExecutorFactory.create_executor(
                CAPType.STRICT_SWAPPED, self
            ),
        }

    def build_sequence(
        self,
        length: int,
        turn_intensity: int,
        level: int,
        slice_size: str,
        CAP_type: str,
        prop_continuity: bool,
    ):
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        self.initialize_sequence(length, CAP_type=CAP_type)

        if prop_continuity == "continuous":
            blue_rot_dir = random.choice([CLOCKWISE, COUNTER_CLOCKWISE])
            red_rot_dir = random.choice([CLOCKWISE, COUNTER_CLOCKWISE])
        elif prop_continuity == "random":
            blue_rot_dir = None
            red_rot_dir = None

        length_of_sequence_upon_start = len(self.sequence) - 2

        if CAP_type == CAPType.STRICT_ROTATED:
            if slice_size == "quartered":
                word_length = length // 4
            elif slice_size == "halved":
                word_length = length // 2
            available_range = word_length - length_of_sequence_upon_start
        elif CAP_type == CAPType.STRICT_MIRRORED or CAP_type == CAPType.STRICT_SWAPPED:
            word_length = length // 2
            available_range = word_length - length_of_sequence_upon_start

        turn_manager = TurnIntensityManager(word_length, level, turn_intensity)
        turns_blue, turns_red = turn_manager.allocate_turns_for_blue_and_red()

        for i in range(available_range):
            is_last_in_word = i == word_length - length_of_sequence_upon_start - 1
            next_pictograph = self._generate_next_pictograph(
                level,
                turns_blue[i],
                turns_red[i],
                is_last_in_word,
                slice_size,
                CAP_type,
                prop_continuity,
                blue_rot_dir,
                red_rot_dir,
            )
            self.sequence.append(next_pictograph)
            self.sequence_workbench.beat_frame.beat_factory.create_new_beat_and_add_to_sequence(
                next_pictograph,
                override_grow_sequence=True,
                update_image_export_preview=False,
            )

            QApplication.processEvents()

        self._apply_CAPs(self.sequence, CAP_type, slice_size)

        construct_tab = self.main_widget.construct_tab
        construct_tab.option_picker.updater.update_options()

        QApplication.restoreOverrideCursor()
        self.sequence_workbench.beat_frame.emit_update_image_export_preview()

    def _generate_next_pictograph(
        self,
        level: int,
        turn_blue: float,
        turn_red: float,
        is_last_in_word: bool,
        rotation_type: str,
        CAP_type: str,
        prop_continuity: str,
        blue_rot_dir: str,
        red_rot_dir: str,
    ) -> dict:
        options = self.main_widget.construct_tab.option_picker.option_getter._load_all_next_option_dicts(
            self.sequence
        )
        options = [deepcopy(option) for option in options]
        if prop_continuity == "continuous":
            options = self.filter_options_by_rotation(
                options, blue_rot_dir, red_rot_dir
            )
        if CAP_type == CAPType.STRICT_ROTATED:
            if is_last_in_word:
                expected_end_pos = self._determine_rotated_end_pos(rotation_type)
                next_beat = self._select_pictograph_with_end_pos(
                    options, expected_end_pos
                )
            else:
                next_beat = random.choice(options)
        elif CAP_type == CAPType.STRICT_MIRRORED:
            if is_last_in_word:
                expected_end_pos = self.sequence[1][END_POS]
                next_beat = self._select_pictograph_with_end_pos(
                    options, expected_end_pos
                )
            else:
                next_beat = random.choice(options)
        elif CAP_type == CAPType.STRICT_SWAPPED:
            if is_last_in_word:
                expected_end_pos = self.get_expected_end_pos_for_swapped(
                    self.sequence[1][END_POS]
                )
                next_beat = self._select_pictograph_with_end_pos(
                    options, expected_end_pos
                )
            else:
                next_beat = random.choice(options)

        if level == 2 or level == 3:
            next_beat = self.set_turns(next_beat, turn_blue, turn_red)
        if next_beat[BLUE_ATTRS][MOTION_TYPE] in [DASH, STATIC] or next_beat[RED_ATTRS][
            MOTION_TYPE
        ] in [DASH, STATIC]:
            self.update_dash_static_prop_rot_dirs(
                next_beat,
                prop_continuity,
                blue_rot_dir,
                red_rot_dir,
            )
        self.update_start_orientations(next_beat, self.sequence[-1])
        self.update_end_orientations(next_beat)

        next_beat = self.update_beat_number(next_beat, self.sequence)
        return next_beat

    def get_expected_end_pos_for_swapped(self, start_pos: str) -> str:

        return position_swap_mapping.get(start_pos, None)

    def _determine_rotated_end_pos(self, slice_size: str) -> str:
        """Determine the expected end position based on rotation type and current sequence."""
        start_pos = self.sequence[1][END_POS]

        if slice_size == "quartered":
            if random.choice([True, False]):
                return quarter_position_map_cw[start_pos]
            else:
                return quarter_position_map_ccw[start_pos]
        elif slice_size == "halved":
            return half_position_map[start_pos]
        else:
            print("Invalid slice size - expected 'quartered' or 'halved'")
            return None

    def _select_pictograph_with_end_pos(
        self, options: list[dict], expected_end_pos: str
    ) -> dict:
        """Select a pictograph from options that has the desired end position."""
        valid_options = [
            option for option in options if option[END_POS] == expected_end_pos
        ]
        if not valid_options:
            raise ValueError(
                f"No valid pictograph found with end position {expected_end_pos}."
            )
        return random.choice(valid_options)

    def _apply_CAPs(
        self, sequence: list[dict], cap_type: CAPType, rotation_type: str
    ) -> None:
        executor = self.executors.get(cap_type)
        if executor:
            if cap_type == CAPType.STRICT_ROTATED:
                if self.can_perform_strict_rotated_CAP(sequence, rotation_type):
                    executor.create_CAPs(sequence)
            elif cap_type == CAPType.STRICT_MIRRORED:
                if self.can_perform_strict_mirrored_CAP(sequence):
                    executor.create_CAPs(sequence)
            elif cap_type == CAPType.STRICT_SWAPPED:
                if executor.can_perform_CAP(sequence):
                    executor.create_CAPs(sequence)

    def can_perform_strict_rotated_CAP(
        self, sequence: list[dict], rotation_type: str
    ) -> bool:
        start_pos = sequence[1][END_POS]
        end_pos = sequence[-1][END_POS]
        if rotation_type == "quartered":
            return (start_pos, end_pos) in quartered_CAPs
        elif rotation_type == "halved":
            return (start_pos, end_pos) in halved_CAPs

    def can_perform_strict_mirrored_CAP(self, sequence: list[dict]) -> bool:
        """Ensures that the sequence can be mirrored."""
        return sequence[1][END_POS] == sequence[-1][END_POS]
