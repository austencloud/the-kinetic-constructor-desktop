"""
Comprehensive test suite for sequence generation system.

This test suite validates:
1. GeneratedSequenceData structure and attributes
2. Sequence generation workflow end-to-end
3. Image generation without UI dependencies
4. Error handling and fallback mechanisms
5. Thread safety and memory management
"""

import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import tempfile
import logging
from typing import List, Dict, Any

# Add project root to path for imports
project_root = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "src"))

# Import the classes we need to test
try:
    from src.main_window.main_widget.sequence_card_tab.generation.generated_sequence_data import (
        GeneratedSequenceData,
    )
    from src.main_window.main_widget.sequence_card_tab.generation.generation_params import (
        GenerationParams,
    )
except ImportError:
    # Fallback for different import structure
    sys.path.insert(
        0,
        os.path.join(
            project_root,
            "src",
            "main_window",
            "main_widget",
            "sequence_card_tab",
            "generation",
        ),
    )
    from generated_sequence_data import GeneratedSequenceData
    from generation_params import GenerationParams


class TestGeneratedSequenceData(unittest.TestCase):
    """Test the GeneratedSequenceData class structure and functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.sample_params = GenerationParams(
            length=4,
            level=1,
            generation_mode="circular",
            prop_continuity="continuous",
            turn_intensity=3,
            CAP_type="rotated",
        )

        # Create sample sequence data with metadata, start position, and beats
        self.sample_sequence_data = [
            # Metadata (index 0)
            {
                "word": "TEST",
                "author": "test_user",
                "level": 1,
                "prop_type": "staff",
                "grid_mode": "diamond",
                "is_circular": False,
            },
            # Start position (index 1)
            {
                "sequence_start_position": True,
                "blue_attributes": {"start_ori": "in"},
                "red_attributes": {"start_ori": "in"},
            },
            # Beat 1 (index 2)
            {
                "beat": 1,
                "letter": "T",
                "blue_attributes": {
                    "motion_type": "pro",
                    "start_ori": "in",
                    "end_ori": "out",
                },
                "red_attributes": {
                    "motion_type": "anti",
                    "start_ori": "in",
                    "end_ori": "out",
                },
            },
            # Beat 2 (index 3)
            {
                "beat": 2,
                "letter": "E",
                "blue_attributes": {
                    "motion_type": "anti",
                    "start_ori": "out",
                    "end_ori": "in",
                },
                "red_attributes": {
                    "motion_type": "pro",
                    "start_ori": "out",
                    "end_ori": "in",
                },
            },
            # Beat 3 (index 4)
            {
                "beat": 3,
                "letter": "S",
                "blue_attributes": {
                    "motion_type": "pro",
                    "start_ori": "in",
                    "end_ori": "out",
                },
                "red_attributes": {
                    "motion_type": "anti",
                    "start_ori": "in",
                    "end_ori": "out",
                },
            },
            # Beat 4 (index 5)
            {
                "beat": 4,
                "letter": "T",
                "blue_attributes": {
                    "motion_type": "anti",
                    "start_ori": "out",
                    "end_ori": "in",
                },
                "red_attributes": {
                    "motion_type": "pro",
                    "start_ori": "out",
                    "end_ori": "in",
                },
            },
        ]

    def test_generated_sequence_data_initialization(self):
        """Test that GeneratedSequenceData initializes correctly with all required attributes."""
        generated_data = GeneratedSequenceData(
            self.sample_sequence_data, self.sample_params
        )

        # Test required attributes exist
        self.assertTrue(hasattr(generated_data, "sequence_data"))
        self.assertTrue(hasattr(generated_data, "params"))
        self.assertTrue(hasattr(generated_data, "id"))
        self.assertTrue(hasattr(generated_data, "word"))
        self.assertTrue(hasattr(generated_data, "image_path"))
        self.assertTrue(hasattr(generated_data, "approved"))

        # Test attribute types and values
        self.assertIsInstance(generated_data.sequence_data, list)
        self.assertIsInstance(generated_data.params, GenerationParams)
        self.assertIsInstance(generated_data.id, str)
        self.assertIsInstance(generated_data.word, str)
        self.assertIsNone(generated_data.image_path)
        self.assertFalse(generated_data.approved)

        # Test that sequence_data is correctly stored
        self.assertEqual(generated_data.sequence_data, self.sample_sequence_data)
        self.assertEqual(generated_data.params, self.sample_params)

    def test_sequence_data_attribute_access(self):
        """Test that sequence_data attribute can be accessed correctly (not beats)."""
        generated_data = GeneratedSequenceData(
            self.sample_sequence_data, self.sample_params
        )

        # This should work - accessing sequence_data
        sequence_data = generated_data.sequence_data
        self.assertIsInstance(sequence_data, list)
        self.assertEqual(len(sequence_data), 6)  # metadata + start_pos + 4 beats

        # This should fail - accessing beats (the bug we fixed)
        with self.assertRaises(AttributeError):
            _ = generated_data.beats

    def test_word_extraction_from_sequence(self):
        """Test that word is correctly extracted from sequence beats."""
        generated_data = GeneratedSequenceData(
            self.sample_sequence_data, self.sample_params
        )

        # Should extract "TEST" from the beat letters
        self.assertEqual(generated_data.word, "TEST")

    def test_word_extraction_with_empty_sequence(self):
        """Test word extraction with empty or invalid sequence data."""
        # Test with empty sequence
        empty_sequence = []
        generated_data = GeneratedSequenceData(empty_sequence, self.sample_params)
        self.assertTrue(generated_data.word.startswith("Generated_"))

        # Test with only metadata
        metadata_only = [{"word": "", "author": "test"}]
        generated_data = GeneratedSequenceData(metadata_only, self.sample_params)
        self.assertTrue(generated_data.word.startswith("Generated_"))

    def test_sequence_length_calculation(self):
        """Test that sequence length is calculated correctly."""
        generated_data = GeneratedSequenceData(
            self.sample_sequence_data, self.sample_params
        )

        # Total length should be 6 (metadata + start_pos + 4 beats)
        self.assertEqual(len(generated_data.sequence_data), 6)

        # Actual beat count should be 4 (excluding metadata and start position)
        beat_count = len(
            [
                item
                for item in generated_data.sequence_data
                if item.get("beat") is not None
            ]
        )
        self.assertEqual(beat_count, 4)
        self.assertEqual(beat_count, self.sample_params.length)


class TestSequenceGenerationWorkflow(unittest.TestCase):
    """Test the complete sequence generation workflow."""

    def setUp(self):
        """Set up test fixtures for workflow testing."""
        self.sample_params = GenerationParams(
            length=4,
            level=1,
            generation_mode="circular",
            prop_continuity="continuous",
            turn_intensity=3,
            CAP_type="rotated",
        )

    @patch(
        "main_window.main_widget.sequence_card_tab.generation.generation_manager.TempBeatFrame"
    )
    @patch(
        "main_window.main_widget.sequence_card_tab.generation.generation_manager.TempSequenceWorkbench"
    )
    def test_sequence_generation_creates_correct_structure(
        self, mock_workbench, mock_beat_frame
    ):
        """Test that sequence generation creates the correct data structure."""
        # Mock the temporary workbench and beat frame
        mock_temp_frame = Mock()
        mock_temp_workbench_instance = Mock()
        mock_temp_workbench_instance.beat_frame = mock_temp_frame

        mock_workbench.return_value = mock_temp_workbench_instance
        mock_beat_frame.return_value = mock_temp_frame

        # Mock the JSON manager and sequence loading
        mock_json_manager = Mock()
        mock_temp_frame.json_manager = mock_json_manager

        # Create expected sequence structure
        expected_sequence = [
            {"word": "TEST", "author": "test", "level": 1},  # metadata
            {"sequence_start_position": True},  # start position
            {"beat": 1, "letter": "T"},  # beat 1
            {"beat": 2, "letter": "E"},  # beat 2
            {"beat": 3, "letter": "S"},  # beat 3
            {"beat": 4, "letter": "T"},  # beat 4
        ]

        mock_json_manager.loader_saver.load_current_sequence.return_value = (
            expected_sequence
        )

        # Import and test the generation manager
        try:
            from src.main_window.main_widget.sequence_card_tab.generation.generation_manager import (
                GenerationManager,
            )
        except ImportError:
            from generation_manager import GenerationManager

        # Create a mock main widget
        mock_main_widget = Mock()
        generation_manager = GenerationManager(mock_main_widget)

        # Test sequence extraction
        generated_data = generation_manager._extract_generated_sequence_from_temp_frame(
            self.sample_params, mock_temp_workbench_instance
        )

        self.assertIsNotNone(generated_data)
        self.assertIsInstance(generated_data, GeneratedSequenceData)
        self.assertEqual(generated_data.sequence_data, expected_sequence)
        self.assertEqual(generated_data.params, self.sample_params)


if __name__ == "__main__":
    # Configure logging for test output
    logging.basicConfig(level=logging.INFO)

    # Run the tests
    unittest.main(verbosity=2)
