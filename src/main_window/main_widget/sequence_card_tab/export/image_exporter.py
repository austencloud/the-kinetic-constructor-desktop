# src/main_window/main_widget/sequence_card_tab/export/image_exporter.py
from datetime import datetime
import os
from typing import TYPE_CHECKING
from PyQt6.QtGui import QImage
from PIL import Image


from main_window.main_widget.browse_tab.temp_beat_frame.temp_beat_frame import (
    TempBeatFrame,
)
from main_window.main_widget.sequence_workbench.sequence_beat_frame.image_export_manager.image_export_manager import (
    ImageExportManager,
)
from utils.path_helpers import (
    get_dictionary_path,
    get_sequence_card_image_exporter_path,
)

if TYPE_CHECKING:
    from ..tab import SequenceCardTab

from .core.export_coordinator import ExportCoordinator
from .managers.memory_manager import MemoryManager
from .managers.image_conversion_manager import ImageConversionManager
from .managers.metadata_manager import MetadataManager
from .managers.file_operations_manager import FileOperationsManager
from .managers.batch_processing_manager import BatchProcessingManager
from .managers.export_configuration_manager import ExportConfigurationManager


class SequenceCardImageExporter:
    def __init__(self, sequence_card_tab: "SequenceCardTab"):
        self.sequence_card_tab = sequence_card_tab
        self.main_widget = sequence_card_tab.main_widget
        self.temp_beat_frame = TempBeatFrame(sequence_card_tab)
        self.export_manager = ImageExportManager(
            self.temp_beat_frame, self.temp_beat_frame.__class__
        )
        self.progress_dialog = None
        self.cancel_requested = False

        self._initialize_managers()
        self.export_coordinator = ExportCoordinator(self)

    def _initialize_managers(self):
        self.config_manager = ExportConfigurationManager()
        self.memory_manager = MemoryManager(
            max_memory_mb=2000,
            check_interval=self.config_manager.get_memory_check_interval(),
        )
        self.image_converter = ImageConversionManager()
        self.metadata_manager = MetadataManager()
        self.file_operations = FileOperationsManager()
        self.batch_processor = BatchProcessingManager(
            self.memory_manager, self.file_operations, self.metadata_manager
        )

    def export_all_images(self):
        return self.export_coordinator.export_all_images()

    def qimage_to_pil(self, qimage: QImage, max_dimension: int = 3000) -> Image.Image:
        return self.image_converter.qimage_to_pil(qimage, max_dimension)

    def convert_qimage_to_pil(
        self, qimage: QImage, max_dimension: int = 3000
    ) -> Image.Image:
        return self.qimage_to_pil(qimage, max_dimension)

    def check_regeneration_needed(self, source_path: str, output_path: str) -> tuple:
        return self.file_operations.check_regeneration_needed(source_path, output_path)

    def get_memory_usage(self) -> float:
        return self.memory_manager.get_memory_usage()

    def force_memory_cleanup(self) -> None:
        self.memory_manager.force_memory_cleanup()

    def cancel_export(self) -> None:
        self.batch_processor.cancel_processing()
        self.cancel_requested = True

    def get_all_images(self, path: str) -> list[str]:
        return self.file_operations.get_all_images(path)

    def get_export_statistics(self) -> dict:
        return {
            "conversion_stats": self.image_converter.get_conversion_stats(),
            "memory_usage": self.memory_manager.get_memory_usage(),
            "batch_size": self.config_manager.get_batch_size(),
        }

    def get_performance_stats(self) -> dict:
        return self.get_export_statistics()

    def process_single_sequence(self, sequence_path: str, output_path: str) -> bool:
        try:
            metadata = self.metadata_manager.extract_metadata_from_file(sequence_path)
            if not self.metadata_manager.validate_metadata(metadata):
                return False

            sequence = metadata["sequence"]
            export_options = self.config_manager.get_default_export_options()

            self.temp_beat_frame.load_sequence(sequence)
            qimage = self.export_manager.image_creator.create_sequence_image(
                sequence, export_options, dictionary=False, fullscreen_preview=False
            )

            pil_image = self.image_converter.qimage_to_pil(qimage)
            enhanced_metadata = self.metadata_manager.prepare_export_metadata(
                metadata, export_options
            )
            png_info = self.metadata_manager.create_png_info(enhanced_metadata)

            quality_settings = self.config_manager.get_quality_settings()
            pil_image.save(
                output_path,
                "PNG",
                compress_level=quality_settings["png_compression"],
                pnginfo=png_info,
            )
            return True

        except Exception:
            return False

    # Legacy methods for backward compatibility
    @property
    def batch_size(self):
        return self.config_manager.get_batch_size()

    @batch_size.setter
    def batch_size(self, value):
        self.config_manager.set_batch_size(value)

    @property
    def memory_check_interval(self):
        return self.config_manager.get_memory_check_interval()

    @property
    def max_memory_usage_mb(self):
        return self.memory_manager.max_memory_mb

    @property
    def quality_settings(self):
        return self.config_manager.get_quality_settings()

    def _on_cancel_requested(self):
        self.cancel_export()

    def _count_total_sequences(self, dictionary_path: str, word_folders: list) -> int:
        return self.batch_processor.count_total_sequences(dictionary_path, word_folders)

    def _check_and_manage_memory(self, force_cleanup: bool = False) -> float:
        return self.memory_manager.check_and_manage_memory(force_cleanup)

    def _needs_regeneration(
        self, source_path: str, output_path: str
    ) -> tuple[bool, str]:
        return self.file_operations.check_regeneration_needed(source_path, output_path)

    def _create_png_info(self, metadata: dict):
        return self.metadata_manager.create_png_info(metadata)

    def _process_sequence_batch(
        self,
        word_folders: list,
        dictionary_path: str,
        export_path: str,
        start_index: int,
        end_index: int,
        processed_sequences: int,
        total_sequences: int,
        regenerated_count: int,
        skipped_count: int,
        failed_count: int,
    ) -> tuple[int, int, int, int]:
        all_sequences = self.batch_processor.get_all_sequences(
            word_folders, dictionary_path
        )

        regenerated, skipped, failed = self.batch_processor.process_sequence_batch(
            all_sequences,
            dictionary_path,
            export_path,
            start_index,
            end_index,
            self.process_single_sequence,
            self.config_manager.get_memory_check_interval(),
        )

        processed_sequences += end_index - start_index
        return (
            processed_sequences,
            regenerated_count + regenerated,
            skipped_count + skipped,
            failed_count + failed,
        )
