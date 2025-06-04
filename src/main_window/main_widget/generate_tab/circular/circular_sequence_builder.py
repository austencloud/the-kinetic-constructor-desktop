from typing import TYPE_CHECKING
from PyQt6.QtWidgets import QApplication
import random
from copy import deepcopy
from PyQt6.QtCore import Qt
from data.constants import (
    BLUE_ATTRS,
    DASH,
    END_POS,
    MOTION_TYPE,
    RED_ATTRS,
    STATIC,
)
from data.positions_maps import (
    swapped_positions,
    mirrored_positions,
    mirrored_swapped_positions,
)
from .CAP_executors.CAP_executor import CAPExecutor
from .CAP_type import CAPType
from ..base_sequence_builder import BaseSequenceBuilder
from ..turn_intensity_manager import TurnIntensityManager
from .utils.rotation_determiner import RotationDeterminer
from .utils.end_position_selector import RotatedEndPositionSelector
from .utils.pictograph_selector import PictographSelector
from .utils.word_length_calculator import WordLengthCalculator
from .CAP_executor_factory import CAPExecutorFactory, StrictRotatedCAPExecutor
from data.constants import *
from data.positions_maps import rotated_and_swapped_positions

if TYPE_CHECKING:
    from main_window.main_widget.generate_tab.generate_tab import GenerateTab


