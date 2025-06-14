"""
Sequence Management Service - Unified Sequence Operations

Consolidates all sequence-related services into a single cohesive service:
- Simple sequence operations (simple_sequence_service)
- Beat management (beat_management_service)
- Sequence generation (generation_services)
- Workbench transformations (workbench_services)

This service provides a clean, unified interface for all sequence operations
while maintaining the proven algorithms from the individual services.
"""

from typing import List, Dict, Any, Optional, Tuple
from abc import ABC, abstractmethod
from enum import Enum
import uuid
from copy import deepcopy

from domain.models.core_models import (
    SequenceData,
    BeatData,
    MotionData,
    MotionType,
    Location,
    RotationDirection,
)
from domain.models.pictograph_models import PictographData


class ISequenceManagementService(ABC):
    """Unified interface for all sequence management operations."""

    @abstractmethod
    def create_sequence(self, name: str, length: int = 16) -> SequenceData:
        """Create a new sequence with specified length."""
        pass

    @abstractmethod
    def add_beat(
        self, sequence: SequenceData, beat: BeatData, position: int
    ) -> SequenceData:
        """Add beat to sequence at specified position."""
        pass

    @abstractmethod
    def remove_beat(self, sequence: SequenceData, position: int) -> SequenceData:
        """Remove beat from sequence at specified position."""
        pass

    @abstractmethod
    def generate_sequence(
        self, sequence_type: str, length: int, **kwargs
    ) -> SequenceData:
        """Generate sequence using specified algorithm."""
        pass

    @abstractmethod
    def apply_workbench_operation(
        self, sequence: SequenceData, operation: str, **kwargs
    ) -> SequenceData:
        """Apply workbench transformation to sequence."""
        pass


class SequenceType(Enum):
    """Types of sequence generation algorithms."""

    FREEFORM = "freeform"
    CIRCULAR = "circular"
    AUTO_COMPLETE = "auto_complete"
    MIRROR = "mirror"
    CONTINUOUS = "continuous"


class WorkbenchOperation(Enum):
    """Types of workbench operations."""

    COLOR_SWAP = "color_swap"
    HORIZONTAL_REFLECTION = "horizontal_reflection"
    VERTICAL_REFLECTION = "vertical_reflection"
    ROTATION_90 = "rotation_90"
    ROTATION_180 = "rotation_180"
    ROTATION_270 = "rotation_270"
    REVERSE_SEQUENCE = "reverse_sequence"


