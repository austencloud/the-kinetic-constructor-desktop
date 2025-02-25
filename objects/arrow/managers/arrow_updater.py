from typing import TYPE_CHECKING
from PyQt6.QtWidgets import QApplication

if TYPE_CHECKING:
    from objects.arrow.arrow import Arrow


class ArrowUpdater:
    def __init__(self, arrow: "Arrow") -> None:
        self.arrow = arrow

    def update_arrow(self, arrow_data=None) -> None:
        if arrow_data:
            self.arrow.attr_manager.update_attributes(arrow_data)
        self.arrow.pictograph.managers.svg_manager.arrow_manager.update_arrow_svg(
            self.arrow
        )
        self.arrow.mirror_manager.update_mirror()
        self.arrow.state.location_manager.update_location()
        self.arrow.rot_angle_manager.update_rotation()
        # self.arrow.update()
        # self.arrow.pictograph.update()
