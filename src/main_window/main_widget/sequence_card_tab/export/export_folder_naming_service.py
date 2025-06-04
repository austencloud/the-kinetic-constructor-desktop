"""
Export Folder Naming Service

Provides comprehensive, human-readable folder naming for sequence card exports
based on the user's selection criteria and export context.
"""

import os
from enum import Enum
from datetime import datetime
from typing import Optional, List, Dict, Any
import logging


class SequenceCardMode(Enum):
    """Export modes for sequence cards."""

    DICTIONARY = "dictionary"
    GENERATION = "generation"
    MIXED = "mixed"


class ExportFolderNamingService:
    """
    Service for generating descriptive folder names for sequence card exports.

    Creates human-readable folder names that reflect:
    - Sequence lengths (16-count, 8-count, etc.)
    - Difficulty levels (Level 1, Level 2-3, etc.)
    - Export modes (Dictionary Browse, Generated Sequences, etc.)
    - Generation batch information for generated sequences
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def generate_folder_name(
        self,
        selected_length: Optional[int] = None,
        selected_levels: Optional[List[int]] = None,
        mode: SequenceCardMode = SequenceCardMode.DICTIONARY,
        sequence_count: Optional[int] = None,
        generated_batch_info: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generate a descriptive folder name for the export.

        Args:
            selected_length: Selected sequence length (None for all lengths)
            selected_levels: Selected difficulty levels (None for all levels)
            mode: Export mode (dictionary, generation, or mixed)
            sequence_count: Total number of sequences being exported
            generated_batch_info: Information about generated sequence batches

        Returns:
            str: Human-readable folder name
        """
        try:
            components = []

            # Add sequence length component
            length_part = self._get_length_component(selected_length)
            if length_part:
                components.append(length_part)

            # Add difficulty level component
            level_part = self._get_level_component(selected_levels)
            if level_part:
                components.append(level_part)

            # Add mode-specific component
            mode_part = self._get_mode_component(mode, generated_batch_info)
            if mode_part:
                components.append(mode_part)

            # Add sequence count if significant
            count_part = self._get_count_component(sequence_count)
            if count_part:
                components.append(count_part)

            # Add timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Combine components
            if components:
                folder_name = "_".join(components) + f"_{timestamp}"
            else:
                # Fallback name
                folder_name = f"sequence_cards_{timestamp}"

            # Clean up the folder name for file systems
            folder_name = self._sanitize_folder_name(folder_name)

            self.logger.info(f"Generated folder name: {folder_name}")
            return folder_name

        except Exception as e:
            self.logger.error(f"Error generating folder name: {e}")
            # Fallback to simple timestamped name
            return f"sequence_cards_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    def _get_length_component(self, selected_length: Optional[int]) -> str:
        """Generate the length component of the folder name."""
        if selected_length and selected_length > 0:
            return f"{selected_length}-count"
        return "all-lengths"

    def _get_level_component(self, selected_levels: Optional[List[int]]) -> str:
        """Generate the difficulty level component of the folder name."""
        if not selected_levels or len(selected_levels) == 0:
            return "all-levels"

        # Sort levels for consistent naming
        sorted_levels = sorted(selected_levels)

        if len(sorted_levels) == 1:
            return f"level-{sorted_levels[0]}"
        elif len(sorted_levels) == 2 and sorted_levels == [1, 2]:
            return "level-1-2"
        elif len(sorted_levels) == 2 and sorted_levels == [2, 3]:
            return "level-2-3"
        elif len(sorted_levels) == 3 and sorted_levels == [1, 2, 3]:
            return "all-levels"
        else:
            # Handle other combinations
            if self._is_consecutive(sorted_levels):
                return f"level-{sorted_levels[0]}-{sorted_levels[-1]}"
            else:
                return f"level-{'-'.join(map(str, sorted_levels))}"

    def _get_mode_component(
        self, mode: SequenceCardMode, generated_batch_info: Optional[Dict[str, Any]]
    ) -> str:
        """Generate the mode-specific component of the folder name."""
        if mode == SequenceCardMode.DICTIONARY:
            return "dictionary"
        elif mode == SequenceCardMode.GENERATION:
            if generated_batch_info:
                return self._get_generation_component(generated_batch_info)
            return "generated"
        elif mode == SequenceCardMode.MIXED:
            return "mixed"
        else:
            return "export"

    def _get_generation_component(self, batch_info: Dict[str, Any]) -> str:
        """Generate component for generated sequence batches."""
        try:
            generation_mode = batch_info.get("generation_mode", "freeform")
            batch_id = batch_info.get("batch_id", "")

            if generation_mode and batch_id:
                return f"generated-{generation_mode}-{batch_id}"
            elif generation_mode:
                return f"generated-{generation_mode}"
            else:
                return "generated"

        except Exception as e:
            self.logger.warning(f"Error generating batch component: {e}")
            return "generated"

    def _get_count_component(self, sequence_count: Optional[int]) -> str:
        """Generate the sequence count component if significant."""
        if sequence_count and sequence_count > 0:
            # Only include count for smaller exports to keep names manageable
            if sequence_count <= 50:
                return f"{sequence_count}-sequences"
        return ""

    def _is_consecutive(self, levels: List[int]) -> bool:
        """Check if a list of levels is consecutive."""
        if len(levels) <= 1:
            return True

        for i in range(1, len(levels)):
            if levels[i] - levels[i - 1] != 1:
                return False
        return True

    def _sanitize_folder_name(self, folder_name: str) -> str:
        """
        Sanitize folder name for file system compatibility.

        Args:
            folder_name: Raw folder name

        Returns:
            str: Sanitized folder name safe for file systems
        """
        # Replace invalid characters with underscores
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            folder_name = folder_name.replace(char, "_")

        # Remove multiple consecutive underscores
        while "__" in folder_name:
            folder_name = folder_name.replace("__", "_")

        # Remove leading/trailing underscores
        folder_name = folder_name.strip("_")

        # Ensure it's not too long (Windows has a 260 character path limit)
        if len(folder_name) > 100:  # Leave room for the full path
            # Keep the timestamp and truncate the descriptive part
            if "_" in folder_name:
                parts = folder_name.split("_")
                timestamp = (
                    parts[-1]
                    if parts[-1].replace("-", "").replace("_", "").isdigit()
                    else ""
                )
                if timestamp:
                    descriptive_part = "_".join(parts[:-1])
                    max_desc_length = 100 - len(timestamp) - 1  # -1 for underscore
                    if len(descriptive_part) > max_desc_length:
                        descriptive_part = descriptive_part[:max_desc_length]
                    folder_name = f"{descriptive_part}_{timestamp}"
                else:
                    folder_name = folder_name[:100]
            else:
                folder_name = folder_name[:100]

        return folder_name