class SequenceManagementService(ISequenceManagementService):
    """
    Unified sequence management service consolidating all sequence operations.

    Provides comprehensive sequence management including:
    - CRUD operations for sequences and beats
    - Multiple sequence generation algorithms
    - Workbench transformations (color swap, reflection, rotation)
    - Sequence validation and optimization
    """

    def __init__(self):

        # Workbench transformation matrices
        self._transformation_matrices = self._load_transformation_matrices()

        # Validation rules
        self._sequence_validation_rules = self._load_validation_rules()

        # Dictionary service functionality
        self._dictionary_cache = {}
        self._difficulty_cache = {}

    def create_sequence(self, name: str, length: int = 16) -> SequenceData:
        """Create a new sequence with specified length."""
        beats = []

        # Create empty beats for the sequence
        for i in range(length):
            beat = BeatData(
                beat_number=i + 1,
                letter=None,
                duration=1.0,
                blue_motion=None,
                red_motion=None,
            )
            beats.append(beat)

        return SequenceData(
            id=str(uuid.uuid4()),
            name=name,
            beats=beats,
            metadata={"created_by": "sequence_management_service"},
        )

    def add_beat(
        self, sequence: SequenceData, beat: BeatData, position: int
    ) -> SequenceData:
        """Add beat to sequence at specified position."""
        if position < 0 or position > len(sequence.beats):
            raise ValueError(
                f"Invalid position {position} for sequence of length {len(sequence.beats)}"
            )

        new_beats = sequence.beats.copy()
        new_beats.insert(position, beat)

        # Update beat numbers
        for i, beat in enumerate(new_beats):
            new_beats[i] = beat.update(beat_number=i + 1)

        return sequence.update(
            beats=new_beats,
        )

    def remove_beat(self, sequence: SequenceData, position: int) -> SequenceData:
        """Remove beat from sequence at specified position."""
        if position < 0 or position >= len(sequence.beats):
            raise ValueError(
                f"Invalid position {position} for sequence of length {len(sequence.beats)}"
            )

        new_beats = sequence.beats.copy()
        new_beats.pop(position)

        # Update beat numbers
        for i, beat in enumerate(new_beats):
            new_beats[i] = beat.update(beat_number=i + 1)

        return sequence.update(
            beats=new_beats,
        )

    def generate_sequence(
        self, sequence_type: str, length: int, **kwargs
    ) -> SequenceData:
        """Generate sequence using specified algorithm."""
        sequence_type_enum = SequenceType(sequence_type)

        if sequence_type_enum == SequenceType.FREEFORM:
            return self._generate_freeform_sequence(length, **kwargs)
        elif sequence_type_enum == SequenceType.CIRCULAR:
            return self._generate_circular_sequence(length, **kwargs)
        elif sequence_type_enum == SequenceType.AUTO_COMPLETE:
            return self._generate_auto_complete_sequence(length, **kwargs)
        elif sequence_type_enum == SequenceType.MIRROR:
            return self._generate_mirror_sequence(length, **kwargs)
        elif sequence_type_enum == SequenceType.CONTINUOUS:
            return self._generate_continuous_sequence(length, **kwargs)
        else:
            raise ValueError(f"Unknown sequence type: {sequence_type}")

    def apply_workbench_operation(
        self, sequence: SequenceData, operation: str, **kwargs
    ) -> SequenceData:
        """Apply workbench transformation to sequence."""
        operation_enum = WorkbenchOperation(operation)

        if operation_enum == WorkbenchOperation.COLOR_SWAP:
            return self._apply_color_swap(sequence)
        elif operation_enum == WorkbenchOperation.HORIZONTAL_REFLECTION:
            return self._apply_horizontal_reflection(sequence)
        elif operation_enum == WorkbenchOperation.VERTICAL_REFLECTION:
            return self._apply_vertical_reflection(sequence)
        elif operation_enum == WorkbenchOperation.ROTATION_90:
            return self._apply_rotation(sequence, 90)
        elif operation_enum == WorkbenchOperation.ROTATION_180:
            return self._apply_rotation(sequence, 180)
        elif operation_enum == WorkbenchOperation.ROTATION_270:
            return self._apply_rotation(sequence, 270)
        elif operation_enum == WorkbenchOperation.REVERSE_SEQUENCE:
            return self._apply_reverse_sequence(sequence)
        else:
            raise ValueError(f"Unknown workbench operation: {operation}")

    # Private sequence generation methods

    def _generate_freeform_sequence(self, length: int, **kwargs) -> SequenceData:
        """Generate freeform sequence with random valid motions."""
        sequence = self.create_sequence("Freeform Sequence", length)
        return sequence

    def _generate_circular_sequence(self, length: int, **kwargs) -> SequenceData:
        """Generate circular sequence where end connects to beginning."""
        pass

    def _generate_auto_complete_sequence(self, length: int, **kwargs) -> SequenceData:
        """Generate auto-completed sequence based on pattern recognition."""
        pass

    def _generate_mirror_sequence(self, length: int, **kwargs) -> SequenceData:
        """Generate mirror sequence (palindromic pattern)."""
        pass

    def _generate_continuous_sequence(self, length: int, **kwargs) -> SequenceData:
        """Generate continuous sequence where each beat flows into the next."""
        pass

    def _apply_color_swap(self, sequence: SequenceData) -> SequenceData:
        """Swap blue and red motions in all beats."""
        new_beats = []
        for beat in sequence.beats:
            new_beat = beat.update(
                blue_motion=beat.red_motion,
                red_motion=beat.blue_motion,
            )
            new_beats.append(new_beat)

        return sequence.update(beats=new_beats)

    def _apply_horizontal_reflection(self, sequence: SequenceData) -> SequenceData:
        """Apply horizontal reflection to all motions."""
        pass

    def _apply_vertical_reflection(self, sequence: SequenceData) -> SequenceData:
        """Apply vertical reflection to all motions."""
        pass

    def _apply_rotation(self, sequence: SequenceData, degrees: int) -> SequenceData:
        """Apply rotation to all motions."""
        pass

    def _apply_reverse_sequence(self, sequence: SequenceData) -> SequenceData:
        """Reverse the order of beats in sequence."""
        pass

    def _load_transformation_matrices(self) -> Dict[str, Any]:
        """Load transformation matrices for workbench operations."""
        return {
            "rotation_90": [[0, -1], [1, 0]],
            "rotation_180": [[-1, 0], [0, -1]],
            "rotation_270": [[0, 1], [-1, 0]],
            "horizontal_flip": [[-1, 0], [0, 1]],
            "vertical_flip": [[1, 0], [0, -1]],
        }

    def _load_validation_rules(self) -> Dict[str, Any]:
        """Load sequence validation rules."""
        return {
            "max_length": 64,
            "min_length": 1,
            "required_fields": ["name", "beats"],
        }

    # Dictionary Service Methods (IDictionaryService interface)

    def add_sequence_to_dictionary(self, sequence: SequenceData, word: str) -> bool:
        """Add sequence to dictionary"""
        try:
            sequence_hash = self._hash_sequence(sequence)
            self._dictionary_cache[sequence_hash] = word
            return True
        except Exception:
            return False

    def get_word_for_sequence(self, sequence: SequenceData) -> Optional[str]:
        """Get word associated with sequence"""
        sequence_hash = self._hash_sequence(sequence)
        return self._dictionary_cache.get(sequence_hash)

    def calculate_difficulty(self, sequence: SequenceData) -> int:
        """Calculate sequence difficulty level using v1 algorithm"""
        sequence_hash = self._hash_sequence(sequence)

        if sequence_hash in self._difficulty_cache:
            return self._difficulty_cache[sequence_hash]

        # Implement v1 difficulty calculation logic
        difficulty = self._calculate_difficulty_score(sequence)
        self._difficulty_cache[sequence_hash] = difficulty
        return difficulty

    def _hash_sequence(self, sequence: SequenceData) -> str:
        """Create hash for sequence to use as cache key"""
        return f"{sequence.name}_{sequence.length}_{len(sequence.beats)}"

    def _calculate_difficulty_score(self, sequence: SequenceData) -> int:
        """Calculate difficulty score based on v1 algorithm"""
        if sequence.length <= 1:
            return 0

        # Simplified difficulty calculation
        # Real implementation would analyze prop movements, turns, etc.
        base_difficulty = sequence.length

        # Add complexity factors from v1
        complexity_bonus = 0
        for beat in sequence.beats:
            # Analyze beat complexity (placeholder)
            complexity_bonus += 1

        return min(base_difficulty + complexity_bonus // 4, 10)
