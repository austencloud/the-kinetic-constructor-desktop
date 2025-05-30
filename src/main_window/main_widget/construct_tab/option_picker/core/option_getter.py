from typing import Any, Optional
from data.constants import (
    BLUE,
    BLUE_ATTRS,
    END_ORI,
    END_POS,
    NO_ROT,
    PROP_ROT_DIR,
    RED,
    RED_ATTRS,
    START_ORI,
    START_POS,
)
from interfaces.json_manager_interface import IJsonManager


class OptionGetter:
    def __init__(
        self,
        pictograph_dataset: dict[Any, list[dict[str, Any]]],
        json_manager: IJsonManager,
    ) -> None:
        self.pictograph_dataset = pictograph_dataset
        self.ori_calculator = json_manager.ori_calculator
        self.ori_validation_engine = json_manager.ori_validation_engine

    def get_next_options(
        self, sequence: list[dict[str, Any]], selected_filter: Optional[str] = None
    ) -> list[dict[str, Any]]:
        options = self._load_all_next_option_dicts(sequence)
        if selected_filter is not None:
            options = [
                o
                for o in options
                if self._determine_reversal_filter(sequence, o) == selected_filter
            ]
        self.update_orientations(sequence, options)
        return options

    def update_orientations(
        self, sequence: list[dict[str, Any]], options: list[dict[str, Any]]
    ) -> None:
        # Validate sequence is not empty before accessing last element
        if not sequence:
            return  # No orientations to update if sequence is empty

        last = sequence[-1]
        for option in options:
            option[BLUE_ATTRS][START_ORI] = last[BLUE_ATTRS][END_ORI]
            option[RED_ATTRS][START_ORI] = last[RED_ATTRS][END_ORI]
            option[BLUE_ATTRS][END_ORI] = self.ori_calculator.calculate_end_ori(
                option, BLUE
            )
            option[RED_ATTRS][END_ORI] = self.ori_calculator.calculate_end_ori(
                option, RED
            )

    def _load_all_next_option_dicts(
        self, sequence: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        next_opts: list[dict[str, Any]] = []
        if not sequence:
            return next_opts

        # Additional safety check for sequence length
        if len(sequence) < 1:
            return next_opts

        # Handle placeholder case with additional safety check
        if sequence[-1].get("is_placeholder") and len(sequence) >= 2:
            last = sequence[-2]
        else:
            last = sequence[-1]
        start = last.get(END_POS)
        if start:
            for group in self.pictograph_dataset.values():
                for item in group:
                    if item.get(START_POS) == start:
                        next_opts.append(item)
        for o in next_opts:
            for color in (BLUE, RED):
                o[f"{color}_attributes"][START_ORI] = last[f"{color}_attributes"][
                    END_ORI
                ]
            self.ori_validation_engine.validate_single_pictograph(o, last)
        return next_opts

    def _determine_reversal_filter(
        self, sequence: list[dict[str, Any]], o: dict[str, Any]
    ) -> str:
        blue_cont, red_cont = self._check_continuity(sequence, o)
        if blue_cont and red_cont:
            return "continuous"
        elif blue_cont ^ red_cont:
            return "one_reversal"
        return "two_reversals"

    def _check_continuity(
        self, sequence: list[dict[str, Any]], o: dict[str, Any]
    ) -> tuple[bool, bool]:
        def get_last_rot(seq: list[dict[str, Any]], color: str) -> Optional[str]:
            for item in reversed(seq):
                rot = item.get(f"{color}_attributes", {}).get(PROP_ROT_DIR)
                if rot and rot != NO_ROT:
                    return rot
            return None

        last_blue = get_last_rot(sequence, BLUE)
        last_red = get_last_rot(sequence, RED)
        curr_blue = o.get(BLUE_ATTRS, {}).get(PROP_ROT_DIR, NO_ROT)
        curr_red = o.get(RED_ATTRS, {}).get(PROP_ROT_DIR, NO_ROT)
        if curr_blue == NO_ROT:
            curr_blue = last_blue
        if curr_red == NO_ROT:
            curr_red = last_red
        blue_cont = last_blue is None or curr_blue is None or curr_blue == last_blue
        red_cont = last_red is None or curr_red is None or curr_red == last_red
        return blue_cont, red_cont
