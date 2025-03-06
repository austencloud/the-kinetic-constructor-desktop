from typing import TYPE_CHECKING
from data.constants import (
    BEAT,
    BLUE_ATTRS,
    DIRECTION,
    END_LOC,
    END_ORI,
    END_POS,
    LETTER,
    MOTION_TYPE,
    NO_ROT,
    PROP_ROT_DIR,
    RED_ATTRS,
    SEQUENCE_START_POSITION,
    START_LOC,
    START_ORI,
    TIMING,
    TURNS,
)
from base_widgets.pictograph.pictograph import Pictograph


if TYPE_CHECKING:
    from main_window.main_widget.json_manager.json_manager import JsonManager


class JsonStartPositionHandler:
    def __init__(self, manager: "JsonManager"):
        self.manager = manager

    def set_start_position_data(
        self, start_pos_pictograph: Pictograph, start_position_dict: dict = {}
    ) -> None:
        red_start_ori = start_pos_pictograph.state.pictograph_data[RED_ATTRS][START_ORI]
        blue_start_ori = start_pos_pictograph.state.pictograph_data[BLUE_ATTRS][
            START_ORI
        ]

        sequence = self.manager.loader_saver.load_current_sequence()
        if not start_position_dict:
            start_position_dict = {
                BEAT: 0,
                SEQUENCE_START_POSITION: self.get_sequence_start_position(
                    start_pos_pictograph
                ),
                LETTER: start_pos_pictograph.state.letter.name,
                END_POS: start_pos_pictograph.state.end_pos,
                TIMING: start_pos_pictograph.state.timing,
                DIRECTION: start_pos_pictograph.state.direction,
                BLUE_ATTRS: {
                    START_LOC: start_pos_pictograph.elements.blue_motion.state.start_loc,
                    END_LOC: start_pos_pictograph.elements.blue_motion.state.end_loc,
                    START_ORI: blue_start_ori,
                    END_ORI: blue_start_ori,
                    PROP_ROT_DIR: NO_ROT,
                    TURNS: 0,
                    MOTION_TYPE: start_pos_pictograph.elements.blue_motion.state.motion_type,
                },
                RED_ATTRS: {
                    START_LOC: start_pos_pictograph.elements.red_motion.state.start_loc,
                    END_LOC: start_pos_pictograph.elements.red_motion.state.end_loc,
                    START_ORI: red_start_ori,
                    END_ORI: red_start_ori,
                    PROP_ROT_DIR: NO_ROT,
                    TURNS: 0,
                    MOTION_TYPE: start_pos_pictograph.elements.red_motion.state.motion_type,
                },
            }

        if len(sequence) == 1:
            sequence.append(start_position_dict)
        else:
            sequence.insert(1, start_position_dict)

        self.manager.loader_saver.save_current_sequence(sequence)

    def update_start_pos_ori(self, color: str, ori: int) -> None:
        sequence = self.manager.loader_saver.load_current_sequence()
        if sequence:
            sequence[1][f"{color}_attributes"][END_ORI] = ori
            sequence[1][f"{color}_attributes"][START_ORI] = ori
            self.manager.loader_saver.save_current_sequence(sequence)

    def get_sequence_start_position(self, start_pos_pictograph: Pictograph) -> str:
        return start_pos_pictograph.state.end_pos.rstrip("0123456789")
