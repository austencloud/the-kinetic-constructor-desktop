"""
Export Coordinator - Orchestrates all image export operations.

This coordinator replaces the monolithic SequenceCardImageExporter with a clean
architecture that follows the Single Responsibility Principle.
"""

from typing import TYPE_CHECKING
from PyQt6.QtWidgets import QProgressDialog, QMessageBox, QPushButton, QApplication
from PyQt6.QtCore import Qt
from utils.path_helpers import (
    get_dictionary_path,
    get_sequence_card_image_exporter_path,
)

if TYPE_CHECKING:
    from ..image_exporter import SequenceCardImageExporter


class ExportCoordinator:
    def __init__(self, exporter: "SequenceCardImageExporter"):
        self.exporter = exporter
        self.progress_dialog = None

    def export_all_images(self):
        dictionary_path = get_dictionary_path()
        export_path = get_sequence_card_image_exporter_path()

        word_folders = self.exporter.file_operations.get_word_folders(dictionary_path)
        if not word_folders:
            self._show_error("No word folders found in the dictionary.")
            return

        total_sequences = self.exporter.batch_processor.count_total_sequences(
            dictionary_path, word_folders
        )
        if total_sequences == 0:
            self._show_info("No sequences found to export.")
            return

        self._setup_progress_dialog(total_sequences)
        self.exporter.batch_processor.reset_cancel_flag()

        try:
            result = self._process_all_sequences(
                word_folders, dictionary_path, export_path, total_sequences
            )
            self._show_completion_message(result)
        finally:
            self._cleanup_progress_dialog()

    def _setup_progress_dialog(self, total_sequences: int):
        self.progress_dialog = QProgressDialog(
            "Exporting sequence card images...",
            "Cancel",
            0,
            total_sequences,
            self.exporter.sequence_card_tab,
        )
        self.progress_dialog.setWindowTitle("Export Progress")
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.setAutoClose(False)
        self.progress_dialog.setAutoReset(False)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.exporter.cancel_export)
        self.progress_dialog.setCancelButton(cancel_button)

        self.progress_dialog.show()

    def _process_all_sequences(
        self,
        word_folders: list,
        dictionary_path: str,
        export_path: str,
        total_sequences: int,
    ) -> dict:
        all_sequences = self.exporter.batch_processor.get_all_sequences(
            word_folders, dictionary_path
        )
        batch_size = self.exporter.config_manager.get_batch_size()

        processed_sequences = 0
        regenerated_count = 0
        skipped_count = 0
        failed_count = 0

        for i in range(0, len(all_sequences), batch_size):
            if self.exporter.batch_processor.cancel_requested:
                break

            end_index = min(i + batch_size, len(all_sequences))

            regenerated, skipped, failed = (
                self.exporter.batch_processor.process_sequence_batch(
                    all_sequences,
                    dictionary_path,
                    export_path,
                    i,
                    end_index,
                    self.exporter.process_single_sequence,
                    self.exporter.config_manager.get_memory_check_interval(),
                )
            )

            processed_sequences += end_index - i
            regenerated_count += regenerated
            skipped_count += skipped
            failed_count += failed

            self._update_progress(
                processed_sequences,
                total_sequences,
                regenerated_count,
                skipped_count,
                failed_count,
            )
            QApplication.processEvents()

        return {
            "total": total_sequences,
            "processed": processed_sequences,
            "regenerated": regenerated_count,
            "skipped": skipped_count,
            "failed": failed_count,
            "cancelled": self.exporter.batch_processor.cancel_requested,
        }

    def _update_progress(
        self, processed: int, total: int, regenerated: int, skipped: int, failed: int
    ):
        if self.progress_dialog:
            self.progress_dialog.setValue(processed)
            status = f"Processed: {processed}/{total} | Regenerated: {regenerated} | Skipped: {skipped}"
            if failed > 0:
                status += f" | Failed: {failed}"
            self.progress_dialog.setLabelText(status)

    def _show_completion_message(self, result: dict):
        if result["cancelled"]:
            QMessageBox.information(
                self.exporter.sequence_card_tab,
                "Export Cancelled",
                f"Export was cancelled.\nProcessed: {result['processed']}/{result['total']} sequences.",
            )
        else:
            message = (
                f"Export completed!\n\n"
                f"Total sequences: {result['total']}\n"
                f"Regenerated: {result['regenerated']}\n"
                f"Skipped (up to date): {result['skipped']}\n"
                f"Failed: {result['failed']}"
            )
            QMessageBox.information(
                self.exporter.sequence_card_tab, "Export Complete", message
            )

    def _show_error(self, message: str):
        QMessageBox.critical(self.exporter.sequence_card_tab, "Export Error", message)

    def _show_info(self, message: str):
        QMessageBox.information(self.exporter.sequence_card_tab, "Export Info", message)

    def _cleanup_progress_dialog(self):
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
        self.exporter.memory_manager.force_memory_cleanup()
