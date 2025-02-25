from typing import TYPE_CHECKING, Literal
from data.constants import BOX, DIAMOND
from data.positions import box_positions, diamond_positions

if TYPE_CHECKING:
    pass


class GridModeChecker:
    """Checks what grid a given pictograph is in by looking at its start and end positions"""

    @staticmethod
    def get_grid_mode(
        pictograph_data: dict,
    ) -> None | Literal["box"] | Literal["diamond"] | Literal["skewed"]:
        start_pos = pictograph_data.get("start_pos") or pictograph_data.get(
            "end_pos"
        )  # Handles the start position
        end_pos = pictograph_data.get("end_pos")

        if start_pos in box_positions and end_pos in box_positions:
            return BOX
        if start_pos in diamond_positions and end_pos in diamond_positions:
            return DIAMOND
        if (start_pos in box_positions and end_pos in diamond_positions) or (
            start_pos in diamond_positions and end_pos in box_positions
        ):
            return "skewed"
        return None
