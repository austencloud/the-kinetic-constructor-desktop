"""
Sequence service implementation for browse tab v2.

This service handles all sequence data operations including loading,
searching, and batch operations with async support.
"""

import logging
from typing import List, Optional, Dict, Any
from pathlib import Path
import json
import time

from ..core.interfaces import (
    SequenceModel,
    SearchCriteria,
    FilterCriteria,
    BrowseTabConfig,
)

logger = logging.getLogger(__name__)


class SequenceService:
    """
    Service for managing sequence data operations.

    Provides async operations for loading, searching, and filtering sequences
    with caching and performance optimization.
    """

    def __init__(self, json_manager=None, config: BrowseTabConfig = None):
        self.json_manager = json_manager
        self.config = config or BrowseTabConfig()

        # Internal cache
        self._sequences_cache: Optional[List[SequenceModel]] = None
        self._cache_timestamp: float = 0
        self._cache_ttl: float = 300  # 5 minutes

        # Performance tracking
        self._load_times: List[float] = []
        self._search_times: List[float] = []

        logger.info("SequenceService initialized")

    def get_all_sequences_sync(self) -> List[SequenceModel]:
        """Get all available sequences synchronously (Qt-native approach)."""
        start_time = time.perf_counter()

        try:
            # Check cache first
            if self._is_cache_valid():
                logger.debug("Returning cached sequences")
                return self._sequences_cache.copy()

            # Load from data source synchronously
            sequences = self._load_sequences_from_source_sync()

            # Update cache
            self._sequences_cache = sequences
            self._cache_timestamp = time.time()

            load_time = time.perf_counter() - start_time
            self._load_times.append(load_time)

            logger.info(f"Loaded {len(sequences)} sequences in {load_time:.3f}s")
            return sequences

        except Exception as e:
            logger.error(f"Failed to load sequences: {e}")
            return []

    def _load_sequences_from_source_sync(self) -> List[SequenceModel]:
        """Load sequences from the actual data source synchronously."""
        sequences = []

        try:
            if self.json_manager:
                # Load from existing JSON manager
                sequences = self._load_from_json_manager_sync()
            else:
                # Load from default dictionary location
                sequences = self._load_from_dictionary_sync()

            logger.info(f"Loaded {len(sequences)} sequences from source")
            return sequences

        except Exception as e:
            logger.error(f"Failed to load from source: {e}")
            return []

    def _load_from_dictionary_sync(self) -> List[SequenceModel]:
        """Load sequences from dictionary files synchronously."""
        sequences = []

        try:
            # Try to import utils, fallback to manual path construction
            try:
                from utils.path_helpers import get_data_path

                dictionary_dir = get_data_path("dictionary")
            except ImportError:
                # Fallback: construct path manually
                import os

                project_root = os.path.dirname(
                    os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                )
                dictionary_dir = os.path.join(project_root, "data", "dictionary")

            import os

            if not os.path.exists(dictionary_dir):
                logger.warning(f"Dictionary directory not found: {dictionary_dir}")
                return []

            logger.info(f"Loading sequences from dictionary: {dictionary_dir}")

            word_count = 0
            word_entries = [
                entry
                for entry in os.listdir(dictionary_dir)
                if os.path.isdir(os.path.join(dictionary_dir, entry))
                and "__pycache__" not in entry
            ]

            logger.info(f"Found {len(word_entries)} word directories to process")
            logger.info(
                "🚀 FULL_COLLECTION_LOADING: Processing complete sequence collection (no limits)"
            )

            for word_entry in word_entries:
                word_path = os.path.join(dictionary_dir, word_entry)

                # Find thumbnails in the word directory
                thumbnails = self._find_thumbnails(word_path)

                if thumbnails:
                    # Create a basic sequence model from the word and thumbnails
                    sequence = self._create_sequence_model_from_directory_sync(
                        word_entry, word_path, thumbnails
                    )
                    if sequence:
                        sequences.append(sequence)
                        word_count += 1

                # Log progress every 50 sequences for monitoring
                if word_count % 50 == 0 and word_count > 0:
                    logger.info(
                        f"🔄 PROGRESS: Loaded {word_count}/{len(word_entries)} sequences..."
                    )

            logger.info(
                f"✅ FULL_COLLECTION_COMPLETE: Loaded {word_count} sequences from {len(word_entries)} directories"
            )
            logger.info(
                f"📊 SEQUENCE_STATS: {len(sequences)} sequences available for Browse Tab"
            )

            logger.info(f"Loaded {len(sequences)} sequences from dictionary")
            return sequences

        except Exception as e:
            logger.error(f"Failed to load from dictionary: {e}")
            return []

    def _load_from_json_manager_sync(self) -> List[SequenceModel]:
        """Load sequences using the existing JSON manager synchronously."""
        # For now, delegate to dictionary loading for simplicity
        return self._load_from_dictionary_sync()

    def _create_sequence_model_from_directory_sync(
        self, word: str, word_path: str, thumbnails: List[str]
    ) -> Optional[SequenceModel]:
        """Create a SequenceModel from a dictionary directory synchronously."""
        try:
            import os

            # Create a basic sequence model
            sequence = SequenceModel(
                id=f"dict_{word}",
                name=word,
                thumbnails=thumbnails,
                difficulty=1,  # Default difficulty
                length=len(thumbnails),
                author="Dictionary",
                tags=[],
                is_favorite=False,
                metadata={
                    "source": "dictionary",
                    "word_path": word_path,
                    "sync_loaded": True,
                    "thumbnail_count": len(thumbnails),
                },
            )

            return sequence

        except Exception as e:
            logger.error(f"Failed to create sequence model for {word}: {e}")
            return None

    def _create_sequence_from_directory(
        self, directory_path: str
    ) -> Optional[SequenceModel]:
        """Create sequence from directory path (synchronous version for optimized startup)."""
        try:
            import os

            # Extract word name from directory path
            word = os.path.basename(directory_path)

            # Find thumbnails in the directory
            thumbnails = self._find_thumbnails(directory_path)

            if not thumbnails:
                return None

            # Create sequence model using existing synchronous method
            return self._create_sequence_model_from_directory_sync(
                word, directory_path, thumbnails
            )

        except Exception as e:
            logger.error(
                f"Failed to create sequence from directory {directory_path}: {e}"
            )
            return None

    async def get_all_sequences(self) -> List[SequenceModel]:
        """Get all available sequences with caching."""
        start_time = time.perf_counter()

        try:
            # Check cache first
            if self._is_cache_valid():
                logger.debug("Returning cached sequences")
                return self._sequences_cache.copy()

            # Load from data source
            sequences = await self._load_sequences_from_source()

            # Update cache
            self._sequences_cache = sequences
            self._cache_timestamp = time.time()

            load_time = time.perf_counter() - start_time
            self._load_times.append(load_time)

            logger.info(f"Loaded {len(sequences)} sequences in {load_time:.3f}s")
            return sequences.copy()

        except Exception as e:
            logger.error(f"Failed to load sequences: {e}")
            raise

    async def get_sequence_by_id(self, sequence_id: str) -> Optional[SequenceModel]:
        """Get specific sequence by ID."""
        sequences = await self.get_all_sequences()

        for sequence in sequences:
            if sequence.id == sequence_id:
                return sequence

        logger.warning(f"Sequence not found: {sequence_id}")
        return None

    async def search_sequences(self, criteria: SearchCriteria) -> List[SequenceModel]:
        """Search sequences by criteria with performance optimization."""
        start_time = time.perf_counter()

        try:
            sequences = await self.get_all_sequences()
            results = await self._perform_search(sequences, criteria)

            search_time = time.perf_counter() - start_time
            self._search_times.append(search_time)

            logger.debug(
                f"Search '{criteria.query}' returned {len(results)} results in {search_time:.3f}s"
            )
            return results

        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise

    async def get_sequences_batch(self, offset: int, limit: int) -> List[SequenceModel]:
        """Get sequences in batches for pagination."""
        sequences = await self.get_all_sequences()

        # Validate parameters
        offset = max(0, offset)
        limit = min(limit, self.config.max_page_size)

        end_index = min(offset + limit, len(sequences))
        batch = sequences[offset:end_index]

        logger.debug(f"Returning batch: {offset}-{end_index} of {len(sequences)}")
        return batch

    async def get_sequences_by_filter(
        self, filter_criteria: List[FilterCriteria]
    ) -> List[SequenceModel]:
        """Get sequences matching filter criteria."""
        sequences = await self.get_all_sequences()

        if not filter_criteria:
            return sequences

        # Apply filters sequentially
        filtered = sequences
        for criteria in filter_criteria:
            filtered = await self._apply_single_filter(filtered, criteria)

        logger.debug(f"Filtered {len(sequences)} -> {len(filtered)} sequences")
        return filtered

    async def refresh_cache(self) -> None:
        """Force refresh of sequence cache."""
        logger.info("Refreshing sequence cache")
        self._sequences_cache = None
        self._cache_timestamp = 0
        await self.get_all_sequences()

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "avg_load_time": 0.0,
            "avg_search_time": 0.0,
            "total_sequences": 0,
        }

        if self._load_times:
            stats["avg_load_time"] = sum(self._load_times) / len(self._load_times)

        if self._search_times:
            stats["avg_search_time"] = sum(self._search_times) / len(self._search_times)

        if self._sequences_cache:
            stats["total_sequences"] = len(self._sequences_cache)

        return stats

    def _is_cache_valid(self) -> bool:
        """Check if cache is valid."""
        if not self._sequences_cache:
            return False

        age = time.time() - self._cache_timestamp
        return age < self._cache_ttl

    async def _load_sequences_from_source(self) -> List[SequenceModel]:
        """Load sequences from the actual data source."""
        sequences = []

        try:
            if self.json_manager:
                # Load from existing JSON manager
                sequences = await self._load_from_json_manager()
            else:
                # Load from default dictionary location
                sequences = await self._load_from_dictionary()

            logger.info(f"Loaded {len(sequences)} sequences from source")
            return sequences

        except Exception as e:
            logger.error(f"Failed to load from source: {e}")
            return []

    async def _load_from_json_manager(self) -> List[SequenceModel]:
        """Load sequences using the existing JSON manager."""
        sequences = []

        try:
            # Load from the dictionary directory structure
            from utils.path_helpers import get_data_path
            import os

            dictionary_dir = get_data_path("dictionary")
            logger.info(f"Loading dictionary from: {dictionary_dir}")

            if not os.path.exists(dictionary_dir):
                logger.warning(f"Dictionary directory does not exist: {dictionary_dir}")
                return sequences

            # Scan dictionary directory for word folders
            word_count = 0
            for word_entry in os.listdir(dictionary_dir):
                word_path = os.path.join(dictionary_dir, word_entry)

                # Skip non-directories and __pycache__
                if not os.path.isdir(word_path) or "__pycache__" in word_entry:
                    continue

                # Find thumbnails in the word directory
                thumbnails = self._find_thumbnails(word_path)

                if thumbnails:
                    # Create a basic sequence model from the word and thumbnails
                    sequence = await self._create_sequence_model_from_directory(
                        word_entry, word_path, thumbnails
                    )
                    if sequence:
                        sequences.append(sequence)
                        word_count += 1

            logger.info(
                f"Found {word_count} words with {len(sequences)} sequences in dictionary"
            )

            return sequences

        except Exception as e:
            logger.error(f"Failed to load from JSON manager: {e}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            return []

    async def _load_from_dictionary(self) -> List[SequenceModel]:
        """Load sequences from dictionary files."""
        sequences = []

        try:
            # Use the same logic as _load_from_json_manager for consistency
            from utils.path_helpers import get_data_path
            import os

            dictionary_dir = get_data_path("dictionary")
            logger.info(f"Loading dictionary from: {dictionary_dir}")

            if not os.path.exists(dictionary_dir):
                logger.warning(f"Dictionary directory does not exist: {dictionary_dir}")
                return sequences

            # Scan dictionary directory for word folders
            word_count = 0
            for word_entry in os.listdir(dictionary_dir):
                word_path = os.path.join(dictionary_dir, word_entry)

                # Skip non-directories and __pycache__
                if not os.path.isdir(word_path) or "__pycache__" in word_entry:
                    continue

                # Find thumbnails in the word directory
                thumbnails = self._find_thumbnails(word_path)

                if thumbnails:
                    # Create a basic sequence model from the word and thumbnails
                    sequence = await self._create_sequence_model_from_directory(
                        word_entry, word_path, thumbnails
                    )
                    if sequence:
                        sequences.append(sequence)
                        word_count += 1

            logger.info(
                f"Found {word_count} words with {len(sequences)} sequences in dictionary"
            )

            return sequences

        except Exception as e:
            logger.error(f"Failed to load from dictionary: {e}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            return []

    async def _create_sequence_model(
        self, word: str, word_data: Dict[str, Any]
    ) -> Optional[SequenceModel]:
        """Create SequenceModel from word data."""
        try:
            # Extract metadata - could be nested or at root level
            metadata = word_data.get("metadata", word_data)

            # Generate unique sequence ID
            sequence_id = f"{word}_{hash(str(word_data)) % 10000}"

            # Extract thumbnails
            thumbnails = []
            if "thumbnails" in word_data:
                thumbnails = word_data["thumbnails"]
            elif "thumbnail" in word_data:
                thumbnails = [word_data["thumbnail"]]

            # Extract beats/sequence data
            beats = []
            if "beats" in word_data:
                beats = word_data["beats"]
            elif isinstance(word_data, list):
                # Sometimes the word_data itself is the sequence
                beats = word_data

            # Extract difficulty
            difficulty = 1
            if "difficulty" in metadata:
                difficulty = metadata["difficulty"]
            elif "level" in metadata:
                difficulty = metadata["level"]
            elif "difficulty" in word_data:
                difficulty = word_data["difficulty"]

            # Extract tags
            tags = []
            if "tags" in metadata:
                tags = metadata["tags"]
            elif "categories" in metadata:
                tags = metadata["categories"]
            elif "tags" in word_data:
                tags = word_data["tags"]

            # Extract author
            author = metadata.get("author", word_data.get("author", "Dictionary"))
            if not author or author == "":
                author = "Dictionary"

            # Calculate length
            length = (
                len(beats)
                if beats
                else metadata.get("length", word_data.get("length", 0))
            )

            # Create sequence model
            sequence = SequenceModel(
                id=sequence_id,
                name=word,
                thumbnails=thumbnails,
                difficulty=difficulty,
                length=length,
                author=author,
                tags=tags,
                is_favorite=metadata.get(
                    "is_favorite", word_data.get("is_favorite", False)
                ),
                metadata={
                    **metadata,
                    "word": word,
                    "beats": beats,
                    "sequence_data": word_data,
                },
            )

            logger.debug(
                f"Created sequence model for '{word}' with {length} beats, difficulty {difficulty}"
            )
            return sequence

        except Exception as e:
            logger.error(f"Failed to create sequence model for {word}: {e}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    def _find_thumbnails(self, word_path: str) -> List[str]:
        """Find thumbnail images in a word directory."""
        thumbnails = []

        try:
            import os

            # Look for PNG files in the word directory
            for file_name in os.listdir(word_path):
                if file_name.lower().endswith(".png"):
                    thumbnail_path = os.path.join(word_path, file_name)
                    thumbnails.append(thumbnail_path)

            # Sort thumbnails to ensure consistent ordering
            thumbnails.sort()

        except Exception as e:
            logger.error(f"Failed to find thumbnails in {word_path}: {e}")

        return thumbnails

    async def _create_sequence_model_from_directory(
        self, word: str, word_path: str, thumbnails: List[str]
    ) -> Optional[SequenceModel]:
        """Create a SequenceModel from a dictionary directory."""
        try:
            import os

            # Generate unique sequence ID
            sequence_id = f"{word}_{hash(word_path) % 10000}"

            # Extract metadata from the first thumbnail if available
            metadata = {}
            difficulty = 1
            length = 0

            if thumbnails:
                # Try to extract metadata from thumbnail filename or path
                first_thumbnail = thumbnails[0]

                # Basic metadata extraction from filename
                filename = os.path.basename(first_thumbnail)
                if "_ver" in filename:
                    # This is a variation
                    base_name = filename.split("_ver")[0]
                    metadata["base_word"] = base_name
                    metadata["is_variation"] = True
                else:
                    metadata["is_variation"] = False

                # Try to determine difficulty from word length or complexity
                difficulty = min(max(1, len(word) // 3), 5)  # Simple heuristic

                # Estimate length from word complexity
                length = len(word)

            # Create sequence model
            sequence = SequenceModel(
                id=sequence_id,
                name=word,
                thumbnails=thumbnails,
                difficulty=difficulty,
                length=length,
                author="Dictionary",
                tags=[],
                is_favorite=False,
                metadata={
                    **metadata,
                    "word": word,
                    "word_path": word_path,
                    "thumbnail_count": len(thumbnails),
                },
            )

            logger.debug(
                f"Created sequence model for '{word}' with {len(thumbnails)} thumbnails"
            )
            return sequence

        except Exception as e:
            logger.error(
                f"Failed to create sequence model from directory {word_path}: {e}"
            )
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    async def _perform_search(
        self, sequences: List[SequenceModel], criteria: SearchCriteria
    ) -> List[SequenceModel]:
        """Perform search operation on sequences."""
        if not criteria.query.strip():
            return sequences

        query = (
            criteria.query.lower() if not criteria.case_sensitive else criteria.query
        )
        results = []

        for sequence in sequences:
            if await self._matches_search_criteria(sequence, query, criteria):
                results.append(sequence)

        return results

    async def _matches_search_criteria(
        self, sequence: SequenceModel, query: str, criteria: SearchCriteria
    ) -> bool:
        """Check if sequence matches search criteria."""
        for field in criteria.fields:
            field_value = getattr(sequence, field, None)

            if field_value is None:
                continue

            # Handle different field types
            if isinstance(field_value, str):
                search_text = (
                    field_value.lower() if not criteria.case_sensitive else field_value
                )
                if criteria.exact_match:
                    if search_text == query:
                        return True
                else:
                    if query in search_text:
                        return True

            elif isinstance(field_value, list):
                # Search in list fields (like tags)
                for item in field_value:
                    if isinstance(item, str):
                        search_text = (
                            item.lower() if not criteria.case_sensitive else item
                        )
                        if criteria.exact_match:
                            if search_text == query:
                                return True
                        else:
                            if query in search_text:
                                return True

        return False

    async def _apply_single_filter(
        self, sequences: List[SequenceModel], criteria: FilterCriteria
    ) -> List[SequenceModel]:
        """Apply a single filter criteria to sequences."""
        filtered = []

        for sequence in sequences:
            if await self._sequence_matches_filter(sequence, criteria):
                filtered.append(sequence)

        return filtered

    async def _sequence_matches_filter(
        self, sequence: SequenceModel, criteria: FilterCriteria
    ) -> bool:
        """Check if sequence matches filter criteria."""
        field_name = criteria.filter_type.value
        field_value = getattr(sequence, field_name, None)

        if field_value is None:
            return False

        # Apply operator
        if criteria.operator == "equals":
            return field_value == criteria.value
        elif criteria.operator == "contains":
            if isinstance(field_value, str):
                return criteria.value.lower() in field_value.lower()
            elif isinstance(field_value, list):
                return criteria.value in field_value
        elif criteria.operator == "range":
            if isinstance(criteria.value, (list, tuple)) and len(criteria.value) == 2:
                min_val, max_val = criteria.value
                return min_val <= field_value <= max_val
        elif criteria.operator == "in":
            if isinstance(criteria.value, (list, tuple)):
                return field_value in criteria.value
        elif criteria.operator == "not_in":
            if isinstance(criteria.value, (list, tuple)):
                return field_value not in criteria.value
        elif criteria.operator == "greater_than":
            return field_value > criteria.value
        elif criteria.operator == "less_than":
            return field_value < criteria.value
        elif criteria.operator == "greater_than_or_equal":
            return field_value >= criteria.value
        elif criteria.operator == "less_than_or_equal":
            return field_value <= criteria.value

        return False
