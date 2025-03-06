from data.constants import (
    BEAT,
    BLUE,
    BLUE_ATTRS,
    CCW_HANDPATH,
    CLOCKWISE,
    COUNTER_CLOCKWISE,
    CW_HANDPATH,
    DASH,
    DIRECTION,
    EAST,
    END_LOC,
    END_ORI,
    END_POS,
    LETTER,
    MOTION_TYPE,
    NORTH,
    NORTHEAST,
    NORTHWEST,
    PREFLOAT_MOTION_TYPE,
    PREFLOAT_PROP_ROT_DIR,
    PROP_ROT_DIR,
    RED,
    RED_ATTRS,
    SEQUENCE_START_POSITION,
    SOUTH,
    SOUTHEAST,
    SOUTHWEST,
    START_LOC,
    START_ORI,
    START_POS,
    STATIC,
    TIMING,
    TURNS,
    WEST,
)
loc_map_cw = {
    SOUTH: WEST,
    WEST: NORTH,
    NORTH: EAST,
    EAST: SOUTH,
    NORTHEAST: SOUTHEAST,
    SOUTHEAST: SOUTHWEST,
    SOUTHWEST: NORTHWEST,
    NORTHWEST: NORTHEAST,
}

loc_map_ccw = {
    SOUTH: EAST,
    EAST: NORTH,
    NORTH: WEST,
    WEST: SOUTH,
    NORTHEAST: NORTHWEST,
    NORTHWEST: SOUTHWEST,
    SOUTHWEST: SOUTHEAST,
    SOUTHEAST: NORTHEAST,
}

loc_map_dash = {
    SOUTH: NORTH,
    NORTH: SOUTH,
    WEST: EAST,
    EAST: WEST,
    NORTHEAST: SOUTHWEST,
    SOUTHEAST: NORTHWEST,
    SOUTHWEST: NORTHEAST,
    NORTHWEST: SOUTHEAST,
}

loc_map_static = {
    SOUTH: SOUTH,
    NORTH: NORTH,
    WEST: WEST,
    EAST: EAST,
    NORTHEAST: NORTHEAST,
    SOUTHEAST: SOUTHEAST,
    SOUTHWEST: SOUTHWEST,
    NORTHWEST: NORTHWEST,
}

hand_rot_dir_map = {
    (SOUTH, WEST): CLOCKWISE,
    (WEST, NORTH): CLOCKWISE,
    (NORTH, EAST): CLOCKWISE,
    (EAST, SOUTH): CLOCKWISE,
    (WEST, SOUTH): COUNTER_CLOCKWISE,
    (NORTH, WEST): COUNTER_CLOCKWISE,
    (EAST, NORTH): COUNTER_CLOCKWISE,
    (SOUTH, EAST): COUNTER_CLOCKWISE,
    (SOUTH, NORTH): DASH,
    (WEST, EAST): DASH,
    (NORTH, SOUTH): DASH,
    (EAST, WEST): DASH,
    (NORTH, NORTH): STATIC,
    (EAST, EAST): STATIC,
    (SOUTH, SOUTH): STATIC,
    (WEST, WEST): STATIC,
    (NORTHEAST, SOUTHEAST): CLOCKWISE,
    (SOUTHEAST, SOUTHWEST): CLOCKWISE,
    (SOUTHWEST, NORTHWEST): CLOCKWISE,
    (NORTHWEST, NORTHEAST): CLOCKWISE,
    (NORTHEAST, NORTHWEST): COUNTER_CLOCKWISE,
    (NORTHWEST, SOUTHWEST): COUNTER_CLOCKWISE,
    (SOUTHWEST, SOUTHEAST): COUNTER_CLOCKWISE,
    (SOUTHEAST, NORTHEAST): COUNTER_CLOCKWISE,
    (NORTHEAST, SOUTHWEST): DASH,
    (SOUTHEAST, NORTHWEST): DASH,
    (SOUTHWEST, NORTHEAST): DASH,
    (NORTHWEST, SOUTHEAST): DASH,
    (NORTHEAST, NORTHEAST): STATIC,
    (SOUTHEAST, SOUTHEAST): STATIC,
    (SOUTHWEST, SOUTHWEST): STATIC,
    (NORTHWEST, NORTHWEST): STATIC,
}
