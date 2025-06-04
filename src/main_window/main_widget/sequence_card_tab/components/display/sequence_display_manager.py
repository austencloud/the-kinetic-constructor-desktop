# src/main_window/main_widget/sequence_card_tab/components/display/sequence_display_manager.py
from dataclasses import dataclass
import logging
from typing import Dict, List, Any, Optional, TYPE_CHECKING
from PyQt6.QtWidgets import QWidget, QGridLayout

from ..pages.printable_layout import PaperSize, PaperOrientation
from .image_processor import ImageProcessor, DEFAULT_IMAGE_CACHE_SIZE
from .sequence_loader import SequenceLoader
from .page_renderer import PageRenderer
from .layout_calculator import LayoutCalculator
from .scroll_view import ScrollView

from .managers.loading_state_manager import LoadingStateManager
from .managers.ui_state_manager import UIStateManager
from .managers.cache_stats_manager import CacheStatsManager
from .managers.page_manager import PageManager
from .managers.sequence_processor import SequenceProcessor


@dataclass
class DisplayConfig:
    columns_per_row: int = 2
    page_spacing: int = 20
    paper_size: PaperSize = PaperSize.LETTER
    paper_orientation: PaperOrientation = PaperOrientation.PORTRAIT


if TYPE_CHECKING:
    from ...tab import SequenceCardTab


