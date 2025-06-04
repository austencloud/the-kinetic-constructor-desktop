import os
import logging
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from PyQt6.QtWidgets import QWidget

from .cache_service import CacheService
from .page_processing_service import PageProcessingService
from .progress_tracking_service import ProgressTrackingService
from ..export_config import ExportConfig
from ..export_ui_manager import ExportUIManager
from ..export_page_renderer import ExportPageRenderer

if TYPE_CHECKING:
    from ...tab import SequenceCardTab


class ExportOrchestrationService:
    def __init__(self, sequence_card_tab: "SequenceCardTab"):
        self.sequence_card_tab = sequence_card_tab
        self.logger = logging.getLogger(__name__)

        self.config = ExportConfig(sequence_card_tab)
        self.ui_manager = ExportUIManager(sequence_card_tab)
        self.cache_service = CacheService()
        self.page_renderer = None
        self.page_processing_service = None
        self.progress_service = ProgressTrackingService()

        self._initialize_services()

    def _initialize_services(self):
        from ..page_image_data_extractor import PageImageDataExtractor
        from ..export_grid_calculator import ExportGridCalculator

        data_extractor = PageImageDataExtractor(self.sequence_card_tab)
        self.page_processing_service = PageProcessingService(data_extractor)

        grid_calculator = ExportGridCalculator(self.config, self.sequence_card_tab)
        self.page_renderer = ExportPageRenderer(self.config, grid_calculator)

    def export_all_pages(self):
        self.logger.info("Starting sequence card page export orchestration")

        pages = self._get_pages_to_export()
        if not pages:
            self.ui_manager.show_warning_message(
                "No Pages to Export",
                "There are no sequence card pages to export. Please select a sequence length first.",
            )
            return

        export_dir = self.ui_manager.get_export_directory()
        if not export_dir:
            return

        self._orchestrate_export(pages, export_dir)

    def _get_pages_to_export(self) -> List[QWidget]:
        pages = self.sequence_card_tab.pages
        if not pages and hasattr(self.sequence_card_tab, "printable_displayer"):
            if hasattr(self.sequence_card_tab.printable_displayer, "pages"):
                pages = self.sequence_card_tab.printable_displayer.pages
            elif hasattr(self.sequence_card_tab.printable_displayer, "manager"):
                pages = self.sequence_card_tab.printable_displayer.manager.pages
        return pages or []

    def _orchestrate_export(self, pages: List[QWidget], export_dir: str):
        try:
            export_subdir = self._prepare_export_directory(pages, export_dir)
            total_images = self.page_processing_service.count_total_images(pages)

            progress = self.progress_service.create_progress_dialog(
                total_images, "images"
            )
            self.config.sync_with_ui_layout()

            success = self._process_pages(pages, export_subdir)

            self.progress_service.close_progress_dialog()

            if success and not self.progress_service.is_cancelled():
                self._handle_export_completion(export_subdir, len(pages))

        except Exception as e:
            self.logger.error(f"Error during export orchestration: {e}")
            self.progress_service.close_progress_dialog()
            self.ui_manager.show_error_message(
                "Export Error", f"An error occurred during export: {str(e)}"
            )

    def _prepare_export_directory(self, pages: List[QWidget], export_dir: str) -> str:
        metadata = self.page_processing_service.get_sequence_metadata(pages)

        selected_length = getattr(
            self.sequence_card_tab.nav_sidebar, "selected_length", 0
        )
        selected_levels = None

        if (
            hasattr(self.sequence_card_tab.nav_sidebar, "level_filter")
            and self.sequence_card_tab.nav_sidebar.level_filter
        ):
            selected_levels = (
                self.sequence_card_tab.nav_sidebar.level_filter.get_selected_levels()
            )

        export_subdir = self.ui_manager.create_export_subdirectory(
            export_dir,
            selected_length=selected_length,
            selected_levels=selected_levels,
            sequence_count=metadata["total_sequences"],
        )

        self.logger.info(f"Export directory prepared: {export_subdir}")
        return export_subdir

    def _process_pages(self, pages: List[QWidget], export_subdir: str) -> bool:
        current_image_index = 0

        for i, page in enumerate(pages):
            if self.progress_service.is_cancelled():
                self.logger.info("Export cancelled by user")
                return False

            try:
                success = self._process_single_page(page, i, export_subdir)
                if not success:
                    self.logger.warning(f"Failed to process page {i+1}")
                    continue

                page_image_count = self.page_processing_service.count_page_images(page)
                current_image_index += page_image_count

                self.progress_service.update_progress(
                    current_image_index,
                    self.page_processing_service.count_total_images(pages),
                    f"Processed page {i+1} of {len(pages)} ({page_image_count} images)",
                )

            except Exception as e:
                self.logger.error(f"Error processing page {i+1}: {e}")
                continue

        return True

    def _process_single_page(
        self, page: QWidget, page_index: int, export_subdir: str
    ) -> bool:
        sequence_items = self.page_processing_service.extract_page_data(page)
        if not sequence_items:
            self.logger.warning(f"No sequence items found for page {page_index + 1}")
            return False

        filename = f"sequence_card_page_{page_index + 1:03d}.png"
        filepath = os.path.join(export_subdir, filename)

        cache_key = self.cache_service.generate_cache_key(page, self.config)

        if self.cache_service.copy_from_cache(cache_key, filepath):
            self.logger.info(f"Used cached version for page {page_index + 1}")
            return True

        success = self.page_renderer.render_page_to_image(page, filepath)
        if success:
            metadata = {
                "export_filepath": filepath,
                "page_id": id(page),
                "page_index": page_index,
            }
            self.cache_service.cache_page(cache_key, filepath, metadata)
            self.logger.info(f"Rendered and cached page {page_index + 1}")
            return True

        return False

    def _handle_export_completion(self, export_subdir: str, page_count: int):
        self.ui_manager.show_export_complete_message(export_subdir, page_count)
        try:
            os.startfile(os.path.normpath(os.path.dirname(export_subdir)))
        except Exception as e:
            self.logger.error(f"Error opening export directory: {e}")

    def clear_cache(self) -> int:
        cache_size = self.cache_service.clear_cache()
        if cache_size > 0:
            self.ui_manager.show_info_message(
                "Cache Refreshed",
                f"Successfully cleared {cache_size} cached pages.\nNext export will regenerate all page images.",
            )
        else:
            self.ui_manager.show_info_message(
                "Cache Refreshed",
                "Cache was already empty.\nNext export will generate fresh page images.",
            )
        return cache_size

    def get_export_statistics(self) -> Dict[str, Any]:
        pages = self._get_pages_to_export()
        if not pages:
            return {"error": "No pages available for export"}

        metadata = self.page_processing_service.get_sequence_metadata(pages)
        cache_stats = self.cache_service.get_cache_stats()

        return {
            "pages": metadata,
            "cache": cache_stats,
            "config": {
                "export_format": self.config.get_export_setting("format", "PNG"),
                "quality": self.config.get_export_setting("quality", 100),
                "page_dimensions": {
                    "width": self.config.get_print_setting("page_width_pixels", 5100),
                    "height": self.config.get_print_setting("page_height_pixels", 6600),
                },
            },
        }