# Example usage and test cases
if __name__ == "__main__":
    service = ExportFolderNamingService()

    # Test cases
    test_cases = [
        {
            "name": "16-count Level 1 Dictionary",
            "params": {
                "selected_length": 16,
                "selected_levels": [1],
                "mode": SequenceCardMode.DICTIONARY,
            },
        },
        {
            "name": "8-count Level 2-3 Dictionary",
            "params": {
                "selected_length": 8,
                "selected_levels": [2, 3],
                "mode": SequenceCardMode.DICTIONARY,
            },
        },
        {
            "name": "12-count All Levels Dictionary",
            "params": {
                "selected_length": 12,
                "selected_levels": [1, 2, 3],
                "mode": SequenceCardMode.DICTIONARY,
            },
        },
        {
            "name": "Generated Sequences Batch",
            "params": {
                "selected_length": 16,
                "selected_levels": [1],
                "mode": SequenceCardMode.GENERATION,
                "sequence_count": 25,
                "generated_batch_info": {
                    "generation_mode": "freeform",
                    "batch_id": "1430",
                },
            },
        },
        {
            "name": "All Lengths All Levels",
            "params": {
                "selected_length": None,
                "selected_levels": None,
                "mode": SequenceCardMode.DICTIONARY,
            },
        },
    ]

    print("Export Folder Naming Service Test Cases:")
    print("=" * 50)

    for test_case in test_cases:
        folder_name = service.generate_folder_name(**test_case["params"])
        print(f"{test_case['name']}: {folder_name}")

    print("\nService ready for integration!")
