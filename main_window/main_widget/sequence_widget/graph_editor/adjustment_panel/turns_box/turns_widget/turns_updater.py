from typing import TYPE_CHECKING, Union
from Enums.Enums import Turns
from data.constants import (
    ANTI,
    CLOCKWISE,
    COUNTER_CLOCKWISE,
    DASH,
    FLOAT,
    NO_ROT,
    PRO,
    STATIC,
)

if TYPE_CHECKING:
    from .turns_widget import TurnsWidget
    from base_widgets.base_pictograph.base_pictograph import BasePictograph
    from objects.motion.motion import Motion


class TurnsUpdater:
    def __init__(self, turns_widget: "TurnsWidget") -> None:
        self.turns_widget = turns_widget
        self.turns_box = turns_widget.turns_box
        self.json_manager = (
            turns_widget.turns_box.adjustment_panel.graph_editor.main_widget.json_manager
        )
        self.json_updater = self.json_manager.updater
        self.beat_frame = (
            turns_widget.turns_box.adjustment_panel.graph_editor.sequence_widget.beat_frame
        )
        self.prop_rot_dir_manager = self.turns_box.prop_rot_dir_button_manager

    def set_motion_turns(self, motion: "Motion", new_turns: Turns) -> None:
        """Set the motion's turns and update related properties."""
        beat_index = self._calculate_beat_index()

        if new_turns == "fl":
            self._handle_float_turn(motion, beat_index)
        elif motion.turns == "fl" and new_turns != "fl":
            self._restore_motion_from_prefloat(motion, beat_index)

        self._update_turns_in_json(motion, new_turns)

    def _calculate_beat_index(self) -> int:
        """Calculate the beat index for JSON updates."""
        current_beat = self.beat_frame.get.beat_number_of_currently_selected_beat()
        duration = self.beat_frame.get.duration_of_currently_selected_beat()
        return current_beat + duration

    def _handle_float_turn(self, motion: "Motion", beat_index: int) -> None:
        """Handle the case when the new turns value is 'float'."""
        motion.prefloat_motion_type = self._get_motion_type_from_json(
            beat_index, motion.color
        )
        motion.prefloat_prop_rot_dir = self._get_prop_rot_dir_from_json(
            beat_index, motion.color
        )

        self._update_prefloat_values_in_json(motion, beat_index)

        motion.motion_type = FLOAT
        motion.prop_rot_dir = NO_ROT

    def _restore_motion_from_prefloat(self, motion: "Motion", beat_index: int) -> None:
        """Restore motion properties from prefloat values."""
        motion.prefloat_motion_type = self._get_prefloat_motion_type_from_json(
            beat_index, motion.color
        )
        motion.prefloat_prop_rot_dir = self._get_prefloat_prop_rot_dir_from_json(
            beat_index, motion.color
        )

        motion.motion_type = motion.prefloat_motion_type
        motion.prop_rot_dir = motion.prefloat_prop_rot_dir

    def _update_turns_in_json(self, motion: "Motion", new_turns: Turns) -> None:
        """Update the turns value in the JSON data."""
        if new_turns == "fl":
            self.json_updater.turns_updater.set_turns_to_fl_from_num_in_json(
                motion, new_turns
            )
        elif motion.motion_type == FLOAT and new_turns != "fl":
            self.json_updater.turns_updater.set_turns_to_num_from_fl_in_json(
                motion, new_turns
            )
        else:
            self.json_updater.turns_updater.set_turns_from_num_to_num_in_json(
                motion, new_turns
            )

    def _get_motion_type_from_json(self, index: int, color: str) -> int:
        """Retrieve motion type from JSON at the given index."""
        return self.json_manager.loader_saver.get_motion_type_from_json_at_index(
            index, color
        )

    def _get_prop_rot_dir_from_json(self, index: int, color: str) -> int:
        """Retrieve prop rotation direction from JSON at the given index."""
        return self.json_manager.loader_saver.get_prop_rot_dir_from_json(index, color)

    def _get_prefloat_motion_type_from_json(self, index: int, color: str) -> int:
        """Retrieve prefloat motion type from JSON at the given index."""
        return (
            self.json_manager.loader_saver.get_prefloat_motion_type_from_json_at_index(
                index, color
            )
        )

    def _get_prefloat_prop_rot_dir_from_json(self, index: int, color: str) -> int:
        """Retrieve prefloat prop rotation direction from JSON at the given index."""
        return self.json_manager.loader_saver.get_prefloat_prop_rot_dir_from_json(
            index, color
        )

    def _update_prefloat_values_in_json(self, motion: "Motion", index: int) -> None:
        """Update prefloat values in JSON."""
        self.json_updater.motion_type_updater.update_prefloat_motion_type_in_json(
            index, motion.color, motion.prefloat_motion_type
        )
        self.json_updater.prop_rot_dir_updater.update_prefloat_prop_rot_dir_in_json(
            index, motion.color, motion.prefloat_prop_rot_dir
        )

    def adjust_turns_for_pictograph(
        self, pictograph: "BasePictograph", new_turns: Union[int, float, str]
    ) -> None:
        """Adjust turns for each relevant motion in the pictograph."""
        for motion in pictograph.motions.values():
            if motion.color == self.turns_box.color:
                if new_turns == "fl":
                    motion.motion_type = FLOAT
                    motion.prop_rot_dir = NO_ROT
                self.set_motion_turns(motion, new_turns)

    def _clamp_turns(self, turns: Turns) -> Turns:
        """Clamp the turns value within the allowable range."""
        return max(0, min(3, turns))
