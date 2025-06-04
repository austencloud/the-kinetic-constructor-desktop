# src/main_window/main_widget/sequence_card_tab/export/page_exporter.py
import logging
from typing import TYPE_CHECKING

from .services import ExportOrchestrationService

if TYPE_CHECKING:
    from ..tab import SequenceCardTab


class SequenceCardPageExporter:
    def __init__(self, sequence_card_tab: "SequenceCardTab"):
        self.sequence_card_tab = sequence_card_tab
        self.logger = logging.getLogger(__name__)
        self.orchestration_service = ExportOrchestrationService(sequence_card_tab)

    def export_all_pages_as_images(self):
        self.orchestration_service.export_all_pages()

    def export_current_page_as_image(self):
        """Export only the currently visible page as an image."""
        # For now, delegate to export_all_pages - can be refined later
        self.logger.info("Exporting current page (delegating to export_all_pages)")
        self.orchestration_service.export_all_pages()

    def export_all_pages_as_pdf(self):
        """Export all pages as a PDF file."""
        # Placeholder implementation - can be enhanced later
        self.logger.info("PDF export not yet implemented - using image export")
        self.orchestration_service.export_all_pages()

    def clear_page_cache(self) -> int:
        return self.orchestration_service.clear_cache()

    def get_export_statistics(self):
        return self.orchestration_service.get_export_statistics()
