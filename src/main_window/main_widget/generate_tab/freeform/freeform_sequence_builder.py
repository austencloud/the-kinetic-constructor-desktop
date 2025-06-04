from typing import TYPE_CHECKING
from PyQt6.QtWidgets import QApplication
import random
import logging
from copy import deepcopy
from PyQt6.QtCore import Qt
from data.constants import CLOCKWISE, COUNTER_CLOCKWISE, LETTER
from ..base_sequence_builder import BaseSequenceBuilder
from ..turn_intensity_manager import TurnIntensityManager

if TYPE_CHECKING:
    from main_window.main_widget.generate_tab.generate_tab import GenerateTab


class FreeFormSequenceBuilder(BaseSequenceBuilder):
    def __init__(self, generate_tab: "GenerateTab"):
        super().__init__(generate_tab)
        self.generate_tab = generate_tab

    def build_sequence(
        self,
        length: int,
        turn_intensity: int,
        level: int,
        prop_continuity: str = "continuous",
        start_position: str = None,
        batch_mode: bool = False,  # Add batch_mode parameter
    ):
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        self.initialize_sequence(length, start_position)

        if prop_continuity == "continuous":
            blue_rot_dir = random.choice([CLOCKWISE, COUNTER_CLOCKWISE])
            red_rot_dir = random.choice([CLOCKWISE, COUNTER_CLOCKWISE])
        elif prop_continuity == "random":
            blue_rot_dir = None
            red_rot_dir = None

        # Fix sequence length calculation - CORRECT LOGIC
        # The sequence structure: [metadata, start_position, beat1, beat2, ..., beatN]
        # After initialization, we have [metadata, start_position] = 2 elements
        # When user requests N beats, they want N beats AFTER the start position
        # The start position does NOT count toward the requested beat count
        current_sequence_length = len(self.sequence)

        # CORRECT CALCULATION: Generate exactly 'length' beats after start position
        # We should always generate exactly 'length' beats, regardless of current sequence length
        # (assuming current sequence has metadata + start_position = 2 elements)
        if current_sequence_length != 2:
            logging.warning(
                f"Unexpected sequence length after initialization: {current_sequence_length}, expected 2"
            )

        beats_to_generate = length  # Generate exactly the requested number of beats

        logging.info(
            f"Sequence length calculation: requested={length}, current_elements={current_sequence_length}, to_generate={beats_to_generate}"
        )

        if beats_to_generate <= 0:
            logging.warning(
                f"No beats to generate - sequence already has {current_sequence_length} beats for requested length {length}"
            )
            QApplication.restoreOverrideCursor()
            return

        turn_manager = TurnIntensityManager(beats_to_generate, level, turn_intensity)
        turns_blue, turns_red = turn_manager.allocate_turns_for_blue_and_red()

        for i in range(beats_to_generate):
            # Ensure we don't go out of bounds on the turns arrays
            blue_turn = turns_blue[i] if i < len(turns_blue) else 0
            red_turn = turns_red[i] if i < len(turns_red) else 0

            next_pictograph = self._generate_next_pictograph(
                level,
                blue_turn,
                red_turn,
                prop_continuity,
                blue_rot_dir,
                red_rot_dir,
                batch_mode=batch_mode,  # Pass batch_mode to pictograph generation
            )
            if next_pictograph is None:
                logging.error(f"Failed to generate pictograph for beat {i+1}")
                break

            self.sequence.append(next_pictograph)
            self.generate_tab.sequence_workbench.beat_frame.beat_factory.create_new_beat_and_add_to_sequence(
                next_pictograph,
                override_grow_sequence=True,
                update_image_export_preview=False,
            )
            QApplication.processEvents()

        self._update_construct_tab_options()

        QApplication.restoreOverrideCursor()

    def _generate_next_pictograph(
        self,
        level: int,
        turn_blue: float,
        turn_red: float,
        prop_continuity: str,
        blue_rot_dir: str,
        red_rot_dir: str,
        batch_mode: bool = False,  # Add batch_mode parameter
    ):
        construct_tab = self._get_construct_tab()
        if not construct_tab:
            raise RuntimeError("Construct tab not available for option generation")

        option_dicts = (
            construct_tab.option_picker.option_getter._load_all_next_option_dicts(
                self.sequence
            )
        )
        option_dicts = [deepcopy(option) for option in option_dicts]

        logging.info(f"Initial option pool size: {len(option_dicts)}")

        # Enhanced filtering logic for batch mode
        if batch_mode:
            # For batch generation, apply more permissive filtering
            filtered_by_letter = self._filter_options_by_letter_type(option_dicts)
            if len(filtered_by_letter) >= 5:  # Ensure minimum variety
                option_dicts = filtered_by_letter
                logging.info(
                    f"Applied letter type filtering: {len(option_dicts)} options"
                )
            else:
                logging.info(
                    "Skipping letter type filtering to maintain option variety"
                )

            # For continuous prop_continuity, only apply rotation filtering if we have many options
            if prop_continuity == "continuous" and len(option_dicts) >= 10:
                rotation_filtered = self.filter_options_by_rotation(
                    option_dicts, blue_rot_dir, red_rot_dir
                )
                if len(rotation_filtered) >= 3:  # Minimum for randomness
                    option_dicts = rotation_filtered
                    logging.info(
                        f"Applied rotation filtering: {len(option_dicts)} options"
                    )
                else:
                    logging.info(
                        "Skipping rotation filtering to maintain option variety"
                    )
        else:
            # Regular generation with standard filtering
            filtered_by_letter = self._filter_options_by_letter_type(option_dicts)
            if len(filtered_by_letter) >= 5:
                option_dicts = filtered_by_letter
                logging.info(
                    f"After letter type filtering: {len(option_dicts)} options"
                )
            else:
                logging.info(
                    f"Skipping letter filtering - only {len(filtered_by_letter)} options available"
                )

            if prop_continuity == "continuous" and len(option_dicts) >= 8:
                rotation_filtered = self.filter_options_by_rotation(
                    option_dicts, blue_rot_dir, red_rot_dir
                )
                if len(rotation_filtered) >= 3:
                    option_dicts = rotation_filtered
                    logging.info(
                        f"After rotation filtering: {len(option_dicts)} options"
                    )
                else:
                    logging.info(
                        f"Skipping rotation filtering - only {len(rotation_filtered)} options available"
                    )

        if len(option_dicts) == 0:
            logging.error(
                "No options available after filtering - this will cause generation failure"
            )
            return None
        elif len(option_dicts) == 1:
            logging.warning("Only 1 option available - sequences will be deterministic")
        else:
            logging.info(
                f"Good: {len(option_dicts)} options available for random selection"
            )

        last_beat = self.sequence[-1]

        # Enhanced randomization for batch mode
        if batch_mode:
            # Use more sophisticated selection that considers recent choices
            import time

            random.seed(int(time.time() * 1000000) % 2147483647)

            # Avoid the same choice as the last few beats if possible
            if len(self.sequence) >= 4 and len(option_dicts) > 3:
                recent_letters = [beat.get("letter", "") for beat in self.sequence[-3:]]
                non_recent_options = [
                    opt
                    for opt in option_dicts
                    if opt.get("letter", "") not in recent_letters
                ]
                if non_recent_options:
                    option_dicts = non_recent_options
                    logging.info(
                        f"Avoiding recent letters: {len(option_dicts)} options remain"
                    )
        else:
            # Standard randomization - avoid recent choices if possible
            if len(self.sequence) >= 4 and len(option_dicts) > 3:
                recent_letters = [beat.get("letter", "") for beat in self.sequence[-3:]]
                non_recent_options = [
                    opt
                    for opt in option_dicts
                    if opt.get("letter", "") not in recent_letters
                ]
                if non_recent_options:
                    option_dicts = non_recent_options
                    logging.info(
                        f"Avoiding recent letters: {len(option_dicts)} options remain"
                    )

        next_beat = random.choice(option_dicts)
        logging.info(f"Chose option with letter: {next_beat.get('letter', 'Unknown')}")

        if level == 2 or level == 3:
            next_beat = self.set_turns(next_beat, turn_blue, turn_red)

        self.update_start_orientations(next_beat, last_beat)
        self.update_dash_static_prop_rot_dirs(
            next_beat, prop_continuity, blue_rot_dir, red_rot_dir
        )
        self.update_end_orientations(next_beat)
        next_beat = self.update_beat_number(next_beat, self.sequence)
        return next_beat

    def _filter_options_by_letter_type(self, options: list[dict]) -> list[dict]:
        """Filter options based on selected letter types."""
        selected_types = self.generate_tab.letter_picker.get_selected_letter_types()
        selected_letters = []
        for letter_type in selected_types:
            selected_letters.extend(letter_type.letters)

        filtered_options = [
            option for option in options if option[LETTER] in selected_letters
        ]

        # If filtering results in too few options (less than 3), be more lenient
        if len(filtered_options) < 3:
            # Log warning and consider expanding letter selection
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(
                f"Letter type filtering too restrictive: {len(filtered_options)} options. Expanding selection."
            )

            # If we have very few selected types, automatically include more types
            if len(selected_types) < 3:
                from enums.letter.letter_type import LetterType

                all_letters = []
                for letter_type in LetterType:
                    all_letters.extend(letter_type.letters)

                expanded_options = [
                    option for option in options if option[LETTER] in all_letters
                ]
                if len(expanded_options) >= 3:
                    logger.info(
                        f"Expanded to all letter types: {len(expanded_options)} options"
                    )
                    return expanded_options

            # Return original options if expansion still doesn't help
            if len(options) > 0:
                return options

        return filtered_options

    def _get_construct_tab(self):
        """Get the construct tab using the new MVVM architecture with graceful fallbacks."""
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
                if hasattr(self.main_widget, "construct_tab"):
                    construct_tab = self.main_widget.construct_tab
            except (AttributeError, TypeError):
                pass

        return construct_tab

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

        construct_tab = self._get_construct_tab()
        if (
            construct_tab
            and hasattr(construct_tab, "option_picker")
            and hasattr(construct_tab.option_picker, "updater")
        ):
            construct_tab.option_picker.updater.update_options()
            return

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
