import os
import re
import logging
from typing import Union, Optional, TYPE_CHECKING

from settings_manager.global_settings.app_context import AppContext
from .structural_variation_checker import StructuralVariationChecker
from .thumbnail_generator import ThumbnailGenerator
from ....main_widget.browse_tab.thumbnail_box.thumbnail_box import ThumbnailBox
from utils.path_helpers import get_data_path

if TYPE_CHECKING:
    from main_window.main_widget.sequence_workbench.sequence_beat_frame.sequence_beat_frame import (
        SequenceBeatFrame,
    )

logger = logging.getLogger(__name__)


class DictionaryService:
    """Service for managing dictionary entries including adding variations, checking for duplicates, and managing thumbnails."""

    dictionary_dir = get_data_path("generated_data/dictionary")

    def __init__(self, beat_frame: "SequenceBeatFrame"):
        """Initialize the dictionary service."""
        self.beat_frame = beat_frame
        self.structural_checker = StructuralVariationChecker()
        self.thumbnail_generator = ThumbnailGenerator(beat_frame)
        self.sequence_workbench = beat_frame.sequence_workbench
        self.main_widget = beat_frame.main_widget

        os.makedirs(self.dictionary_dir, exist_ok=True)

    def add_to_dictionary(self) -> None:
        """Public method to add the current sequence to dictionary."""
        current_sequence = (
            AppContext.json_manager().loader_saver.load_current_sequence()
        )

        if self.is_sequence_invalid(current_sequence):
            self.display_message(
                "You must build a sequence to add it to your dictionary."
            )
            return

        self._process_sequence(current_sequence)

    def add_variation(
        self, sequence_data: list[dict], base_word: str
    ) -> dict[str, Union[str, int]]:
        """Add a variation of a sequence to the dictionary."""
        if len(sequence_data) <= 1:
            return {"status": "invalid"}

        base_path = os.path.join(self.dictionary_dir, base_word)
        os.makedirs(base_path, exist_ok=True)

        if self.structural_checker.check_for_structural_variation(
            sequence_data, base_word
        ):
            return {"status": "duplicate"}

        variation_number = self.get_next_variation_number(base_word)
        self._save_variation(sequence_data, base_word, variation_number)

        return {"status": "ok", "variation_number": variation_number}

    def _process_sequence(self, current_sequence: list[dict]) -> None:
        """Process a sequence to add to the dictionary."""
        base_word = self.beat_frame.get.current_word()
        base_path = os.path.join(self.dictionary_dir, base_word)

        if not os.path.exists(base_path):
            os.makedirs(base_path)

        if self.structural_checker.check_for_structural_variation(
            current_sequence, base_word
        ):
            self.display_message(
                f"This exact structural variation for {base_word} already exists."
            )
        else:
            variation_number = self.get_next_variation_number(base_word)
            self._save_variation(current_sequence, base_word, variation_number)
            self.display_message(
                f"New variation added to '{base_word}' as version {variation_number}."
            )

            self._update_thumbnail_box(base_word)

    def get_next_variation_number(self, base_word: str) -> int:
        """Get the next available version number for a word."""
        base_path = os.path.join(self.dictionary_dir, base_word)

        os.makedirs(base_path, exist_ok=True)

        existing_versions = []
        for file in os.listdir(base_path):
            match = re.search(r"_ver(\d+)", file)
            if match:
                existing_versions.append(int(match.group(1)))

        return max(existing_versions, default=0) + 1

    def _save_variation(
        self, sequence: list[dict], base_word: str, variation_number: int
    ) -> None:
        """Save a new variation to the dictionary."""
        base_path = os.path.join(self.dictionary_dir, base_word)

        self.thumbnail_generator.generate_and_save_thumbnail(
            sequence, variation_number, base_path, dictionary=True
        )

        logger.info(
            f"Saved new variation for '{base_word}' as version {variation_number}."
        )

    def collect_thumbnails(self, base_word: str) -> list[str]:
        """Collect all thumbnails for a word in the dictionary."""
        base_path = os.path.join(self.dictionary_dir, base_word)
        thumbnails = []

        if os.path.exists(base_path):
            for filename in os.listdir(base_path):
                if filename.lower().endswith((".png", ".jpg", ".jpeg")):
                    thumbnails.append(os.path.join(base_path, filename))

        return thumbnails

    def is_sequence_invalid(self, sequence: list[dict]) -> bool:
        """Check if a sequence is invalid."""
        return len(sequence) <= 1

    def display_message(self, message: str) -> None:
        """Display a message in the UI."""
        if hasattr(self.sequence_workbench, "indicator_label"):
            self.sequence_workbench.indicator_label.show_message(message)

    def _update_thumbnail_box(self, base_word: str) -> None:
        """Update the thumbnail box in the UI for a given word."""
        thumbnails = self.collect_thumbnails(base_word)
        thumbnail_box = self._find_thumbnail_box(base_word)

        if thumbnail_box:
            thumbnail_box.update_thumbnails(thumbnails)

    def _find_thumbnail_box(self, base_word: str) -> Optional["ThumbnailBox"]:
        """Find the thumbnail box for a given word."""
        try:
            return self.sequence_workbench.main_widget.browse_tab.sequence_picker.scroll_widget.thumbnail_boxes.get(
                base_word
            )
        except (AttributeError, KeyError):
            logger.warning(f"Could not find thumbnail box for {base_word}")
            return None
