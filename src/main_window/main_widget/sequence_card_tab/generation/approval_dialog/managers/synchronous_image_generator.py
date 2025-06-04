from PyQt6.QtCore import pyqtSignal, QObject, QTimer
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QApplication
from typing import TYPE_CHECKING, List, Dict
import logging
import os
import json

from ...generation_manager import GeneratedSequenceData
from ...sequence_card import SequenceCard
from .fallback_image_provider import FallbackImageProvider
from .progress_tracker import ProgressTracker

if TYPE_CHECKING:
    from main_window.main_widget.main_widget import MainWidget


class SynchronousImageGenerator(QObject):
    image_loaded = pyqtSignal()
    all_images_processed = pyqtSignal()

    def __init__(self, main_widget: "MainWidget"):
        super().__init__()
        self.main_widget = main_widget
        self.fallback_provider = FallbackImageProvider()
        self.progress_tracker = ProgressTracker()

        self.current_sequences = []
        self.current_cards = {}
        self.current_index = 0

        self.generation_timer = QTimer()
        self.generation_timer.timeout.connect(self._process_next_sequence)
        self.generation_timer.setSingleShot(True)

    def start_generation(
        self, sequences: List[GeneratedSequenceData], cards: Dict[str, SequenceCard]
    ):
        if not self.main_widget:
            logging.error("Main widget not found")
            return

        self.current_sequences = sequences
        self.current_cards = cards
        self.current_index = 0
        self.progress_tracker.reset(len(sequences))

        if sequences:
            self.generation_timer.start(10)

    def _process_next_sequence(self):
        if self.current_index >= len(self.current_sequences):
            self.all_images_processed.emit()
            return

        sequence_data = self.current_sequences[self.current_index]

        try:
            pixmap = self._generate_image_synchronously(sequence_data)

            if pixmap and not pixmap.isNull():
                self.current_cards[sequence_data.id].set_image(pixmap)
                logging.info(f"Successfully generated image for {sequence_data.id}")
            else:
                self._apply_fallback(sequence_data.id, "Image generation failed")

        except Exception as e:
            logging.error(f"Error generating image for {sequence_data.id}: {e}")
            self._apply_fallback(sequence_data.id, str(e))

        self.progress_tracker.increment_progress()
        self.current_index += 1

        QApplication.processEvents()

        if self.current_index < len(self.current_sequences):
            self.generation_timer.start(50)
        else:
            self.all_images_processed.emit()

    def _generate_image_synchronously(
        self, sequence_data: GeneratedSequenceData
    ) -> QPixmap:
        try:
            # Get export_manager through the correct path
            export_manager = (
                self.main_widget.sequence_workbench.beat_frame.image_export_manager
            )
            if not export_manager:
                return None

            # Fix: Access sequence_card_tab through the tab manager with graceful fallbacks
            sequence_card_tab = None
            try:
                # Try the new coordinator pattern first
                sequence_card_tab = self.main_widget.tab_manager.get_tab_widget(
                    "sequence_card"
                )
            except AttributeError:
                try:
                    # Try through tab_manager with correct method name
                    sequence_card_tab = self.main_widget.tab_manager.get_tab_widget(
                        "sequence_card"
                    )
                except AttributeError:
                    try:
                        # Final fallback: direct access
                        if hasattr(self.main_widget, "sequence_card_tab"):
                            sequence_card_tab = self.main_widget.sequence_card_tab
                    except AttributeError:
                        pass

            if not sequence_card_tab:
                logging.error("Could not access sequence card tab")
                return None

            # Fix: Access temp_beat_frame through the image_exporter, not directly on sequence_card_tab
            if not hasattr(sequence_card_tab, "image_exporter"):
                logging.error("Sequence card tab missing image_exporter")
                return None

            temp_beat_frame = sequence_card_tab.image_exporter.temp_beat_frame
            if not temp_beat_frame:
                return None

            # Use the sequence data directly instead of loading from temp_beat_frame
            current_sequence = sequence_data.sequence_data

            # If we have an isolated JSON file, try to load from there as fallback
            if (
                hasattr(sequence_data, "session_json_file")
                and sequence_data.session_json_file
            ):
                try:
                    if os.path.exists(sequence_data.session_json_file):
                        with open(
                            sequence_data.session_json_file, "r", encoding="utf-8"
                        ) as f:
                            isolated_sequence = json.load(f)
                            if isolated_sequence and len(isolated_sequence) > len(
                                current_sequence
                            ):
                                current_sequence = isolated_sequence
                                logging.info(
                                    f"Using isolated JSON file: {sequence_data.session_json_file}"
                                )
                except Exception as e:
                    logging.warning(f"Could not load from isolated JSON file: {e}")

            image_creator = export_manager.image_creator
            if not image_creator:
                return None

            # Extract word and difficulty level from sequence data for proper display
            override_word = (
                sequence_data.word if hasattr(sequence_data, "word") else None
            )
            override_difficulty_level = (
                sequence_data.params.level
                if hasattr(sequence_data, "params")
                and hasattr(sequence_data.params, "level")
                else None
            )

            # Calculate optimal scale factor for approval dialog images
            scale_factor = self._calculate_optimal_scale_factor_for_approval_dialog()

            # Create image using page-optimized options with scale factor
            options = {
                "add_beat_numbers": True,
                "add_reversal_symbols": False,  # Skip for speed in approval dialog
                "add_user_info": True,
                "add_word": True,
                "add_difficulty_level": True,
                "include_start_position": True,  # Enable start position for approval dialog
                "combined_grids": False,
                "additional_height_top": 0,  # Will be calculated by HeightDeterminer
                "additional_height_bottom": 0,  # Will be calculated by HeightDeterminer
                "dynamic_scale_factor": scale_factor,  # Apply reverse-calculated scale factor
            }

            logging.info(f"🎨 Approval dialog using scale factor: {scale_factor:.3f}")

            qimage = image_creator.create_sequence_image(
                current_sequence,
                options=options,
                override_word=override_word,
                override_difficulty_level=override_difficulty_level,
            )

            # Convert QImage to QPixmap
            from PyQt6.QtGui import QPixmap

            pixmap = QPixmap.fromImage(qimage)
            return pixmap

        except Exception as e:
            logging.error(f"Error in synchronous generation: {e}")
            return None

    def _apply_fallback(self, sequence_id: str, error_message: str):
        if sequence_id in self.current_cards:
            self.fallback_provider.apply_fallback_to_card(
                sequence_id, self.current_cards[sequence_id], error_message
            )

    def cleanup_workers(self):
        self.generation_timer.stop()

    def force_complete_with_fallbacks(self):
        self.generation_timer.stop()
        self.progress_tracker.force_complete()

    @property
    def images_loaded(self) -> int:
        return self.progress_tracker.images_loaded

    @property
    def total_images(self) -> int:
        return self.progress_tracker.total_images

    def _calculate_optimal_scale_factor_for_approval_dialog(self) -> float:
        """
        Calculate the optimal scale factor for approval dialog images using the same
        reverse-calculation approach as other generation modes.

        This ensures consistent sizing across all image generation contexts.

        Returns:
            float: Scale factor to apply to the image creator
        """
        try:
            # Use approval dialog specific target size (larger than page cells)
            # Approval dialog images should be larger for better review experience
            target_width = 400  # Larger than page cells for better visibility
            target_height = 300  # Proportional height

            # Base pictograph size is hardcoded at 950x950 throughout the system
            BASE_PICTOGRAPH_SIZE = 950

            # Step 1: Estimate layout for typical approval dialog sequences
            # Most approval sequences are 16 beats + start position
            columns, rows = 5, 4  # Standard layout for 16-beat + start position

            # Step 2: Calculate what the full-size image dimensions would be
            core_image_width = columns * BASE_PICTOGRAPH_SIZE
            core_image_height = rows * BASE_PICTOGRAPH_SIZE

            # Estimate additional heights (using standard calculations)
            estimated_additional_height_top = 300  # Standard for word label
            estimated_additional_height_bottom = 150  # Standard for user info

            full_image_width = core_image_width
            full_image_height = (
                core_image_height
                + estimated_additional_height_top
                + estimated_additional_height_bottom
            )

            # Step 3: Calculate scale ratio based on approval dialog target size
            width_scale_ratio = target_width / full_image_width
            height_scale_ratio = target_height / full_image_height

            # Use the smaller ratio to ensure the image fits within the target size
            scale_factor = min(width_scale_ratio, height_scale_ratio)

            # Step 4: Apply safety bounds to prevent extreme scaling
            scale_factor = max(scale_factor, 0.05)  # Minimum 5% to maintain readability
            scale_factor = min(
                scale_factor, 0.5
            )  # Maximum 50% for approval dialog (larger than page cells)

            logging.info(f"🎯 APPROVAL DIALOG SCALE FACTOR: {scale_factor:.3f}")
            logging.info(
                f"   📐 Layout: {columns}x{rows}, Full size: {full_image_width}x{full_image_height}"
            )
            logging.info(
                f"   📏 Target: {target_width}x{target_height}, Ratios: W={width_scale_ratio:.3f}, H={height_scale_ratio:.3f}"
            )

            return scale_factor

        except Exception as e:
            logging.error(f"Error calculating approval dialog scale factor: {e}")
            # Fallback to a conservative default that should work for approval dialogs
            return 0.15  # 15% of original size (larger than page cells)
