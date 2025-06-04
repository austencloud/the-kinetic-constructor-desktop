"""
Core interfaces for the browse tab v2 architecture.

This module defines the fundamental interfaces and data models that form
the foundation of the new browse tab architecture.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncIterator, Callable
from dataclasses import dataclass, field
from enum import Enum
import time
import uuid


@dataclass
class SequenceModel:
    """Core sequence data model for the browse tab."""

    id: str
    name: str
    thumbnails: List[str]
    difficulty: int
    length: int
    author: str
    tags: List[str]
    is_favorite: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class FilterType(Enum):
    """Available filter types for sequences."""

    LENGTH = "length"
    DIFFICULTY = "difficulty"
    AUTHOR = "author"
    CATEGORY = "category"
    STARTING_LETTER = "starting_letter"
    CONTAINS_LETTERS = "contains_letters"
    TAGS = "tags"
    FAVORITES = "favorites"
    STARTING_POSITION = "starting_position"
    GRID_MODE = "grid_mode"


class SortOrder(Enum):
    """Sort order options."""

    ASC = "asc"
    DESC = "desc"


@dataclass
class FilterCriteria:
    """Filter criteria container."""

    filter_type: FilterType
    value: Any
    operator: str = "equals"  # equals, contains, range, in, not_in

    def __post_init__(self):
        # Validate operator
        valid_operators = [
            "equals",
            "contains",
            "range",
            "in",
            "not_in",
            "greater_than",
            "less_than",
            "greater_than_or_equal",
            "less_than_or_equal",
        ]
        if self.operator not in valid_operators:
            raise ValueError(f"Invalid operator: {self.operator}")


@dataclass
class SearchCriteria:
    """Search criteria for sequences."""

    query: str
    fields: List[str] = field(default_factory=lambda: ["name", "author", "tags"])
    case_sensitive: bool = False
    exact_match: bool = False


class LoadingState(Enum):
    """Loading states for async operations."""

    IDLE = "idle"
    LOADING = "loading"
    LOADED = "loaded"
    ERROR = "error"
    CANCELLED = "cancelled"


# Service Interfaces


class ISequenceService(ABC):
    """Interface for sequence data operations."""

    @abstractmethod
    async def get_all_sequences(self) -> List[SequenceModel]:
        """Get all available sequences."""
        pass

    @abstractmethod
    async def get_sequence_by_id(self, sequence_id: str) -> Optional[SequenceModel]:
        """Get specific sequence by ID."""
        pass

    @abstractmethod
    async def search_sequences(self, criteria: SearchCriteria) -> List[SequenceModel]:
        """Search sequences by criteria."""
        pass

    @abstractmethod
    async def get_sequences_batch(self, offset: int, limit: int) -> List[SequenceModel]:
        """Get sequences in batches for pagination."""
        pass

    @abstractmethod
    async def get_sequences_by_filter(
        self, filter_criteria: List[FilterCriteria]
    ) -> List[SequenceModel]:
        """Get sequences matching filter criteria."""
        pass


class IFilterService(ABC):
    """Interface for filtering operations."""

    @abstractmethod
    async def apply_filters(
        self, sequences: List[SequenceModel], criteria: List[FilterCriteria]
    ) -> List[SequenceModel]:
        """Apply filter criteria to sequence list."""
        pass

    @abstractmethod
    async def get_filter_suggestions(
        self, filter_type: FilterType, partial_value: str
    ) -> List[str]:
        """Get auto-complete suggestions for filters."""
        pass

    @abstractmethod
    async def get_available_filter_values(
        self, filter_type: FilterType, sequences: List[SequenceModel]
    ) -> List[Any]:
        """Get all available values for a filter type."""
        pass

    @abstractmethod
    async def sort_sequences(
        self, sequences: List[SequenceModel], sort_by: str, sort_order: SortOrder
    ) -> List[SequenceModel]:
        """Sort sequences by specified criteria."""
        pass


class ICacheService(ABC):
    """Interface for caching operations."""

    @abstractmethod
    async def get_cached_image(
        self, image_path: str, size: tuple
    ) -> Optional["QPixmap"]:
        """Get cached image if available."""
        pass

    @abstractmethod
    async def cache_image(
        self, image_path: str, pixmap: "QPixmap", size: tuple
    ) -> None:
        """Cache image for future use."""
        pass

    @abstractmethod
    async def preload_images(self, image_paths: List[str], size: tuple) -> None:
        """Preload images in background."""
        pass

    @abstractmethod
    async def clear_cache(self) -> None:
        """Clear all cached data."""
        pass

    @abstractmethod
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        pass


class IStateManager(ABC):
    """Interface for state management."""

    @abstractmethod
    def get_current_state(self) -> "BrowseState":
        """Get current state."""
        pass

    @abstractmethod
    def update_state(self, **changes) -> None:
        """Update state with changes."""
        pass

    @abstractmethod
    def subscribe(self, callback: Callable[["BrowseState"], None]) -> str:
        """Subscribe to state changes. Returns subscription ID."""
        pass

    @abstractmethod
    def unsubscribe(self, subscription_id: str) -> None:
        """Unsubscribe from state changes."""
        pass

    @abstractmethod
    def reset_state(self) -> None:
        """Reset state to initial values."""
        pass


class IImageLoader(ABC):
    """Interface for image loading operations."""

    @abstractmethod
    async def load_image_async(
        self, image_path: str, target_size: tuple = None
    ) -> Optional["QPixmap"]:
        """Load single image asynchronously."""
        pass

    @abstractmethod
    async def load_batch_async(
        self, image_paths: List[str], target_size: tuple = None
    ) -> Dict[str, "QPixmap"]:
        """Load multiple images in parallel."""
        pass

    @abstractmethod
    def cancel_loading(self, image_path: str = None) -> None:
        """Cancel loading operations."""
        pass


class IPerformanceMonitor(ABC):
    """Interface for performance monitoring."""

    @abstractmethod
    def start_timer(self, operation_name: str) -> str:
        """Start timing an operation. Returns timer ID."""
        pass

    @abstractmethod
    def stop_timer(self, timer_id: str) -> float:
        """Stop timer and return duration in seconds."""
        pass

    @abstractmethod
    def record_metric(self, metric_name: str, value: float) -> None:
        """Record a performance metric."""
        pass

    @abstractmethod
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report."""
        pass


