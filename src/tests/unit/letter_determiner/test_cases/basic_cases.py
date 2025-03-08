from ..dataclasses import LetterDeterminationCase
from data.constants import (
    ANTI,
    BLUE,
    BLUE_ATTRS,
    CLOCK,
    CLOCKWISE,
    COLOR,
    COUNTER_CLOCKWISE,
    DIRECTION,
    EAST,
    END_LOC,
    FLOAT,
    MOTION_TYPE,
    NO_ROT,
    NORTH,
    OPP,
    PRO,
    PROP_ROT_DIR,
    RED,
    RED_ATTRS,
    SOUTH,
    START_LOC,
    PREFLOAT_MOTION_TYPE,
    PREFLOAT_PROP_ROT_DIR,
    ALPHA1,
    ALPHA3,
    SPLIT,
    IN,
    OUT,
    LETTER_TYPE,
    WEST,
    BEAT,
    LETTER,
    START_POS,
    END_POS,
    TIMING,
    TURNS,
    START_ORI,
    END_ORI,
    DURATION,
    SAME,
)
from enums.letter.letter import Letter

BASIC_CASES = [
    LetterDeterminationCase(
        name="C -> B",
        pictograph_data={
            BEAT: 1,
            LETTER: "C",
            LETTER_TYPE: "Type1",
            DURATION: 1,
            START_POS: ALPHA1,
            END_POS: ALPHA3,
            TIMING: SPLIT,
            DIRECTION: SAME,
            BLUE_ATTRS: {
                MOTION_TYPE: ANTI,
                START_ORI: IN,
                PROP_ROT_DIR: COUNTER_CLOCKWISE,
                START_LOC: SOUTH,
                END_LOC: WEST,
                TURNS: 0,
                END_ORI: OUT,
            },
            RED_ATTRS: {
                MOTION_TYPE: FLOAT,
                START_ORI: IN,
                PROP_ROT_DIR: NO_ROT,
                START_LOC: NORTH,
                END_LOC: EAST,
                TURNS: "fl",
                END_ORI: CLOCK,
                PREFLOAT_MOTION_TYPE: ANTI,
                PREFLOAT_PROP_ROT_DIR: COUNTER_CLOCKWISE,
            },
        },
        expected=Letter.B,
        description="Letter C turned into B",
        direction=SAME,
        swap_prop_rot=False,
    ),
    LetterDeterminationCase(
        name="C -> A",
        pictograph_data={
            BEAT: 1,
            LETTER: "C",
            LETTER_TYPE: "Type1",
            DURATION: 1,
            START_POS: ALPHA1,
            END_POS: ALPHA3,
            TIMING: SPLIT,
            DIRECTION: SAME,
            BLUE_ATTRS: {
                MOTION_TYPE: PRO,
                START_ORI: IN,
                PROP_ROT_DIR: CLOCKWISE,
                START_LOC: SOUTH,
                END_LOC: WEST,
                TURNS: 0,
                END_ORI: IN,
            },
            RED_ATTRS: {
                MOTION_TYPE: FLOAT,
                START_ORI: IN,
                PROP_ROT_DIR: NO_ROT,
                START_LOC: NORTH,
                END_LOC: EAST,
                TURNS: "fl",
                END_ORI: CLOCK,
                PREFLOAT_MOTION_TYPE: ANTI,
                PREFLOAT_PROP_ROT_DIR: COUNTER_CLOCKWISE,
            },
        },
        expected=Letter.A,
        description="Letter C turned into A",
        direction=SAME,
        swap_prop_rot=False,
    ),
    LetterDeterminationCase(
        name="O -> N",
        pictograph_data={
            BEAT: 5,
            LETTER: "O",
            LETTER_TYPE: "Type1",
            DURATION: 1,
            START_POS: "gamma13",
            END_POS: "gamma3",
            TIMING: "quarter",
            DIRECTION: OPP,
            BLUE_ATTRS: {
                MOTION_TYPE: ANTI,
                START_ORI: IN,
                PROP_ROT_DIR: COUNTER_CLOCKWISE,
                START_LOC: WEST,
                END_LOC: NORTH,
                TURNS: 0,
                END_ORI: OUT,
            },
            RED_ATTRS: {
                MOTION_TYPE: FLOAT,
                START_ORI: "counter",
                PROP_ROT_DIR: NO_ROT,
                START_LOC: SOUTH,
                END_LOC: EAST,
                TURNS: "fl",
                END_ORI: OUT,
                PREFLOAT_MOTION_TYPE: ANTI,
                PREFLOAT_PROP_ROT_DIR: COUNTER_CLOCKWISE,
            },
        },
        expected=Letter.N,
        description="Letter O turned into N",
        direction=OPP,
        swap_prop_rot=False,
    ),
]
