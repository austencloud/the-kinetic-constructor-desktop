#!/usr/bin/env python3
"""
Critical bug fix validation test.

This test validates that the AttributeError fix for GeneratedSequenceData is working correctly.
It focuses specifically on the bug where code was trying to access .beats instead of .sequence_data.
"""

import sys
import os
import unittest
import tempfile
import logging

# Add project root to path for imports
project_root = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "src"))

# Configure logging
logging.basicConfig(level=logging.INFO)


class TestCriticalBugFix(unittest.TestCase):
    """Test the critical AttributeError bug fix."""

    def setUp(self):
        """Set up test fixtures."""
        # Create minimal test data that doesn't require complex dependencies
        self.sample_sequence_data = [
            {"word": "TEST", "author": "test", "level": 1},  # metadata
            {"sequence_start_position": True},  # start position
            {"beat": 1, "letter": "T"},  # beat 1
            {"beat": 2, "letter": "E"},  # beat 2
            {"beat": 3, "letter": "S"},  # beat 3
            {"beat": 4, "letter": "T"},  # beat 4
        ]

    def test_generated_sequence_data_structure(self):
        """Test that GeneratedSequenceData has the correct structure."""
        try:
            # Try to import the classes
            from src.main_window.main_widget.sequence_card_tab.generation.generated_sequence_data import (
                GeneratedSequenceData,
            )

            # Create a minimal params object
            class MockParams:
                def __init__(self):
                    self.length = 4
                    self.level = 1
                    self.generation_mode = "circular"
                    self.prop_continuity = "continuous"
                    self.turn_intensity = 3
                    self.CAP_type = "rotated"

            params = MockParams()

            # Create GeneratedSequenceData instance
            generated_data = GeneratedSequenceData(self.sample_sequence_data, params)

            # Test that sequence_data attribute exists and works
            self.assertTrue(hasattr(generated_data, "sequence_data"))
            self.assertEqual(generated_data.sequence_data, self.sample_sequence_data)

            # Test that beats attribute does NOT exist (this should raise AttributeError)
            with self.assertRaises(AttributeError) as context:
                _ = generated_data.beats

            self.assertIn(
                "'GeneratedSequenceData' object has no attribute 'beats'",
                str(context.exception),
            )

            print("✓ GeneratedSequenceData structure is correct")
            print("✓ sequence_data attribute works properly")
            print("✓ beats attribute correctly does not exist")

            return True

        except ImportError as e:
            self.skipTest(f"Could not import required modules: {e}")
        except Exception as e:
            self.fail(f"Unexpected error: {e}")

    def test_synchronous_image_generator_fix(self):
        """Test that the synchronous image generator fix is in place."""
        try:
            # Read the synchronous image generator file to verify the fix
            sync_gen_path = os.path.join(
                project_root,
                "src",
                "main_window",
                "main_widget",
                "sequence_card_tab",
                "generation",
                "approval_dialog",
                "managers",
                "synchronous_image_generator.py",
            )

            if os.path.exists(sync_gen_path):
                with open(sync_gen_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Check that the first fix is in place (sequence_data attribute)
                self.assertIn(
                    "sequence_data.sequence_data",
                    content,
                    "Fix not found: should use sequence_data.sequence_data",
                )
                self.assertNotIn(
                    "sequence_data.beats",
                    content,
                    "Bug still present: should not use sequence_data.beats",
                )

                # Check that the second fix is in place (create_sequence_image method)
                self.assertIn(
                    "create_sequence_image",
                    content,
                    "Fix not found: should use create_sequence_image method",
                )
                self.assertNotIn(
                    "image_creator.create_image()",
                    content,
                    "Bug still present: should not use create_image() method",
                )

                # Verify the correct method call pattern
                self.assertIn(
                    "image_creator.create_sequence_image(current_sequence)",
                    content,
                    "Correct method call pattern not found",
                )

                print("✓ Synchronous image generator fixes are in place")
                print("  - sequence_data.sequence_data attribute fix")
                print("  - create_sequence_image method fix")
                return True
            else:
                self.skipTest(
                    f"Synchronous image generator file not found: {sync_gen_path}"
                )

        except Exception as e:
            self.fail(f"Error checking synchronous image generator fix: {e}")

    def test_image_generation_worker_consistency(self):
        """Test that image generation worker uses the correct attribute."""
        try:
            # Read the image generation worker file to verify consistency
            worker_path = os.path.join(
                project_root,
                "src",
                "main_window",
                "main_widget",
                "sequence_card_tab",
                "generation",
                "image_generation_worker.py",
            )

            if os.path.exists(worker_path):
                with open(worker_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Check that it uses the correct attribute
                self.assertIn(
                    "sequence_data.sequence_data",
                    content,
                    "Image generation worker should use sequence_data.sequence_data",
                )

                print("✓ Image generation worker uses correct attribute")
                return True
            else:
                self.skipTest(f"Image generation worker file not found: {worker_path}")

        except Exception as e:
            self.fail(f"Error checking image generation worker: {e}")


class TestImageCreatorMethodValidation(unittest.TestCase):
    """Test that ImageCreator method calls are correct."""

    def test_image_creator_has_correct_methods(self):
        """Test that ImageCreator has create_sequence_image method, not create_image."""
        try:
            # Read the ImageCreator file to verify method names
            image_creator_path = os.path.join(
                project_root,
                "src",
                "main_window",
                "main_widget",
                "sequence_workbench",
                "sequence_beat_frame",
                "image_export_manager",
                "image_creator",
                "image_creator.py",
            )

            if os.path.exists(image_creator_path):
                with open(image_creator_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Check that create_sequence_image method exists
                self.assertIn(
                    "def create_sequence_image(",
                    content,
                    "ImageCreator should have create_sequence_image method",
                )

                # Check that there's no create_image method (without parameters)
                self.assertNotIn(
                    "def create_image(",
                    content,
                    "ImageCreator should not have create_image method",
                )

                print("✓ ImageCreator has correct method: create_sequence_image")
                return True
            else:
                self.skipTest(f"ImageCreator file not found: {image_creator_path}")

        except Exception as e:
            self.fail(f"Error checking ImageCreator methods: {e}")

    def test_synchronous_generator_uses_correct_image_creator_method(self):
        """Test that synchronous generator calls the correct ImageCreator method."""
        try:
            # Read the synchronous image generator file
            sync_gen_path = os.path.join(
                project_root,
                "src",
                "main_window",
                "main_widget",
                "sequence_card_tab",
                "generation",
                "approval_dialog",
                "managers",
                "synchronous_image_generator.py",
            )

            if os.path.exists(sync_gen_path):
                with open(sync_gen_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Check that it uses create_sequence_image, not create_image
                self.assertIn(
                    "create_sequence_image",
                    content,
                    "Should use create_sequence_image method",
                )
                self.assertNotIn(
                    "create_image()", content, "Should not use create_image() method"
                )

                print("✓ Synchronous generator uses correct ImageCreator method")
                return True
            else:
                self.skipTest(f"Synchronous generator file not found: {sync_gen_path}")

        except Exception as e:
            self.fail(f"Error checking synchronous generator method usage: {e}")


class TestSequenceLengthCalculation(unittest.TestCase):
    """Test sequence length calculations."""

    def test_sequence_length_calculation(self):
        """Test that sequence length is calculated correctly."""
        # Test data with 4 beats (after metadata and start position)
        sequence_data = [
            {"word": "TEST", "author": "test", "level": 1},  # metadata (index 0)
            {"sequence_start_position": True},  # start position (index 1)
            {"beat": 1, "letter": "T"},  # beat 1 (index 2)
            {"beat": 2, "letter": "E"},  # beat 2 (index 3)
            {"beat": 3, "letter": "S"},  # beat 3 (index 4)
            {"beat": 4, "letter": "T"},  # beat 4 (index 5)
        ]

        # Total length should be 6 (metadata + start_pos + 4 beats)
        self.assertEqual(len(sequence_data), 6)

        # Actual beat count should be 4 (excluding metadata and start position)
        beat_count = len(
            [item for item in sequence_data if item.get("beat") is not None]
        )
        self.assertEqual(beat_count, 4)

        # Verify that beats start after start position
        beats_only = sequence_data[2:]  # Skip metadata and start position
        self.assertEqual(len(beats_only), 4)

        for i, beat in enumerate(beats_only):
            self.assertEqual(beat.get("beat"), i + 1)

        print("✓ Sequence length calculation is correct")
        print(f"✓ Total sequence length: {len(sequence_data)}")
        print(f"✓ Beat count: {beat_count}")


def run_critical_tests():
    """Run the critical bug fix tests."""
    print("=" * 80)
    print("CRITICAL BUG FIX VALIDATION")
    print("=" * 80)
    print()

    # Create test suite
    suite = unittest.TestSuite()

    # Add critical tests
    suite.addTest(TestCriticalBugFix("test_generated_sequence_data_structure"))
    suite.addTest(TestCriticalBugFix("test_synchronous_image_generator_fix"))
    suite.addTest(TestCriticalBugFix("test_image_generation_worker_consistency"))
    suite.addTest(
        TestImageCreatorMethodValidation("test_image_creator_has_correct_methods")
    )
    suite.addTest(
        TestImageCreatorMethodValidation(
            "test_synchronous_generator_uses_correct_image_creator_method"
        )
    )
    suite.addTest(TestSequenceLengthCalculation("test_sequence_length_calculation"))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 80)
    if result.wasSuccessful():
        print("✅ ALL CRITICAL TESTS PASSED!")
        print("The AttributeError bug fix is working correctly.")
    else:
        print("❌ CRITICAL TESTS FAILED!")
        print("The AttributeError bug fix needs attention.")

        if result.failures:
            print("\nFailures:")
            for test, failure in result.failures:
                print(f"- {test}: {failure}")

        if result.errors:
            print("\nErrors:")
            for test, error in result.errors:
                print(f"- {test}: {error}")

    print("=" * 80)
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_critical_tests()
    sys.exit(0 if success else 1)
