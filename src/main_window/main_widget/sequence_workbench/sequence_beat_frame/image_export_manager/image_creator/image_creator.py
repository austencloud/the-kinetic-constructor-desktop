from datetime import datetime
import logging
from PyQt6.QtGui import QImage, QPainter, QPen
from PyQt6.QtCore import Qt
from typing import TYPE_CHECKING

from base_widgets.pictograph.elements.views.beat_view import (
    BeatView,
)
from main_window.main_widget.sequence_workbench.sequence_beat_frame.image_export_manager.image_creator.beat_reversal_processor import (
    BeatReversalProcessor,
)

from .height_determiner import HeightDeterminer
from .beat_drawer import BeatDrawer
from .user_info_drawer import UserInfoDrawer
from .word_drawer import WordDrawer
from .image_export_difficulty_level_drawer import ImageExportDifficultyLevelDrawer

if TYPE_CHECKING:
    from ..image_export_manager import ImageExportManager


# image_export_manager/image_creator.py


class ImageCreator:
    BASE_MARGIN = 50

    def __init__(self, export_manager: "ImageExportManager"):
        self.export_manager = export_manager
        self.beat_frame = export_manager.beat_frame
        self.layout_manager = export_manager.layout_handler
        # Get beat size with safety check for None beat
        if (
            hasattr(self.beat_frame, "start_pos_view")
            and self.beat_frame.start_pos_view
            and hasattr(self.beat_frame.start_pos_view, "beat")
            and self.beat_frame.start_pos_view.beat
        ):
            self.beat_size = self.beat_frame.start_pos_view.beat.width()
        else:
            # Default beat size if start_pos_view.beat is None
            self.beat_size = 950  # Standard beat size
        self.beat_factory = export_manager.beat_factory
        self.beat_scale = 1
        self._setup_drawers()
        self.reversal_processor = BeatReversalProcessor()

    def _setup_drawers(self):
        self.beat_drawer = BeatDrawer(self)
        self.word_drawer = WordDrawer(self)
        self.user_info_drawer = UserInfoDrawer(self)
        self.difficulty_level_drawer = ImageExportDifficultyLevelDrawer()

    def create_sequence_image(
        self,
        sequence: list[dict],
        options: dict = None,
        dictionary: bool = False,
        fullscreen_preview: bool = False,
        override_word: str = None,
        override_difficulty_level: int = None,
    ) -> QImage:
        if options is None:
            options = (
                self.export_manager.settings_manager.image_export.get_all_image_export_options()
            )

        filled_beats = self._process_sequence(sequence)
        num_filled_beats = len(filled_beats)

        # Special case: If there are no filled beats but we should include the start position,
        # we still need to create an image with just the start position
        include_start_pos = options.get("include_start_position", False)
        if num_filled_beats == 0 and include_start_pos:
            # Force at least a 1x1 layout for the start position
            num_filled_beats = (
                0  # Explicitly set to 0 to ensure proper height calculation
            )

        if not fullscreen_preview:
            options.update(self._update_options(options, num_filled_beats))

        # Apply dynamic scale factor FIRST if provided (for page-optimized generation)
        original_beat_scale = self.beat_scale
        if (
            "dynamic_scale_factor" in options
            and options["dynamic_scale_factor"] is not None
        ):
            self.beat_scale = options["dynamic_scale_factor"]
            logging.info(f"🎯 Applied dynamic scale factor: {self.beat_scale:.3f}")

        if options["add_reversal_symbols"]:
            self.reversal_processor.process_reversals(sequence, filled_beats)

        # Calculate additional heights AFTER scale factor is applied
        options["additional_height_top"], options["additional_height_bottom"] = (
            self._determine_additional_heights(options, num_filled_beats)
        )

        if dictionary or fullscreen_preview:
            options = self._parse_options_for_dictionary_or_fullscreen_preview(options)

        # Get the layout based on the current beat frame layout
        # Note: layout_manager.calculate_layout returns (columns, rows) for the image
        column_count, row_count = self.layout_manager.calculate_layout(
            num_filled_beats,
            options["include_start_position"],
        )

        image = self._create_image(
            column_count,
            row_count,
            options["additional_height_top"] + options["additional_height_bottom"],
        )

        # Extract start position data from sequence if available
        start_pos_data = None
        if options["include_start_position"] and len(sequence) > 1:
            # Look for start position data in the sequence (usually at index 1)
            for entry in sequence:
                if entry.get("sequence_start_position"):
                    start_pos_data = entry
                    break

        self.beat_drawer.draw_beats(
            image,
            filled_beats,
            column_count,
            row_count,
            options["include_start_position"],
            options["additional_height_top"],
            options["add_beat_numbers"],
            start_pos_data,  # Pass start position data to BeatDrawer
        )
        if not fullscreen_preview and not dictionary:
            self._draw_additional_info(
                image,
                filled_beats,
                options,
                num_filled_beats,
                override_word=override_word,
                override_difficulty_level=override_difficulty_level,
            )

        # Restore original beat scale to avoid affecting subsequent operations
        self.beat_scale = original_beat_scale

        return image

    def _update_options(self, options: dict, num_filled_beats: int) -> dict:
        options["additional_height_top"], options["additional_height_bottom"] = (
            self._determine_additional_heights(options, num_filled_beats)
        )
        options["user_name"] = (
            self.export_manager.settings_manager.users.get_current_user()
        )
        options["export_date"] = datetime.now().strftime("%m-%d-%Y")
        return options

    def _parse_options_for_dictionary_or_fullscreen_preview(
        self, options: dict
    ) -> dict:
        dictionary_options = {
            "add_beat_numbers": True,
            "add_reversal_symbols": True,
            "add_user_info": False,
            "add_word": False,
            "add_difficulty_level": False,
            "include_start_position": options.get(
                "include_start_position", False
            ),  # Preserve start position setting instead of forcing False
            "combined_grids": options.get(
                "combined_grids", False
            ),  # Preserve combined grids setting
            "additional_height_top": 0,
            "additional_height_bottom": 0,
        }
        options.update(dictionary_options)
        return options

    def _process_sequence(self, sequence: list[dict]) -> list[BeatView]:
        filled_beats = self.beat_factory.process_sequence_to_beats(sequence)
        # Apply visibility settings to beats
        self._apply_visibility_settings(filled_beats)
        return filled_beats

    def _apply_visibility_settings(self, beats: list[BeatView]) -> None:
        """Apply visibility settings to all beats before exporting."""
        visibility_settings = self.export_manager.settings_manager.visibility

        # Get visibility settings for red and blue props
        red_visible = visibility_settings.get_motion_visibility("red")
        blue_visible = visibility_settings.get_motion_visibility("blue")

        # Apply visibility settings to each beat
        for beat_view in beats:
            # Apply to props
            if hasattr(beat_view.beat.elements, "props"):
                red_prop = beat_view.beat.elements.props.get("red")
                blue_prop = beat_view.beat.elements.props.get("blue")

                if red_prop:
                    red_prop.setVisible(red_visible)
                if blue_prop:
                    blue_prop.setVisible(blue_visible)

            # Apply to arrows
            if hasattr(beat_view.beat.elements, "arrows"):
                red_arrow = beat_view.beat.elements.arrows.get("red")
                blue_arrow = beat_view.beat.elements.arrows.get("blue")

                if red_arrow:
                    red_arrow.setVisible(red_visible)
                if blue_arrow:
                    blue_arrow.setVisible(blue_visible)

    def _determine_additional_heights(
        self, options: dict, num_filled_beats: int
    ) -> tuple:
        return HeightDeterminer.determine_additional_heights(
            options, num_filled_beats, self.beat_scale
        )

    def _draw_additional_info(
        self,
        image: QImage,
        filled_beats: list[BeatView],
        options: dict,
        num_filled_beats: int,
        override_word: str = None,
        override_difficulty_level: int = None,
    ):
        if options["add_user_info"]:
            self.user_info_drawer.draw_user_info(image, options, num_filled_beats)

        if options["add_word"]:
            # Use override word if provided, otherwise get from beat frame
            if override_word is not None:
                word = override_word
            else:
                word = self.beat_frame.get.current_word()
            self.word_drawer.draw_word(
                image, word, num_filled_beats, options["additional_height_top"]
            )

        if options["add_difficulty_level"]:
            # Use override difficulty level if provided, otherwise calculate from current sequence
            if override_difficulty_level is not None:
                difficulty_level = override_difficulty_level
            else:
                difficulty_level = self.export_manager.main_widget.sequence_level_evaluator.get_sequence_difficulty_level(
                    self.export_manager.beat_frame.json_manager.loader_saver.load_current_sequence()
                )
            self.difficulty_level_drawer.draw_difficulty_level(
                image,
                difficulty_level,
                options["additional_height_top"],
                self.beat_scale,
            )

        for beat_view in filled_beats:
            beat_view.beat.beat_number_item.setVisible(options["add_beat_numbers"])

    def _create_image(self, column_count, row_count, additional_height=0) -> QImage:
        image_width = int((column_count * self.beat_size * self.beat_scale))
        image_height = int(
            (row_count * self.beat_size * self.beat_scale) + additional_height
        )
        image = QImage(image_width, image_height, QImage.Format.Format_ARGB32)
        image.fill(Qt.GlobalColor.white)
        return image
