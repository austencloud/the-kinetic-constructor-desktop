import logging
from typing import Optional, Callable
from PyQt6.QtWidgets import QProgressDialog, QApplication
from PyQt6.QtCore import Qt


class ProgressTrackingService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.cancel_requested = False
        self._progress_dialog: Optional[QProgressDialog] = None

    def create_progress_dialog(
        self, total_items: int, item_type: str = "items"
    ) -> QProgressDialog:
        self.cancel_requested = False

        progress = QProgressDialog(
            f"Preparing to export {total_items} {item_type}...",
            "Cancel",
            0,
            total_items,
        )

        progress.setWindowTitle("Exporting Sequence Cards")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)

        progress.canceled.connect(self._handle_cancel_request)
        self._progress_dialog = progress

        return progress

    def _handle_cancel_request(self):
        self.cancel_requested = True
        self.logger.info("Export cancellation requested by user")

    def update_progress(self, current: int, total: int, message: str = ""):
        if self._progress_dialog:
            self._progress_dialog.setValue(current)
            if message:
                self._progress_dialog.setLabelText(message)
            QApplication.processEvents()

    def close_progress_dialog(self):
        if self._progress_dialog:
            try:
                self._progress_dialog.canceled.disconnect(self._handle_cancel_request)
            except TypeError:
                pass
            self._progress_dialog.close()
            self._progress_dialog = None

    def is_cancelled(self) -> bool:
        return self.cancel_requested

    def reset_cancellation(self):
        self.cancel_requested = False
