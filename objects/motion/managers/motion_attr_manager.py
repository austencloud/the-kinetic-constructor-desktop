from typing import TYPE_CHECKING
from Enums.Enums import Letter
from data.constants import *


if TYPE_CHECKING:
    from objects.motion.motion import Motion


class MotionAttrManager:
    def __init__(self, motion: "Motion") -> None:
        self.motion = motion
        self.motion.state.color = self.motion.motion_dict.get(COLOR)
        self.motion.state.turns = self.motion.motion_dict.get(TURNS)
        self.motion.state.start_loc = None
        self.motion.state.end_loc = None
        self.motion.state.motion_type = None

    def update_attributes(self, motion_dict: dict[str, str]) -> None:
        for attribute, value in motion_dict.items():
            if value is not None:
                setattr(self.motion, attribute, value)
        if self.motion.check.is_shift():
            if "prefloat_motion_type" not in motion_dict:
                if self.motion.state.motion_type != FLOAT:
                    self.motion.state.prefloat_motion_type = (
                        self.motion.state.motion_type
                    )
            if "prefloat_motion_type" in motion_dict:
                if motion_dict["prefloat_motion_type"] == FLOAT:
                    print("Warning: prefloat_motion_type cannot be 'float'")
                else:
                    self.motion.state.prefloat_motion_type = motion_dict[
                        "prefloat_motion_type"
                    ]
            if "prefloat_prop_rot_dir" in motion_dict:
                if motion_dict["prefloat_prop_rot_dir"] == NO_ROT:
                    print("Warning: prefloat_prop_rot_dir cannot be 'no_rot'")
                else:
                    self.motion.state.prefloat_prop_rot_dir = motion_dict[
                        "prefloat_prop_rot_dir"
                    ]

    def update_prop_ori(self) -> None:
        if hasattr(self.motion, PROP) and self.motion.prop:
            if not self.motion.state.end_ori:
                self.motion.state.end_ori = self.motion.ori_calculator.get_end_ori()
            self.motion.prop.ori = self.motion.state.end_ori
            self.motion.prop.loc = self.motion.state.end_loc
            self.motion.prop.axis = self.motion.prop.attr_manager.get_axis_from_ori()

    def get_attributes(self) -> dict[str, str]:
        return {
            COLOR: self.motion.state.color,
            MOTION_TYPE: self.motion.state.motion_type,
            TURNS: self.motion.state.turns,
            PROP_ROT_DIR: self.motion.state.prop_rot_dir,
            START_LOC: self.motion.state.start_loc,
            END_LOC: self.motion.state.end_loc,
            START_ORI: self.motion.state.start_ori,
            END_ORI: self.motion.state.end_ori,
        }

    def assign_lead_states(self) -> None:
        leading_motion = self.motion.pictograph.managers.get.leading_motion()
        trailing_motion = self.motion.pictograph.managers.get.trailing_motion()
        if self.motion.pictograph.managers.get.leading_motion():
            leading_motion.arrow.motion.state.lead_state = LEADING
            trailing_motion.arrow.motion.state.lead_state = TRAILING
