# src/main_window/main_widget/sequence_card_tab/components/display/sequence_loader.py
import os
from typing import Dict, List, Any, Optional, TYPE_CHECKING
from main_window.main_widget.metadata_extractor import MetaDataExtractor

if TYPE_CHECKING:
    from ...generation.generated_sequence_store import GeneratedSequenceStore


class SequenceLoader:
    """
    Responsible for loading and filtering sequence card images.

    This class:
    1. Loads sequence card images from the file system
    2. Extracts metadata from images
    3. Filters sequences based on length
    4. Provides a consistent interface for accessing sequence data
    5. Integrates generated sequences from the sequence store
    """

    def __init__(
        self, generated_sequence_store: Optional["GeneratedSequenceStore"] = None
    ):
        self.metadata_extractor = MetaDataExtractor()
        self.generated_sequence_store = generated_sequence_store

    def get_all_sequences(self, images_path: str) -> List[Dict[str, Any]]:
        """
        Get all sequences from the sequence_card_images directory.

        Args:
            images_path: Path to the sequence card images directory

        Returns:
            List[Dict[str, Any]]: List of sequence data dictionaries
        """
        return self.get_filtered_sequences(images_path)

    def get_filtered_sequences(
        self,
        images_path: str,
        length_filter: int = None,
        level_filters: List[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get sequences from the sequence_card_images directory with optional filtering.
        Also includes generated sequences from the sequence store.

        Args:
            images_path: Path to the sequence card images directory
            length_filter: Optional sequence length filter (None = all lengths)
            level_filters: Optional list of difficulty levels to include (None = all levels)

        Returns:
            List[Dict[str, Any]]: List of filtered sequence data dictionaries
        """
        sequences = []

        # Load dictionary sequences
        dictionary_sequences = self._load_dictionary_sequences(
            images_path, length_filter, level_filters
        )
        sequences.extend(dictionary_sequences)

        # Load generated sequences if store is available
        if self.generated_sequence_store:
            generated_sequences = (
                self.generated_sequence_store.get_sequences_for_display_system(
                    length_filter, level_filters
                )
            )
            sequences.extend(generated_sequences)

        return sequences

    def get_dictionary_sequences_only(
        self,
        images_path: str,
        length_filter: int = None,
        level_filters: List[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get only dictionary sequences, excluding generated sequences.

        Args:
            images_path: Path to the sequence card images directory
            length_filter: Optional sequence length filter (None = all lengths)
            level_filters: Optional list of difficulty levels to include (None = all levels)

        Returns:
            List[Dict[str, Any]]: List of filtered dictionary sequence data dictionaries
        """
        return self._load_dictionary_sequences(
            images_path, length_filter, level_filters
        )

    def get_generated_sequences_only(
        self,
        length_filter: int = None,
        level_filters: List[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get only generated sequences, excluding dictionary sequences.

        Args:
            length_filter: Optional sequence length filter (None = all lengths)
            level_filters: Optional list of difficulty levels to include (None = all levels)

        Returns:
            List[Dict[str, Any]]: List of filtered generated sequence data dictionaries
        """
        if not self.generated_sequence_store:
            return []

        return self.generated_sequence_store.get_sequences_for_display_system(
            length_filter, level_filters
        )

    def _load_dictionary_sequences(
        self,
        images_path: str,
        length_filter: int = None,
        level_filters: List[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Load sequences from the dictionary folder structure.

        Args:
            images_path: Path to the sequence card images directory
            length_filter: Optional sequence length filter (None = all lengths)
            level_filters: Optional list of difficulty levels to include (None = all levels)

        Returns:
            List[Dict[str, Any]]: List of filtered sequence data dictionaries
        """
        sequences = []

        # Validate the images path
        if not os.path.exists(images_path):
            print(
                f"Warning: Sequence card images directory does not exist: {images_path}"
            )
            return sequences

        # Process each word folder
        for word in os.listdir(images_path):
            word_path = os.path.join(images_path, word)

            # Skip non-directories and special directories
            if not os.path.isdir(word_path) or word.startswith("__"):
                continue

            # Process each image file
            for file in os.listdir(word_path):
                if file.endswith(".png") and not file.startswith("__"):
                    file_path = os.path.join(word_path, file)

                    # Extract sequence metadata
                    try:
                        # Get the sequence length from the metadata
                        sequence_length = self.metadata_extractor.get_length(file_path)
                        if sequence_length is None:
                            sequence_length = 0

                        # Get the sequence level from the metadata
                        sequence_level = self.metadata_extractor.get_level(file_path)
                        if sequence_level is None:
                            sequence_level = 1  # Default to level 1 if not available

                    except Exception as e:
                        print(f"Error extracting metadata from {file_path}: {e}")
                        sequence_length = 0
                        sequence_level = 1

                    # Apply length filter
                    if length_filter is not None and length_filter > 0:
                        if sequence_length != length_filter:
                            continue

                    # Apply level filter
                    if level_filters is not None and len(level_filters) > 0:
                        if sequence_level not in level_filters:
                            continue

                    sequences.append(
                        {
                            "path": file_path,
                            "word": word,
                            "metadata": {
                                "sequence_length": sequence_length,
                                "sequence_level": sequence_level,
                                "sequence": word,
                            },
                        }
                    )

        return sequences

    def filter_sequences_by_length(
        self, sequences: List[Dict[str, Any]], length: int
    ) -> List[Dict[str, Any]]:
        """
        Filter sequences by the specified length.

        Args:
            sequences: List of sequence data dictionaries
            length: Length to filter by (0 for all)

        Returns:
            List[Dict[str, Any]]: Filtered list of sequence data dictionaries
        """
        if length == 0:
            return sequences

        filtered_sequences = []

        for sequence in sequences:
            metadata = sequence.get("metadata", {})
            sequence_length = metadata.get("sequence_length", 0)

            if sequence_length == length:
                filtered_sequences.append(sequence)

        return filtered_sequences
