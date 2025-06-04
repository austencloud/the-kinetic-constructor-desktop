# src/main_window/main_widget/sequence_card_tab/export/page_exporter.py
import os
import time
import logging
from typing import TYPE_CHECKING, List, Optional, Dict, Any
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt

from .export_config import ExportConfig
from .export_ui_manager import ExportUIManager
from .page_image_data_extractor import PageImageDataExtractor
from .export_grid_calculator import ExportGridCalculator
from .export_page_renderer import ExportPageRenderer

if TYPE_CHECKING:
    from ..tab import SequenceCardTab


class SequenceCardPageExporter:
    """
    Exports sequence card pages as high-quality images.

    This class orchestrates the export process by coordinating the following components:
    1. ExportConfig: Manages print and export settings
    2. ExportUIManager: Handles file dialogs and progress updates
    3. PageImageDataExtractor: Extracts image paths and metadata from UI widgets
    4. ExportGridCalculator: Calculates optimal grid layouts
    5. ExportPageRenderer: Renders high-quality images
    """

    def __init__(self, sequence_card_tab: "SequenceCardTab"):
        self.sequence_card_tab = sequence_card_tab
        self.logger = logging.getLogger(__name__)

        # Initialize components
        self.config = ExportConfig(sequence_card_tab)
        self.ui_manager = ExportUIManager(sequence_card_tab)
        self.data_extractor = PageImageDataExtractor(sequence_card_tab)
        self.grid_calculator = ExportGridCalculator(self.config, sequence_card_tab)
        self.page_renderer = ExportPageRenderer(self.config, self.grid_calculator)

    def export_all_pages_as_images(self):
        """
        Export all currently displayed sequence card pages as high-quality print-ready images.

        This method:
        1. Prompts the user for a directory to save the images
        2. Creates high-quality images using original source files
        3. Saves the images with appropriate naming
        4. Shows progress during export
        """
        self.logger.info("Starting sequence card page export")

        # Get the pages to export - check both the tab's pages and the printable displayer's pages
        pages = self._get_pages_to_export()
        if not pages:
            self.ui_manager.show_warning_message(
                "No Pages to Export",
                "There are no sequence card pages to export. Please select a sequence length first.",
            )
            return

        self.logger.info(f"Found {len(pages)} pages to export")

        # Get the export directory
        export_dir = self.ui_manager.get_export_directory()
        if not export_dir:
            return  # User cancelled

        # Export the pages
        self._export_pages(pages, export_dir)

    def export_current_page_as_image(self):
        """
        Export only the currently visible page as a high-quality print-ready image.

        This method:
        1. Gets the currently visible page
        2. Prompts the user for a directory to save the image
        3. Creates a high-quality image using original source files
        4. Saves the image with appropriate naming
        """
        self.logger.info("Starting current page export")

        # Get the current page
        current_page = self._get_current_page()
        if not current_page:
            self.ui_manager.show_warning_message(
                "No Current Page",
                "There is no current page to export. Please ensure sequences are loaded.",
            )
            return

        self.logger.info("Found current page to export")

        # Get the export directory
        export_dir = self.ui_manager.get_export_directory()
        if not export_dir:
            return  # User cancelled

        # Export just the current page
        self._export_pages([current_page], export_dir)

    def _get_current_page(self) -> QWidget:
        """
        Get the currently visible page from the sequence card tab.

        Returns:
            QWidget: The current page widget, or None if no page is visible
        """
        # Try to get the current page from the printable displayer
        if hasattr(self.sequence_card_tab, "printable_displayer"):
            if hasattr(self.sequence_card_tab.printable_displayer, "current_page"):
                current_page = self.sequence_card_tab.printable_displayer.current_page
                if current_page:
                    self.logger.info("Using current page from PrintableDisplayer")
                    return current_page

            # Try to get from the manager
            if hasattr(self.sequence_card_tab.printable_displayer, "manager"):
                manager = self.sequence_card_tab.printable_displayer.manager
                if hasattr(manager, "current_page") and manager.current_page:
                    self.logger.info("Using current page from SequenceDisplayManager")
                    return manager.current_page

                # If no current_page property, try to get the first page
                if hasattr(manager, "pages") and manager.pages:
                    self.logger.info(
                        "Using first page from SequenceDisplayManager as current"
                    )
                    return manager.pages[0]

        # Fallback: try to get the first page from the tab's pages
        if self.sequence_card_tab.pages:
            self.logger.info("Using first page from tab as current")
            return self.sequence_card_tab.pages[0]

        return None

    def _get_pages_to_export(self) -> List[QWidget]:
        """
        Get the pages to export from the sequence card tab.

        Returns:
            List[QWidget]: List of page widgets to export
        """
        # First try to get pages directly from the tab
        pages = self.sequence_card_tab.pages

        # If the tab's pages list is empty, try to get pages from the printable displayer
        if not pages and hasattr(self.sequence_card_tab, "printable_displayer"):
            if hasattr(self.sequence_card_tab.printable_displayer, "pages"):
                # Get pages directly from the PrintableDisplayer
                pages = self.sequence_card_tab.printable_displayer.pages
                self.logger.info("Using pages from PrintableDisplayer")
            elif hasattr(self.sequence_card_tab.printable_displayer, "manager"):
                # Get pages from the SequenceDisplayManager
                pages = self.sequence_card_tab.printable_displayer.manager.pages
                self.logger.info("Using pages from SequenceDisplayManager")

        return pages

    def _export_pages(self, pages: List[QWidget], export_dir: str):
        """
        Export the sequence card pages as high-quality print-ready images.

        Args:
            pages: List of page widgets to export
            export_dir: Directory to save the exported images
        """
        # Get the selected length
        selected_length = getattr(
            self.sequence_card_tab.nav_sidebar, "selected_length", 0
        )

        # Sync the export config with the UI layout to ensure consistency
        self.logger.info("Synchronizing export configuration with UI layout")
        sync_success = self.config.sync_with_ui_layout()
        if sync_success:
            self.logger.info(
                "Successfully synchronized export configuration with UI layout"
            )
        else:
            self.logger.warning(
                "Failed to synchronize export configuration with UI layout, using default settings"
            )

        # Create a subdirectory for this export
        export_subdir = self.ui_manager.create_export_subdirectory(
            export_dir, selected_length
        )

        # Create a progress dialog
        # self.ui_manager.cancel_requested is reset to False inside create_progress_dialog
        progress = self.ui_manager.create_progress_dialog(len(pages))

        was_cancelled_by_user = False  # Local flag to track explicit cancellation

        # Process each page
        for i, page in enumerate(pages):
            if self.ui_manager.cancel_requested:  # Check the flag from UIManager
                self.logger.info("Export cancelled by user during loop.")
                was_cancelled_by_user = True  # Set local flag
                break

            # Update progress
            self.ui_manager.update_progress(
                i, f"Exporting page {i+1} of {len(pages)}..."
            )

            try:
                # Export the page
                filename = f"sequence_card_page_{i+1:03d}.png"
                filepath = os.path.join(export_subdir, filename)

                self.logger.info(f"Exporting page {i+1} to: {filepath}")

                # Extract sequence data from the page
                sequence_items = self.data_extractor.extract_sequence_data_from_page(
                    page
                )

                # Store the sequence items on the page for the renderer to use
                page.setProperty("sequence_items", sequence_items)

                # Render the page as a high-quality print-ready image
                self.page_renderer.render_page_to_image(page, filepath)

                # Add a small delay to keep UI responsive
                time.sleep(
                    0.1
                )  # Consider if this is truly necessary or if QApplication.processEvents() is enough
                QApplication.processEvents()

            except Exception as e:
                self.logger.error(f"Error exporting page {i+1}: {e}", exc_info=True)
                self.ui_manager.show_error_message(
                    "Export Error", f"Error exporting page {i+1}: {str(e)}"
                )
                # Optionally, you might want to set was_cancelled_by_user = True here or break
                # depending on whether one error should halt the entire batch.
                # For now, it continues to the next page.

        # Close the progress dialog
        if progress:  # Check if progress dialog was created
            # Disconnect the canceled signal before closing to prevent it from
            # setting cancel_requested to True if it's an auto-close.
            try:
                progress.canceled.disconnect(self.ui_manager.handle_cancel_request)
            except TypeError:  # Signal already disconnected or never connected
                pass
            progress.close()

        # Show completion message only if the loop wasn't broken by explicit user cancellation
        if not was_cancelled_by_user:
            self.ui_manager.show_export_complete_message(export_subdir, len(pages))

            # Open the parent export directory
            try:
                if os.path.exists(export_dir):
                    # Use os.path.normpath to ensure the path is in the OS's preferred format
                    normalized_export_dir = os.path.normpath(export_dir)
                    os.startfile(normalized_export_dir)
                    self.logger.info(
                        f"Opened export directory: {normalized_export_dir}"
                    )
                else:
                    self.logger.warning(
                        f"Export directory {export_dir} not found. Cannot open."
                    )
            except Exception as e:
                self.logger.error(f"Error opening export directory {export_dir}: {e}")
        else:
            self.logger.info(
                "Export was cancelled by the user. Skipping completion message and opening directory."
            )
