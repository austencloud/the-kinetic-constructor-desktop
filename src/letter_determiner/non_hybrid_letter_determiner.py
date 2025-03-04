from typing import TYPE_CHECKING
from enums.letter.letter import Letter

from data.constants import (
    ANTI,
    COUNTER_CLOCKWISE,
    CLOCKWISE,
    END_LOC,
    FLOAT,
    OPP,
    PRO,
    START_LOC,
    PROP_ROT_DIR,
    MOTION_TYPE,
)

if TYPE_CHECKING:
    from objects.motion.motion import Motion
    from .letter_determiner import LetterDeterminer


class NonHybridShiftLetterDeterminer:
    """
    This is for when there is one float and one shift,
    It ensures that we don't use hybrid letters (like C, F, I, or L)
    to describe letters that have one float and one Pro/Anti.
    """

    def __init__(self, letter_engine: "LetterDeterminer"):
        self.main_widget = letter_engine.main_widget
        self.letters = letter_engine.letters

    def determine_letter(
        self, motion: "Motion", new_motion_type: str, swap_prop_rot_dir: bool
    ) -> Letter:
        """Handle the case where there is one float and one shift, and the user changes the motion type of the shift."""
        other_motion = motion.pictograph.managers.get.other_motion(motion)
        if new_motion_type in [PRO, ANTI]:
            self._update_motion_attributes(motion, new_motion_type, other_motion)
            if swap_prop_rot_dir:
                self._update_motion_attributes(other_motion, new_motion_type, motion)
        return self._find_matching_letter(motion)

    def _update_motion_attributes(
        self, motion: "Motion", new_motion_type: str, other_motion: "Motion"
    ) -> None:
        """Update the attributes of the other motion."""
        motion.state.prefloat_motion_type = new_motion_type
        if motion.state.motion_type == FLOAT:
            json_index = self._get_json_index_for_current_beat()
            self._update_json_with_prefloat_attributes(
                json_index, motion, new_motion_type
            )
            motion.state.prefloat_prop_rot_dir = self._get_prop_rot_dir(
                json_index, other_motion
            )

            self.main_widget.json_manager.updater.prop_rot_dir_updater.update_prefloat_prop_rot_dir_in_json(
                json_index,
                motion.state.color,
                motion.state.prefloat_prop_rot_dir,
            )

    def _update_json_with_prefloat_attributes(
        self, json_index: int, other_motion: "Motion", motion_type: str
    ) -> None:
        """Update JSON with pre-float motion type and rotation direction."""
        self.main_widget.json_manager.updater.motion_type_updater.update_json_prefloat_motion_type(
            json_index,
            other_motion.state.color,
            motion_type,
        )

    def _get_json_index_for_current_beat(self) -> int:
        """Calculate the JSON index for the currently selected beat."""
        return (
            self.main_widget.sequence_workbench.sequence_beat_frame.get.index_of_currently_selected_beat()
            + 2
        )

    def _get_prop_rot_dir(self, json_index: int, other_motion: "Motion") -> str:
        """Retrieve the prop rotation direction from JSON."""
        if other_motion.state.motion_type == FLOAT:
            prop_rot_dir = self.main_widget.json_manager.loader_saver.get_json_prefloat_prop_rot_dir(
                json_index,
                other_motion.state.color,
            )
            if other_motion.pictograph.state.direction == OPP:
                prop_rot_dir = self._get_opposite_rotation_direction(prop_rot_dir)
        elif other_motion.state.motion_type in [PRO, ANTI]:
            prop_rot_dir = (
                self.main_widget.json_manager.loader_saver.get_json_prop_rot_dir(
                    json_index,
                    other_motion.state.color,
                )
            )
            if other_motion.pictograph.state.direction == OPP:
                prop_rot_dir = self._get_opposite_rotation_direction(prop_rot_dir)

        return prop_rot_dir

    def _get_opposite_rotation_direction(self, rotation_direction: str) -> str:
        """Return the opposite prop rotation direction."""
        return COUNTER_CLOCKWISE if rotation_direction == CLOCKWISE else CLOCKWISE

    def _find_matching_letter(self, motion: "Motion") -> Letter:
        """Find and return the letter that matches the motion attributes."""
        for letter, examples in self.letters.items():
            for example in examples:
                if self._compare_motion_attributes(motion, example):
                    return letter
        return None

    def _compare_motion_attributes(self, motion: "Motion", example) -> bool:
        """Compare the motion attributes with the example to find a match."""
        float_motion = motion.pictograph.managers.get.float_motion()
        non_float_motion = float_motion.pictograph.managers.get.other_motion(
            float_motion
        )

        does_example_match = (
            self._is_shift_motion_type_matching(float_motion, example)
            and example[f"{float_motion.state.color}_attributes"][START_LOC]
            == float_motion.state.start_loc
            and example[f"{float_motion.state.color}_attributes"][END_LOC]
            == float_motion.state.end_loc
            and self._is_shift_prop_rot_dir_matching(float_motion, example)
            and self._is_shift_motion_type_matching(non_float_motion, example)
            and example[f"{non_float_motion.state.color}_attributes"][START_LOC]
            == non_float_motion.state.start_loc
            and example[f"{non_float_motion.state.color}_attributes"][END_LOC]
            == non_float_motion.state.end_loc
            and self._is_shift_prop_rot_dir_matching(non_float_motion, example)
        )

        return does_example_match

    def _is_shift_prop_rot_dir_matching(self, motion: "Motion", example):
        is_rot_dir_matching = example[f"{motion.state.color}_attributes"][
            PROP_ROT_DIR
        ] == self.main_widget.json_manager.loader_saver.get_json_prefloat_prop_rot_dir(
            self.main_widget.sequence_workbench.sequence_beat_frame.get.index_of_currently_selected_beat()
            + 2,
            motion.state.color,
        ) or example[
            f"{motion.state.color}_attributes"
        ][
            PROP_ROT_DIR
        ] == self.main_widget.json_manager.loader_saver.get_json_prop_rot_dir(
            self.main_widget.sequence_workbench.sequence_beat_frame.get.index_of_currently_selected_beat()
            + 2,
            motion.state.color,
        )

        return is_rot_dir_matching

    def _is_shift_motion_type_matching(self, motion: "Motion", example) -> bool:
        """Check if the motion type matches."""
        return (
            example[f"{motion.state.color}_attributes"][MOTION_TYPE]
            == motion.state.motion_type
            or example[f"{motion.state.color}_attributes"][MOTION_TYPE]
            == motion.state.prefloat_motion_type
        )
