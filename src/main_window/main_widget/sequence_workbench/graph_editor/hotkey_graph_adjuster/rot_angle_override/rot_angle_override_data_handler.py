# src/main_window/main_widget/sequence_workbench/graph_editor/hotkey_graph_adjuster/arrow_rot_angle_override_manager.py
from typing import TYPE_CHECKING
from enums.letter.letter import Letter
from main_window.main_widget.sequence_workbench.graph_editor.hotkey_graph_adjuster.rot_angle_override.types import (
    GridMode,
    OriKey,
    OverrideData,
    RotationKey,
    TurnsTuple,
)
from main_window.main_widget.sequence_workbench.graph_editor.hotkey_graph_adjuster.rotation_angle_override_key_generator import (
    ArrowRotAngleOverrideKeyGenerator,
)
from settings_manager.global_settings.app_context import AppContext
from .types import is_valid_grid_mode, is_valid_ori_key

from typing import cast

if TYPE_CHECKING:
    from .rot_angle_override_manager import RotAngleOverrideManager


class RotAngleOverrideDataHandler:
    """Manages data operations for rotation overrides"""

    def __init__(self, manager: "RotAngleOverrideManager"):
        self.manager = manager
        self.key_generator = ArrowRotAngleOverrideKeyGenerator()

    def prepare_override_data(self) -> OverrideData:
        return cast(
            OverrideData,
            {
                "letter": self.manager.current_letter,
                "ori_key": OriKey(self._generate_ori_key()),
                "turns_tuple": TurnsTuple(
                    self.manager.turns_generator.generate_turns_tuple(
                        self.manager.view.pictograph
                    )
                ),
                "rot_angle_key": RotationKey(self._generate_rotation_key()),
                "placement_data": AppContext.special_placement_loader().load_or_return_special_placements(),
            },
        )

    def apply_rotation_override(self, override_data: OverrideData) -> None:
        letter_data = self._get_letter_data(override_data)
        turn_data = letter_data.get(override_data["turns_tuple"], {})

        if override_data["rot_angle_key"] in turn_data:
            self._remove_rotation_override(override_data, turn_data)
        else:
            self._add_rotation_override(override_data, turn_data)

        self._save_updated_data(override_data, letter_data)
        self._handle_mirrored_entries(override_data, turn_data)

    def _generate_ori_key(self) -> OriKey:
        return self.manager.data_updater.ori_key_generator.generate_ori_key_from_motion(
            AppContext.get_selected_arrow().motion
        )

    def _generate_rotation_key(self) -> RotationKey:
        return self.key_generator.generate_rotation_angle_override_key(
            AppContext.get_selected_arrow()
        )

    # rot_angle_override_data_handler.py

    def _get_letter_data(
        self, override_data: OverrideData
    ) -> dict[TurnsTuple, dict[RotationKey, bool]]:
        raw_grid_mode = self.manager.view.pictograph.state.grid_mode
        if not is_valid_grid_mode(raw_grid_mode):
            raise ValueError(f"Invalid grid mode: {raw_grid_mode}")

        grid_mode = GridMode(raw_grid_mode)
        ori_key = override_data["ori_key"]

        if not is_valid_ori_key(ori_key):
            raise ValueError(f"Invalid orientation key: {ori_key}")

        return (
            override_data["placement_data"]
            .get(grid_mode, {})
            .get(ori_key, {})
            .get(override_data["letter"].value, {})
        )

    def _remove_rotation_override(self, override_data: dict, turn_data: dict) -> None:
        del turn_data[override_data["rot_angle_key"]]
        self.manager.mirror_handler.handle_removal(override_data["rot_angle_key"])

    # rot_angle_override_data_handler.py
    def _add_rotation_override(
        self, override_data: OverrideData, turn_data: dict[RotationKey, bool]
    ) -> None:
        turn_data[override_data["rot_angle_key"]] = True
        self.manager.mirror_handler.handle_addition(
            cast(dict[RotationKey, bool], turn_data)
        )

    def _save_updated_data(self, override_data: dict, letter_data: dict) -> None:
        self.manager.data_updater.update_specific_entry_in_json(
            override_data["letter"], letter_data, override_data["ori_key"]
        )

    def _handle_mirrored_entries(self, override_data: dict, turn_data: dict) -> None:
        self.manager.mirror_handler.update_mirrored_entries(
            override_data["rot_angle_key"],
            turn_data.get(override_data["rot_angle_key"], None),
        )