class SequenceDisplayManager:
    """
    Main orchestrator for displaying sequence cards.
    Manages image processing, sequence loading, page rendering, layout calculations, and view updates.
    """

    def __init__(self, sequence_card_tab: "SequenceCardTab"):
        self.sequence_card_tab = sequence_card_tab
        self.nav_sidebar = sequence_card_tab.nav_sidebar
        self.page_factory = sequence_card_tab.page_factory
        self.config = DisplayConfig()
        self.logger = logging.getLogger(__name__)

        # Initialize component managers
        self.loading_manager = LoadingStateManager()
        self.ui_manager = UIStateManager(sequence_card_tab)

        self.layout_calculator = LayoutCalculator(
            sequence_card_tab, self.page_factory, self.config
        )
        self.image_processor = ImageProcessor(
            self.page_factory,
            columns_per_row=self.config.columns_per_row,
            cache_size=DEFAULT_IMAGE_CACHE_SIZE,
        )

        generated_sequence_store = getattr(
            sequence_card_tab, "generated_sequence_store", None
        )
        self.sequence_loader = SequenceLoader(generated_sequence_store)
        self.scroll_view = ScrollView(sequence_card_tab, self.config)

        try:
            self.preview_grid = self.scroll_view.create_multi_column_layout()
            logging.debug("Initial preview grid created successfully")
        except Exception as e:
            logging.debug(f"Error creating initial preview grid: {e}")
            self.preview_grid = QGridLayout()  # Placeholder

        # Use original page renderer for stable image display
        self.page_renderer = PageRenderer(
            self.page_factory, self.layout_calculator, self.config, self.preview_grid
        )

        self.cache_manager = CacheStatsManager(self.image_processor)
        self.page_manager = PageManager(
            sequence_card_tab, self.page_renderer, self.scroll_view
        )
        self.sequence_processor = SequenceProcessor(
            self.sequence_loader,
            self.image_processor,
            self.page_renderer,
            self.cache_manager,
            self.page_manager,
            self.ui_manager,
        )

    @property
    def columns_per_row(self) -> int:
        return self.config.columns_per_row

    @columns_per_row.setter
    def columns_per_row(self, value: int) -> None:
        if 1 <= value <= 6 and value != self.config.columns_per_row:
            self.config.columns_per_row = value
            self.image_processor.set_columns_per_row(value)  # Update image processor
            if self.pages:  # Refresh layout if pages are currently displayed
                self.refresh_layout()

    @property
    def pages(self) -> List[QWidget]:
        return self.page_manager.pages

    @property
    def is_loading(self) -> bool:
        return self.loading_manager.is_currently_loading()

    def set_paper_size(self, paper_size: PaperSize) -> None:
        self.config.paper_size = paper_size
        self.page_factory.set_paper_size(paper_size)
        if self.pages:
            self.refresh_layout()  # Refresh if visual change occurs

    def set_orientation(self, orientation: PaperOrientation) -> None:
        self.config.paper_orientation = orientation
        self.page_factory.set_orientation(orientation)
        if self.pages:
            self.refresh_layout()  # Refresh if visual change occurs

    def refresh_layout(self) -> None:
        """
        Refresh the layout with current settings.
        This method clears and recreates UI pages and their contents.
        Image cache is NOT cleared here; it's managed by LRU in ImageProcessor.
        """
        current_length = self.nav_sidebar.selected_length
        self.ui_manager.set_loading_cursor()
        self.logger.debug(
            f"Refreshing layout with columns_per_row={self.config.columns_per_row}, length={current_length}"
        )

        try:
            self.page_manager.clear_existing_pages()  # Clears QWidget pages from UI and internal list
            self.scroll_view._clear_scroll_layout()  # Clears the main scroll view layout

            try:
                self.preview_grid = self.scroll_view.create_multi_column_layout()
                self.page_renderer.set_preview_grid(self.preview_grid)
            except Exception as e:
                self.logger.error(f"Error creating preview grid in refresh_layout: {e}")
                self.preview_grid = QGridLayout()  # Fallback
                self.page_renderer.set_preview_grid(self.preview_grid)

            self.layout_calculator.set_optimal_grid_dimensions(current_length)

            # Re-display sequences which will use the (persistent) image cache
            self.display_sequences(current_length)
        except Exception as e:
            self.logger.error(f"Error in refresh_layout: {e}", exc_info=True)
        finally:
            self.ui_manager.set_normal_cursor()

    def display_sequences(
        self,
        selected_length: Optional[int] = None,
        selected_levels: Optional[List[int]] = None,
    ) -> None:
        """
        Display sequence card images. Clears existing UI pages and re-populates.
        Relies on ImageProcessor's LRU cache for image data.

        Args:
            selected_length: Optional length filter (None = use sidebar selection)
            selected_levels: Optional level filters (None = use sidebar selection or all levels)
        """
        if not self.loading_manager.start_loading(selected_length):
            return

        if selected_length is None:
            selected_length = self.nav_sidebar.selected_length

        if selected_levels is None:
            if (
                hasattr(self.nav_sidebar, "level_filter")
                and self.nav_sidebar.level_filter
            ):
                selected_levels = self.nav_sidebar.level_filter.get_selected_levels()
            else:
                selected_levels = [1, 2, 3]  # Default to all levels

        self.cache_manager.reset_stats()
        self.page_manager.clear_existing_pages()
        self.scroll_view._clear_scroll_layout()

        self.ui_manager.set_loading_cursor()
        filter_text = self.ui_manager.format_filter_description(
            selected_length or 0, selected_levels
        )
        self.ui_manager.update_header_text(f"Loading {filter_text}...")
        self.ui_manager.show_progress_bar()

        try:
            self.layout_calculator.set_optimal_grid_dimensions(selected_length)

            try:
                self.preview_grid = self.scroll_view.create_multi_column_layout()
                self.page_renderer.set_preview_grid(self.preview_grid)
            except Exception as e:
                self.logger.error(
                    f"Error creating preview grid in display_sequences: {e}"
                )
                self.preview_grid = QGridLayout()  # Fallback
                self.page_renderer.set_preview_grid(self.preview_grid)

            # Get current mode for proper page isolation
            current_mode = getattr(self.sequence_card_tab, "mode_manager", None)
            mode = current_mode.current_mode if current_mode else None

            success = self.sequence_processor.process_sequences(
                selected_length, selected_levels, mode
            )

        except Exception as e:
            self.logger.error(f"Error displaying sequences: {e}", exc_info=True)
            self.ui_manager.update_header_text(f"Error: {str(e)}")
        finally:
            self.loading_manager.stop_loading()
            self.ui_manager.set_normal_cursor()
            self.ui_manager.hide_progress_bar()

    def cancel_loading(self) -> None:
        self.loading_manager.cancel_loading()
