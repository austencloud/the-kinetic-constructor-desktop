"""
Reactive state management system for browse tab v2.

This module implements a centralized, immutable state management system
with automatic UI updates and comprehensive debugging capabilities.
"""

from typing import Dict, Any, List, Optional, Callable, Set
from dataclasses import dataclass, field, fields
from PyQt6.QtCore import QObject, pyqtSignal
from enum import Enum
import uuid
import time

import logging

from .interfaces import (
    SequenceModel,
    FilterCriteria,
    SearchCriteria,
    LoadingState,
    SortOrder,
    StateError,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class BrowseState:
    """Immutable state container for browse tab."""

    # Data state
    sequences: List[SequenceModel] = field(default_factory=list)
    filtered_sequences: List[SequenceModel] = field(default_factory=list)
    visible_sequences: List[SequenceModel] = field(default_factory=list)

    # Filter state
    active_filters: List[FilterCriteria] = field(default_factory=list)
    search_criteria: Optional[SearchCriteria] = None
    sort_by: str = "name"
    sort_order: SortOrder = SortOrder.ASC

    # UI state
    loading_state: LoadingState = LoadingState.IDLE
    selected_sequence_id: Optional[str] = None
    viewport_start: int = 0
    viewport_end: int = 50

    # Layout state
    grid_columns: int = 3
    card_size: tuple = (280, 320)
    container_width: int = 1200
    container_height: int = 800

    # Cache state
    cached_images: Set[str] = field(default_factory=set)
    cache_hit_rate: float = 0.0

    # Pagination state
    current_page: int = 0
    page_size: int = 50
    total_pages: int = 0
    total_sequences: int = 0

    # Performance state
    last_load_time: float = 0.0
    last_filter_time: float = 0.0

    # Metadata
    state_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    version: int = 1

    def copy_with(self, **changes) -> "BrowseState":
        """Create new state with changes."""
        current_data = {field.name: getattr(self, field.name) for field in fields(self)}
        current_data.update(changes)
        current_data["state_id"] = str(uuid.uuid4())
        current_data["timestamp"] = time.time()
        current_data["version"] = self.version + 1
        return BrowseState(**current_data)

    def get_filter_by_type(self, filter_type) -> Optional[FilterCriteria]:
        """Get active filter by type."""
        for filter_criteria in self.active_filters:
            if filter_criteria.filter_type == filter_type:
                return filter_criteria
        return None

    def has_filter(self, filter_type) -> bool:
        """Check if filter type is active."""
        return self.get_filter_by_type(filter_type) is not None

    def get_visible_sequence_ids(self) -> List[str]:
        """Get IDs of currently visible sequences."""
        return [seq.id for seq in self.visible_sequences]

    def is_sequence_selected(self, sequence_id: str) -> bool:
        """Check if sequence is selected."""
        return self.selected_sequence_id == sequence_id

    def get_filter_summary(self) -> Dict[str, Any]:
        """Get summary of active filters."""
        return {
            "active_count": len(self.active_filters),
            "filters": [
                {"type": f.filter_type.value, "value": f.value, "operator": f.operator}
                for f in self.active_filters
            ],
            "search_query": (
                self.search_criteria.query if self.search_criteria else None
            ),
            "sort_by": self.sort_by,
            "sort_order": self.sort_order.value,
        }


class StateAction(Enum):
    """Possible state actions."""

    # Data actions
    LOAD_SEQUENCES = "load_sequences"
    SET_SEQUENCES = "set_sequences"

    # Filter actions
    APPLY_FILTER = "apply_filter"
    REMOVE_FILTER = "remove_filter"
    CLEAR_FILTERS = "clear_filters"
    SET_FILTERED_SEQUENCES = "set_filtered_sequences"

    # Search actions
    SET_SEARCH = "set_search"
    CLEAR_SEARCH = "clear_search"

    # Sort actions
    SET_SORT = "set_sort"

    # Selection actions
    SET_SELECTION = "set_selection"
    CLEAR_SELECTION = "clear_selection"

    # Viewport actions
    UPDATE_VIEWPORT = "update_viewport"
    SET_VISIBLE_SEQUENCES = "set_visible_sequences"

    # Layout actions
    RESIZE_CONTAINER = "resize_container"
    SET_GRID_COLUMNS = "set_grid_columns"

    # Cache actions
    UPDATE_CACHE_STATS = "update_cache_stats"
    ADD_CACHED_IMAGE = "add_cached_image"

    # Loading actions
    SET_LOADING_STATE = "set_loading_state"

    # Pagination actions
    SET_PAGE = "set_page"
    SET_PAGE_SIZE = "set_page_size"

    # Performance actions
    RECORD_LOAD_TIME = "record_load_time"
    RECORD_FILTER_TIME = "record_filter_time"


@dataclass
class StateChange:
    """Represents a state change with metadata."""

    action: StateAction
    payload: Dict[str, Any]
    previous_state: BrowseState
    new_state: BrowseState
    timestamp: float = field(default_factory=time.time)
    duration: float = 0.0

    def get_changed_fields(self) -> List[str]:
        """Get list of fields that changed."""
        changed = []
        for field in fields(BrowseState):
            old_value = getattr(self.previous_state, field.name)
            new_value = getattr(self.new_state, field.name)
            if old_value != new_value:
                changed.append(field.name)
        return changed


class StateManager(QObject):
    """Reactive state management with history and debugging."""

    # Signals
    state_changed = pyqtSignal(object)  # BrowseState
    action_dispatched = pyqtSignal(object)  # StateChange

    def __init__(self, initial_state: BrowseState = None):
        super().__init__()

        self._current_state = initial_state or BrowseState()
        self._history: List[StateChange] = []
        self._max_history = 50
        self._subscribers: Dict[str, Callable[[BrowseState], None]] = {}
        self._middleware: List[
            Callable[[StateAction, Dict[str, Any], BrowseState], Dict[str, Any]]
        ] = []

        logger.info(
            f"StateManager initialized with state ID: {self._current_state.state_id}"
        )

    def get_current_state(self) -> BrowseState:
        """Get current state."""
        return self._current_state

    def dispatch(self, action: StateAction, payload: Dict[str, Any] = None) -> None:
        """Dispatch action to update state."""
        if payload is None:
            payload = {}

        start_time = time.perf_counter()

        try:
            # Apply middleware
            for middleware in self._middleware:
                payload = middleware(action, payload, self._current_state)

            # Calculate new state
            new_state = self._reduce_state(action, payload, self._current_state)

            # Only update if state actually changed
            if new_state.state_id != self._current_state.state_id:
                # Record change
                duration = time.perf_counter() - start_time
                change = StateChange(
                    action=action,
                    payload=payload,
                    previous_state=self._current_state,
                    new_state=new_state,
                    duration=duration,
                )

                # Update state
                self._current_state = new_state

                # Add to history
                self._history.append(change)
                if len(self._history) > self._max_history:
                    self._history.pop(0)

                # Notify subscribers
                self.action_dispatched.emit(change)
                self.state_changed.emit(new_state)

                # Notify functional subscribers
                for subscriber in self._subscribers.values():
                    try:
                        subscriber(new_state)
                    except Exception as e:
                        logger.error(f"Error in state subscriber: {e}")

                logger.debug(f"State updated: {action.value} -> {new_state.state_id}")

        except Exception as e:
            logger.error(f"Error dispatching action {action.value}: {e}")
            raise StateError(f"Failed to dispatch action {action.value}: {e}")

    def update_state(self, **changes) -> None:
        """Update state with direct changes."""
        if changes:
            self.dispatch(StateAction.SET_SEQUENCES, changes)

    def subscribe(self, callback: Callable[[BrowseState], None]) -> str:
        """Subscribe to state changes. Returns subscription ID."""
        subscription_id = str(uuid.uuid4())
        self._subscribers[subscription_id] = callback
        logger.debug(f"Added state subscriber: {subscription_id}")
        return subscription_id

    def unsubscribe(self, subscription_id: str) -> None:
        """Unsubscribe from state changes."""
        if subscription_id in self._subscribers:
            del self._subscribers[subscription_id]
            logger.debug(f"Removed state subscriber: {subscription_id}")

    def reset_state(self) -> None:
        """Reset state to initial values."""
        self.dispatch(StateAction.LOAD_SEQUENCES, {"sequences": []})

    def add_middleware(
        self,
        middleware: Callable[
            [StateAction, Dict[str, Any], BrowseState], Dict[str, Any]
        ],
    ) -> None:
        """Add middleware for action processing."""
        self._middleware.append(middleware)

    def get_history(self) -> List[StateChange]:
        """Get state change history."""
        return self._history.copy()

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        if not self._history:
            return {}

        action_times = {}
        for change in self._history:
            action = change.action.value
            if action not in action_times:
                action_times[action] = []
            action_times[action].append(change.duration)

        stats = {}
        for action, times in action_times.items():
            stats[action] = {
                "count": len(times),
                "avg_duration": sum(times) / len(times),
                "max_duration": max(times),
                "min_duration": min(times),
            }

        return stats

    def _reduce_state(
        self, action: StateAction, payload: Dict[str, Any], current_state: BrowseState
    ) -> BrowseState:
        """Reduce state based on action (pure function)."""

        if action == StateAction.LOAD_SEQUENCES:
            sequences = payload.get("sequences", [])
            return current_state.copy_with(
                sequences=sequences,
                filtered_sequences=sequences,
                loading_state=LoadingState.LOADED,
                total_sequences=len(sequences),
            )

        elif action == StateAction.SET_SEQUENCES:
            return current_state.copy_with(**payload)

        elif action == StateAction.APPLY_FILTER:
            filter_criteria = payload.get("filter_criteria")
            if filter_criteria:
                # Remove existing filter of same type
                new_filters = [
                    f
                    for f in current_state.active_filters
                    if f.filter_type != filter_criteria.filter_type
                ]
                new_filters.append(filter_criteria)
                return current_state.copy_with(active_filters=new_filters)

        elif action == StateAction.REMOVE_FILTER:
            filter_type = payload.get("filter_type")
            if filter_type:
                new_filters = [
                    f
                    for f in current_state.active_filters
                    if f.filter_type != filter_type
                ]
                return current_state.copy_with(active_filters=new_filters)

        elif action == StateAction.CLEAR_FILTERS:
            return current_state.copy_with(
                active_filters=[], filtered_sequences=current_state.sequences
            )

        elif action == StateAction.SET_FILTERED_SEQUENCES:
            filtered = payload.get("filtered_sequences", [])
            return current_state.copy_with(filtered_sequences=filtered)

        elif action == StateAction.SET_SEARCH:
            search_criteria = payload.get("search_criteria")
            return current_state.copy_with(search_criteria=search_criteria)

        elif action == StateAction.CLEAR_SEARCH:
            return current_state.copy_with(search_criteria=None)

        elif action == StateAction.SET_SORT:
            sort_by = payload.get("sort_by", current_state.sort_by)
            sort_order = payload.get("sort_order", current_state.sort_order)
            return current_state.copy_with(sort_by=sort_by, sort_order=sort_order)

        elif action == StateAction.SET_SELECTION:
            sequence_id = payload.get("sequence_id")
            return current_state.copy_with(selected_sequence_id=sequence_id)

        elif action == StateAction.CLEAR_SELECTION:
            return current_state.copy_with(selected_sequence_id=None)

        elif action == StateAction.UPDATE_VIEWPORT:
            viewport_start = payload.get("viewport_start", current_state.viewport_start)
            viewport_end = payload.get("viewport_end", current_state.viewport_end)
            return current_state.copy_with(
                viewport_start=viewport_start, viewport_end=viewport_end
            )

        elif action == StateAction.SET_VISIBLE_SEQUENCES:
            visible = payload.get("visible_sequences", [])
            return current_state.copy_with(visible_sequences=visible)

        elif action == StateAction.RESIZE_CONTAINER:
            width = payload.get("width", current_state.container_width)
            height = payload.get("height", current_state.container_height)
            return current_state.copy_with(
                container_width=width, container_height=height
            )

        elif action == StateAction.SET_GRID_COLUMNS:
            columns = payload.get("columns", current_state.grid_columns)
            return current_state.copy_with(grid_columns=columns)

        elif action == StateAction.UPDATE_CACHE_STATS:
            cached_images = payload.get("cached_images", current_state.cached_images)
            hit_rate = payload.get("cache_hit_rate", current_state.cache_hit_rate)
            return current_state.copy_with(
                cached_images=cached_images, cache_hit_rate=hit_rate
            )

        elif action == StateAction.ADD_CACHED_IMAGE:
            image_path = payload.get("image_path")
            if image_path:
                new_cached = current_state.cached_images.copy()
                new_cached.add(image_path)
                return current_state.copy_with(cached_images=new_cached)

        elif action == StateAction.SET_LOADING_STATE:
            loading_state = payload.get("loading_state", LoadingState.IDLE)
            return current_state.copy_with(loading_state=loading_state)

        elif action == StateAction.SET_PAGE:
            page = payload.get("page", 0)
            return current_state.copy_with(current_page=page)

        elif action == StateAction.SET_PAGE_SIZE:
            page_size = payload.get("page_size", 50)
            return current_state.copy_with(page_size=page_size)

        elif action == StateAction.RECORD_LOAD_TIME:
            load_time = payload.get("load_time", 0.0)
            return current_state.copy_with(last_load_time=load_time)

        elif action == StateAction.RECORD_FILTER_TIME:
            filter_time = payload.get("filter_time", 0.0)
            return current_state.copy_with(last_filter_time=filter_time)

        # If no action matched, return current state unchanged
        return current_state
