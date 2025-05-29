from PyQt6.QtCore import pyqtSignal, QObject, QTimer
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QApplication
from typing import List, Dict
import logging
import os
import json

from ...generation_manager import GeneratedSequenceData
from ...sequence_card import SequenceCard
from .fallback_image_provider import FallbackImageProvider
from .progress_tracker import ProgressTracker


class SynchronousImageGenerator(QObject):
    image_loaded = pyqtSignal()
    all_images_processed = pyqtSignal()

    def __init__(self, main_widget):
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
                sequence_card_tab = self.main_widget.get_tab_widget("sequence_card")
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

            # Create image using the correct method name
            qimage = image_creator.create_sequence_image(current_sequence)

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
