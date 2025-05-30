import logging
from typing import Optional
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication


class LoadingStateManager:
    def __init__(self):
        self.is_loading = False
        self.cancel_requested = False
        self.current_loading_length: Optional[int] = None
        self.logger = logging.getLogger(__name__)

    def start_loading(self, length: Optional[int] = None) -> bool:
        if self.is_loading:
            self.logger.debug(
                f"Cancelling previous loading operation for length {self.current_loading_length}"
            )
            self.cancel_loading()

        self.is_loading = True
        self.cancel_requested = False
        self.current_loading_length = length
        return True

    def stop_loading(self):
        self.is_loading = False
        self.cancel_requested = False
        self.current_loading_length = None

    def cancel_loading(self):
        if self.is_loading:
            self.logger.debug("Cancelling in-progress loading operation")
            self.cancel_requested = True
            QTimer.singleShot(50, self._reset_cancellation_state)

    def _reset_cancellation_state(self):
        self.cancel_requested = False
        self.is_loading = False
        self.logger.debug("Cancellation state reset")

    def should_cancel(self) -> bool:
        return self.cancel_requested

    def is_currently_loading(self) -> bool:
        return self.is_loading
