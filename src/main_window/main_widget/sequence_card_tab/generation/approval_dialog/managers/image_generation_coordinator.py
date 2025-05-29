from PyQt6.QtCore import pyqtSignal, QObject, Qt
from PyQt6.QtGui import QPixmap
from typing import List, Dict, Optional
import logging

from ...generation_manager import GeneratedSequenceData
from ...sequence_card import SequenceCard
from .circuit_breaker_manager import CircuitBreakerManager
from .retry_manager import RetryManager
from .fallback_image_provider import FallbackImageProvider
from .progress_tracker import ProgressTracker
from .worker_manager import WorkerManager


class ImageGenerationCoordinator(QObject):
    """Main coordinator for image generation that orchestrates specialized managers"""

    image_loaded = pyqtSignal()
    all_images_processed = pyqtSignal()
    retry_attempted = pyqtSignal(str, int)  # sequence_id, attempt_number

    def __init__(self, main_widget):
        super().__init__()
        self.main_widget = main_widget
        self.diagnostics = {}

        # Initialize specialized managers
        self.circuit_breaker = CircuitBreakerManager()
        self.retry_manager = RetryManager()
        self.fallback_provider = FallbackImageProvider()
        self.progress_tracker = ProgressTracker()
        self.worker_manager = WorkerManager()

        # Store sequence data for retries
        self._sequence_data_cache: Dict[str, GeneratedSequenceData] = {}
        self._cards_cache: Optional[Dict[str, SequenceCard]] = None

        # Connect signals
        self._setup_signal_connections()

    def _setup_signal_connections(self) -> None:
        """Setup signal connections between managers"""
        self.retry_manager.retry_attempted.connect(self.retry_attempted)
        self.progress_tracker.image_loaded.connect(self.image_loaded)
        self.progress_tracker.all_images_processed.connect(self.all_images_processed)

    def start_generation(
        self, sequences: List[GeneratedSequenceData], cards: Dict[str, SequenceCard]
    ) -> None:
        """Start image generation with comprehensive error handling"""
        if not self._validate_generation_prerequisites():
            return

        # Cache data for retries
        self._sequence_data_cache = {seq.id: seq for seq in sequences}
        self._cards_cache = cards

        self._reset_generation_state(len(sequences))

        if self.circuit_breaker.is_open():
            logging.warning("Circuit breaker is open, attempting recovery")
            self.circuit_breaker.attempt_recovery()
            return

        for sequence_data in sequences:
            try:
                self._initiate_generation_for_sequence(sequence_data, cards)
            except Exception as e:
                logging.error(
                    f"Failed to initiate generation for {sequence_data.id}: {e}"
                )
                self._handle_generation_failure(sequence_data.id, str(e), cards)

    def _validate_generation_prerequisites(self) -> bool:
        """Validate that all prerequisites for generation are met"""
        if not self.main_widget:
            logging.error("Main widget not found, cannot generate images")
            return False
        return True

    def _reset_generation_state(self, total_images: int) -> None:
        """Reset all generation state for a new batch"""
        self.progress_tracker.reset(total_images)
        self.retry_manager.clear_retry_queue()
        self.diagnostics.clear()

    def _initiate_generation_for_sequence(
        self, sequence_data: GeneratedSequenceData, cards: Dict[str, SequenceCard]
    ) -> None:
        """Safely initiate generation for a single sequence"""
        try:
            worker = self.worker_manager.create_worker(sequence_data, self.main_widget)
            self.worker_manager.setup_worker_connections(
                worker,
                self._handle_image_generated,
                self._handle_image_failed,
                self._on_diagnostic_info,
                self._handle_worker_finished,
            )
            worker.start()
        except Exception as e:
            logging.error(f"Error creating worker for {sequence_data.id}: {e}")
            raise

    def _handle_image_generated(self, sequence_id: str, pixmap: QPixmap) -> None:
        """Handle successful image generation with validation"""
        try:
            if not self._validate_generated_image(sequence_id, pixmap):
                self._handle_image_failed(sequence_id, "Invalid pixmap generated")
                return

            if not self._cards_cache or sequence_id not in self._cards_cache:
                logging.warning(f"Sequence card {sequence_id} not found in cards cache")
                self.progress_tracker.increment_progress()
                return

            self._cards_cache[sequence_id].set_image(pixmap)
            self.circuit_breaker.record_success()
            logging.info(f"Successfully set image for sequence card {sequence_id}")
        except Exception as e:
            logging.error(f"Error handling generated image for {sequence_id}: {e}")
            self._handle_image_failed(sequence_id, f"Error setting image: {str(e)}")
        finally:
            self.progress_tracker.increment_progress()

    def _validate_generated_image(self, sequence_id: str, pixmap: QPixmap) -> bool:
        """Validate that the generated image is usable"""
        if not pixmap or pixmap.isNull():
            logging.warning(f"Null or invalid pixmap for sequence {sequence_id}")
            return False

        if pixmap.width() <= 0 or pixmap.height() <= 0:
            logging.warning(
                f"Invalid dimensions for sequence {sequence_id}: {pixmap.width()}x{pixmap.height()}"
            )
            return False

        return True

    def _handle_image_failed(self, sequence_id: str, error_message: str) -> None:
        """Handle image generation failure with retry logic"""
        try:
            self.retry_manager.record_failure(sequence_id, error_message)
            self.circuit_breaker.record_failure()

            if self.retry_manager.should_retry(
                sequence_id, self.circuit_breaker.is_open()
            ):
                self.retry_manager.schedule_retry(
                    sequence_id, lambda seq_id: self._retry_sequence_generation(seq_id)
                )
                return

            self._apply_fallback_image(sequence_id, error_message)
        except Exception as e:
            logging.error(f"Error handling image failure for {sequence_id}: {e}")
            self._apply_fallback_image(sequence_id, f"Handler error: {str(e)}")
        finally:
            self.progress_tracker.increment_progress()

    def _retry_sequence_generation(self, sequence_id: str) -> None:
        """Retry generation for a specific sequence"""
        try:
            if sequence_id in self._sequence_data_cache and self._cards_cache:
                sequence_data = self._sequence_data_cache[sequence_id]
                logging.info(f"Retrying generation for sequence {sequence_id}")
                self._initiate_generation_for_sequence(sequence_data, self._cards_cache)
            else:
                logging.warning(f"Cannot retry {sequence_id}: sequence data not cached")
        except Exception as e:
            logging.error(f"Error retrying sequence {sequence_id}: {e}")

    def _apply_fallback_image(self, sequence_id: str, error_message: str) -> None:
        """Apply fallback image when generation fails"""
        try:
            if self._cards_cache and sequence_id in self._cards_cache:
                self.fallback_provider.apply_fallback_to_card(
                    sequence_id, self._cards_cache[sequence_id], error_message
                )
            else:
                logging.warning(
                    f"Cannot apply fallback: sequence {sequence_id} not in cards cache"
                )
        except Exception as e:
            logging.error(f"Error applying fallback for {sequence_id}: {e}")

    def _on_diagnostic_info(self, sequence_id: str, diagnostics: dict) -> None:
        """Handle diagnostic information with error tracking"""
        try:
            self.diagnostics[sequence_id] = diagnostics

            if not diagnostics.get("image_generation_success", False):
                error_details = {
                    k: v
                    for k, v in diagnostics.items()
                    if "error" in k.lower()
                    or k
                    in ["sequence_loaded", "has_export_manager", "has_image_creator"]
                }

                if error_details:
                    logging.error(
                        f"Image generation diagnostics for {sequence_id}: {error_details}"
                    )

        except Exception as e:
            logging.error(f"Error processing diagnostics for {sequence_id}: {e}")

    def _handle_worker_finished(self, worker) -> None:
        """Handle worker cleanup with error safety"""
        self.worker_manager.cleanup_worker(worker)

    def _handle_generation_failure(
        self, sequence_id: str, error_message: str, cards: Dict[str, SequenceCard]
    ) -> None:
        """Handle initial generation failure"""
        self.retry_manager.record_failure(sequence_id, error_message)
        self.circuit_breaker.record_failure()
        self._apply_fallback_image(sequence_id, error_message)

    def get_progress(self) -> dict:
        """Get current progress with retry information"""
        progress_info = self.progress_tracker.get_progress_info()
        progress_info.update(
            {
                "pending_retries": self.retry_manager.get_pending_retries_count(),
                "circuit_breaker_state": self.circuit_breaker.get_state(),
            }
        )
        return progress_info

    def cleanup_workers(self) -> None:
        """Cleanup all workers and reset state"""
        self.retry_manager.clear_retry_queue()
        self.worker_manager.cleanup_all_workers()

    def force_complete_with_fallbacks(self) -> None:
        """Force completion by applying fallbacks to any remaining sequences"""
        try:
            self.worker_manager.terminate_all_workers()
            self.retry_manager.clear_retry_queue()
            self.progress_tracker.force_complete()

        except Exception as e:
            logging.error(f"Error during force completion: {e}")

    def reset_circuit_breaker(self) -> None:
        """Manually reset the circuit breaker"""
        self.circuit_breaker.reset()

    def configure_retry_policy(
        self, max_retries: int = 3, base_delay: int = 1000, max_delay: int = 10000
    ) -> None:
        """Configure retry policy parameters"""
        self.retry_manager.configure_policy(max_retries, base_delay, max_delay)
