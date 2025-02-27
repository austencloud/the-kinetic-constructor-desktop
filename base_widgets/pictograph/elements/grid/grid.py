from typing import TYPE_CHECKING

from main_window.main_widget.grid_mode_checker import GridModeChecker
from main_window.settings_manager.global_settings.app_context import AppContext
from utilities.path_helpers import get_images_and_data_path

from .grid_data import GridData
from .grid_item import GridItem
from .non_radial_points_group import NonRadialPointsGroup

if TYPE_CHECKING:
    from base_widgets.pictograph.pictograph import Pictograph
    
GRID_DIR = get_images_and_data_path("images/grid/")


class Grid:
    def __init__(self, pictograph: "Pictograph", grid_data: GridData, grid_mode: str):

        self.pictograph = pictograph
        self.grid_data = grid_data
        self.grid_mode = grid_mode
        self.items: dict[str, GridItem] = {}
        self.center = self.grid_data.center_points.get(grid_mode)

        self._create_grid_items()

    def _create_grid_items(self):
        paths = {
            "diamond": f"{GRID_DIR}diamond_grid.svg",
            "box": f"{GRID_DIR}box_grid.svg",
        }

        for mode, path in paths.items():
            grid_item = GridItem(path)
            self.pictograph.addItem(grid_item)
            grid_item.setVisible(mode == self.grid_mode)
            self.items[mode] = grid_item

        non_radial_paths = {
            "diamond": f"{GRID_DIR}diamond_nonradial_points.svg",
            "box": f"{GRID_DIR}box_nonradial_points.svg",
        }

        non_radial_path = non_radial_paths.get(self.grid_mode)
        if non_radial_path:
            non_radial_points = NonRadialPointsGroup(non_radial_path)
            self.pictograph.addItem(non_radial_points)
            is_visible = (
                AppContext.settings_manager().visibility.get_non_radial_visibility()
            )
            non_radial_points.setVisible(is_visible)
            self.items[f"{self.grid_mode}_nonradial"] = non_radial_points

    def toggle_non_radial_points(self, visible: bool):
        non_radial_key = f"{self.grid_mode}_nonradial"
        self.items[non_radial_key].setVisible(visible)

    def hide(self):
        for item in self.items.values():
            item.setVisible(False)

    def update_grid_mode(self):
        grid_mode = GridModeChecker.get_grid_mode(self.pictograph.state.pictograph_data)
        self.pictograph.elements.grid.hide()
        self.pictograph.elements.grid.__init__(
            self.pictograph, self.pictograph.elements.grid.grid_data, grid_mode
        )
