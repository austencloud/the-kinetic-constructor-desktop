import logging
import os
from typing import Dict, List, Any, Optional, TYPE_CHECKING
from PyQt6.QtWidgets import QApplication

from utils.path_helpers import get_sequence_card_image_exporter_path
from ....core.mode_manager import SequenceCardMode

if TYPE_CHECKING:
    from ..sequence_loader import SequenceLoader
    from ..image_processor import ImageProcessor
    from ..page_renderer import PageRenderer
    from .cache_stats_manager import CacheStatsManager
    from .page_manager import PageManager
    from .ui_state_manager import UIStateManager


class SequenceProcessor:
    def __init__(
        self,
        sequence_loader: "SequenceLoader",
        image_processor: "ImageProcessor",
        page_renderer: "PageRenderer",
        cache_manager: "CacheStatsManager",
        page_manager: "PageManager",
        ui_manager: "UIStateManager",
    ):
        self.sequence_loader = sequence_loader
        self.image_processor = image_processor
        self.page_renderer = page_renderer
        self.cache_manager = cache_manager
        self.page_manager = page_manager
        self.ui_manager = ui_manager
        self.logger = logging.getLogger(__name__)

    def process_sequences(
        self,
        selected_length: Optional[int] = None,
        selected_levels: Optional[List[int]] = None,
        mode: Optional[SequenceCardMode] = None,
    ) -> bool:
        try:
            images_path = get_sequence_card_image_exporter_path()

            # Load sequences based on the current mode for proper page isolation
            if mode == SequenceCardMode.GENERATION:
                # Generation mode: show only generated sequences
                filtered_sequences = self.sequence_loader.get_generated_sequences_only(
                    length_filter=(
                        selected_length
                        if selected_length and selected_length > 0
                        else None
                    ),
                    level_filters=selected_levels if selected_levels else None,
                )

            elif mode == SequenceCardMode.DICTIONARY:
                # Dictionary mode: show only dictionary sequences
                filtered_sequences = self.sequence_loader.get_dictionary_sequences_only(
                    images_path,
                    length_filter=(
                        selected_length
                        if selected_length and selected_length > 0
                        else None
                    ),
                    level_filters=selected_levels if selected_levels else None,
                )

            else:
                # Fallback: show all sequences (mixed mode)
                filtered_sequences = self.sequence_loader.get_filtered_sequences(
                    images_path,
                    length_filter=(
                        selected_length
                        if selected_length and selected_length > 0
                        else None
                    ),
                    level_filters=selected_levels if selected_levels else None,
                )

            total_sequences = len(filtered_sequences)
            if total_sequences == 0:
                filter_text = self.ui_manager.format_filter_description(
                    selected_length or 0, selected_levels or []
                )
                self.ui_manager.update_header_text(f"No {filter_text} found")
                self.ui_manager.hide_progress_bar()
                return False

            self.ui_manager.show_progress_bar(total_sequences)
            self.page_manager.ensure_first_page_exists()

            cache_ratio = self.cache_manager.check_cache_availability(
                filtered_sequences
            )

            if self.cache_manager.using_cached_content:
                filter_text = self.ui_manager.format_filter_description(
                    selected_length or 0, selected_levels or []
                )
                self.ui_manager.update_header_text(
                    f"Loading {filter_text} from cache..."
                )

            cached_count = self._process_cached_images(filtered_sequences)
            remaining_count = self._process_remaining_images(
                filtered_sequences, cached_count
            )

            self._finalize_processing(total_sequences, selected_length, selected_levels)
            return True

        except Exception as e:
            self.logger.error(f"Error processing sequences: {e}", exc_info=True)
            self.ui_manager.update_header_text(f"Error: {str(e)}")
            return False

    def _process_cached_images(self, filtered_sequences: List[Dict[str, Any]]) -> int:
        page_scale_factor = self.page_manager.get_current_page_scale_factor()
        image_paths = [
            seq.get("path", "")
            for seq in filtered_sequences
            if seq and seq.get("path", "") and os.path.exists(seq.get("path", ""))
        ]

        cached_images = self.image_processor.load_images_batch_if_cached(
            image_paths, page_scale_factor, self.page_manager.current_page_index
        )

        cached_count = 0
        for sequence_data in filtered_sequences:
            if sequence_data:
                image_path = sequence_data.get("path", "")
                if image_path in cached_images:
                    try:
                        pixmap = cached_images[image_path]
                        if not pixmap.isNull():
                            label = self.page_renderer.create_image_label(
                                sequence_data, pixmap
                            )
                            self.page_manager.add_widget_to_current_page(label)
                            cached_count += 1
                            self.cache_manager.record_cache_hit()
                    except Exception as e:
                        self.logger.error(
                            f"Error displaying cached image {image_path}: {e}"
                        )

        self.cache_manager.log_cache_performance(cached_count)
        return cached_count

    def _process_remaining_images(
        self, filtered_sequences: List[Dict[str, Any]], cached_count: int
    ) -> int:
        page_scale_factor = self.page_manager.get_current_page_scale_factor()
        remaining_count = 0

        for i, sequence_data in enumerate(filtered_sequences):
            if i % 10 == 0:
                self.ui_manager.update_progress(cached_count + i + 1)

                if self.cache_manager.cache_hits + self.cache_manager.cache_misses > 0:
                    cache_ratio = self.cache_manager.get_cache_hit_ratio()
                    self.logger.debug(f"Cache hit ratio: {cache_ratio:.2f}")

            try:
                image_path = sequence_data.get("path", "")
                if image_path and os.path.exists(image_path):
                    pixmap = self.image_processor.load_image_with_consistent_scaling(
                        image_path,
                        page_scale_factor,
                        self.page_manager.current_page_index,
                    )

                    self.cache_manager.record_cache_miss()

                    if not pixmap.isNull():
                        label = self.page_renderer.create_image_label(
                            sequence_data, pixmap
                        )
                        self.page_manager.add_widget_to_current_page(label)
                        remaining_count += 1

                    QApplication.processEvents()
            except Exception as e:
                self.logger.error(
                    f"Error processing image {sequence_data.get('path', 'unknown')}: {e}"
                )

            if i % 100 == 0 and i > 0:
                QApplication.processEvents()

        return remaining_count

    def _finalize_processing(
        self,
        total_sequences: int,
        selected_length: Optional[int],
        selected_levels: Optional[List[int]],
    ):
        filter_text = self.ui_manager.format_filter_description(
            selected_length or 0, selected_levels or []
        )

        page_count = self.page_manager.get_page_count()
        columns = 2  # This should come from config, but keeping it simple for now

        self.ui_manager.update_header_text(
            f"Showing {total_sequences} {filter_text} across {page_count} pages in {columns} columns"
        )