class CircularSequenceBuilder(BaseSequenceBuilder):
    def __init__(self, generate_tab: "GenerateTab"):
        super().__init__(generate_tab)
        self.executors: dict[CAPType, CAPExecutor] = {
            cap_type: CAPExecutorFactory.create_executor(cap_type, self)
            for cap_type in CAPType
        }

    @property
    def sequence_workbench(self):
        """Delegate to the generate_tab's sequence_workbench for context-aware access."""
        return self.generate_tab.sequence_workbench

    def build_sequence(
        self, length, turn_intensity, level, slice_size, CAP_type, prop_continuity
    ):
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            self._build_sequence_internal(
                length, turn_intensity, level, slice_size, CAP_type, prop_continuity
            )
        finally:
            QApplication.restoreOverrideCursor()
            self.generate_tab.sequence_workbench.beat_frame.emit_update_image_export_preview()

    def _build_sequence_internal(
        self,
        length,
        turn_intensity,
        level,
        slice_size,
        CAP_type,
        prop_continuity,
        start_position=None,
    ):
        self.initialize_sequence(
            length, start_position=start_position, CAP_type=CAP_type
        )
        blue_rot_dir, red_rot_dir = RotationDeterminer.get_rotation_dirs(
            prop_continuity
        )

        word_length, available_range = WordLengthCalculator.calculate(
            CAP_type, slice_size, length, len(self.sequence)
        )
        if CAP_type in [
            CAPType.MIRRORED_ROTATED,
            CAPType.MIRRORED_COMPLEMENTARY_ROTATED,
        ]:
            word_length = int(word_length / 2)
            available_range = int(available_range / 2)

        turn_manager = TurnIntensityManager(word_length, level, turn_intensity)
        turns_blue, turns_red = turn_manager.allocate_turns_for_blue_and_red()

        self._generate_pictographs(
            available_range,
            level,
            turns_blue,
            turns_red,
            slice_size,
            CAP_type,
            prop_continuity,
            blue_rot_dir,
            red_rot_dir,
        )

        self._apply_CAPs(self.sequence, CAP_type, slice_size)
        # current_word_label = self.sequence_workbench.current_word_label
        # current_word_label.update_current_word_label()
        self._update_construct_tab_options()

    def _generate_pictographs(
        self,
        available_range,
        level,
        turns_blue,
        turns_red,
        slice_size,
        CAP_type,
        prop_continuity,
        blue_rot_dir,
        red_rot_dir,
    ):
        for i in range(available_range):
            is_last_in_word = i == available_range - 1
            next_pictograph = self._generate_next_pictograph(
                level,
                turns_blue[i],
                turns_red[i],
                is_last_in_word,
                slice_size,
                CAP_type,
                prop_continuity,
                blue_rot_dir,
                red_rot_dir,
            )
            self._add_pictograph_to_sequence(next_pictograph)
            QApplication.processEvents()

    def _add_pictograph_to_sequence(self, next_pictograph):
        self.sequence.append(next_pictograph)
        self.generate_tab.sequence_workbench.beat_frame.beat_factory.create_new_beat_and_add_to_sequence(
            next_pictograph,
            override_grow_sequence=True,
            update_image_export_preview=False,
        )

    def _generate_next_pictograph(
        self,
        level,
        turn_blue,
        turn_red,
        is_last_in_word,
        slice_size,
        CAP_type,
        prop_continuity,
        blue_rot_dir,
        red_rot_dir,
    ):
        options = self._get_filtered_options(prop_continuity, blue_rot_dir, red_rot_dir)

        next_beat = self._select_next_beat(
            options, is_last_in_word, CAP_type, slice_size
        )

        if level in (2, 3):
            next_beat = self.set_turns(next_beat, turn_blue, turn_red)

        if next_beat[BLUE_ATTRS][MOTION_TYPE] in [DASH, STATIC] or next_beat[RED_ATTRS][
            MOTION_TYPE
        ] in [DASH, STATIC]:
            self.update_dash_static_prop_rot_dirs(
                next_beat, prop_continuity, blue_rot_dir, red_rot_dir
            )

        self.update_start_orientations(next_beat, self.sequence[-1])
        self.update_end_orientations(next_beat)
        return self.update_beat_number(next_beat, self.sequence)

    def _get_filtered_options(self, prop_continuity, blue_rot_dir, red_rot_dir):
        options = []
        construct_tab = None

        # Strategy 1: Try new tab manager system with on-demand creation
        try:
            if (
                hasattr(self.main_widget, "tab_manager")
                and self.main_widget.tab_manager
            ):
                # First try to get existing tab
                construct_tab = self.main_widget.tab_manager.get_tab_widget("construct")

                # If tab doesn't exist, create it on demand
                if not construct_tab:
                    import logging

                    logger = logging.getLogger(__name__)
                    logger.info(
                        "Construct tab not found, creating it for sequence generation"
                    )
                    construct_tab = self.main_widget.tab_manager._create_tab(
                        "construct"
                    )
                    if construct_tab:
                        logger.info("Successfully created construct tab on demand")
                    else:
                        logger.error("Failed to create construct tab on demand")
        except (AttributeError, TypeError) as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(f"Tab manager access failed: {e}")

        # Strategy 2: Try direct access if tab manager failed
        if not construct_tab:
            try:
                if (
                    hasattr(self.main_widget, "construct_tab")
                    and self.main_widget.construct_tab
                ):
                    construct_tab = self.main_widget.construct_tab
            except (AttributeError, TypeError):
                pass

        # Get options if construct tab is available
        if construct_tab:
            try:
                if (
                    hasattr(construct_tab, "option_picker")
                    and construct_tab.option_picker
                    and hasattr(construct_tab.option_picker, "option_getter")
                    and construct_tab.option_picker.option_getter
                    and hasattr(
                        construct_tab.option_picker.option_getter,
                        "_load_all_next_option_dicts",
                    )
                ):

                    options = deepcopy(
                        construct_tab.option_picker.option_getter._load_all_next_option_dicts(
                            self.sequence
                        )
                    )
                else:
                    import logging

                    logger = logging.getLogger(__name__)
                    logger.warning(
                        "Construct tab found but option_picker chain is incomplete"
                    )
            except Exception as e:
                import logging

                logger = logging.getLogger(__name__)
                logger.warning(f"Error accessing construct tab options: {e}")

        # If we still don't have options, this is a critical error
        if not options:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(
                "No construct tab available and failed to create it - sequence generation cannot continue"
            )
            raise RuntimeError(
                "Cannot access construct tab for pictograph options. "
                "This is required for sequence generation. "
                "Please ensure the construct tab can be properly initialized."
            )

        # Apply filtering if we have options
        if prop_continuity == "continuous":
            options = self.filter_options_by_rotation(
                options, blue_rot_dir, red_rot_dir
            )

        return options

    def _select_next_beat(self, options, is_last_in_word, CAP_type, slice_size):
        if not options:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(
                "No options available for beat selection - sequence generation cannot continue"
            )
            raise RuntimeError(
                "No pictograph options available for sequence generation. Ensure construct tab is properly initialized."
            )

        if is_last_in_word:
            expected_end_pos = self._determine_expected_end_pos(CAP_type, slice_size)
            next_beat = PictographSelector.select_pictograph(options, expected_end_pos)
        else:
            next_beat = random.choice(options)
        return next_beat

    def _determine_expected_end_pos(self, CAP_type, slice_size):
        end_pos_selectors = {
            CAPType.STRICT_ROTATED: lambda: RotatedEndPositionSelector.determine_rotated_end_pos(
                slice_size, self.sequence[1][END_POS]
            ),
            CAPType.STRICT_MIRRORED: lambda: mirrored_positions[VERTICAL][
                self.sequence[1][END_POS]
            ],
            CAPType.MIRRORED_SWAPPED: lambda: mirrored_swapped_positions[VERTICAL][
                self.sequence[1][END_POS]
            ],
            CAPType.STRICT_SWAPPED: lambda: swapped_positions[
                self.sequence[1][END_POS]
            ],
            CAPType.SWAPPED_COMPLEMENTARY: lambda: swapped_positions[
                self.sequence[1][END_POS]
            ],
            CAPType.STRICT_COMPLEMENTARY: lambda: self.sequence[1][END_POS],
            CAPType.ROTATED_COMPLEMENTARY: lambda: RotatedEndPositionSelector.determine_rotated_end_pos(
                "halved", self.sequence[1][END_POS]
            ),
            CAPType.MIRRORED_COMPLEMENTARY: lambda: mirrored_positions[VERTICAL][
                self.sequence[1][END_POS]
            ],
            CAPType.ROTATED_SWAPPED: lambda: rotated_and_swapped_positions[
                self.sequence[1][END_POS]
            ],
            CAPType.MIRRORED_ROTATED: lambda: (
                RotatedEndPositionSelector.determine_rotated_end_pos(
                    "halved", self.sequence[1][END_POS]
                )
            ),
            CAPType.MIRRORED_COMPLEMENTARY_ROTATED: lambda: (
                RotatedEndPositionSelector.determine_rotated_end_pos(
                    "halved", self.sequence[1][END_POS]
                )
            ),
        }

        end_pos_selector = end_pos_selectors.get(CAP_type)
        if end_pos_selector:
            return end_pos_selector()
        else:
            raise ValueError(
                "CAP type not implemented yet. Please implement the CAP type."
            )

    def _apply_CAPs(self, sequence, cap_type: CAPType, slice_size):
        executor = self.executors.get(cap_type)
        if executor and CAPType(cap_type) in [
            CAPType.MIRRORED_ROTATED,
            CAPType.MIRRORED_COMPLEMENTARY_ROTATED,
        ]:
            strict_rotated_executor: "StrictRotatedCAPExecutor" = self.executors.get(
                CAPType.STRICT_ROTATED
            )
            sequence = strict_rotated_executor.create_CAPs(
                sequence, slice_size="halved", end_mirrored=True
            )
            if cap_type == CAPType.MIRRORED_COMPLEMENTARY_ROTATED:
                self.executors.get(CAPType.MIRRORED_COMPLEMENTARY).create_CAPs(sequence)
            elif cap_type == CAPType.MIRRORED_ROTATED:
                self.executors.get(CAPType.STRICT_MIRRORED).create_CAPs(sequence)

        elif executor and CAPType(cap_type) in [
            CAPType.STRICT_ROTATED,
        ]:
            sequence = executor.create_CAPs(sequence, slice_size=slice_size)
        elif executor:
            executor.create_CAPs(sequence)
        else:
            raise ValueError(f"No executor found for CAP type: {cap_type.name}")

    def _update_construct_tab_options(self):
        """Update construct tab options using the new MVVM architecture with graceful fallbacks."""
        # Skip construct tab updates during isolated generation to prevent context conflicts
        if hasattr(self.generate_tab, "original_sequence_workbench"):
            import logging

            logger = logging.getLogger(__name__)
            logger.debug(
                "Skipping construct tab options update during isolated generation"
            )
            return

        try:
            # Try to get construct tab through the new coordinator pattern
            construct_tab = self.main_widget.tab_manager.get_tab_widget("construct")
            if (
                construct_tab
                and hasattr(construct_tab, "option_picker")
                and hasattr(construct_tab.option_picker, "updater")
            ):
                construct_tab.option_picker.updater.update_options()
                return
        except AttributeError:
            pass

        try:
            # Fallback: try through tab_manager for backward compatibility
            construct_tab = self.main_widget.tab_manager.get_tab_widget("construct")
            if (
                construct_tab
                and hasattr(construct_tab, "option_picker")
                and hasattr(construct_tab.option_picker, "updater")
            ):
                construct_tab.option_picker.updater.update_options()
                return
        except AttributeError:
            pass

        try:
            # Final fallback: try direct access for legacy compatibility
            if hasattr(self.main_widget, "construct_tab"):
                construct_tab = self.main_widget.construct_tab
                if hasattr(construct_tab, "option_picker") and hasattr(
                    construct_tab.option_picker, "updater"
                ):
                    construct_tab.option_picker.updater.update_options()
                    return
        except AttributeError:
            pass

        # If all else fails, log a warning but don't crash
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(
            "Could not update construct tab options - construct tab not available"
        )
