from PyQt6.QtCore import pyqtSignal, QObject
from typing import List, Dict

from ...generation_manager import GeneratedSequenceData
from ...sequence_card import SequenceCard
from .synchronous_image_generator import SynchronousImageGenerator


class ApprovalDialogImageManager(QObject):
    """
    Main image manager that uses SynchronousImageGenerator.
    """

    image_loaded = pyqtSignal()
    all_images_processed = pyqtSignal()

    def __init__(self, main_widget):
        super().__init__()
        self.generator = SynchronousImageGenerator(main_widget)

        # Forward signals from generator
        self.generator.image_loaded.connect(self.image_loaded)
        self.generator.all_images_processed.connect(self.all_images_processed)

    def start_generation(
        self, sequences: List[GeneratedSequenceData], cards: Dict[str, SequenceCard]
    ) -> None:
        """Start image generation"""
        self.generator.start_generation(sequences, cards)

    def get_progress(self) -> dict:
        """Get the current progress of the image generation"""
        return {
            "images_loaded": self.generator.images_loaded,
            "total_images": self.generator.total_images,
            "progress_percentage": (
                (self.generator.images_loaded / self.generator.total_images * 100)
                if self.generator.total_images > 0
                else 0
            ),
            "pending_retries": 0,
            "circuit_breaker_state": "CLOSED",
        }

    def cleanup_workers(self) -> None:
        """Cleanup all workers and reset state"""
        self.generator.cleanup_workers()

    def force_complete_with_fallbacks(self) -> None:
        """Force completion by applying fallbacks to any remaining sequences"""
        self.generator.force_complete_with_fallbacks()

    # Legacy properties for backward compatibility
    @property
    def images_loaded(self) -> int:
        """Get number of images loaded (for backward compatibility)"""
        return self.generator.images_loaded

    @property
    def total_images(self) -> int:
        """Get total number of images (for backward compatibility)"""
        return self.generator.total_images

    @property
    def diagnostics(self) -> dict:
        """Get diagnostics information (for backward compatibility)"""
        return {}
