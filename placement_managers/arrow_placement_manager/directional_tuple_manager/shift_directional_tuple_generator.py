from data.constants import (
    BOX,
    CCW_HANDPATH,
    CLOCKWISE,
    COUNTER_CLOCKWISE,
    CW_HANDPATH,
    DIAMOND,
    FLOAT,
    PRO,
    ANTI,
)
from .base_directional_tuple_generator import BaseDirectionalGenerator


class ShiftDirectionalGenerator(BaseDirectionalGenerator):
    def generate_directional_tuples(self, x: int, y: int) -> list[tuple[int, int]]:
        grid_mode = self._get_grid_mode()
        if grid_mode == DIAMOND:
            directional_generators = {
                PRO: self._generate_diamond_pro_directional_tuples,
                ANTI: self._generate_diamond_anti_directional_tuples,
                FLOAT: self._generate_diamond_float_directional_tuples,
            }
        elif grid_mode == BOX:
            directional_generators = {
                PRO: self._generate_box_pro_directional_tuples,
                ANTI: self._generate_box_anti_directional_tuples,
                FLOAT: self._generate_box_float_directional_tuples,
            }
        else:
            raise ValueError(f"Unsupported grid mode: {grid_mode}")

        generator = directional_generators.get(self.motion.state.motion_type)
        if not generator:
            return []
        return generator(x, y)

    def _generate_diamond_pro_directional_tuples(
        self, x: int, y: int
    ) -> list[tuple[int, int]]:
        directional_tuples = {
            CLOCKWISE: [(x, y), (-y, x), (-x, -y), (y, -x)],
            COUNTER_CLOCKWISE: [(-y, -x), (x, -y), (y, x), (-x, y)],
        }
        return directional_tuples.get(self.motion.state.prop_rot_dir, [])

    def _generate_diamond_anti_directional_tuples(
        self, x: int, y: int
    ) -> list[tuple[int, int]]:
        directional_tuples = {
            CLOCKWISE: [(-y, -x), (x, -y), (y, x), (-x, y)],
            COUNTER_CLOCKWISE: [(x, y), (-y, x), (-x, -y), (y, -x)],
        }
        return directional_tuples.get(self.motion.state.prop_rot_dir, [])

    def _generate_diamond_float_directional_tuples(
        self, x: int, y: int
    ) -> list[tuple[int, int]]:
        return self._generate_float_directional_tuples(x, y)

    def _generate_box_pro_directional_tuples(
        self, x: int, y: int
    ) -> list[tuple[int, int]]:
        directional_tuples = {
            CLOCKWISE: [(-x, y), (-y, -x), (x, -y), (y, x)],
            COUNTER_CLOCKWISE: [(x, y), (-y, x), (-x, -y), (y, -x)],
        }
        return directional_tuples.get(self.motion.state.prop_rot_dir, [])

    def _generate_box_anti_directional_tuples(
        self, x: int, y: int
    ) -> list[tuple[int, int]]:
        directional_tuples = {
            CLOCKWISE: [(-x, y), (-y, -x), (x, -y), (y, x)],
            COUNTER_CLOCKWISE: [(x, y), (-y, x), (-x, -y), (y, -x)],
        }
        return directional_tuples.get(self.motion.state.prop_rot_dir, [])

    def _generate_box_float_directional_tuples(
        self, x: int, y: int
    ) -> list[tuple[int, int]]:
        return self._generate_float_directional_tuples(x, y)

    def _generate_float_directional_tuples(
        self, x: int, y: int
    ) -> list[tuple[int, int]]:
        handpath_direction = self.hand_rot_dir_calculator.get_hand_rot_dir(
            self.motion.state.start_loc, self.motion.state.end_loc
        )
        directional_tuples = {
            CW_HANDPATH: [(-y, -x), (x, -y), (y, x), (-x, y)],
            CCW_HANDPATH: [(-y, -x), (x, -y), (y, x), (-x, y)],
        }
        return directional_tuples.get(handpath_direction, [])
