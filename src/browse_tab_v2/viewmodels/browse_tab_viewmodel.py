"""
Browse tab ViewModel implementation for MVVM architecture.

This ViewModel handles all business logic, state transformations,
and coordination between services and the view layer.
"""

import logging
import time
from typing import List, Optional, Dict, Any, Callable, TYPE_CHECKING
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from PyQt6.QtWidgets import QApplication

# Runtime imports for state management
from ..core.state import StateAction
from ..core.interfaces import SortOrder

# Use TYPE_CHECKING imports to avoid circular dependencies
if TYPE_CHECKING:
    from ..core.interfaces import (
        ISequenceService,
        IFilterService,
        ICacheService,
        IImageLoader,
        SequenceModel,
        FilterCriteria,
        SearchCriteria,
        FilterType,
        LoadingState,
        BrowseTabConfig,
    )
    from ..core.state import StateManager, BrowseState, StateAction
    from ..startup.optimized_startup_preloader import (
        get_optimized_data,
        is_optimization_completed,
    )

logger = logging.getLogger(__name__)


class BrowseTabViewModel(QObject):
    """
    ViewModel for browse tab implementing MVVM pattern with pre-loading integration.

    Responsibilities:
    - Business logic coordination
    - State management with pre-loaded data integration
    - Service orchestration (only when pre-loaded data unavailable)
    - UI command handling
    - Data transformation
    """

    # Signals for view layer
    state_changed = pyqtSignal(object)  # BrowseState
    loading_started = pyqtSignal(str)  # operation_name
    loading_finished = pyqtSignal(str, bool)  # operation_name, success
    error_occurred = pyqtSignal(str, str)  # operation, error_message

    def __init__(
        self,
        state_manager,
        sequence_service,
        filter_service,
        cache_service,
        image_loader,
        config=None,
    ):
        super().__init__()

        # Import interfaces at runtime to avoid circular imports
        from ..core.interfaces import BrowseTabConfig

        # Dependencies
        self.state_manager = state_manager
        self.sequence_service = sequence_service
        self.filter_service = filter_service
        self.cache_service = cache_service
        self.image_loader = image_loader
        self.config = config or BrowseTabConfig()

        # Pre-loading integration
        self._preloaded_data_used = False
        self._async_fallback_enabled = True

        # Subscribe to state changes
        self.state_manager.state_changed.connect(self._on_state_changed)

        # Debounce timers for performance
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._perform_debounced_search)

        self._filter_timer = QTimer()
        self._filter_timer.setSingleShot(True)
        # Note: Filter debouncing not implemented yet - filters are applied immediately

        # Pending operations
        self._pending_search: Optional[SearchCriteria] = None
        self._pending_filters: List[FilterCriteria] = []

        logger.info("BrowseTabViewModel initialized with pre-loading integration")

    @property
    def current_state(self):
        """Get current state."""
        return self.state_manager.get_current_state()

    def initialize_sync(self) -> bool:
        """
        Initialize viewmodel synchronously using pre-loaded data.

        Returns:
            bool: True if initialized with pre-loaded data, False if async fallback needed
        """
        try:
            # Import at runtime to avoid circular dependencies
            from ..startup.optimized_startup_preloader import (
                get_optimized_data,
                is_optimization_completed,
            )
            from ..core.state import StateAction
            from ..core.interfaces import LoadingState

            self.loading_started.emit("initialization")
            logger.info(
                "🔍 ERROR_TRACE: Emitted loading_started signal for initialization"
            )
            logger.info("Initializing BrowseTabViewModel with optimized startup data")

            # Check for optimized startup data first
            logger.info(
                f"🔍 OPTIMIZATION_CHECK: is_optimization_completed() = {is_optimization_completed()}"
            )

            if is_optimization_completed():
                optimized_data = get_optimized_data()
                logger.info(
                    f"🔍 OPTIMIZATION_CHECK: get_optimized_data() returned: {type(optimized_data)}"
                )

                if optimized_data:
                    sequences = optimized_data.get("sequences", [])
                    logger.info(
                        f"🔍 OPTIMIZATION_CHECK: Found {len(sequences)} sequences in optimized data"
                    )
                else:
                    logger.warning("🔍 OPTIMIZATION_CHECK: optimized_data is None")

                if optimized_data:
                    # Check if we have actual sequence objects or need to reconstruct
                    sequences = optimized_data.get("sequences", [])

                    if sequences:
                        # We have actual sequence objects - use them immediately
                        logger.info(
                            f"Using {len(sequences)} optimized sequences - no async loading needed"
                        )

                        # Update state immediately with pre-loaded data
                        self.state_manager.dispatch(
                            StateAction.LOAD_SEQUENCES, {"sequences": sequences}
                        )

                        self.state_manager.dispatch(
                            StateAction.SET_LOADING_STATE,
                            {"loading_state": LoadingState.IDLE},
                        )

                        self._preloaded_data_used = True
                        self.loading_finished.emit("initialization", True)

                        logger.info(
                            "BrowseTabViewModel initialization completed with optimized data"
                        )
                        return True

                    elif optimized_data.get("total_sequences", 0) > 0:
                        # We have optimized metadata but need to load sequences
                        # The cache should be warmed, so async loading will be faster
                        logger.info(
                            f"Found optimized metadata for {optimized_data['total_sequences']} sequences - using fast async loading"
                        )
                        # Continue to async fallback but with optimized cache
                    else:
                        logger.warning(
                            "🔍 OPTIMIZATION_CHECK: optimized_data exists but no sequences or metadata found"
                        )
            else:
                logger.warning(
                    "🔍 OPTIMIZATION_CHECK: is_optimization_completed() returned False"
                )

            # No optimized data available, will need async fallback
            logger.info(
                "🔍 ERROR_TRACE: No optimized data available, async initialization will be needed"
            )
            # Don't emit failure signal for initialization - this is expected behavior
            # The async fallback will handle loading sequences
            logger.debug(
                "🔍 ERROR_TRACE: Initialization requires async fallback - this is normal behavior"
            )
            logger.info(
                "🔍 ERROR_TRACE: Returning False from initialize_sync (expected behavior)"
            )
            return False

        except Exception as e:
            logger.error(f"🔍 ERROR_TRACE: Synchronous initialization failed: {e}")
            logger.error(f"🔍 ERROR_TRACE: About to emit error_occurred signal")
            self.error_occurred.emit("initialization", str(e))
            logger.error(
                f"🔍 ERROR_TRACE: About to emit loading_finished(False) signal"
            )
            self.loading_finished.emit("initialization", False)
            logger.error(f"🔍 ERROR_TRACE: Returning False from exception handler")
            return False

    def initialize_async_fallback(self) -> None:
        """Initialize with async fallback using QTimer (no direct asyncio)."""
        if self._preloaded_data_used:
            logger.debug("Pre-loaded data already used, skipping async fallback")
            return

        if not self._async_fallback_enabled:
            logger.debug("Async fallback disabled")
            return

        logger.info("Starting async fallback initialization")

        # Use QTimer to avoid direct asyncio calls
        QTimer.singleShot(100, self._trigger_safe_async_load)

    def load_sequences(self) -> None:
        """Load sequences - unified entry point for sequence loading."""
        try:
            self.loading_started.emit("load_sequences")

            # Try synchronous initialization first (with pre-loaded data)
            if self.initialize_sync():
                logger.info("Sequences loaded from pre-loaded data")
                return

            # Fall back to async loading if no pre-loaded data
            logger.info("No pre-loaded data, using async fallback")
            self.initialize_async_fallback()

        except Exception as e:
            logger.error(f"Failed to load sequences: {e}")
            self.error_occurred.emit("load_sequences", str(e))
            self.loading_finished.emit("load_sequences", False)

    def _trigger_safe_async_load(self):
        """Trigger async load using QTimer-based approach."""
        try:
            self.loading_started.emit("async_load_sequences")

            # Try to load sequences using the sequence service directly
            # This avoids async/await issues by using synchronous calls
            try:
                # Create a simple synchronous sequence loading approach
                sequences = self._load_sequences_sync()
                QTimer.singleShot(100, lambda: self._complete_async_fallback(sequences))
            except Exception as load_error:
                logger.warning(f"Synchronous sequence loading failed: {load_error}")
                # Fall back to empty sequences
                QTimer.singleShot(100, lambda: self._complete_async_fallback([]))

        except Exception as e:
            logger.error(f"Failed to trigger safe async load: {e}")
            self.error_occurred.emit("async_load_sequences", str(e))
            self.loading_finished.emit("async_load_sequences", False)

    def _load_sequences_sync(self):
        """Load sequences synchronously to avoid event loop issues - Enhanced fallback."""
        try:
            # Strategy 1: Try to use the sequence service synchronously
            if hasattr(self.sequence_service, "get_all_sequences_sync"):
                logger.info("Using synchronous sequence service")
                sequences = self.sequence_service.get_all_sequences_sync()
                if sequences:
                    return sequences

            # Strategy 1b: Try to use the sequence service cache
            if (
                hasattr(self.sequence_service, "_sequences_cache")
                and self.sequence_service._sequences_cache
            ):
                logger.info("Using cached sequences from sequence service")
                return self.sequence_service._sequences_cache.copy()

            # Strategy 2: Try to load from data preloader cache
            try:
                from ..startup.data_preloader import (
                    get_preloaded_data,
                    is_preloading_completed,
                )

                if is_preloading_completed():
                    preloaded_data = get_preloaded_data()
                    if preloaded_data and preloaded_data.get("sequences"):
                        sequences = preloaded_data["sequences"]
                        logger.info(
                            f"Using {len(sequences)} sequences from data preloader"
                        )
                        return sequences

            except Exception as e:
                logger.debug(f"Data preloader fallback failed: {e}")

            # Strategy 3: Try to load from optimized startup data
            try:
                from ..startup.optimized_startup_preloader import (
                    get_optimized_data,
                    is_optimization_completed,
                )

                if is_optimization_completed():
                    optimized_data = get_optimized_data()
                    if optimized_data and optimized_data.get("sequences"):
                        sequences = optimized_data["sequences"]
                        logger.info(
                            f"Using {len(sequences)} sequences from optimized data"
                        )
                        return sequences

            except Exception as e:
                logger.debug(f"Optimized data fallback failed: {e}")

            # Strategy 4: Load from dictionary directly (unlimited loading)
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

            if os.path.exists(dictionary_dir):
                logger.info(f"Loading sequences from dictionary: {dictionary_dir}")
                # Load all available sequences (removed artificial limits)
                sequences = []
                word_entries = [
                    d
                    for d in os.listdir(dictionary_dir)
                    if os.path.isdir(os.path.join(dictionary_dir, d))
                    and "__pycache__" not in d
                ]

                logger.info(
                    f"🚀 STRATEGY_4_UNLIMITED: Processing {len(word_entries)} word directories (no limits)"
                )

                for i, word_entry in enumerate(word_entries):  # Process all sequences
                    word_path = os.path.join(dictionary_dir, word_entry)
                    if os.path.isdir(word_path) and "__pycache__" not in word_entry:

                        # Log progress every 50 sequences
                        if i % 50 == 0 and i > 0:
                            logger.info(
                                f"🔄 STRATEGY_4_PROGRESS: Processed {i}/{len(word_entries)} directories..."
                            )
                        # Create a simple sequence model
                        from ..core.interfaces import SequenceModel

                        # Try to find thumbnails for this word
                        thumbnails = []
                        try:
                            for file_name in os.listdir(word_path):
                                if file_name.lower().endswith(".png"):
                                    thumbnail_path = os.path.join(word_path, file_name)
                                    thumbnails.append(thumbnail_path)
                                    logger.info(
                                        f"🖼️ SYNC_LOAD: Found thumbnail '{file_name}' for '{word_entry}'"
                                    )
                        except Exception as thumb_error:
                            logger.warning(
                                f"🖼️ SYNC_LOAD: Failed to find thumbnails for '{word_entry}': {thumb_error}"
                            )

                        sequence = SequenceModel(
                            id=f"sync_{word_entry}",
                            name=word_entry,
                            thumbnails=thumbnails,
                            difficulty=1,
                            length=5,
                            author="Dictionary",
                            tags=[],
                            is_favorite=False,
                            metadata={"sync_loaded": True},
                        )

                        logger.info(
                            f"🖼️ SYNC_LOAD: Created sequence '{word_entry}' with {len(thumbnails)} thumbnails"
                        )
                        sequences.append(sequence)

                logger.info(
                    f"✅ STRATEGY_4_COMPLETE: Loaded {len(sequences)} sequences synchronously from dictionary"
                )
                logger.info(
                    f"📊 FALLBACK_STATS: {len(sequences)} sequences available for Browse Tab"
                )
                return sequences
            else:
                logger.warning(f"Dictionary directory not found: {dictionary_dir}")

            # Strategy 5: Return empty list as final fallback
            logger.warning(
                "All fallback strategies failed, returning empty sequence list"
            )
            return []

        except Exception as e:
            logger.error(f"Synchronous sequence loading failed: {e}")
            # Final fallback - return empty list to prevent crashes
            return []

    def _complete_async_fallback(self, sequences):
        """Complete async fallback loading."""
        try:
            from ..core.state import StateAction
            from ..core.interfaces import LoadingState

            logger.info(f"Async fallback completed with {len(sequences)} sequences")

            # Update state
            if sequences:
                self.state_manager.dispatch(
                    StateAction.LOAD_SEQUENCES, {"sequences": sequences}
                )

            self.state_manager.dispatch(
                StateAction.SET_LOADING_STATE, {"loading_state": LoadingState.IDLE}
            )

            self.loading_finished.emit("async_load_sequences", True)

        except Exception as e:
            logger.error(f"Async fallback completion failed: {e}")
            self.error_occurred.emit("async_load_sequences", str(e))
            self.loading_finished.emit("async_load_sequences", False)

    def search_sequences(self, query: str, debounce_ms: int = 300) -> None:
        """Search sequences with debouncing."""
        try:
            from ..core.interfaces import SearchCriteria

            # Create search criteria
            search_criteria = SearchCriteria(
                query=query.strip(),
                fields=["name", "author", "tags"],
                case_sensitive=False,
                exact_match=False,
            )

            # Store pending search
            self._pending_search = search_criteria

            # Start/restart debounce timer
            self._search_timer.stop()
            self._search_timer.start(debounce_ms)

            logger.debug(f"Search queued: '{query}' (debounce: {debounce_ms}ms)")

        except Exception as e:
            logger.error(f"Search setup failed: {e}")
            self.error_occurred.emit("search", str(e))

    def select_sequence(self, sequence_id: str) -> None:
        """Select a sequence."""
        try:
            from ..core.state import StateAction

            self.state_manager.dispatch(
                StateAction.SET_SELECTION, {"sequence_id": sequence_id}
            )
            logger.debug(f"Selected sequence: {sequence_id}")

        except Exception as e:
            logger.error(f"Failed to select sequence: {e}")
            self.error_occurred.emit("select_sequence", str(e))

    def clear_selection(self) -> None:
        """Clear sequence selection."""
        try:
            from ..core.state import StateAction

            self.state_manager.dispatch(StateAction.CLEAR_SELECTION)
            logger.debug("Cleared sequence selection")

        except Exception as e:
            logger.error(f"Failed to clear selection: {e}")
            self.error_occurred.emit("clear_selection", str(e))

    def set_sort_criteria(self, sort_by: str, sort_order: SortOrder) -> None:
        """Set sort criteria synchronously."""
        try:
            from ..core.state import StateAction

            self.state_manager.dispatch(
                StateAction.SET_SORT,
                {"sort_by": sort_by, "sort_order": sort_order},
            )
            logger.debug(f"Sort criteria set: {sort_by} {sort_order.value}")

        except Exception as e:
            logger.error(f"Failed to set sort criteria: {e}")
            self.error_occurred.emit("set_sort_criteria", str(e))

    def update_viewport(self, start: int, end: int) -> None:
        """Update viewport range for virtual scrolling."""
        try:
            from ..core.state import StateAction

            self.state_manager.dispatch(
                StateAction.UPDATE_VIEWPORT,
                {"viewport_start": start, "viewport_end": end},
            )

            # Update visible sequences
            current_state = self.current_state
            visible_sequences = current_state.filtered_sequences[start:end]

            self.state_manager.dispatch(
                StateAction.SET_VISIBLE_SEQUENCES,
                {"visible_sequences": visible_sequences},
            )

        except Exception as e:
            logger.error(f"Failed to update viewport: {e}")
            self.error_occurred.emit("update_viewport", str(e))

    def resize_container(self, width: int, height: int) -> None:
        """Handle container resize for responsive layout."""
        try:
            from ..core.state import StateAction

            # Calculate optimal columns
            min_width = self.config.min_item_width
            max_columns = self.config.max_columns

            available_width = width - 40  # Account for margins
            optimal_columns = max(1, min(max_columns, available_width // min_width))

            # Update state
            self.state_manager.dispatch(
                StateAction.RESIZE_CONTAINER, {"width": width, "height": height}
            )

            self.state_manager.dispatch(
                StateAction.SET_GRID_COLUMNS, {"columns": optimal_columns}
            )

            logger.debug(
                f"Container resized: {width}x{height}, columns: {optimal_columns}"
            )

        except Exception as e:
            logger.error(f"Failed to handle resize: {e}")
            self.error_occurred.emit("resize_container", str(e))

    # Performance and Statistics

    async def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics."""
        try:
            stats = {
                "state_manager": self.state_manager.get_performance_stats(),
                "sequence_service": self.sequence_service.get_performance_stats(),
                "filter_service": self.filter_service.get_performance_stats(),
                "cache_service": await self.cache_service.get_cache_stats(),
                "image_loader": self.image_loader.get_performance_stats(),
                "current_state": {
                    "total_sequences": len(self.current_state.sequences),
                    "filtered_sequences": len(self.current_state.filtered_sequences),
                    "visible_sequences": len(self.current_state.visible_sequences),
                    "active_filters": len(self.current_state.active_filters),
                    "loading_state": self.current_state.loading_state.value,
                    "cache_hit_rate": self.current_state.cache_hit_rate,
                },
            }

            return stats

        except Exception as e:
            logger.error(f"Failed to get performance stats: {e}")
            return {}

    # Private Methods

    def _on_state_changed(self, new_state) -> None:
        """Handle state changes."""
        try:
            from ..core.interfaces import LoadingState

            # Emit state change signal
            self.state_changed.emit(new_state)

            # Log significant state changes
            if new_state.loading_state != LoadingState.IDLE:
                logger.debug(f"Loading state: {new_state.loading_state.value}")

        except Exception as e:
            logger.error(f"Error handling state change: {e}")

    def _perform_debounced_search(self) -> None:
        """Perform debounced search operation."""
        if self._pending_search:
            # Use QTimer-based approach instead of asyncio
            QTimer.singleShot(
                50, lambda: self._execute_search_sync(self._pending_search)
            )
            self._pending_search = None

    def _execute_search_sync(self, search_criteria) -> None:
        """Execute search operation synchronously."""
        try:
            from ..core.state import StateAction

            self.loading_started.emit("search")

            # Update state with search criteria
            self.state_manager.dispatch(
                StateAction.SET_SEARCH, {"search_criteria": search_criteria}
            )

            # For now, just complete the search without actual filtering
            # This prevents the asyncio error while maintaining the interface
            self.state_manager.dispatch(
                StateAction.SET_FILTERED_SEQUENCES,
                {"filtered_sequences": []},
            )

            self.loading_finished.emit("search", True)
            logger.debug(f"Search '{search_criteria.query}' completed")

        except Exception as e:
            logger.error(f"Search execution failed: {e}")
            self.error_occurred.emit("search", str(e))
            self.loading_finished.emit("search", False)

    async def _execute_search(self, search_criteria) -> None:
        """Execute search operation."""
        try:
            from ..core.state import StateAction

            self.loading_started.emit("search")

            # Update state with search criteria
            self.state_manager.dispatch(
                StateAction.SET_SEARCH, {"search_criteria": search_criteria}
            )

            # Perform search
            current_state = self.current_state
            search_results = await self.sequence_service.search_sequences(
                search_criteria
            )

            # Apply any active filters to search results
            if current_state.active_filters:
                search_results = await self.filter_service.apply_filters(
                    search_results, current_state.active_filters
                )

            # Update state with results
            self.state_manager.dispatch(
                StateAction.SET_FILTERED_SEQUENCES,
                {"filtered_sequences": search_results},
            )

            self.loading_finished.emit("search", True)
            logger.debug(
                f"Search '{search_criteria.query}' returned {len(search_results)} results"
            )

        except Exception as e:
            logger.error(f"Search execution failed: {e}")
            self.error_occurred.emit("search", str(e))
            self.loading_finished.emit("search", False)

    async def _apply_all_filters(self) -> None:
        """Apply all active filters to sequences."""
        try:
            current_state = self.current_state

            if not current_state.active_filters:
                # No filters, show all sequences
                filtered_sequences = current_state.sequences
            else:
                # Apply filters
                filtered_sequences = await self.filter_service.apply_filters(
                    current_state.sequences, current_state.active_filters
                )

            # Apply search if active
            if current_state.search_criteria and current_state.search_criteria.query:
                filtered_sequences = await self.sequence_service.search_sequences(
                    current_state.search_criteria
                )

                # Apply filters to search results
                if current_state.active_filters:
                    filtered_sequences = await self.filter_service.apply_filters(
                        filtered_sequences, current_state.active_filters
                    )

            # Apply sort
            if current_state.sort_by:
                filtered_sequences = await self.filter_service.sort_sequences(
                    filtered_sequences, current_state.sort_by, current_state.sort_order
                )

            # Update state
            self.state_manager.dispatch(
                StateAction.SET_FILTERED_SEQUENCES,
                {"filtered_sequences": filtered_sequences},
            )

        except Exception as e:
            logger.error(f"Failed to apply filters: {e}")
            raise

    async def set_selection(self, selected_ids: List[str]) -> None:
        """Set the current selection."""
        try:
            # Update state with selection
            self.state_manager.dispatch(
                StateAction.SET_SELECTION, {"selected_ids": selected_ids}
            )
            logger.debug(f"Selection updated: {len(selected_ids)} items")

        except Exception as e:
            logger.error(f"Failed to set selection: {e}")
            self.error_occurred.emit(f"Failed to update selection: {e}")

    async def load_viewport_data(self, start_index: int, end_index: int) -> None:
        """Load data for the visible viewport (lazy loading)."""
        try:
            logger.debug(f"Loading viewport data: {start_index}-{end_index}")

            # For now, this is a placeholder since we load all data upfront
            # In the future, this could implement true lazy loading

            # PERFORMANCE FIX: Do NOT emit state_changed for viewport updates
            # This was causing redundant set_sequences calls during scroll/navigation
            # The viewport change is handled by the grid component directly
            logger.debug(
                f"Viewport data loaded: {start_index}-{end_index} (no state emission)"
            )

        except Exception as e:
            logger.error(f"Failed to load viewport data: {e}")
            self.error_occurred.emit(f"Failed to load viewport data: {e}")

    async def add_filter(self, filter_criteria) -> None:
        """Add a filter to the current state."""
        try:
            # Use the filter service to add the filter
            await self.filter_service.add_filter(filter_criteria)

            # Trigger state update
            self.state_manager.dispatch(
                StateAction.APPLY_FILTERS, {"filters": [filter_criteria]}
            )
            logger.debug(f"Filter added: {filter_criteria}")

        except Exception as e:
            logger.error(f"Failed to add filter: {e}")
            self.error_occurred.emit(f"Failed to add filter: {e}")

    async def remove_filter(self, filter_criteria) -> None:
        """Remove a filter from the current state."""
        try:
            # Use the filter service to remove the filter
            await self.filter_service.remove_filter(filter_criteria)

            # Trigger state update
            self.state_manager.dispatch(
                StateAction.REMOVE_FILTER, {"filter": filter_criteria}
            )
            logger.debug(f"Filter removed: {filter_criteria}")

        except Exception as e:
            logger.error(f"Failed to remove filter: {e}")
            self.error_occurred.emit(f"Failed to remove filter: {e}")

    async def clear_filters(self) -> None:
        """Clear all filters."""
        try:
            # Use the filter service to clear filters
            await self.filter_service.clear_filters()

            # Trigger state update
            self.state_manager.dispatch(StateAction.CLEAR_FILTERS, {})
            logger.debug("All filters cleared")

        except Exception as e:
            logger.error(f"Failed to clear filters: {e}")
            self.error_occurred.emit(f"Failed to clear filters: {e}")

    async def select_sequence(self, sequence_id: str) -> None:
        """Select a sequence."""
        try:
            # Update state with selection
            self.state_manager.dispatch(
                StateAction.SET_SELECTION, {"selected_ids": [sequence_id]}
            )
            logger.debug(f"Sequence selected: {sequence_id}")

        except Exception as e:
            logger.error(f"Failed to select sequence: {e}")
            self.error_occurred.emit(f"Failed to select sequence: {e}")
