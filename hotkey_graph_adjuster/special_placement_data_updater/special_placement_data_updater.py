import os
import logging
from typing import TYPE_CHECKING

from .mirrored_entry_manager.mirrored_entry_manager import MirroredEntryManager
from .ori_key_generator import OriKeyGenerator
from main_window.main_widget.turns_tuple_generator.turns_tuple_generator import (
    TurnsTupleGenerator,
)
from main_window.settings_manager.global_settings.app_context import AppContext
from placement_managers.attr_key_generator import (
    AttrKeyGenerator,
)


from .special_placement_entry_remover import SpecialPlacementEntryRemover
from objects.arrow.arrow import Arrow
from Enums.Enums import Letter
from PyQt6.QtCore import QPointF

if TYPE_CHECKING:

    from base_widgets.pictograph.managers.pictograph_checker import PictographChecker
    from base_widgets.pictograph.managers.getter.pictograph_getter import PictographGetter
    from base_widgets.pictograph.state.pictograph_state import PictographState

    from placement_managers.arrow_placement_manager.arrow_placement_manager import (
        ArrowPlacementManager,
    )


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class SpecialPlacementDataUpdater:
    def __init__(
        self,
        placement_manager: "ArrowPlacementManager",
        state: "PictographState",
        get_default_adjustment_callback: callable,
        getter: "PictographGetter",
        checker: "PictographChecker",
    ) -> None:
        self.placement_manager = placement_manager
        self.state = state
        self.attr_key_generator = AttrKeyGenerator()
        self.get_default_adjustment_callback = get_default_adjustment_callback
        self.getter = getter
        self.checker = checker
        self.get_grid_mode = getter.grid_mode()
        self.ori_key_generator = OriKeyGenerator(getter)
        self.turns_tuple_generator = TurnsTupleGenerator()
        self.entry_remover = SpecialPlacementEntryRemover(self)
        self.mirrored_entry_manager = MirroredEntryManager(self)

    def _get_letter_data(self, letter: Letter, ori_key: str) -> dict:
        letter_data = (
            AppContext.special_placement_loader()
            .load_special_placements_fresh()
            .get(self.state.grid_mode, {})
            .get(ori_key, {})
            .get(letter.value, {})
        )

        return letter_data

    def _update_or_create_turn_data(
        self,
        letter_data: dict,
        turns_tuple: str,
        arrow: Arrow,
        adjustment: QPointF,  # Ensure this is a QPointF
    ) -> None:
        turn_data = letter_data.get(turns_tuple, {})
        key = self.attr_key_generator.get_key_from_arrow(arrow)

        if key in turn_data and turn_data[key] != {}:
            turn_data[key][0] += adjustment.x()  # ✅ Extract x value
            turn_data[key][1] += adjustment.y()  # ✅ Extract y value
        else:
            default_adjustment = self.get_default_adjustment_callback(arrow)
            turn_data[key] = [
                default_adjustment.x() + adjustment.x(),  # ✅ Extract x value
                default_adjustment.y() + adjustment.y(),  # ✅ Extract y value
            ]

        letter_data[turns_tuple] = turn_data

    def _update_placement_json_data(
        self, letter: Letter, letter_data: dict, ori_key: str, grid_mode: str
    ) -> None:
        file_path = os.path.join(
            "data",
            "arrow_placement",
            grid_mode,
            "special",
            ori_key,
            f"{letter.value}_placements.json",
        )
        wrapped_data = {letter.value: letter_data}
        AppContext.special_placement_saver().save_json_data(wrapped_data, file_path)

    def update_arrow_adjustments_in_json(
        self, adjustment: tuple[int, int] | QPointF, turns_tuple: str
    ) -> None:
        selected_arrow = AppContext.get_selected_arrow()
        if not selected_arrow:
            return

        if isinstance(adjustment, tuple):
            adjustment = QPointF(*adjustment)

        letter = selected_arrow.pictograph.state.letter
        ori_key = self.ori_key_generator.generate_ori_key_from_motion(
            selected_arrow.motion
        )
        letter_data = self._get_letter_data(letter, ori_key)
        self._update_or_create_turn_data(
            letter_data, turns_tuple, selected_arrow, adjustment
        )
        self._update_placement_json_data(
            letter, letter_data, ori_key, self.state.grid_mode
        )

    def update_specific_entry_in_json(
        self, letter: Letter, letter_data: dict, ori_key
    ) -> None:
        try:
            self._update_placement_json_data(
                letter, letter_data, ori_key, self.state.grid_mode
            )
        except Exception as e:
            logging.error(f"Error in update_specific_entry_in_json: {e}")
