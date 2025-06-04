# src/main_window/main_widget/sequence_card_tab/export/page_image_data_extractor.py
import os
import logging
import tempfile
import uuid
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from PyQt6.QtWidgets import QWidget, QLabel, QGridLayout
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import QRect

from main_window.main_widget.metadata_extractor import MetaDataExtractor
from utils.path_helpers import get_sequence_card_image_exporter_path

if TYPE_CHECKING:
    from ..tab import SequenceCardTab


class PageImageDataExtractor:
    """
    Extracts sequence data from page widgets for high-quality export.

    This class handles:
    1. Extracting sequence data from page widgets
    2. Finding original high-resolution images
    3. Extracting metadata from images
    4. Organizing sequence data for export
    """

    def __init__(self, sequence_card_tab: "SequenceCardTab"):
        self.sequence_card_tab = sequence_card_tab
        self.logger = logging.getLogger(__name__)
        self.metadata_extractor = MetaDataExtractor()

    def extract_sequence_data_from_page(self, page: QWidget) -> List[Dict[str, Any]]:
        """
        Extract sequence data from a page widget.

        This method:
        1. Finds all image-containing widgets in the page (QLabel with pixmaps)
        2. Extracts image paths and metadata from these widgets
        3. Uses MetaDataExtractor to get metadata from image files
        4. Returns a list of dictionaries with sequence data and position info

        Args:
            page: The page widget to extract sequence data from

        Returns:
            List[Dict[str, Any]]: A list of dictionaries with sequence data and position info
        """
        sequence_items = []

        # Log detailed information about the page
        self.logger.debug(f"Extracting sequence data from page: {type(page).__name__}")
        self.logger.debug(f"Page size: {page.size().width()}x{page.size().height()}")
        self.logger.debug(f"Page has layout: {page.layout() is not None}")

        # First try to extract sequence data from the page's direct children
        direct_items = self._extract_sequence_data_from_layout(page)
        if direct_items:
            sequence_items.extend(direct_items)
            self.logger.debug(
                f"Found {len(direct_items)} sequence items from direct layout"
            )

        # If we didn't find any sequence items, try to search recursively through all children
        if not sequence_items:
            self.logger.debug(
                "No sequence items found in direct layout, searching recursively"
            )
            recursive_items = self._extract_sequence_data_recursively(page)
            if recursive_items:
                sequence_items.extend(recursive_items)
                self.logger.debug(
                    f"Found {len(recursive_items)} sequence items from recursive search"
                )

        self.logger.debug(f"Total sequence items found: {len(sequence_items)}")
        return sequence_items

    def _extract_sequence_data_from_layout(self, page: QWidget) -> List[Dict[str, Any]]:
        """
        Extract sequence data from the page's layout.

        This method:
        1. Extracts sequence data from widgets in the page's grid layout
        2. Captures the exact grid position (row, column) of each item
        3. Includes these grid positions in the extracted data

        Args:
            page: The page widget to extract sequence data from

        Returns:
            List[Dict[str, Any]]: A list of dictionaries with sequence data, position info, and grid position
        """
        sequence_items = []

        # Get the page layout
        layout = page.layout()
        if not layout or not isinstance(layout, QGridLayout):
            return sequence_items

        # Iterate through all items in the layout
        for i in range(layout.count()):
            item = layout.itemAt(i)
            widget = item.widget()
            if not widget:
                continue

            # Skip page number labels
            if widget.objectName() == "pageNumberLabel":
                continue

            # Get the widget's geometry
            geometry = widget.geometry()

            # Try to extract sequence data from the widget
            sequence_data = self._extract_sequence_data_from_widget(widget)

            # If we have sequence data, add it to our list
            if sequence_data:
                # Log sequence data details
                word = sequence_data.get("word", "unknown")
                path = sequence_data.get("path", "unknown")
                self.logger.debug(f"Found sequence data - Word: {word}, Path: {path}")

                # Find the grid position (row, column) of this widget in the layout
                grid_position = self._find_widget_grid_position(layout, widget)

                # Add the widget geometry and grid position to the sequence data
                item_data = {
                    "sequence_data": sequence_data,
                    "geometry": {
                        "x": geometry.x(),
                        "y": geometry.y(),
                        "width": geometry.width(),
                        "height": geometry.height(),
                    },
                    "grid_position": grid_position,
                }

                sequence_items.append(item_data)
                self.logger.debug(
                    f"Added sequence item {len(sequence_items)}: {word} at grid position {grid_position}"
                )

        return sequence_items

    def _find_widget_grid_position(
        self, layout: QGridLayout, widget: QWidget
    ) -> Dict[str, int]:
        """
        Find the grid position (row, column) of a widget in a QGridLayout.

        Args:
            layout: The QGridLayout to search in
            widget: The widget to find

        Returns:
            Dict[str, int]: Dictionary with 'row' and 'column' keys
        """
        # Default position if we can't find it
        position = {"row": -1, "column": -1}

        # Try to find the widget in the layout
        for row in range(layout.rowCount()):
            for col in range(layout.columnCount()):
                item = layout.itemAtPosition(row, col)
                if item and item.widget() == widget:
                    position["row"] = row
                    position["column"] = col
                    self.logger.debug(
                        f"Found widget at grid position: row={row}, column={col}"
                    )
                    return position

        # If we couldn't find the widget, log a warning
        self.logger.warning(f"Could not find widget in layout: {widget}")
        return position

    def _extract_sequence_data_recursively(
        self, parent_widget: QWidget
    ) -> List[Dict[str, Any]]:
        """
        Recursively extract sequence data from all child widgets.

        This method:
        1. Recursively searches through child widgets
        2. Extracts sequence data from each widget
        3. Attempts to determine grid positions for widgets

        Args:
            parent_widget: The parent widget to search

        Returns:
            List[Dict[str, Any]]: A list of dictionaries with sequence data, position info, and grid position
        """
        sequence_items = []

        # Process all child widgets
        for child in parent_widget.findChildren(QWidget):
            # Skip if the child is not directly parented by the parent_widget
            if child.parent() != parent_widget:
                continue

            # Skip page number labels
            if child.objectName() == "pageNumberLabel":
                continue

            # Get the widget's geometry
            geometry = child.geometry()

            # Try to extract sequence data from the widget
            sequence_data = self._extract_sequence_data_from_widget(child)

            # If we have sequence data, add it to our list
            if sequence_data:
                # Log sequence data details
                word = sequence_data.get("word", "unknown")
                path = sequence_data.get("path", "unknown")
                self.logger.debug(f"Found sequence data - Word: {word}, Path: {path}")

                # Try to determine grid position based on widget properties
                grid_position = {"row": -1, "column": -1}

                # Check if the widget has grid position properties
                if (
                    child.property("grid_row") is not None
                    and child.property("grid_column") is not None
                ):
                    grid_position["row"] = child.property("grid_row")
                    grid_position["column"] = child.property("grid_column")
                    self.logger.debug(
                        f"Found grid position from properties: {grid_position}"
                    )
                # Try to infer position from geometry
                else:
                    # Estimate position based on geometry relative to other widgets
                    # This is a fallback and may not be accurate
                    self.logger.debug("No explicit grid position found, using default")

                # Add the widget geometry and grid position to the sequence data
                item_data = {
                    "sequence_data": sequence_data,
                    "geometry": {
                        "x": geometry.x(),
                        "y": geometry.y(),
                        "width": geometry.width(),
                        "height": geometry.height(),
                    },
                    "grid_position": grid_position,
                }

                sequence_items.append(item_data)
                self.logger.debug(
                    f"Added sequence item {len(sequence_items)}: {word} at grid position {grid_position}"
                )

        return sequence_items

    def _extract_sequence_data_from_widget(
        self, widget: QWidget
    ) -> Optional[Dict[str, Any]]:
        """
        Extract sequence data from a widget.

        Args:
            widget: The widget to extract sequence data from

        Returns:
            Optional[Dict[str, Any]]: Dictionary with sequence data or None if not found
        """
        sequence_data = None

        # Check if the widget is a QLabel with a pixmap
        if (
            isinstance(widget, QLabel)
            and widget.pixmap()
            and not widget.pixmap().isNull()
        ):
            # Try to get sequence data from widget properties
            if widget.property("sequence_data"):
                sequence_data = widget.property("sequence_data")
                self.logger.debug("Found sequence_data property on label")
            elif widget.property("sequence_word"):
                word = widget.property("sequence_word")
                self.logger.debug(f"Found sequence_word property: {word}")

                # Create a minimal sequence_data dict to use with _find_original_image
                temp_sequence_data = {"word": word}

                # Try to find the original image path
                image_path = self._find_original_image(temp_sequence_data)

                if image_path:
                    self.logger.debug(f"Found original image at: {image_path}")

                    # Extract metadata from the image file
                    metadata = self.metadata_extractor.extract_metadata_from_file(
                        image_path
                    )

                    if metadata:
                        self.logger.debug(f"Successfully extracted metadata from image")

                        # Create sequence_data dictionary
                        sequence_data = {
                            "word": word,
                            "path": image_path,
                            "metadata": metadata,
                        }

            # If still no sequence data, try to extract from pixmap
            if not sequence_data:
                # Try to extract image path from widget
                image_path = self._extract_image_path_from_widget(widget)

                if image_path and os.path.exists(image_path):
                    self.logger.debug(f"Found image path from widget: {image_path}")

                    # Extract metadata from the image file
                    metadata = self.metadata_extractor.extract_metadata_from_file(
                        image_path
                    )

                    if metadata:
                        self.logger.debug("Successfully extracted metadata from image")

                        # Try to get word from metadata or filename
                        word = self._extract_word_from_path_or_metadata(
                            image_path, metadata
                        )

                        # Create sequence_data dictionary
                        sequence_data = {
                            "word": word,
                            "path": image_path,
                            "metadata": metadata,
                        }

        return sequence_data

    def _extract_image_path_from_widget(self, widget: QWidget) -> Optional[str]:
        """
        Extract the image path from a widget.

        Args:
            widget: The widget to extract the image path from

        Returns:
            Optional[str]: Image path or None if not found
        """
        # Check if the widget has an image_path property
        if widget.property("image_path"):
            return widget.property("image_path")

        # Check if the widget has a source_path property
        if widget.property("source_path"):
            return widget.property("source_path")

        # Check if the widget has a filepath property
        if widget.property("filepath"):
            return widget.property("filepath")

        return None

    def _extract_word_from_path_or_metadata(
        self, image_path: str, metadata: Dict[str, Any]
    ) -> str:
        """
        Extract the word from the image path or metadata.

        Args:
            image_path: Path to the image file
            metadata: Metadata dictionary

        Returns:
            str: Extracted word
        """
        # Try to get the word from the metadata
        if metadata and "sequence" in metadata:
            if isinstance(metadata["sequence"], str):
                return metadata["sequence"]
            elif (
                isinstance(metadata["sequence"], list) and len(metadata["sequence"]) > 0
            ):
                # The sequence might be a list of dictionaries
                if (
                    isinstance(metadata["sequence"][0], dict)
                    and "word" in metadata["sequence"][0]
                ):
                    return metadata["sequence"][0]["word"]

        # Try to get the word from the path
        if image_path:
            # The word is usually the parent directory name
            parent_dir = os.path.basename(os.path.dirname(image_path))
            if parent_dir and parent_dir != "sequence_card_images":
                return parent_dir

        # Default to the filename without extension
        if image_path:
            filename = os.path.basename(image_path)
            return os.path.splitext(filename)[0]

        return "unknown"

    def _find_original_image(self, sequence_data: Dict[str, Any]) -> Optional[str]:
        """
        Find the original high-resolution image for a sequence.

        Args:
            sequence_data: Sequence data dictionary

        Returns:
            Optional[str]: Path to the original image or None if not found
        """
        word = sequence_data.get("word")
        if not word:
            return None

        # Check if the sequence_data already has a path
        if "path" in sequence_data and os.path.exists(sequence_data["path"]):
            return sequence_data["path"]

        # Look for the image in the sequence_card_images directory
        images_path = get_sequence_card_image_exporter_path()
        word_dir = os.path.join(images_path, word)

        if os.path.exists(word_dir) and os.path.isdir(word_dir):
            # Look for PNG files in the word directory
            for file in os.listdir(word_dir):
                if file.endswith(".png") and not file.startswith("__"):
                    return os.path.join(word_dir, file)

        return None

    def count_total_sequence_images(self, pages: List[QWidget]) -> int:
        """
        Count the total number of sequence images across all pages for progress tracking.

        This method provides accurate counts for fine-grained progress updates during export.

        Args:
            pages: List of page widgets to count images from

        Returns:
            int: Total number of sequence images across all pages
        """
        total_images = 0

        try:
            self.logger.info(f"Counting sequence images across {len(pages)} pages")

            for page_index, page in enumerate(pages):
                try:
                    # Extract sequence data from this page
                    sequence_items = self.extract_sequence_data_from_page(page)

                    # Count valid sequence items (those with image paths)
                    page_image_count = 0
                    for item in sequence_items:
                        if isinstance(item, dict) and "sequence_data" in item:
                            sequence_data = item["sequence_data"]
                            if isinstance(sequence_data, dict) and sequence_data.get(
                                "path"
                            ):
                                # Verify the image file exists
                                image_path = sequence_data["path"]
                                if os.path.exists(image_path):
                                    page_image_count += 1
                                else:
                                    self.logger.warning(
                                        f"Image file not found: {image_path}"
                                    )

                    total_images += page_image_count
                    self.logger.debug(
                        f"Page {page_index + 1}: {page_image_count} images"
                    )

                except Exception as e:
                    self.logger.error(
                        f"Error counting images on page {page_index + 1}: {e}"
                    )
                    # Continue counting other pages even if one fails
                    continue

            self.logger.info(f"Total sequence images counted: {total_images}")
            return total_images

        except Exception as e:
            self.logger.error(f"Error counting total sequence images: {e}")
            # Return a reasonable fallback based on page count
            fallback_count = len(pages) * 12  # Assume ~12 images per page as fallback
            self.logger.warning(f"Using fallback count: {fallback_count}")
            return fallback_count
