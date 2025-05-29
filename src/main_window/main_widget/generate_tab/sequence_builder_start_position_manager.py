# base_classes/start_position_manager.py

from copy import deepcopy
import random
from typing import TYPE_CHECKING, Dict, Any

from data.constants import (
    BLUE_ATTRS,
    DIAMOND,
    END_POS,
    IN,
    RED_ATTRS,
    START_ORI,
    END_ORI,
    START_POS,
)
from main_window.main_widget.sequence_workbench.sequence_beat_frame.start_pos_beat import (
    StartPositionBeat,
)

if TYPE_CHECKING:
    from main_window.main_widget.main_widget import MainWidget


class SequenceBuilderStartPosManager:
    """
    Manages the logic for adding a starting position pictograph to the sequence.
    """

    DIAMOND_KEYS = ["alpha1_alpha1", "beta5_beta5", "gamma11_gamma11"]
    OTHER_KEYS = ["alpha2_alpha2", "beta4_beta4", "gamma12_gamma12"]
    ALPHABETA_KEYS = ["alpha1_alpha1", "beta5_beta5"]

    def __init__(self, main_widget: "MainWidget") -> None:
        self.main_widget = main_widget
        # This could be parameterized; for now, we assume DIAMOND mode.
        self.grid_mode = DIAMOND

    def add_start_position(self, CAP_type: str = "") -> None:
        """
        Chooses a random valid start position and adds it to the sequence.
        """
        if CAP_type == "mirrored":
            start_keys = self.ALPHABETA_KEYS
        else:
            start_keys = (
                self.DIAMOND_KEYS if self.grid_mode == DIAMOND else self.OTHER_KEYS
            )
        chosen_key = random.choice(start_keys)
        try:
            start_pos, end_pos = chosen_key.split("_")
        except ValueError:
            raise ValueError(f"Invalid position key format: {chosen_key}")

        # Get pictograph dataset through the new dependency injection system
        try:
            from main_window.main_widget.pictograph_data_loader import (
                PictographDataLoader,
            )

            pictograph_data_loader = self.main_widget.app_context.get_service(
                PictographDataLoader
            )
            dataset = deepcopy(pictograph_data_loader.get_pictograph_dataset())
        except (AttributeError, KeyError):
            # Fallback: check if main_widget has pictograph_dataset
            if hasattr(self.main_widget, "pictograph_dataset"):
                dataset = deepcopy(self.main_widget.pictograph_dataset)
            else:
                import logging

                logger = logging.getLogger(__name__)
                logger.warning(
                    "pictograph_dataset not available in SequenceBuilderStartPositionManager"
                )
                dataset = {}
        for pictograph_list in dataset.values():
            for pictograph_data in pictograph_list:
                if (
                    pictograph_data.get(START_POS) == start_pos
                    and pictograph_data.get(END_POS) == end_pos
                ):
                    self._set_orientation_in(pictograph_data)

                    # Get sequence workbench through the new widget manager system
                    try:
                        sequence_workbench = self.main_widget.widget_manager.get_widget(
                            "sequence_workbench"
                        )
                        if sequence_workbench:
                            beat_frame = sequence_workbench.beat_frame
                        else:
                            # Fallback: try direct access for backward compatibility
                            if hasattr(self.main_widget, "sequence_workbench"):
                                beat_frame = (
                                    self.main_widget.sequence_workbench.beat_frame
                                )
                            else:
                                import logging

                                logger = logging.getLogger(__name__)
                                logger.warning(
                                    "sequence_workbench not available in SequenceBuilderStartPositionManager"
                                )
                                return
                    except AttributeError:
                        # Fallback: try direct access for backward compatibility
                        if hasattr(self.main_widget, "sequence_workbench"):
                            beat_frame = self.main_widget.sequence_workbench.beat_frame
                        else:
                            import logging

                            logger = logging.getLogger(__name__)
                            logger.warning(
                                "sequence_workbench not available in SequenceBuilderStartPositionManager"
                            )
                            return

                    start_pos_beat = StartPositionBeat(beat_frame)
                    start_pos_beat.managers.updater.update_pictograph(
                        deepcopy(pictograph_data)
                    )
                    try:
                        json_manager = self.main_widget.app_context.json_manager
                        json_manager.start_pos_handler.set_start_position_data(
                            start_pos_beat
                        )
                    except AttributeError:
                        # Fallback for cases where app_context is not available
                        import logging

                        logger = logging.getLogger(__name__)
                        logger.warning(
                            "json_manager not available in SequenceBuilderStartPositionManager"
                        )
                    beat_frame.start_pos_view.set_start_pos(start_pos_beat)
                    return
        raise LookupError(f"No matching start position found for key: {chosen_key}")

    def _set_orientation_in(self, pictograph_data: Dict[str, Any]) -> None:
        """
        Sets all relevant orientation attributes to 'in'.
        """
        pictograph_data[BLUE_ATTRS][START_ORI] = IN
        pictograph_data[RED_ATTRS][START_ORI] = IN
        pictograph_data[BLUE_ATTRS][END_ORI] = IN
        pictograph_data[RED_ATTRS][END_ORI] = IN

    def add_specific_start_position(
        self, start_position: str, CAP_type: str = ""
    ) -> None:
        """
        Adds a specific start position based on user selection (alpha1, beta5, or gamma11).
        """
        # Map user-friendly names to internal keys
        position_map = {
            "alpha1": "alpha1_alpha1",
            "beta5": "beta5_beta5",
            "gamma11": "gamma11_gamma11",
        }

        chosen_key = position_map.get(start_position.lower())
        if not chosen_key:
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(
                f"Unknown start position: {start_position}, falling back to random"
            )
            self.add_start_position(CAP_type)
            return

        start_pos, end_pos = chosen_key.split("_")

        try:
            from main_window.main_widget.pictograph_data_loader import (
                PictographDataLoader,
            )

            pictograph_data_loader = self.main_widget.app_context.get_service(
                PictographDataLoader
            )
            dataset = deepcopy(pictograph_data_loader.get_pictograph_dataset())
        except (AttributeError, KeyError):
            # Fallback: check if main_widget has pictograph_dataset
            if hasattr(self.main_widget, "pictograph_dataset"):
                dataset = deepcopy(self.main_widget.pictograph_dataset)
            else:
                import logging

                logger = logging.getLogger(__name__)
                logger.warning(
                    "pictograph_dataset not available in SequenceBuilderStartPositionManager"
                )
                dataset = {}

        for pictograph_list in dataset.values():
            for pictograph_data in pictograph_list:
                if (
                    pictograph_data.get(START_POS) == start_pos
                    and pictograph_data.get(END_POS) == end_pos
                ):
                    self._set_orientation_in(pictograph_data)

                    # Get sequence workbench through the new widget manager system
                    try:
                        sequence_workbench = self.main_widget.widget_manager.get_widget(
                            "sequence_workbench"
                        )
                        if sequence_workbench:
                            beat_frame = sequence_workbench.beat_frame
                        else:
                            # Fallback: try direct access for backward compatibility
                            if hasattr(self.main_widget, "sequence_workbench"):
                                beat_frame = (
                                    self.main_widget.sequence_workbench.beat_frame
                                )
                            else:
                                import logging

                                logger = logging.getLogger(__name__)
                                logger.warning(
                                    "sequence_workbench not available in SequenceBuilderStartPositionManager"
                                )
                                return
                    except AttributeError:
                        # Fallback: try direct access for backward compatibility
                        if hasattr(self.main_widget, "sequence_workbench"):
                            beat_frame = self.main_widget.sequence_workbench.beat_frame
                        else:
                            import logging

                            logger = logging.getLogger(__name__)
                            logger.warning(
                                "sequence_workbench not available in SequenceBuilderStartPositionManager"
                            )
                            return

                    start_pos_beat = StartPositionBeat(beat_frame)
                    start_pos_beat.managers.updater.update_pictograph(
                        deepcopy(pictograph_data)
                    )
                    try:
                        json_manager = self.main_widget.app_context.json_manager
                        json_manager.start_pos_handler.set_start_position_data(
                            start_pos_beat
                        )
                    except AttributeError:
                        # Fallback for cases where app_context is not available
                        import logging

                        logger = logging.getLogger(__name__)
                        logger.warning(
                            "json_manager not available in SequenceBuilderStartPositionManager"
                        )
                    beat_frame.start_pos_view.set_start_pos(start_pos_beat)
                    return
        raise LookupError(f"No matching start position found for key: {chosen_key}")
