from typing import TYPE_CHECKING
from data.constants import LETTER, SEQUENCE_START_POSITION
from src.settings_manager.global_settings.app_context import AppContext
from utils.reversal_detector import ReversalDetector
from utils.word_simplifier import WordSimplifier

if TYPE_CHECKING:
    from .sequence_beat_frame import SequenceBeatFrame
from PyQt6.QtCore import QTimer


class BeatFramePopulator:
    loading_text = "Loading sequence..."

    def __init__(self, beat_frame: "SequenceBeatFrame"):
        self.beat_frame = beat_frame
        self.main_widget = beat_frame.main_widget
        self.sequence_workbench = beat_frame.sequence_workbench
        self.start_pos_view = beat_frame.start_pos_view
        self.selection_overlay = beat_frame.selection_overlay
        self.current_sequence_json = []

    def populate_beat_frame_from_json(
        self,
        current_sequence_json: list[dict[str, str]],
        initial_state_load: bool = False,
    ) -> None:
        self.current_sequence_json = current_sequence_json
        indicator_label = self.sequence_workbench.indicator_label
        indicator_label.show_message(self.loading_text)
        AppContext.json_manager().loader_saver.clear_current_sequence_file()

        # Get construct tab through the new widget manager system
        self.construct_tab = self.main_widget.tab_manager.get_tab_widget("construct")
        if not self.construct_tab:
            # Fallback: try direct access for backward compatibility
            self.construct_tab = getattr(self.main_widget, "construct_tab", None)

        if not self.current_sequence_json:
            return
        if not initial_state_load:
            self.beat_frame.updater.reset_beat_frame()
        self._set_start_position()
        self._update_sequence_layout()
        self._update_sequence_word()
        self._update_difficulty_level()
        self._populate_beats(select_beat=False)
        self._finalize_sequence(initial_state_load)

        indicator_label.show_message(
            f"{self.current_word} loaded successfully! Ready to edit."
        )

    def _set_start_position(self):
        if not self.construct_tab or not hasattr(
            self.construct_tab, "start_pos_picker"
        ):
            # Handle case where construct tab is not available yet
            import logging

            logger = logging.getLogger(__name__)
            logger.warning("Construct tab not available during start position setup")
            return

        start_pos_picker = self.construct_tab.start_pos_picker
        start_pos_beat = start_pos_picker.convert_current_sequence_json_entry_to_start_pos_pictograph(
            self.current_sequence_json
        )
        AppContext.json_manager().start_pos_handler.set_start_position_data(
            start_pos_beat
        )
        self.start_pos_view.set_start_pos(start_pos_beat)

    def _update_sequence_layout(self):
        length = len(self.current_sequence_json) - 2
        self.modify_layout_for_chosen_number_of_beats(length)

    def _update_difficulty_level(self):
        if len(self.current_sequence_json) > 2:
            self.sequence_workbench.difficulty_label.update_difficulty_label()
            # Update the circular indicator
            self.sequence_workbench.circular_indicator.update_indicator()
        else:
            self.sequence_workbench.difficulty_label.set_difficulty_level("")
            # Hide the circular indicator for sequences with only start position
            self.sequence_workbench.circular_indicator.hide()

    def _update_sequence_word(self):
        self.current_word = "".join(
            [beat[LETTER] for beat in self.current_sequence_json[2:] if LETTER in beat]
        )
        self.current_word = WordSimplifier.simplify_repeated_word(self.current_word)
        self.sequence_workbench.current_word_label.set_current_word(self.current_word)

    def _populate_beats(self, select_beat=True):
        for _, pictograph_data in enumerate(self.current_sequence_json[1:]):
            if pictograph_data.get(SEQUENCE_START_POSITION) or pictograph_data.get(
                "is_placeholder", False
            ):
                continue

            reversal_info = ReversalDetector.detect_reversal(
                self.current_sequence_json, pictograph_data
            )
            self.sequence_workbench.beat_frame.beat_factory.create_new_beat_and_add_to_sequence(
                pictograph_data,
                override_grow_sequence=True,
                update_word=True,
                update_level=False,
                reversal_info=reversal_info,
                select_beat=select_beat,
            )

    def _finalize_sequence(self, initial_state_load):
        last_beat = self.sequence_workbench.beat_frame.get.last_filled_beat().beat

        # Update construct tab if available
        if self.construct_tab and hasattr(self.construct_tab, "last_beat"):
            self.construct_tab.last_beat = last_beat
            if hasattr(self.construct_tab, "option_picker"):
                self.construct_tab.option_picker.updater.update_options()

            # Automatically switch construct tab view based on sequence state (only if construct tab is active)
            if self._is_construct_tab_active():
                self._auto_switch_construct_tab_view()
        else:
            import logging

            logger = logging.getLogger(__name__)
            logger.warning("Construct tab not available during sequence finalization")

        self.sequence_workbench.difficulty_label.update_difficulty_label()
        # Update the circular indicator
        self.sequence_workbench.circular_indicator.update_indicator()
        if initial_state_load:
            target_tab = AppContext.settings_manager().global_settings.get_current_tab()
            toggle_animation = target_tab == "construct"
            QTimer.singleShot(
                1500,
                lambda: self.selection_overlay.select_beat_view(
                    last_beat.view, toggle_animation
                ),
            )

    def _auto_switch_construct_tab_view(self):
        """
        Automatically switch the construct tab view based on the current sequence state.

        Logic:
        - Empty sequence (no beats): Show start position picker
        - Sequence with only start position: Show start position picker
        - Sequence with multiple beats: Show option picker
        """
        if not self.construct_tab:
            return

        try:
            # Get the current beat count (excluding start position)
            beat_count = self.beat_frame.get.beat_count()

            import logging

            logger = logging.getLogger(__name__)
            logger.info(f"Auto-switching construct tab view: beat_count={beat_count}")

            # Use centralized picker determination logic
            picker_type = self._determine_appropriate_picker()

            if picker_type == "start_pos_picker":
                if hasattr(self.construct_tab, "transition_to_start_pos_picker"):
                    self.construct_tab.transition_to_start_pos_picker()
                    logger.info(
                        "Switched to start position picker (sequence completely empty)"
                    )
            elif picker_type == "option_picker":
                if hasattr(self.construct_tab, "transition_to_option_picker"):
                    self.construct_tab.transition_to_option_picker()
                    logger.info(
                        "Switched to option picker (start position set or beats exist)"
                    )

        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to auto-switch construct tab view: {e}")

    def _determine_appropriate_picker(self) -> str:
        """
        Centralized logic to determine which picker should be shown based on current sequence state.

        Returns:
            "start_pos_picker" if sequence is completely empty (no start position AND no beats)
            "option_picker" if start position is set OR beats exist
        """
        try:
            # Get current sequence state
            beat_count = self.beat_frame.get.beat_count()
            start_pos_is_filled = self.beat_frame.start_pos_view.is_filled

            import logging

            logger = logging.getLogger(__name__)
            logger.debug(
                f"Determining picker: beat_count={beat_count}, start_pos_filled={start_pos_is_filled}"
            )

            # Show Start Position Picker only when sequence is completely empty
            if beat_count == 0 and not start_pos_is_filled:
                return "start_pos_picker"

            # Show Option Picker when start position is set OR beats exist
            return "option_picker"

        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(f"Error determining appropriate picker: {e}")
            # Default to option picker on error
            return "option_picker"

    def _is_construct_tab_active(self) -> bool:
        """
        Check if the construct tab is currently the active tab.

        Returns:
            True if construct tab is active, False otherwise
        """
        try:
            # Get main widget through beat frame
            main_widget = self.beat_frame.main_widget

            # Check if we have a tab manager and get the current tab
            if hasattr(main_widget, "tab_manager"):
                current_tab = main_widget.tab_manager.get_current_tab()
                return current_tab == "construct"

            # Fallback: check if construct tab is visible in the right stack
            if hasattr(main_widget, "right_stack"):
                current_widget = main_widget.right_stack.currentWidget()
                if current_widget:
                    # Check if the current widget is related to construct tab
                    widget_name = current_widget.__class__.__name__
                    return widget_name in [
                        "StartPosPicker",
                        "OptionPicker",
                        "AdvancedStartPosPicker",
                    ]

            return False

        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(f"Error checking if construct tab is active: {e}")
            # Default to False to avoid unwanted picker switching
            return False

    def modify_layout_for_chosen_number_of_beats(self, beat_count):
        self.beat_frame.layout_manager.configure_beat_frame(
            beat_count, override_grow_sequence=True
        )
