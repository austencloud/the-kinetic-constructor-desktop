# src/main_window/main_widget/sequence_card_tab/components/display/sequence_display_manager.py
from dataclasses import dataclass
import os
import logging
from typing import Dict, List, Any, Optional, TYPE_CHECKING
from PyQt6.QtWidgets import QWidget, QApplication, QGridLayout
from PyQt6.QtCore import Qt, QTimer

from utils.path_helpers import get_sequence_card_image_exporter_path
from ..pages.printable_layout import PaperSize, PaperOrientation

from .image_processor import (
    ImageProcessor,
    DEFAULT_IMAGE_CACHE_SIZE,
)  # Import DEFAULT_IMAGE_CACHE_SIZE
from .sequence_loader import SequenceLoader
from .page_renderer import PageRenderer
from .layout_calculator import LayoutCalculator
from .scroll_view import ScrollView

# Assuming DisplayConfig is in display_config.py as shown in the problem description


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

        # Add cancellation mechanism
        self.is_loading = False
        self.cancel_requested = False
        self.current_loading_length = None

        # Add cache statistics tracking
        self.cache_hits = 0
        self.cache_misses = 0
        self.using_cached_content = False

        self.layout_calculator = LayoutCalculator(
            sequence_card_tab, self.page_factory, self.config
        )

        # Initialize ImageProcessor with a specific cache size
        # DEFAULT_IMAGE_CACHE_SIZE can be made configurable if needed
        self.image_processor = ImageProcessor(
            self.page_factory,
            columns_per_row=self.config.columns_per_row,
            cache_size=DEFAULT_IMAGE_CACHE_SIZE,
        )

        # Pass the generated sequence store to the sequence loader
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

        self.page_renderer = PageRenderer(
            self.page_factory, self.layout_calculator, self.config, self.preview_grid
        )

        self.pages: List[QWidget] = []
        self.current_page_index = -1
        self.current_position = 0

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
        self.sequence_card_tab.setCursor(Qt.CursorShape.WaitCursor)
        logging.debug(
            f"Refreshing layout with columns_per_row={self.config.columns_per_row}, length={current_length}"
        )

        try:
            self._clear_existing_pages()  # Clears QWidget pages from UI and internal list

            # DO NOT CLEAR THE IMAGE CACHE: self.image_processor.clear_cache() # REMOVED

            self.scroll_view._clear_scroll_layout()  # Clears the main scroll view layout

            try:
                self.preview_grid = self.scroll_view.create_multi_column_layout()
                self.page_renderer.set_preview_grid(self.preview_grid)
            except Exception as e:
                logging.error(f"Error creating preview grid in refresh_layout: {e}")
                self.preview_grid = QGridLayout()  # Fallback
                self.page_renderer.set_preview_grid(self.preview_grid)

            self.layout_calculator.set_optimal_grid_dimensions(current_length)

            # Re-display sequences which will use the (persistent) image cache
            self.display_sequences(current_length)
        except Exception as e:
            logging.error(f"Error in refresh_layout: {e}", exc_info=True)
        finally:
            self.sequence_card_tab.setCursor(Qt.CursorShape.ArrowCursor)

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
        # Cancel any in-progress loading operations
        if self.is_loading:
            logging.debug(
                f"Cancelling previous loading operation for length {self.current_loading_length}"
            )
            self.cancel_loading()

        # Set loading state
        self.is_loading = True
        self.cancel_requested = False

        # Store the current loading parameters
        if selected_length is None:
            selected_length = self.nav_sidebar.selected_length
        self.current_loading_length = selected_length

        # Get selected levels from sidebar if available, otherwise default to all levels
        if selected_levels is None:
            if (
                hasattr(self.nav_sidebar, "level_filter")
                and self.nav_sidebar.level_filter
            ):
                selected_levels = self.nav_sidebar.level_filter.get_selected_levels()
            else:
                selected_levels = [1, 2, 3]  # Default to all levels

        # Reset cache statistics for this loading operation
        self.cache_hits = 0
        self.cache_misses = 0
        self.using_cached_content = False

        # STEP 1: Clear existing QWidget pages and their rendered content
        self._clear_existing_pages()

        # DO NOT CLEAR THE IMAGE CACHE: self.image_processor.clear_cache() # REMOVED

        # STEP 2: Clear the scroll area's main layout
        self.scroll_view._clear_scroll_layout()

        # Update UI to show loading state
        self.sequence_card_tab.setCursor(Qt.CursorShape.WaitCursor)
        length_text = f"{selected_length}-step" if selected_length > 0 else "all"

        # Create level description
        if selected_levels and len(selected_levels) < 3:
            level_names = {1: "Basic", 2: "Intermediate", 3: "Advanced"}
            level_text = ", ".join(
                [level_names[lvl] for lvl in sorted(selected_levels)]
            )
            filter_text = f"{length_text} sequences (Levels: {level_text})"
        else:
            filter_text = f"{length_text} sequences"

        self.sequence_card_tab.header.description_label.setText(
            f"Loading {filter_text}..."
        )

        # Show progress bar and reset it
        if hasattr(self.sequence_card_tab.header, "progress_bar"):
            self.sequence_card_tab.header.progress_bar.setValue(0)
            self.sequence_card_tab.header.progress_bar.show()
            # Make sure the progress container is visible too
            if hasattr(self.sequence_card_tab.header, "progress_container"):
                self.sequence_card_tab.header.progress_container.setVisible(True)
            QApplication.processEvents()  # Ensure UI updates are visible

        try:
            images_path = get_sequence_card_image_exporter_path()

            # Use the enhanced filtering method that combines length and level filtering
            filtered_sequences = self.sequence_loader.get_filtered_sequences(
                images_path,
                length_filter=(
                    selected_length if selected_length and selected_length > 0 else None
                ),
                level_filters=selected_levels if selected_levels else None,
            )

            total_sequences = len(filtered_sequences)
            if total_sequences == 0:
                self.sequence_card_tab.header.description_label.setText(
                    f"No {filter_text} found"
                )
                # Hide progress bar and container when no sequences found
                if hasattr(self.sequence_card_tab.header, "progress_bar"):
                    self.sequence_card_tab.header.progress_bar.hide()
                    if hasattr(self.sequence_card_tab.header, "progress_container"):
                        self.sequence_card_tab.header.progress_container.setVisible(
                            False
                        )
                return

            # Set up progress bar with total count
            if hasattr(self.sequence_card_tab.header, "progress_bar"):
                self.sequence_card_tab.header.progress_bar.setRange(0, total_sequences)
                self.sequence_card_tab.header.progress_bar.setValue(0)

            self.layout_calculator.set_optimal_grid_dimensions(selected_length)

            try:
                self.preview_grid = self.scroll_view.create_multi_column_layout()
                self.page_renderer.set_preview_grid(self.preview_grid)
            except Exception as e:
                logging.error(f"Error creating preview grid in display_sequences: {e}")
                self.preview_grid = QGridLayout()  # Fallback
                self.page_renderer.set_preview_grid(self.preview_grid)

            self._ensure_first_page_exists()  # Creates the first QWidget page

            # Check if we can use cached content
            cache_check_result = self._check_cache_availability(filtered_sequences)
            self.using_cached_content = (
                cache_check_result > 0.8
            )  # If >80% of images are cached

            # Update UI to show if we're using cached content
            if self.using_cached_content:
                self.sequence_card_tab.header.description_label.setText(
                    f"Loading {filter_text} from cache..."
                )

            # First, try to load all images instantly from cache
            page_scale_factor = self._get_current_page_scale_factor()
            image_paths = [
                seq.get("path", "")
                for seq in filtered_sequences
                if seq and seq.get("path", "") and os.path.exists(seq.get("path", ""))
            ]

            # Get cached images in batch for instant display
            cached_images = self.image_processor.load_images_batch_if_cached(
                image_paths, page_scale_factor, self.current_page_index
            )

            # Display cached images instantly
            cached_count = 0
            remaining_sequences = []

            for sequence_data in filtered_sequences:
                if self.cancel_requested:
                    logging.debug("Loading cancelled by user")
                    break

                if sequence_data:
                    image_path = sequence_data.get("path", "")
                    if image_path in cached_images:
                        # Instant display from cache
                        try:
                            pixmap = cached_images[image_path]
                            if not pixmap.isNull():
                                label = self.page_renderer.create_image_label(
                                    sequence_data, pixmap
                                )
                                self._add_image_to_page(label)
                                cached_count += 1
                                self.cache_hits += 1
                        except Exception as e:
                            logging.error(
                                f"Error displaying cached image {image_path}: {e}"
                            )
                            remaining_sequences.append(sequence_data)
                    else:
                        # Need to load this image
                        remaining_sequences.append(sequence_data)

            # Log cache performance
            if cached_count > 0:
                logging.info(f"Instantly displayed {cached_count} cached images")
                # Update UI to reflect instant loading
                if cached_count == len(filtered_sequences):
                    self.sequence_card_tab.header.description_label.setText(
                        f"Showing {len(filtered_sequences)} {filter_text} (loaded from cache)"
                    )

            # Process remaining images that need loading
            for i, sequence_data in enumerate(remaining_sequences):
                # Check for cancellation request
                if self.cancel_requested:
                    logging.debug(
                        f"Loading cancelled at item {i}/{len(remaining_sequences)}"
                    )
                    break

                if i % 10 == 0:  # Periodic UI update
                    # Update progress bar
                    if hasattr(self.sequence_card_tab.header, "progress_bar"):
                        self.sequence_card_tab.header.progress_bar.setValue(
                            cached_count + i + 1
                        )

                    # Calculate cache hit ratio for debugging
                    if self.cache_hits + self.cache_misses > 0:
                        cache_ratio = self.cache_hits / (
                            self.cache_hits + self.cache_misses
                        )
                        logging.debug(f"Cache hit ratio: {cache_ratio:.2f}")

                    self.sequence_card_tab.header.description_label.setText(
                        f"Loading {filter_text}... ({cached_count + i + 1}/{total_sequences})"
                    )

                try:
                    image_path = sequence_data.get("path", "")
                    if image_path and os.path.exists(image_path):
                        # ImageProcessorCoordinator will use its multi-layer cache here
                        pixmap = (
                            self.image_processor.load_image_with_consistent_scaling(
                                image_path, page_scale_factor, self.current_page_index
                            )
                        )

                        # For now, assume cache miss for non-cached images
                        # The coordinator handles cache statistics internally
                        self.cache_misses += 1

                        if not pixmap.isNull():
                            label = self.page_renderer.create_image_label(
                                sequence_data, pixmap
                            )
                            self._add_image_to_page(label)
                        QApplication.processEvents()
                except Exception as e:
                    logging.error(
                        f"Error processing image {sequence_data.get('path', 'unknown')}: {e}"
                    )
                # Process events less frequently to avoid UI state inconsistencies
                if (
                    i % 100 == 0 and i > 0
                ):  # Less frequent UI responsiveness check for long lists
                    QApplication.processEvents()

            self.sequence_card_tab.header.description_label.setText(
                f"Showing {len(filtered_sequences)} {filter_text} across {len(self.pages)} pages in {self.config.columns_per_row} columns"
            )

        except Exception as e:
            logging.error(f"Error displaying sequences: {e}", exc_info=True)
            self.sequence_card_tab.header.description_label.setText(f"Error: {str(e)}")
        finally:
            # Reset loading state
            self.is_loading = False
            self.cancel_requested = False
            self.sequence_card_tab.setCursor(Qt.CursorShape.ArrowCursor)

            # Hide progress bar and its container
            if hasattr(self.sequence_card_tab.header, "progress_bar"):
                self.sequence_card_tab.header.progress_bar.hide()
                # Also hide the container to ensure consistent layout
                if hasattr(self.sequence_card_tab.header, "progress_container"):
                    self.sequence_card_tab.header.progress_container.setVisible(False)

    def _check_cache_availability(self, sequences: List[Dict[str, Any]]) -> float:
        """
        Check what percentage of the sequences are available in the cache.

        Args:
            sequences: List of sequence data dictionaries

        Returns:
            float: Ratio of cached images (0.0 to 1.0)
        """
        if not sequences:
            return 0.0

        cached_count = 0
        total_count = 0

        # Sample up to 20 images to estimate cache availability
        sample_size = min(20, len(sequences))
        sample_step = max(1, len(sequences) // sample_size)

        for i in range(0, len(sequences), sample_step):
            if i >= len(sequences):
                break

            sequence_data = sequences[i]
            image_path = sequence_data.get("path", "")

            if image_path and os.path.exists(image_path):
                total_count += 1

                # Check if the raw image is in the cache
                cached_image = (
                    self.image_processor.coordinator.cache_manager.get_raw_image(
                        image_path
                    )
                )
                if cached_image is not None:
                    cached_count += 1

        if total_count == 0:
            return 0.0

        return cached_count / total_count

    def _ensure_first_page_exists(self) -> None:
        """
        Ensures that the first page exists and has a proper layout.
        This is called at the beginning of display_sequences.
        """
        if self.current_page_index == -1:
            logging.debug("Creating first page...")
            new_page = self.page_renderer.create_new_page()

            # Double-check that the page has a layout
            if new_page.layout() is None:
                logging.warning(
                    "First page created without layout. Adding QGridLayout."
                )
                grid_layout = QGridLayout(new_page)
                grid_layout.setContentsMargins(10, 10, 10, 10)
                grid_layout.setSpacing(5)

            self.pages.append(new_page)
            self.current_page_index = 0
            self.current_position = 0
            logging.debug(f"Created first page with layout: {new_page.layout()}")

    def _get_current_page_scale_factor(self) -> float:
        if self.current_page_index >= 0 and self.current_page_index < len(self.pages):
            current_page = self.pages[self.current_page_index]
            scale_factor = current_page.property("scale_factor")
            if scale_factor is not None:
                return float(scale_factor)
        return 1.0  # Fallback

    def cancel_loading(self) -> None:
        """
        Cancel any in-progress loading operations.
        This method is called when the user selects a different sequence length.
        """
        if self.is_loading:
            logging.debug("Cancelling in-progress loading operation")
            self.cancel_requested = True

            # Wait briefly for any ongoing operations to notice the cancellation
            QTimer.singleShot(50, self._reset_cancellation_state)

    def _reset_cancellation_state(self) -> None:
        """Reset the cancellation state after cancellation is complete."""
        self.cancel_requested = False
        self.is_loading = False
        logging.debug("Cancellation state reset")

    def _clear_existing_pages(self) -> None:
        """
        Clears all existing pages from the UI and internal lists.
        This resets the state for a fresh display.
        """
        logging.debug(f"Clearing {len(self.pages)} existing pages")

        # First, clear pages from the UI
        self.scroll_view.clear_existing_pages(self.pages)  # Clears from UI

        # Clear internal lists
        self.pages = []  # Clears internal list of QWidget pages
        self.page_renderer.clear_pages()  # Resets PageRenderer's internal page list

        # Reset state
        self.current_page_index = -1
        self.current_position = 0

        logging.debug("All pages cleared and state reset")

    def _add_image_to_page(self, label: QWidget) -> None:
        # Check if current page is full and create a new one if needed
        if self.page_renderer.is_page_full(self.current_position):
            logging.debug(
                f"Current page {self.current_page_index} is full at position {self.current_position}. Creating new page."
            )
            new_page = self.page_renderer.create_new_page()

            # Ensure the new page has a layout
            if new_page.layout() is None:
                logging.warning(f"New page created without layout. Adding QGridLayout.")
                grid_layout = QGridLayout(new_page)
                grid_layout.setContentsMargins(10, 10, 10, 10)
                grid_layout.setSpacing(5)

            self.pages.append(new_page)
            self.current_page_index = len(self.pages) - 1
            self.current_position = 0
            logging.debug(
                f"Created new page {self.current_page_index} with layout: {new_page.layout()}"
            )

        # Validate page index
        if self.current_page_index < 0 or self.current_page_index >= len(self.pages):
            logging.error(
                f"Invalid page index {self.current_page_index}, pages length: {len(self.pages)}"
            )
            return

        # Get the current page and its layout
        page = self.pages[self.current_page_index]
        grid_layout_on_page = (
            page.layout()
        )  # This is the QGridLayout on the QWidget page

        # If layout is missing, create one
        if grid_layout_on_page is None:
            logging.warning(
                f"Page {self.current_page_index} has no layout. Adding QGridLayout."
            )
            grid_layout_on_page = QGridLayout(page)
            grid_layout_on_page.setContentsMargins(10, 10, 10, 10)
            grid_layout_on_page.setSpacing(5)

        # Get grid positions and add the widget
        positions = (
            self.page_factory.get_grid_positions()
        )  # Positions within a page's internal grid
        if self.current_position < len(positions):
            row, col = positions[self.current_position]
            try:
                grid_layout_on_page.addWidget(
                    label, row, col, Qt.AlignmentFlag.AlignCenter
                )
                self.current_position += 1
                logging.debug(
                    f"Added widget to page {self.current_page_index} at position ({row}, {col})"
                )
            except Exception as e:
                logging.error(
                    f"Error adding widget to page {self.current_page_index}: {e}"
                )
        else:
            logging.error(
                f"Invalid position {self.current_position} for page's internal grid, max positions: {len(positions)}"
            )
