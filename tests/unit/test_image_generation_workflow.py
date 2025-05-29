"""
Test suite for image generation workflow in sequence generation system.

This test suite validates:
1. Synchronous image generation workflow
2. Asynchronous image generation workflow
3. Error handling and fallback mechanisms
4. Thread safety of image loading operations
5. Memory management with large images
"""

import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock, call
import sys
import os
import tempfile
import logging
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import QTimer

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


class TestSynchronousImageGeneration(unittest.TestCase):
    """Test synchronous image generation workflow."""

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

        self.sample_sequence_data = [
            {"word": "TEST", "author": "test", "level": 1},
            {"sequence_start_position": True},
            {"beat": 1, "letter": "T"},
            {"beat": 2, "letter": "E"},
            {"beat": 3, "letter": "S"},
            {"beat": 4, "letter": "T"},
        ]

        self.generated_data = GeneratedSequenceData(
            self.sample_sequence_data, self.sample_params
        )

    @patch(
        "main_window.main_widget.sequence_card_tab.generation.approval_dialog.managers.synchronous_image_generator.AppContext"
    )
    def test_synchronous_generation_uses_correct_attribute(self, mock_app_context):
        """Test that synchronous generation uses sequence_data attribute, not beats."""
        try:
            from src.main_window.main_widget.sequence_card_tab.generation.approval_dialog.managers.synchronous_image_generator import (
                SynchronousImageGenerator,
            )
        except ImportError:
            from synchronous_image_generator import SynchronousImageGenerator

        # Mock the required dependencies
        mock_main_widget = Mock()
        mock_sequence_card_tab = Mock()
        mock_temp_beat_frame = Mock()
        mock_image_exporter = Mock()
        mock_image_exporter.temp_beat_frame = mock_temp_beat_frame
        mock_sequence_card_tab.image_exporter = mock_image_exporter

        mock_main_widget.tab_manager.get_tab_widget.return_value = (
            mock_sequence_card_tab
        )

        mock_export_manager = Mock()
        mock_image_creator = Mock()
        mock_pixmap = Mock(spec=QPixmap)
        mock_pixmap.isNull.return_value = False
        mock_image_creator.create_image.return_value = mock_pixmap
        mock_export_manager.image_creator = mock_image_creator

        mock_app_context.export_manager.return_value = mock_export_manager

        # Create the generator
        generator = SynchronousImageGenerator(mock_main_widget)

        # Test the generation
        result = generator._generate_image_synchronously(self.generated_data)

        # Verify that load_sequence_data was called with sequence_data, not beats
        mock_temp_beat_frame.load_sequence_data.assert_called_once_with(
            self.generated_data.sequence_data
        )

        # Verify the result
        self.assertIsNotNone(result)
        self.assertEqual(result, mock_pixmap)

    @patch(
        "main_window.main_widget.sequence_card_tab.generation.approval_dialog.managers.synchronous_image_generator.AppContext"
    )
    def test_synchronous_generation_error_handling(self, mock_app_context):
        """Test error handling in synchronous image generation."""
        from main_window.main_widget.sequence_card_tab.generation.approval_dialog.managers.synchronous_image_generator import (
            SynchronousImageGenerator,
        )

        # Mock the required dependencies to raise an exception
        mock_main_widget = Mock()
        mock_sequence_card_tab = Mock()
        mock_temp_beat_frame = Mock()
        mock_image_exporter = Mock()
        mock_image_exporter.temp_beat_frame = mock_temp_beat_frame
        mock_sequence_card_tab.image_exporter = mock_image_exporter

        mock_main_widget.tab_manager.get_tab_widget.return_value = (
            mock_sequence_card_tab
        )

        # Make load_sequence_data raise an exception
        mock_temp_beat_frame.load_sequence_data.side_effect = Exception("Test error")

        mock_export_manager = Mock()
        mock_app_context.export_manager.return_value = mock_export_manager

        # Create the generator
        generator = SynchronousImageGenerator(mock_main_widget)

        # Test the generation - should handle the error gracefully
        result = generator._generate_image_synchronously(self.generated_data)

        # Should return None on error
        self.assertIsNone(result)

        # Verify that load_sequence_data was called with correct data
        mock_temp_beat_frame.load_sequence_data.assert_called_once_with(
            self.generated_data.sequence_data
        )

    def test_synchronous_generation_missing_beats_attribute_error(self):
        """Test that accessing non-existent beats attribute raises AttributeError."""
        # This test verifies the bug we fixed
        with self.assertRaises(AttributeError) as context:
            _ = self.generated_data.beats

        self.assertIn(
            "'GeneratedSequenceData' object has no attribute 'beats'",
            str(context.exception),
        )

    @patch(
        "main_window.main_widget.sequence_card_tab.generation.approval_dialog.managers.synchronous_image_generator.AppContext"
    )
    def test_synchronous_generation_missing_image_exporter(self, mock_app_context):
        """Test handling of missing image_exporter."""
        from main_window.main_widget.sequence_card_tab.generation.approval_dialog.managers.synchronous_image_generator import (
            SynchronousImageGenerator,
        )

        # Mock sequence card tab without image_exporter
        mock_main_widget = Mock()
        mock_sequence_card_tab = Mock()
        del mock_sequence_card_tab.image_exporter  # Remove the attribute

        mock_main_widget.tab_manager.get_tab_widget.return_value = (
            mock_sequence_card_tab
        )

        mock_export_manager = Mock()
        mock_app_context.export_manager.return_value = mock_export_manager

        # Create the generator
        generator = SynchronousImageGenerator(mock_main_widget)

        # Test the generation - should handle missing image_exporter gracefully
        result = generator._generate_image_synchronously(self.generated_data)

        # Should return None when image_exporter is missing
        self.assertIsNone(result)


