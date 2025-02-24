from PyQt6.QtCore import QPointF
from objects.arrow.arrow import Arrow
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from base_widgets.pictograph.pictograph import Pictograph


class InitialPlacementStrategy:
    def __init__(self, pictograph: "Pictograph"):
        self.pictograph = pictograph

    def compute_initial_position(self, arrow: Arrow) -> QPointF:
        """Determines the initial position of an arrow based on motion type and pictograph data."""
        motion_type = arrow.motion.state.motion_type

        if motion_type in ["pro", "anti", "float"]:
            return self._get_shift_coords(arrow)
        elif motion_type in ["static", "dash"]:
            return self._get_static_dash_coords(arrow)
        return QPointF(0, 0)

    def _get_shift_coords(self, arrow: Arrow) -> QPointF:
        """Retrieves shift coordinates from the pictograph."""
        point_name = f"{arrow.state.loc}_{self.pictograph.state.grid_mode}_layer2_point"
        coord = self.pictograph.elements.grid.grid_data.get_shift_coord(point_name)
        return coord if coord else QPointF(0, 0)

    def _get_static_dash_coords(self, arrow: Arrow) -> QPointF:
        """Retrieves static/dash coordinates from the pictograph."""
        point_name = f"{arrow.state.loc}_{self.pictograph.state.grid_mode}_hand_point"
        coord = self.pictograph.elements.grid.grid_data.get_static_dash_coord(
            point_name
        )
        return coord if coord else QPointF(0, 0)
