import logging
from typing import TYPE_CHECKING, Tuple

from Enums.letters import LetterType
from data.constants import BLUE_ATTRIBUTES, RED, BLUE, RED_ATTRIBUTES

if TYPE_CHECKING:
    from ...pictograph import Pictograph

logger = logging.getLogger(__name__)


class ArrowDataUpdater:
    def __init__(self, pictograph: "Pictograph") -> None:
        self.pictograph = pictograph

    def update(self, pictograph_data: dict) -> None:
        """
        Extracts arrow dataset information from the data and updates arrow objects.
        """
        red_arrow_data, blue_arrow_data = (
            self._extract_arrow_datasets(pictograph_data)
            if pictograph_data
            else (None, None)
        )
        if self.pictograph.state.letter_type == LetterType.Type3:
            self.pictograph.managers.get.shift().arrow.updater.update_arrow()
            self.pictograph.managers.get.dash().arrow.updater.update_arrow()
        else:
            self.pictograph.elements.arrows.get(RED).updater.update_arrow(
                red_arrow_data
            )
            self.pictograph.elements.arrows.get(BLUE).updater.update_arrow(
                blue_arrow_data
            )

    def _extract_arrow_datasets(self, pictograph_data: dict) -> Tuple[dict, dict]:
        red_data = (
            self._get_arrow_data_from_pictograph_data(pictograph_data, RED)
            if pictograph_data.get(RED_ATTRIBUTES, {})
            else None
        )
        blue_data = (
            self._get_arrow_data_from_pictograph_data(pictograph_data, BLUE)
            if pictograph_data.get(BLUE_ATTRIBUTES, {})
            else None
        )
        return red_data, blue_data

    def _get_arrow_data_from_pictograph_data(
        self, pictograph_data: dict, color: str
    ) -> dict:
        attributes = pictograph_data[f"{color}_attributes"]
        arrow_data = {}
        if "turns" in attributes or attributes.get("turns") == 0:
            arrow_data["turns"] = attributes["turns"]
        elif attributes.get("prop_rot_dir"):
            arrow_data["prop_rot_dir"] = attributes["prop_rot_dir"]
        if attributes.get("loc"):
            arrow_data["loc"] = attributes["loc"]
        return arrow_data