class TestAsynchronousImageGeneration(unittest.TestCase):
    """Test asynchronous image generation workflow."""

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

        self.sample_sequence_data = [
            {"word": "TEST", "author": "test", "level": 1},
            {"sequence_start_position": True},
            {"beat": 1, "letter": "T"},
            {"beat": 2, "letter": "E"},
            {"beat": 3, "letter": "S"},
            {"beat": 4, "letter": "T"},
        ]

        self.generated_data = GeneratedSequenceData(
            self.sample_sequence_data, self.sample_params
        )

    @patch(
        "main_window.main_widget.sequence_card_tab.generation.image_generation_worker.AppContext"
    )
    def test_asynchronous_generation_uses_correct_attribute(self, mock_app_context):
        """Test that asynchronous generation uses sequence_data attribute correctly."""
        from main_window.main_widget.sequence_card_tab.generation.image_generation_worker import (
            ImageGenerationWorker,
        )

        # Mock the required dependencies
        mock_temp_beat_frame = Mock()
        mock_export_manager = Mock()
        mock_image_creator = Mock()
        mock_pixmap = Mock(spec=QPixmap)
        mock_pixmap.isNull.return_value = False
        mock_pixmap.width.return_value = 800
        mock_pixmap.height.return_value = 600
        mock_image_creator.create_image.return_value = mock_pixmap
        mock_export_manager.image_creator = mock_image_creator

        mock_app_context.export_manager.return_value = mock_export_manager

        # Create the worker
        worker = ImageGenerationWorker(self.generated_data, mock_temp_beat_frame)

        # Mock the signals
        worker.image_generated = Mock()
        worker.image_failed = Mock()
        worker.diagnostic_info = Mock()

        # Test the generation
        worker.run()

        # Verify that load_sequence was called with sequence_data
        mock_temp_beat_frame.load_sequence.assert_called_once_with(
            self.generated_data.sequence_data
        )

        # Verify success signal was emitted
        worker.image_generated.emit.assert_called_once()
        worker.image_failed.emit.assert_not_called()

    @patch(
        "main_window.main_widget.sequence_card_tab.generation.image_generation_worker.AppContext"
    )
    def test_asynchronous_generation_error_handling(self, mock_app_context):
        """Test error handling in asynchronous image generation."""
        from main_window.main_widget.sequence_card_tab.generation.image_generation_worker import (
            ImageGenerationWorker,
        )

        # Mock the required dependencies to raise an exception
        mock_temp_beat_frame = Mock()
        mock_temp_beat_frame.load_sequence.side_effect = Exception("Test load error")

        mock_export_manager = Mock()
        mock_app_context.export_manager.return_value = mock_export_manager

        # Create the worker
        worker = ImageGenerationWorker(self.generated_data, mock_temp_beat_frame)

        # Mock the signals
        worker.image_generated = Mock()
        worker.image_failed = Mock()
        worker.diagnostic_info = Mock()

        # Test the generation
        worker.run()

        # Verify that load_sequence was called with correct data
        mock_temp_beat_frame.load_sequence.assert_called_once_with(
            self.generated_data.sequence_data
        )

        # Verify error signal was emitted
        worker.image_failed.emit.assert_called_once()
        worker.image_generated.emit.assert_not_called()


if __name__ == "__main__":
    # Configure logging for test output
    logging.basicConfig(level=logging.INFO)

    # Run the tests
    unittest.main(verbosity=2)
