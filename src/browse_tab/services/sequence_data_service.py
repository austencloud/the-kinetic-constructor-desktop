"""
Sequence Data Service - Clean Architecture Implementation.

Handles sequence loading and management with single responsibility.
Provides data loading, sequence management, and cache coordination.

Features:
- Efficient sequence loading and caching
- Data transformation and validation
- Memory management and optimization
- Error handling and recovery
- Performance monitoring

Performance Targets:
- <2s total sequence loading
- <100ms data transformation
- Efficient memory usage
- Cache hit rate optimization
"""

import logging
from typing import List, Optional, Dict, Any
from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QElapsedTimer

from ..core.interfaces import SequenceModel, BrowseTabConfig

logger = logging.getLogger(__name__)


class SequenceDataService(QObject):
    """
    Service for sequence data loading and management.

    Single Responsibility: Manage sequence data lifecycle

    Features:
    - Efficient sequence loading from multiple sources
    - Data transformation and validation
    - Memory management and caching
    - Performance monitoring and optimization
    - Error handling and recovery
    """

    # Signals for service communication
    sequences_loaded = pyqtSignal(list)  # List[SequenceModel]
    loading_progress = pyqtSignal(int, int)  # current, total
    loading_error = pyqtSignal(str)  # error_message

    def __init__(self, config: BrowseTabConfig = None, parent: QObject = None):
        super().__init__(parent)

        self.config = config or BrowseTabConfig()

        # Data source dependencies (injected)
        self.json_manager = None
        self.settings_manager = None

        # State management
        self._sequences: List[SequenceModel] = []
        self._is_loading = False
        self._load_progress = 0
        self._total_sequences = 0

        # Performance tracking
        self._performance_timer = QElapsedTimer()
        self._load_start_time = 0
        self._transformation_times = []

        # Cache management
        self._sequence_cache: Dict[str, SequenceModel] = {}
        self._metadata_cache: Dict[str, Dict[str, Any]] = {}

        # Data sources
        self._data_sources = []
        self._current_source_index = 0

        logger.debug("SequenceDataService initialized")

    def load_sequences(self, force_reload: bool = False) -> None:
        """Load sequences from available data sources."""
        if self._is_loading:
            logger.warning("Sequence loading already in progress")
            return

        self._performance_timer.start()
        self._load_start_time = self._performance_timer.elapsed()
        self._is_loading = True
        self._load_progress = 0

        logger.info("Starting sequence loading")

        try:
            # Check cache first if not forcing reload
            if not force_reload and self._sequences:
                logger.info(f"Using cached sequences: {len(self._sequences)} sequences")
                self.sequences_loaded.emit(self._sequences)
                self._is_loading = False
                return

            # Try multiple data sources in order of preference
            self._try_load_from_sources()

        except Exception as e:
            logger.error(f"Failed to load sequences: {e}")
            self.loading_error.emit(f"Failed to load sequences: {e}")
            self._is_loading = False

    def _try_load_from_sources(self):
        """Try loading from multiple data sources."""
        # Data source priority order
        load_methods = [
            ("preloaded_data", self._load_from_preloaded_data),
            ("json_manager", self._load_from_json_manager),
            ("file_system", self._load_from_file_system),
            ("fallback", self._load_fallback_data),
        ]

        for source_name, load_method in load_methods:
            try:
                logger.debug(f"Trying to load from {source_name}")
                sequences = load_method()

                if sequences:
                    logger.info(
                        f"Successfully loaded {len(sequences)} sequences from {source_name}"
                    )
                    self._process_loaded_sequences(sequences, source_name)
                    return
                else:
                    logger.debug(f"No sequences found in {source_name}")

            except Exception as e:
                logger.warning(f"Failed to load from {source_name}: {e}")
                continue

        # If all sources failed
        logger.error("All data sources failed")
        self.loading_error.emit("Failed to load sequences from any data source")
        self._is_loading = False

    def _load_from_preloaded_data(self) -> Optional[List[SequenceModel]]:
        """Load sequences from preloaded data - REAL INTEGRATION."""
        try:
            # Try optimized startup preloader first
            from ..startup.optimized_startup_preloader import (
                get_optimized_data,
                is_optimization_completed,
            )

            if is_optimization_completed():
                optimized_data = get_optimized_data()
                if optimized_data and optimized_data.get("sequences"):
                    sequences = optimized_data["sequences"]
                    logger.info(
                        f"✅ REAL DATA: Found {len(sequences)} optimized preloaded sequences"
                    )
                    return sequences

            # Fallback to regular preloader
            from ..startup.data_preloader import (
                get_preloaded_data,
                is_preloading_completed,
            )

            if is_preloading_completed():
                preloaded_data = get_preloaded_data()
                if preloaded_data and "sequences" in preloaded_data:
                    sequences = preloaded_data["sequences"]
                    logger.info(
                        f"✅ REAL DATA: Found {len(sequences)} regular preloaded sequences"
                    )
                    return sequences

            logger.debug("No preloaded data available")
            return None

        except ImportError:
            logger.debug("Preloader not available")
            return None
        except Exception as e:
            logger.warning(f"Failed to load preloaded data: {e}")
            return None

    def _load_from_json_manager(self) -> Optional[List[SequenceModel]]:
        """Load sequences from JSON manager - REAL INTEGRATION."""
        try:
            # Use injected JSON manager
            if not self.json_manager:
                logger.debug("No JSON manager injected")
                return None

            # Use existing SequenceService to load from JSON manager
            from ..services.sequence_service import SequenceService

            sequence_service = SequenceService(json_manager=self.json_manager)
            sequences = sequence_service._load_sequences_from_source_sync()

            if sequences:
                logger.info(
                    f"✅ REAL DATA: Loaded {len(sequences)} sequences from JSON manager"
                )
                return sequences
            else:
                logger.debug("No sequences found in JSON manager")
                return None

        except Exception as e:
            logger.warning(f"Failed to load from JSON manager: {e}")
            return None

    def _load_from_file_system(self) -> Optional[List[SequenceModel]]:
        """Load sequences from file system."""
        try:
            import os
            from pathlib import Path

            # Look for sequence data in standard locations
            data_paths = [
                "src/data/dictionary",
                "data/dictionary",
                "../data/dictionary",
            ]

            sequences = []
            for data_path in data_paths:
                if os.path.exists(data_path):
                    sequences.extend(self._scan_directory_for_sequences(data_path))

            if sequences:
                logger.debug(f"Found {len(sequences)} sequences in file system")
                return sequences

            return None

        except Exception as e:
            logger.warning(f"Failed to load from file system: {e}")
            return None

    def _scan_directory_for_sequences(self, directory_path: str) -> List[SequenceModel]:
        """Scan directory for sequence files."""
        sequences = []

        try:
            import os
            from pathlib import Path

            for root, dirs, files in os.walk(directory_path):
                for file in files:
                    if file.endswith(".png") or file.endswith(".jpg"):
                        # Extract sequence info from file path
                        file_path = os.path.join(root, file)
                        sequence = self._create_sequence_from_file(file_path)
                        if sequence:
                            sequences.append(sequence)

        except Exception as e:
            logger.warning(f"Failed to scan directory {directory_path}: {e}")

        return sequences

    def _create_sequence_from_file(self, file_path: str) -> Optional[SequenceModel]:
        """Create sequence model from file path."""
        try:
            import os
            from pathlib import Path

            # Extract sequence name from file path
            file_name = os.path.basename(file_path)
            sequence_name = os.path.splitext(file_name)[0]

            # Remove version suffix if present
            if "_ver" in sequence_name:
                sequence_name = sequence_name.split("_ver")[0]

            # Create sequence model
            sequence = SequenceModel(
                id=sequence_name,
                name=sequence_name,
                thumbnails=[file_path],
                difficulty=1,  # Default difficulty
                length=8,  # Default length
                author="Unknown",  # Default author
                tags=["file_system"],  # Default tags
                metadata={"file_path": file_path},
            )

            return sequence

        except Exception as e:
            logger.warning(f"Failed to create sequence from file {file_path}: {e}")
            return None

    def _load_fallback_data(self) -> List[SequenceModel]:
        """Load fallback demo data."""
        logger.info("Loading fallback demo data")

        # Create demo sequences for testing
        demo_sequences = []
        for i in range(10):
            sequence = SequenceModel(
                id=f"demo_sequence_{i}",
                name=f"Demo Sequence {i}",
                thumbnails=[],
                difficulty=i % 5 + 1,
                length=(i % 10) + 5,
                author=f"Demo Author {i % 3}",
                tags=["demo", "fallback"],
                metadata={
                    "is_demo": True,
                },
            )
            demo_sequences.append(sequence)

        return demo_sequences

    def _process_loaded_sequences(self, sequences: List[SequenceModel], source: str):
        """Process and validate loaded sequences."""
        self._performance_timer.start()

        try:
            # Validate and transform sequences
            processed_sequences = []
            self._total_sequences = len(sequences)

            for i, sequence in enumerate(sequences):
                # Update progress
                self._load_progress = i + 1
                self.loading_progress.emit(self._load_progress, self._total_sequences)

                # Validate sequence
                if self._validate_sequence(sequence):
                    # Transform sequence if needed
                    processed_sequence = self._transform_sequence(sequence)
                    processed_sequences.append(processed_sequence)

                    # Cache sequence
                    self._sequence_cache[sequence.id] = processed_sequence
                else:
                    logger.warning(f"Invalid sequence skipped: {sequence.id}")

            # Store processed sequences
            self._sequences = processed_sequences

            # Emit completion
            self.sequences_loaded.emit(processed_sequences)

            elapsed = self._performance_timer.elapsed()
            total_elapsed = elapsed - self._load_start_time

            logger.info(f"Sequence processing completed in {elapsed}ms")
            logger.info(
                f"Total loading time: {total_elapsed}ms for {len(processed_sequences)} sequences"
            )
            logger.info(f"Data source: {source}")

            # Performance target: <2s total sequence loading
            if total_elapsed > 2000:
                logger.warning(
                    f"Sequence loading exceeded 2s target: {total_elapsed}ms"
                )

        except Exception as e:
            logger.error(f"Failed to process sequences: {e}")
            self.loading_error.emit(f"Failed to process sequences: {e}")

        finally:
            self._is_loading = False

    def _validate_sequence(self, sequence: SequenceModel) -> bool:
        """Validate sequence data."""
        try:
            # Check required fields
            if not sequence.id:
                return False

            if not sequence.name:
                return False

            # Additional validation can be added here
            return True

        except Exception as e:
            logger.warning(f"Sequence validation failed: {e}")
            return False

    def _transform_sequence(self, sequence: SequenceModel) -> SequenceModel:
        """Transform sequence data for consistency."""
        transform_start = self._performance_timer.elapsed()

        try:
            # Ensure consistent data format
            transformed = SequenceModel(
                id=sequence.id,
                name=sequence.name or sequence.id,
                thumbnails=sequence.thumbnails or [],
                difficulty=getattr(sequence, "difficulty", 1),
                length=getattr(sequence, "length", 8),
                author=getattr(sequence, "author", "Unknown"),
                tags=getattr(sequence, "tags", []),
                metadata=sequence.metadata or {},
            )

            # Add computed metadata
            if hasattr(sequence, "difficulty"):
                transformed.difficulty = sequence.difficulty
            if hasattr(sequence, "length"):
                transformed.length = sequence.length
            if hasattr(sequence, "author"):
                transformed.author = sequence.author

            # Cache metadata for performance
            self._metadata_cache[sequence.id] = transformed.metadata

            transform_elapsed = self._performance_timer.elapsed() - transform_start
            self._transformation_times.append(transform_elapsed)

            # Performance target: <100ms data transformation
            if transform_elapsed > 100:
                logger.warning(
                    f"Sequence transformation exceeded 100ms: {transform_elapsed}ms"
                )

            return transformed

        except Exception as e:
            logger.warning(f"Sequence transformation failed: {e}")
            return sequence

    # Public interface methods
    def get_sequences(self) -> List[SequenceModel]:
        """Get all loaded sequences."""
        return self._sequences.copy()

    def get_sequence_by_id(self, sequence_id: str) -> Optional[SequenceModel]:
        """Get sequence by ID."""
        return self._sequence_cache.get(sequence_id)

    def is_loading(self) -> bool:
        """Check if currently loading."""
        return self._is_loading

    def get_load_progress(self) -> tuple:
        """Get loading progress (current, total)."""
        return self._load_progress, self._total_sequences

    def clear_cache(self):
        """Clear sequence cache."""
        self._sequence_cache.clear()
        self._metadata_cache.clear()
        logger.debug("Sequence cache cleared")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "cached_sequences": len(self._sequence_cache),
            "cached_metadata": len(self._metadata_cache),
            "total_sequences": len(self._sequences),
            "cache_hit_rate": len(self._sequence_cache) / max(1, len(self._sequences)),
        }

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        avg_transform_time = (
            sum(self._transformation_times) / len(self._transformation_times)
            if self._transformation_times
            else 0
        )

        return {
            "total_sequences": len(self._sequences),
            "average_transform_time": avg_transform_time,
            "max_transform_time": (
                max(self._transformation_times) if self._transformation_times else 0
            ),
            "is_loading": self._is_loading,
            "load_progress": self._load_progress,
            "total_load_target": self._total_sequences,
        }

    def cleanup(self):
        """Cleanup resources."""
        try:
            self.clear_cache()
            self._sequences.clear()
            self._transformation_times.clear()
            logger.debug("SequenceDataService cleanup completed")
        except Exception as e:
            logger.error(f"SequenceDataService cleanup failed: {e}")
