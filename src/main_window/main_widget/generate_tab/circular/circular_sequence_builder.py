from typing import TYPE_CHECKING
from PyQt6.QtWidgets import QApplication
import random
from copy import deepcopy
from PyQt6.QtCore import Qt
from data.constants import (
    BLUE_ATTRS,
    DASH,
    END_POS,
    MOTION_TYPE,
    RED_ATTRS,
    STATIC,
)
from data.positions_maps import (
    swapped_positions,
    mirrored_positions,
    mirrored_swapped_positions,
)
from .CAP_executors.CAP_executor import CAPExecutor
from .CAP_type import CAPType
from ..base_sequence_builder import BaseSequenceBuilder
from ..turn_intensity_manager import TurnIntensityManager
from .utils.rotation_determiner import RotationDeterminer
from .utils.end_position_selector import RotatedEndPositionSelector
from .utils.pictograph_selector import PictographSelector
from .utils.word_length_calculator import WordLengthCalculator
from .CAP_executor_factory import CAPExecutorFactory
from data.constants import *

if TYPE_CHECKING:
    from main_window.main_widget.generate_tab.generate_tab import GenerateTab


class CircularSequenceBuilder(BaseSequenceBuilder):
    def __init__(self, generate_tab: "GenerateTab"):
        super().__init__(generate_tab)
        self.executors: dict[CAPType, CAPExecutor] = {
            cap_type: CAPExecutorFactory.create_executor(cap_type, self)
            for cap_type in CAPType
        }

    def build_sequence(
        self, length, turn_intensity, level, slice_size, CAP_type, prop_continuity
    ):
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            self.initialize_sequence(length, CAP_type=CAP_type)

            blue_rot_dir, red_rot_dir = RotationDeterminer.get_rotation_dirs(
                prop_continuity
            )

            word_length, available_range = WordLengthCalculator.calculate(
                CAP_type, slice_size, length, len(self.sequence)
            )

            turn_manager = TurnIntensityManager(word_length, level, turn_intensity)
            turns_blue, turns_red = turn_manager.allocate_turns_for_blue_and_red()

            for i in range(available_range):
                is_last_in_word = i == available_range - 1
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

        finally:
            QApplication.restoreOverrideCursor()
            self.main_widget.generate_tab.auto_complete_button.setEnabled(False)
            self.sequence_workbench.beat_frame.emit_update_image_export_preview()

    def _generate_next_pictograph(
        self,
        level,
        turn_blue,
        turn_red,
        is_last_in_word,
        slice_size,
        CAP_type,
        prop_continuity,
        blue_rot_dir,
        red_rot_dir,
    ):
        options = deepcopy(
            self.main_widget.construct_tab.option_picker.option_getter._load_all_next_option_dicts(
                self.sequence
            )
        )
        if prop_continuity == "continuous":
            options = self.filter_options_by_rotation(
                options, blue_rot_dir, red_rot_dir
            )

        if is_last_in_word:
            if CAP_type == CAPType.STRICT_ROTATED:
                expected_end_pos = RotatedEndPositionSelector.determine_rotated_end_pos(
                    slice_size, self.sequence[1][END_POS]
                )
            elif CAP_type == CAPType.STRICT_MIRRORED:

                expected_end_pos = mirrored_positions[VERTICAL][
                    self.sequence[1][END_POS]
                ]
            elif CAP_type == CAPType.MIRRORED_SWAPPED:
                expected_end_pos = mirrored_swapped_positions[VERTICAL][
                    self.sequence[1][END_POS]
                ]

            elif CAP_type == CAPType.STRICT_SWAPPED:
                expected_end_pos = swapped_positions[self.sequence[1][END_POS]]
            elif CAP_type == CAPType.SWAPPED_COMPLEMENTARY:
                expected_end_pos = swapped_positions[self.sequence[1][END_POS]]
            elif CAP_type == CAPType.STRICT_COMPLEMENTARY:
                expected_end_pos = self.sequence[1][END_POS]
            elif CAP_type == CAPType.ROTATED_COMPLEMENTARY:
                expected_end_pos = RotatedEndPositionSelector.determine_rotated_end_pos(
                    "halved", self.sequence[1][END_POS]
                )
            else:
                raise ValueError(
                    "CAP type not implemented yet. Please implement the CAP type."
                )
            next_beat = PictographSelector.select_pictograph(options, expected_end_pos)
        else:
            next_beat = random.choice(options)

        if level in (2, 3):
            next_beat = self.set_turns(next_beat, turn_blue, turn_red)

        if next_beat[BLUE_ATTRS][MOTION_TYPE] in [DASH, STATIC] or next_beat[RED_ATTRS][
            MOTION_TYPE
        ] in [DASH, STATIC]:
            self.update_dash_static_prop_rot_dirs(
                next_beat, prop_continuity, blue_rot_dir, red_rot_dir
            )

        self.update_start_orientations(next_beat, self.sequence[-1])
        self.update_end_orientations(next_beat)
        return self.update_beat_number(next_beat, self.sequence)

    def _apply_CAPs(self, sequence, cap_type: CAPType, rotation_type):
        executor = self.executors.get(cap_type)
        if executor:
            executor.create_CAPs(sequence)
        else:
            raise ValueError(f"No executor found for CAP type: {cap_type.name}")
