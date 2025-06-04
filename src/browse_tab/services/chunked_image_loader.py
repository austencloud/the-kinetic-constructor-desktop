"""
Chunked Image Loading Manager for PyQt6-compatible asynchronous image loading.

This module provides a PyQt6-compatible chunked synchronous loading system that
replaces true async operations while maintaining UI responsiveness and stability.

Key Features:
- Chunked synchronous loading using QTimer.singleShot(0, callback) for yielding
- Queue-based processing with configurable chunk sizes
- Fallback to synchronous loading if QTimer operations fail
- Progressive display as images load within each batch
- Error boundaries around all QTimer operations

CRITICAL CONSTRAINTS:
- NO asyncio, threading, or complex async patterns
- Uses only QTimer.singleShot(0, callback) for yielding between batches
- All image loading is synchronous within each batch
- Maintains existing _load_image_sync(), _on_image_loaded(), set_thumbnail_image() methods
"""

import logging
from typing import List, Tuple, Optional, Callable
from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from PyQt6.QtWidgets import QApplication

logger = logging.getLogger(__name__)


class ChunkedImageLoadingManager(QObject):
    """
    PyQt6-compatible chunked image loading manager.

    Processes image loading in small chunks using QTimer.singleShot(0, callback)
    to yield control back to the UI event loop between batches, maintaining
    responsiveness without true async operations.
    """

    # Signals
    loading_started = pyqtSignal(int)  # total_count
    loading_progress = pyqtSignal(int, int)  # current, total
    loading_finished = pyqtSignal(bool)  # success
    batch_completed = pyqtSignal(int)  # batch_number

    def __init__(self, chunk_size: int = 1, parent: QObject = None):
        super().__init__(parent)

        # Configuration - Use individual processing for progressive display
        self.chunk_size = 1  # Always process images individually for instant feedback
        self.yield_delay = 0  # No delay for maximum responsiveness

        # State
        self._loading_queue: List[Tuple[object, str]] = []  # (card, image_path) pairs
        self._current_batch = 0
        self._total_batches = 0
        self._processed_count = 0
        self._total_count = 0
        self._is_loading = False
        self._cancelled = False

        # Error tracking
        self._failed_loads = []
        self._fallback_to_sync = False

        # Layout stability integration
        self._grid_reference = (
            None  # Reference to ResponsiveThumbnailGrid for layout locking
        )

        logger.info(
            f"ChunkedImageLoadingManager initialized with chunk_size={chunk_size}"
        )

    def queue_image_load(self, card, image_path: str):
        """Queue an image for chunked loading."""
        if not self._is_loading:
            # Start new loading session
            self._loading_queue = [(card, image_path)]
            self._start_chunked_loading()
        else:
            # Add to existing queue
            self._loading_queue.append((card, image_path))
            self._total_count = len(self._loading_queue)
            self._total_batches = (
                self._total_count + self.chunk_size - 1
            ) // self.chunk_size

    def queue_multiple_loads(self, card_path_pairs: List[Tuple[object, str]]):
        """Queue multiple images for chunked loading."""
        if self._is_loading:
            logger.warning("Loading already in progress, cancelling previous operation")
            self.cancel_loading()

        self._loading_queue = card_path_pairs.copy()
        self._start_chunked_loading()

    def cancel_loading(self):
        """Cancel the current loading operation."""
        self._cancelled = True
        self._is_loading = False
        logger.info("Chunked loading cancelled")

    def _start_chunked_loading(self):
        """Start the chunked loading process."""
        if not self._loading_queue:
            return

        self._is_loading = True
        self._cancelled = False
        self._current_batch = 0
        self._processed_count = 0
        self._total_count = len(self._loading_queue)
        self._total_batches = (
            self._total_count + self.chunk_size - 1
        ) // self.chunk_size
        self._failed_loads = []
        self._fallback_to_sync = False

        # Lock grid layout to prevent resize events during loading
        if self._grid_reference:
            self._grid_reference.lock_layout_during_loading(True)

        logger.info(
            f"Starting chunked loading: {self._total_count} images in {self._total_batches} batches"
        )
        self.loading_started.emit(self._total_count)

        # Start processing first batch
        self._process_next_batch()

    def _process_next_batch(self):
        """Process the next image individually for progressive display.

        Replaces batch processing with individual image loading to eliminate
        batch completion delays that cause poor UX.
        """
        if self._cancelled:
            self._finish_loading(False)
            return

        if self._processed_count >= self._total_count:
            self._finish_loading(True)
            return

        # Get next image to process (individual processing)
        if self._processed_count < len(self._loading_queue):
            card, image_path = self._loading_queue[self._processed_count]

            logger.debug(
                f"Processing image {self._processed_count + 1}/{self._total_count}: {image_path}"
            )

            try:
                # Check if card is still valid before loading
                if not self._is_card_valid(card):
                    logger.debug(f"Skipping deleted card for {image_path}")
                    self._processed_count += 1
                    # Continue with next image immediately
                    QTimer.singleShot(1, self._process_next_batch)
                    return

                # Load image synchronously using the card's existing method
                card._load_image_sync(image_path)
                self._processed_count += 1

                # Emit progress for individual image
                self.loading_progress.emit(self._processed_count, self._total_count)

                # Process events to keep UI responsive after each image
                QApplication.processEvents()

                logger.debug(f"✅ Image loaded successfully: {image_path}")

            except Exception as e:
                logger.error(f"Failed to load image {image_path}: {e}")
                self._failed_loads.append((image_path, str(e)))
                self._processed_count += 1

                # Try to set error state on card if it's still valid
                try:
                    if self._is_card_valid(card):
                        card.set_error_state("Load failed")
                except Exception as card_error:
                    logger.error(f"Failed to set error state on card: {card_error}")

            # Emit individual completion (for compatibility)
            self.batch_completed.emit(self._processed_count)

            # Continue with next image using minimal delay for smooth progression
            if self._processed_count < self._total_count and not self._cancelled:
                try:
                    QTimer.singleShot(self.yield_delay, self._process_next_batch)
                except Exception as timer_error:
                    logger.error(f"QTimer.singleShot failed: {timer_error}")
                    # Fallback to immediate processing
                    self._fallback_to_sync = True
                    self._process_next_batch()
            else:
                self._finish_loading(True)
        else:
            self._finish_loading(True)

    def _finish_loading(self, success: bool):
        """Finish the loading process."""
        self._is_loading = False

        if self._failed_loads:
            logger.warning(f"Loading completed with {len(self._failed_loads)} failures")
            for image_path, error in self._failed_loads:
                logger.warning(f"  Failed: {image_path} - {error}")

        if self._fallback_to_sync:
            logger.warning(
                "Chunked loading fell back to synchronous mode due to QTimer issues"
            )

        logger.info(
            f"Chunked loading finished: {self._processed_count}/{self._total_count} images loaded"
        )

        # Unlock grid layout after loading is complete
        if self._grid_reference:
            self._grid_reference.lock_layout_during_loading(False)

        self.loading_finished.emit(success)

        # Clear state
        self._loading_queue.clear()
        self._current_batch = 0
        self._total_batches = 0
        self._processed_count = 0
        self._total_count = 0

    def is_loading(self) -> bool:
        """Check if loading is currently in progress."""
        return self._is_loading

    def get_progress(self) -> Tuple[int, int]:
        """Get current progress as (processed, total)."""
        return self._processed_count, self._total_count

    def get_failed_loads(self) -> List[Tuple[str, str]]:
        """Get list of failed loads as (image_path, error) pairs."""
        return self._failed_loads.copy()

    def set_chunk_size(self, chunk_size: int):
        """Set the chunk size for batch processing."""
        if chunk_size < 1:
            chunk_size = 1
        elif chunk_size > 20:
            chunk_size = 20  # Reasonable upper limit

        self.chunk_size = chunk_size
        logger.info(f"Chunk size set to {chunk_size}")

    def set_yield_delay(self, delay_ms: int):
        """Set the delay between batches in milliseconds."""
        if delay_ms < 0:
            delay_ms = 0
        elif delay_ms > 100:
            delay_ms = 100  # Reasonable upper limit

        self.yield_delay = delay_ms
        logger.info(f"Yield delay set to {delay_ms}ms")

    def _is_card_valid(self, card) -> bool:
        """Check if a card widget is still valid and not deleted."""
        try:
            # Try to access a basic property to check if the widget is still valid
            _ = card.isVisible()
            return True
        except RuntimeError:
            # Widget has been deleted
            return False
        except AttributeError:
            # Card doesn't have the expected interface
            return False

    def set_grid_reference(self, grid):
        """Set reference to ResponsiveThumbnailGrid for layout locking integration."""
        self._grid_reference = grid
        logger.debug("Grid reference set for layout stability integration")
