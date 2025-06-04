import logging
from typing import List, Dict, Any
from PyQt6.QtWidgets import QWidget, QApplication

from ..page_image_data_extractor import PageImageDataExtractor


class PageProcessingService:
    def __init__(self, data_extractor: PageImageDataExtractor):
        self.logger = logging.getLogger(__name__)
        self.data_extractor = data_extractor

    def extract_page_data(self, page: QWidget) -> List[Dict[str, Any]]:
        try:
            sequence_items = self.data_extractor.extract_sequence_data_from_page(page)
            page.setProperty("sequence_items", sequence_items)
            return sequence_items
        except Exception as e:
            self.logger.error(f"Error extracting page data: {e}")
            return []

    def count_page_images(self, page: QWidget) -> int:
        try:
            sequence_items = self.extract_page_data(page)
            return len(
                [
                    item
                    for item in sequence_items
                    if isinstance(item, dict)
                    and item.get("sequence_data", {}).get("path")
                ]
            )
        except Exception as e:
            self.logger.error(f"Error counting page images: {e}")
            return 0

    def count_total_images(self, pages: List[QWidget]) -> int:
        return sum(self.count_page_images(page) for page in pages)

    def validate_page(self, page: QWidget) -> bool:
        try:
            sequence_items = self.extract_page_data(page)
            return len(sequence_items) > 0
        except Exception as e:
            self.logger.error(f"Error validating page: {e}")
            return False

    def prepare_pages_batch(self, pages: List[QWidget], batch_size: int = 4):
        for i in range(0, len(pages), batch_size):
            yield pages[i : i + batch_size]

    def get_sequence_metadata(self, pages: List[QWidget]) -> Dict[str, Any]:
        total_sequences = 0
        sequences_by_length = {}
        sequences_by_level = {}

        for page in pages:
            sequence_items = self.extract_page_data(page)

            for item in sequence_items:
                if not isinstance(item, dict):
                    continue

                sequence_data = item.get("sequence_data", {})
                if not sequence_data.get("path"):
                    continue

                total_sequences += 1

                metadata = sequence_data.get("metadata", {})
                length = metadata.get("length", "unknown")
                level = metadata.get("level", "unknown")

                sequences_by_length[length] = sequences_by_length.get(length, 0) + 1
                sequences_by_level[level] = sequences_by_level.get(level, 0) + 1

        return {
            "total_sequences": total_sequences,
            "sequences_by_length": sequences_by_length,
            "sequences_by_level": sequences_by_level,
            "total_pages": len(pages),
        }
