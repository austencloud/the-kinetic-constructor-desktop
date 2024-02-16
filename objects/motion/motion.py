from typing import TYPE_CHECKING
from .managers.motion_checker import MotionChecker
from .managers.motion_attr_manager import MotionAttrManager
from .managers.motion_manipulator import MotionManipulator
from .managers.motion_ori_calculator import MotionOriCalculator
from .managers.motion_updater import MotionUpdater
from .managers.motion_turn_manager import MotionTurnsManager
from Enums.MotionAttributes import (
    Color,
    Locations,
    Orientations,
    MotionTypes,
    PropRotDirs,
    LeadStates,
    Turns,
)

if TYPE_CHECKING:
    from widgets.pictograph.pictograph import Pictograph
    from objects.arrow.arrow import Arrow
    from objects.prop.prop import Prop


class Motion:
    def __init__(self, pictograph: "Pictograph", motion_dict: dict) -> None:
        self.pictograph = pictograph
        self.motion_dict = motion_dict
        self.ori_calculator = MotionOriCalculator(self)
        self.manipulator = MotionManipulator(self)
        self.attr_manager = MotionAttrManager(self)
        self.turns_manager = MotionTurnsManager(self)
        self.updater = MotionUpdater(self)
        self.check = MotionChecker(self)

    pictograph: "Pictograph"
    color: Color
    turns: Turns
    arrow: "Arrow"
    prop: "Prop"
    motion_type: MotionTypes
    start_loc: Locations
    start_ori: Orientations
    end_loc: Locations
    end_ori: Orientations
    prop_rot_dir: PropRotDirs
    lead_state: LeadStates = None
