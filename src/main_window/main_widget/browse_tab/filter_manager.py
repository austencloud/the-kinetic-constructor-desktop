from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from utils.path_helpers import get_data_path

if TYPE_CHECKING:
    from main_window.main_widget.browse_tab.browse_tab import BrowseTab


class BrowseTabFilterManager:
    def __init__(self, browse_tab: "BrowseTab"):
        self.browse_tab = browse_tab
        self.metadata_extractor = self.browse_tab.metadata_extractor

    def filter_favorites(self) -> list[tuple[str, list[str], int]]:
        return [
            (word, thumbnails, self._get_sequence_length(thumbnails[0]))
            for word, thumbnails in self.browse_tab.get.base_words()
            if any(self._is_favorite(thumbnail) for thumbnail in thumbnails)
        ]

    def filter_by_difficulty(self) -> list[tuple[str, list[str], int]]:
        """Sort sequences by difficulty level (ascending order)."""

        sequences = []
        for word, thumbnails in self.browse_tab.get.base_words():
            difficulty_levels = [
                self.metadata_extractor.get_level(thumbnail) for thumbnail in thumbnails
            ]

            # Filter out None values and get the max difficulty in case of multiple variations
            difficulty_levels = [
                level for level in difficulty_levels if level is not None
            ]
            max_difficulty = max(difficulty_levels, default=1)

            sequences.append((word, thumbnails, max_difficulty))

        # Sort by difficulty level (ascending)
        return sorted(sequences, key=lambda seq: seq[2])

    def filter_all_sequences(self) -> list[tuple[str, list[str], int]]:
        sequences = []
        for word, thumbnails in self.browse_tab.get.base_words():
            if not thumbnails:
                print(f"No thumbnails found for {word}. Skipping...")
                continue
            try:
                sequence_length = self._get_sequence_length(thumbnails[0])
                sequences.append((word, thumbnails, sequence_length))
            except Exception as e:
                print(f"Error processing {word}: {e}")
        return sequences

    def filter_most_recent(self) -> list[tuple[str, list[str], int]]:
        filtered_sequences = []

        # Set the date range to the past two weeks
        now = datetime.now()
        two_weeks_ago = now - timedelta(weeks=2)

        for word, thumbnails in self.browse_tab.get.base_words():
            date_added = self.browse_tab.sequence_picker.section_manager.get_date_added(
                thumbnails
            )

            # Ensure date_added is a datetime object
            if isinstance(date_added, str):
                try:
                    date_added = datetime.fromisoformat(date_added)
                except ValueError:
                    print(f"Invalid date format for {word}: {date_added}")
                    continue

            if not isinstance(date_added, datetime):
                print(f"Unexpected date type for {word}: {type(date_added)}")
                continue

            # Check if date_added is within the past two weeks
            if two_weeks_ago <= date_added <= now:
                sequence_length = self._get_sequence_length(thumbnails[0])
                filtered_sequences.append((word, thumbnails, sequence_length))

        return filtered_sequences

    def filter_by_tag(self, tag: str) -> list[tuple[str, list[str], int]]:
        return [
            (word, thumbnails, self._get_sequence_length(thumbnails[0]))
            for word, thumbnails in self.browse_tab.get.base_words()
            if tag in self.metadata_extractor.get_tags(thumbnails[0])
        ]

    def _get_sequence_length(self, thumbnail: str) -> int:
        return self.metadata_extractor.get_length(thumbnail)

    def _is_favorite(self, thumbnail: str) -> bool:
        return self.metadata_extractor.get_favorite_status(thumbnail)
