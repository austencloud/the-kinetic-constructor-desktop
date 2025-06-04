"""
Filter service implementation for browse tab v2.

This service handles all filtering operations including filter application,
auto-suggestions, and sorting with optimized algorithms.
"""

import logging
from typing import List, Dict, Any, Set
from collections import defaultdict
import time
import re

from ..core.interfaces import (
    SequenceModel,
    FilterCriteria,
    FilterType,
    SortOrder,
    FilterError,
    BrowseTabConfig,
)

logger = logging.getLogger(__name__)


class FilterService:
    """
    Service for filtering and sorting sequence data.

    Provides optimized filtering algorithms with caching and
    auto-suggestion capabilities.
    """

    def __init__(self, config: BrowseTabConfig = None):
        self.config = config or BrowseTabConfig()

        # Cache for filter suggestions
        self._suggestion_cache: Dict[str, List[str]] = {}
        self._available_values_cache: Dict[FilterType, List[Any]] = {}

        # Performance tracking
        self._filter_times: List[float] = []
        self._sort_times: List[float] = []

        logger.info("FilterService initialized")

    def apply_filters_sync(
        self, sequences: List[SequenceModel], criteria: List[FilterCriteria]
    ) -> List[SequenceModel]:
        """Apply filter criteria to sequence list synchronously (Qt-native approach)."""
        start_time = time.perf_counter()

        try:
            if not criteria:
                return sequences

            # Apply filters sequentially without async complications
            filtered = sequences
            for filter_criteria in criteria:
                filtered = self._apply_single_filter_sync(filtered, filter_criteria)

                # Early termination if no results
                if not filtered:
                    break

            filter_time = time.perf_counter() - start_time
            self._filter_times.append(filter_time)

            logger.debug(f"Applied {len(criteria)} filters in {filter_time:.3f}s")
            return filtered

        except Exception as e:
            logger.error(f"Filter application failed: {e}")
            return sequences  # Return original sequences on error

    def _apply_single_filter_sync(
        self, sequences: List[SequenceModel], criteria: FilterCriteria
    ) -> List[SequenceModel]:
        """Apply a single filter criteria to sequences synchronously."""
        filtered = []

        for sequence in sequences:
            if self._sequence_matches_filter_sync(sequence, criteria):
                filtered.append(sequence)

        return filtered

    def _sequence_matches_filter_sync(
        self, sequence: SequenceModel, criteria: FilterCriteria
    ) -> bool:
        """Check if sequence matches filter criteria synchronously."""
        try:
            value = self._extract_filter_value_sync(sequence, criteria.filter_type)

            if value is None:
                return False

            return self._apply_filter_operator_sync(value, criteria)

        except Exception as e:
            logger.error(f"Error matching filter: {e}")
            return False

    def _extract_filter_value_sync(
        self, sequence: SequenceModel, filter_type: FilterType
    ) -> Any:
        """Extract the value for a specific filter type from a sequence synchronously."""
        if filter_type == FilterType.LENGTH:
            return sequence.length
        elif filter_type == FilterType.DIFFICULTY:
            return sequence.difficulty
        elif filter_type == FilterType.AUTHOR:
            return sequence.author
        elif filter_type == FilterType.TAGS:
            return sequence.tags
        elif filter_type == FilterType.IS_FAVORITE:
            return sequence.is_favorite
        elif filter_type == FilterType.STARTING_LETTER:
            return sequence.name[0].upper() if sequence.name else None
        elif filter_type == FilterType.CONTAINS_LETTERS:
            return sequence.name.upper() if sequence.name else None
        elif filter_type == FilterType.GRID_MODE:
            return sequence.metadata.get("grid_mode", "Unknown")

        return None

    def _apply_filter_operator_sync(self, value: Any, criteria: FilterCriteria) -> bool:
        """Apply filter operator to value synchronously."""
        if criteria.operator == "equals":
            return value == criteria.value
        elif criteria.operator == "not_equals":
            return value != criteria.value
        elif criteria.operator == "contains":
            if isinstance(value, str):
                return criteria.value.lower() in value.lower()
            elif isinstance(value, list):
                return any(
                    criteria.value.lower() in str(item).lower() for item in value
                )
        elif criteria.operator == "starts_with":
            if isinstance(value, str):
                return value.lower().startswith(criteria.value.lower())
        elif criteria.operator == "ends_with":
            if isinstance(value, str):
                return value.lower().endswith(criteria.value.lower())
        elif criteria.operator == "greater_than":
            return value > criteria.value
        elif criteria.operator == "less_than":
            return value < criteria.value
        elif criteria.operator == "greater_than_or_equal":
            return value >= criteria.value
        elif criteria.operator == "less_than_or_equal":
            return value <= criteria.value

        return False

    async def apply_filters(
        self, sequences: List[SequenceModel], criteria: List[FilterCriteria]
    ) -> List[SequenceModel]:
        """Apply filter criteria to sequence list with optimization."""
        start_time = time.perf_counter()

        try:
            if not criteria:
                return sequences

            # Sort criteria by selectivity (most selective first)
            sorted_criteria = await self._sort_criteria_by_selectivity(
                criteria, sequences
            )

            # Apply filters sequentially
            filtered = sequences
            for filter_criteria in sorted_criteria:
                filtered = await self._apply_single_filter(filtered, filter_criteria)

                # Early termination if no results
                if not filtered:
                    break

            filter_time = time.perf_counter() - start_time
            self._filter_times.append(filter_time)

            logger.debug(
                f"Applied {len(criteria)} filters: {len(sequences)} -> {len(filtered)} in {filter_time:.3f}s"
            )
            return filtered

        except Exception as e:
            logger.error(f"Filter application failed: {e}")
            raise FilterError(f"Failed to apply filters: {e}")

    async def get_filter_suggestions(
        self, filter_type: FilterType, partial_value: str
    ) -> List[str]:
        """Get auto-complete suggestions for filters."""
        cache_key = f"{filter_type.value}:{partial_value.lower()}"

        # Check cache first
        if cache_key in self._suggestion_cache:
            return self._suggestion_cache[cache_key]

        suggestions = []

        try:
            if filter_type == FilterType.AUTHOR:
                suggestions = await self._get_author_suggestions(partial_value)
            elif filter_type == FilterType.TAGS:
                suggestions = await self._get_tag_suggestions(partial_value)
            elif filter_type == FilterType.STARTING_LETTER:
                suggestions = await self._get_starting_letter_suggestions(partial_value)
            elif filter_type == FilterType.CONTAINS_LETTERS:
                suggestions = await self._get_contains_letter_suggestions(partial_value)

            # Cache suggestions
            self._suggestion_cache[cache_key] = suggestions

            logger.debug(
                f"Generated {len(suggestions)} suggestions for {filter_type.value}:{partial_value}"
            )
            return suggestions

        except Exception as e:
            logger.error(f"Failed to get suggestions: {e}")
            return []

    async def get_available_filter_values(
        self, filter_type: FilterType, sequences: List[SequenceModel]
    ) -> List[Any]:
        """Get all available values for a filter type."""
        # Check cache first
        if filter_type in self._available_values_cache:
            return self._available_values_cache[filter_type]

        values = set()

        try:
            for sequence in sequences:
                value = await self._extract_filter_value(sequence, filter_type)
                if value is not None:
                    if isinstance(value, list):
                        values.update(value)
                    else:
                        values.add(value)

            sorted_values = sorted(list(values))

            # Cache values
            self._available_values_cache[filter_type] = sorted_values

            logger.debug(
                f"Found {len(sorted_values)} unique values for {filter_type.value}"
            )
            return sorted_values

        except Exception as e:
            logger.error(f"Failed to get available values: {e}")
            return []

    async def sort_sequences(
        self, sequences: List[SequenceModel], sort_by: str, sort_order: SortOrder
    ) -> List[SequenceModel]:
        """Sort sequences by specified criteria."""
        start_time = time.perf_counter()

        try:
            if not sequences:
                return sequences

            # Define sort key function
            def get_sort_key(sequence: SequenceModel):
                value = getattr(sequence, sort_by, None)

                # Handle None values
                if value is None:
                    return (
                        "" if isinstance(getattr(sequences[0], sort_by, ""), str) else 0
                    )

                # Handle string sorting (case-insensitive)
                if isinstance(value, str):
                    return value.lower()

                return value

            # Sort sequences
            sorted_sequences = sorted(
                sequences, key=get_sort_key, reverse=(sort_order == SortOrder.DESC)
            )

            sort_time = time.perf_counter() - start_time
            self._sort_times.append(sort_time)

            logger.debug(
                f"Sorted {len(sequences)} sequences by {sort_by} ({sort_order.value}) in {sort_time:.3f}s"
            )
            return sorted_sequences

        except Exception as e:
            logger.error(f"Sorting failed: {e}")
            raise FilterError(f"Failed to sort sequences: {e}")

    async def clear_cache(self) -> None:
        """Clear all filter caches."""
        self._suggestion_cache.clear()
        self._available_values_cache.clear()
        logger.info("Filter caches cleared")

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        stats = {
            "avg_filter_time": 0.0,
            "avg_sort_time": 0.0,
            "cache_size": len(self._suggestion_cache),
            "available_values_cached": len(self._available_values_cache),
        }

        if self._filter_times:
            stats["avg_filter_time"] = sum(self._filter_times) / len(self._filter_times)

        if self._sort_times:
            stats["avg_sort_time"] = sum(self._sort_times) / len(self._sort_times)

        return stats

    async def _sort_criteria_by_selectivity(
        self, criteria: List[FilterCriteria], sequences: List[SequenceModel]
    ) -> List[FilterCriteria]:
        """Sort filter criteria by selectivity (most selective first)."""
        # For now, use a simple heuristic
        # In practice, you might want to analyze the data to determine selectivity

        selectivity_order = {
            FilterType.FAVORITES: 1,  # Usually very selective
            FilterType.AUTHOR: 2,
            FilterType.DIFFICULTY: 3,
            FilterType.LENGTH: 4,
            FilterType.STARTING_POSITION: 5,
            FilterType.GRID_MODE: 6,
            FilterType.TAGS: 7,
            FilterType.STARTING_LETTER: 8,
            FilterType.CONTAINS_LETTERS: 9,  # Usually least selective
        }

        return sorted(criteria, key=lambda c: selectivity_order.get(c.filter_type, 10))

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
        try:
            value = await self._extract_filter_value(sequence, criteria.filter_type)

            if value is None:
                return False

            return await self._apply_filter_operator(value, criteria)

        except Exception as e:
            logger.error(f"Error matching filter: {e}")
            return False

    async def _extract_filter_value(
        self, sequence: SequenceModel, filter_type: FilterType
    ) -> Any:
        """Extract the value for a specific filter type from a sequence."""
        if filter_type == FilterType.LENGTH:
            return sequence.length
        elif filter_type == FilterType.DIFFICULTY:
            return sequence.difficulty
        elif filter_type == FilterType.AUTHOR:
            return sequence.author
        elif filter_type == FilterType.TAGS:
            return sequence.tags
        elif filter_type == FilterType.FAVORITES:
            return sequence.is_favorite
        elif filter_type == FilterType.STARTING_LETTER:
            return sequence.name[0].upper() if sequence.name else ""
        elif filter_type == FilterType.CONTAINS_LETTERS:
            return sequence.name.upper() if sequence.name else ""
        elif filter_type == FilterType.STARTING_POSITION:
            return sequence.metadata.get("starting_position", "Unknown")
        elif filter_type == FilterType.GRID_MODE:
            return sequence.metadata.get("grid_mode", "Unknown")

        return None

    async def _apply_filter_operator(
        self, value: Any, criteria: FilterCriteria
    ) -> bool:
        """Apply filter operator to value."""
        if criteria.operator == "equals":
            return value == criteria.value

        elif criteria.operator == "contains":
            if isinstance(value, str):
                return criteria.value.lower() in value.lower()
            elif isinstance(value, list):
                return any(
                    criteria.value.lower() in str(item).lower() for item in value
                )

        elif criteria.operator == "range":
            if isinstance(criteria.value, (list, tuple)) and len(criteria.value) == 2:
                min_val, max_val = criteria.value
                return min_val <= value <= max_val

        elif criteria.operator == "in":
            if isinstance(criteria.value, (list, tuple)):
                return value in criteria.value

        elif criteria.operator == "not_in":
            if isinstance(criteria.value, (list, tuple)):
                return value not in criteria.value

        elif criteria.operator == "greater_than":
            return value > criteria.value

        elif criteria.operator == "less_than":
            return value < criteria.value

        elif criteria.operator == "greater_than_or_equal":
            return value >= criteria.value

        elif criteria.operator == "less_than_or_equal":
            return value <= criteria.value

        return False

    async def _get_author_suggestions(self, partial_value: str) -> List[str]:
        """Get author suggestions based on partial input."""
        # This would typically query a database or cache
        # For now, return some common author suggestions
        common_authors = [
            "Alice",
            "Bob",
            "Charlie",
            "Diana",
            "Eve",
            "Frank",
            "Grace",
            "Henry",
        ]

        partial_lower = partial_value.lower()
        suggestions = [
            author
            for author in common_authors
            if author.lower().startswith(partial_lower)
        ]

        return suggestions[:10]  # Limit to 10 suggestions

    async def _get_tag_suggestions(self, partial_value: str) -> List[str]:
        """Get tag suggestions based on partial input."""
        common_tags = [
            "beginner",
            "intermediate",
            "advanced",
            "expert",
            "flow",
            "static",
            "dynamic",
            "creative",
            "technical",
            "poi",
            "staff",
            "hoop",
            "fan",
            "rope",
        ]

        partial_lower = partial_value.lower()
        suggestions = [
            tag for tag in common_tags if tag.lower().startswith(partial_lower)
        ]

        return suggestions[:10]

    async def _get_starting_letter_suggestions(self, partial_value: str) -> List[str]:
        """Get starting letter suggestions."""
        if not partial_value:
            return list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

        letter = partial_value[0].upper()
        return [letter] if letter.isalpha() else []

    async def _get_contains_letter_suggestions(self, partial_value: str) -> List[str]:
        """Get contains letter suggestions."""
        # Return common letter combinations
        common_combinations = [
            "TH",
            "ER",
            "ON",
            "AN",
            "RE",
            "ED",
            "ND",
            "OU",
            "EA",
            "NI",
            "TO",
            "IT",
            "IS",
            "OR",
            "TI",
            "AS",
            "TE",
            "ET",
            "NG",
            "OF",
        ]

        partial_upper = partial_value.upper()
        suggestions = [
            combo for combo in common_combinations if combo.startswith(partial_upper)
        ]

        return suggestions[:10]

    async def add_filter(self, filter_criteria: FilterCriteria) -> None:
        """Add a filter criteria to the service."""
        # This method was missing - add implementation
        logger.debug(f"Filter added to service: {filter_criteria}")

    async def remove_filter(self, filter_criteria: FilterCriteria) -> None:
        """Remove a filter criteria from the service."""
        # This method was missing - add implementation
        logger.debug(f"Filter removed from service: {filter_criteria}")

    async def clear_filters(self) -> None:
        """Clear all filters from the service."""
        # This method was missing - add implementation
        logger.debug("All filters cleared from service")
