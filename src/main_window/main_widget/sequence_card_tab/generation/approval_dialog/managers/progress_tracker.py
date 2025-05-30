from PyQt6.QtCore import pyqtSignal, QObject
import logging


class ProgressTracker(QObject):
    image_loaded = pyqtSignal()
    all_images_processed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.images_loaded = 0
        self.total_images = 0

    def reset(self, total_images: int) -> None:
        """Reset progress tracking for a new batch"""
        self.total_images = total_images
        self.images_loaded = 0

    def increment_progress(self) -> None:
        """Increment the progress counter and emit appropriate signals"""
        self.images_loaded += 1
        self.image_loaded.emit()

        if self.images_loaded >= self.total_images:
            self.all_images_processed.emit()
            logging.info(
                f"All images processed: {self.images_loaded}/{self.total_images}"
            )

    def force_complete(self) -> None:
        """Force completion by setting progress to 100%"""
        remaining = self.total_images - self.images_loaded
        if remaining > 0:
            logging.info(f"Force completing {remaining} remaining sequences")
            for _ in range(remaining):
                self.increment_progress()

    def get_progress_info(self) -> dict:
        """Get current progress information"""
        return {
            "images_loaded": self.images_loaded,
            "total_images": self.total_images,
            "progress_percentage": (
                (self.images_loaded / self.total_images * 100)
                if self.total_images > 0
                else 0
            ),
        }

    def is_complete(self) -> bool:
        """Check if all images have been processed"""
        return self.images_loaded >= self.total_images