# Event Interfaces


class IBrowseTabEvents(ABC):
    """Interface for browse tab events."""

    @abstractmethod
    def on_sequence_selected(self, sequence_id: str) -> None:
        """Handle sequence selection."""
        pass

    @abstractmethod
    def on_filter_applied(self, filter_criteria: FilterCriteria) -> None:
        """Handle filter application."""
        pass

    @abstractmethod
    def on_search_performed(self, search_criteria: SearchCriteria) -> None:
        """Handle search operation."""
        pass

    @abstractmethod
    def on_loading_state_changed(self, state: LoadingState) -> None:
        """Handle loading state changes."""
        pass


# Configuration


@dataclass
class BrowseTabConfig:
    """Configuration for browse tab behavior."""

    # Performance settings
    max_concurrent_image_loads: int = 4
    image_cache_size: int = 200
    virtual_scroll_buffer_rows: int = 3

    # UI settings
    default_columns: int = 3
    min_item_width: int = 280
    max_columns: int = 4
    animation_duration: int = 250

    # Animation settings (Phase 2 Modern UI Components)
    enable_animations: bool = True
    enable_glassmorphism: bool = True
    enable_hover_effects: bool = True
    enable_smooth_scrolling: bool = True
    animation_fps_target: int = 60
    respect_reduced_motion: bool = True

    # Modern UI settings
    glassmorphism_opacity: float = 0.1
    border_radius: int = 20
    shadow_blur_radius: int = 20
    hover_scale_factor: float = 1.02

    # Service references (set by factory)
    image_loader: Optional["IImageLoader"] = None

    # Pagination settings
    default_page_size: int = 50
    max_page_size: int = 200

    # Cache settings
    enable_disk_cache: bool = True
    cache_expiry_hours: int = 24

    # Debug settings
    enable_performance_monitoring: bool = True
    enable_debug_logging: bool = False


# Exceptions


class BrowseTabError(Exception):
    """Base exception for browse tab operations."""

    pass


class SequenceNotFoundError(BrowseTabError):
    """Raised when a sequence is not found."""

    pass


class FilterError(BrowseTabError):
    """Raised when filter operations fail."""

    pass


class CacheError(BrowseTabError):
    """Raised when cache operations fail."""

    pass


class StateError(BrowseTabError):
    """Raised when state operations fail."""

    pass
