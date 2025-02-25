import json
import codecs
from typing import Union
from PyQt6.QtCore import QPointF
from Enums.letters import LetterConditions
from data.constants import BOX, CLOCK, COUNTER, DIAMOND, IN, NONRADIAL, OUT, RADIAL
from placement_managers.arrow_placement_manager.arrow_placement_context import (
    ArrowPlacementContext,
)
from objects.arrow.arrow import Arrow
from placement_managers.arrow_placement_manager.strategies.placement_key_generator import (
    PlacementKeyGenerator,
)
from utilities.path_helpers import get_images_and_data_path


class DefaultPlacementStrategy:
    def __init__(self):
        self.all_defaults = {
            "diamond": {},
            "box": {},
        }
        self.placements_files = {
            "diamond": {
                "pro": "default_diamond_pro_placements.json",
                "anti": "default_diamond_anti_placements.json",
                "float": "default_diamond_float_placements.json",
                "dash": "default_diamond_dash_placements.json",
                "static": "default_diamond_static_placements.json",
            },
            "box": {
                "pro": "default_box_pro_placements.json",
                "anti": "default_box_anti_placements.json",
                "float": "default_box_float_placements.json",
                "dash": "default_box_dash_placements.json",
                "static": "default_box_static_placements.json",
            },
        }
        self._load_all_default_placements()
        self.key_generator = PlacementKeyGenerator()

    def _load_all_default_placements(self) -> None:
        for grid_mode, motion_files in self.placements_files.items():
            for motion_type, filename in motion_files.items():
                filepath = get_images_and_data_path(
                    f"data/arrow_placement/{grid_mode}/default/{filename}"
                )
                self.all_defaults[grid_mode][motion_type] = self._load_json(filepath)

    def _load_json(self, path: str) -> dict:
        try:
            with codecs.open(path, "r", encoding="utf-8") as file:
                return json.load(file)
        except Exception as e:
            print(f"Error loading default placements from {path}: {e}")
            return {}


    def get_default_adjustment(self, arrow: Arrow) -> QPointF:
        grid_mode = arrow.pictograph.state.grid_mode
        if grid_mode not in [DIAMOND, BOX]:
            grid_mode = DIAMOND

        default_placements = self.all_defaults.get(grid_mode, {}).get(
            arrow.motion.state.motion_type, {}
        )
        adjustment_key = self.key_generator.generate_key(arrow, default_placements)
        return QPointF(*default_placements.get(adjustment_key, {}).get(
            str(arrow.motion.state.turns), (0, 0)
        ))
