from typing import TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from main_window.main_widget.browse_tab.temp_beat_frame.temp_beat_frame import (
        TempBeatFrame,
    )


class TempBeatFactory:
    def __init__(self, temp_beat_frame: "TempBeatFrame"):
        self.beat_frame = temp_beat_frame
        self.main_widget = temp_beat_frame.main_widget

    def create_new_beat_and_add_to_sequence(
        self,
        pictograph_data: dict,
        override_grow_sequence=False,
        update_word=True,
        update_level=True,
        reversal_info: dict = None,
        select_beat: bool = True,
        update_image_export_preview: bool = True,
    ) -> None:
        try:
            from main_window.main_widget.sequence_workbench.sequence_beat_frame.beat import (
                Beat,
            )
            from data.constants import FLOAT

            new_beat = Beat(
                self.beat_frame, duration=pictograph_data.get("duration", 1)
            )
            new_beat.managers.updater.update_pictograph(pictograph_data)

            if reversal_info:
                new_beat.state.blue_reversal = reversal_info.get("blue_reversal", False)
                new_beat.state.red_reversal = reversal_info.get("red_reversal", False)

            # CRITICAL FIX: Ensure beat has a proper view to prevent NoneType errors
            if not hasattr(new_beat, "view") or new_beat.view is None:
                # Create a minimal view object to prevent null reference errors
                class MinimalBeatView:
                    def __init__(self):
                        self.is_start_pos = False
                        self.is_filled = True
                        self.is_selected = False

                new_beat.view = MinimalBeatView()
                logging.info("Created minimal view for beat to prevent NoneType errors")

            self.beat_frame.add_beat_to_sequence(new_beat)

            for motion in new_beat.elements.motion_set.values():
                if motion.state.motion_type == FLOAT:
                    if hasattr(self.main_widget, "letter_determiner"):
                        letter = self.main_widget.letter_determiner.determine_letter(
                            pictograph_data
                        )
                        new_beat.state.letter = letter
                        new_beat.elements.tka_glyph.update_tka_glyph()

            logging.info(
                f"Successfully added beat to temporary sequence: beat {pictograph_data.get('beat', '?')}"
            )

        except Exception as e:
            logging.error(
                f"Error in TempBeatFactory.create_new_beat_and_add_to_sequence: {e}"
            )
            import traceback

            traceback.print_exc()
