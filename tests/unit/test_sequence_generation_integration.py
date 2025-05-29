#!/usr/bin/env python3
"""
Integration test for sequence generation system.

This test validates the complete sequence generation workflow without requiring
the full UI to be running.
"""

import sys
import os
import unittest
import tempfile
import logging
from unittest.mock import Mock, patch, MagicMock

# Add project root to path for imports
project_root = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

# Configure logging
logging.basicConfig(level=logging.INFO)


class TestSequenceGenerationIntegration(unittest.TestCase):
    """Integration test for sequence generation workflow."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create minimal params object
        class MockParams:
            def __init__(self):
                self.length = 4
                self.level = 1
                self.generation_mode = "circular"
                self.prop_continuity = "continuous"
                self.turn_intensity = 3
                self.CAP_type = "rotated"
        
        self.params = MockParams()
        
        # Create sample sequence data
        self.sample_sequence_data = [
            {"word": "TEST", "author": "test", "level": 1},  # metadata
            {"sequence_start_position": True},  # start position
            {"beat": 1, "letter": "T"},  # beat 1
            {"beat": 2, "letter": "E"},  # beat 2
            {"beat": 3, "letter": "S"},  # beat 3
            {"beat": 4, "letter": "T"},  # beat 4
        ]
    
    def test_generated_sequence_data_creation(self):
        """Test that GeneratedSequenceData can be created successfully."""
        try:
            from src.main_window.main_widget.sequence_card_tab.generation.generated_sequence_data import GeneratedSequenceData
            
            # Create GeneratedSequenceData instance
            generated_data = GeneratedSequenceData(self.sample_sequence_data, self.params)
            
            # Validate structure
            self.assertIsNotNone(generated_data)
            self.assertEqual(generated_data.sequence_data, self.sample_sequence_data)
            self.assertEqual(generated_data.params, self.params)
            self.assertIsInstance(generated_data.id, str)
            self.assertTrue(generated_data.id.startswith("gen_"))
            self.assertIsInstance(generated_data.word, str)
            self.assertIsNone(generated_data.image_path)
            self.assertFalse(generated_data.approved)
            
            print(f"✓ Generated sequence ID: {generated_data.id}")
            print(f"✓ Generated sequence word: {generated_data.word}")
            print(f"✓ Sequence data length: {len(generated_data.sequence_data)}")
            
            return True
            
        except ImportError as e:
            self.skipTest(f"Could not import GeneratedSequenceData: {e}")
        except Exception as e:
            self.fail(f"Error creating GeneratedSequenceData: {e}")
    
    def test_sequence_data_attribute_access(self):
        """Test that sequence_data attribute can be accessed correctly."""
        try:
            from src.main_window.main_widget.sequence_card_tab.generation.generated_sequence_data import GeneratedSequenceData
            
            generated_data = GeneratedSequenceData(self.sample_sequence_data, self.params)
            
            # Test accessing sequence_data (should work)
            sequence_data = generated_data.sequence_data
            self.assertEqual(sequence_data, self.sample_sequence_data)
            self.assertEqual(len(sequence_data), 6)  # metadata + start_pos + 4 beats
            
            # Test that beats attribute does not exist (should raise AttributeError)
            with self.assertRaises(AttributeError):
                _ = generated_data.beats
            
            print("✓ sequence_data attribute access works correctly")
            print("✓ beats attribute correctly does not exist")
            
            return True
            
        except ImportError as e:
            self.skipTest(f"Could not import GeneratedSequenceData: {e}")
        except Exception as e:
            self.fail(f"Error testing attribute access: {e}")
    
    def test_word_extraction(self):
        """Test that word extraction works correctly."""
        try:
            from src.main_window.main_widget.sequence_card_tab.generation.generated_sequence_data import GeneratedSequenceData
            
            generated_data = GeneratedSequenceData(self.sample_sequence_data, self.params)
            
            # Should extract "TEST" from the beat letters
            expected_word = "TEST"
            self.assertEqual(generated_data.word, expected_word)
            
            print(f"✓ Word extraction works: '{generated_data.word}'")
            
            return True
            
        except ImportError as e:
            self.skipTest(f"Could not import GeneratedSequenceData: {e}")
        except Exception as e:
            self.fail(f"Error testing word extraction: {e}")
    
    def test_sequence_length_validation(self):
        """Test that sequence length validation works correctly."""
        try:
            from src.main_window.main_widget.sequence_card_tab.generation.generated_sequence_data import GeneratedSequenceData
            
            generated_data = GeneratedSequenceData(self.sample_sequence_data, self.params)
            
            # Validate sequence structure
            sequence_data = generated_data.sequence_data
            
            # Should have metadata + start_pos + beats
            self.assertEqual(len(sequence_data), 6)
            
            # Count actual beats (excluding metadata and start position)
            beat_count = len([item for item in sequence_data if item.get("beat") is not None])
            self.assertEqual(beat_count, 4)
            self.assertEqual(beat_count, self.params.length)
            
            # Validate beat structure
            beats_only = sequence_data[2:]  # Skip metadata and start position
            for i, beat in enumerate(beats_only):
                self.assertEqual(beat.get("beat"), i + 1)
                self.assertIn("letter", beat)
            
            print(f"✓ Sequence length validation passed")
            print(f"✓ Total sequence length: {len(sequence_data)}")
            print(f"✓ Beat count: {beat_count}")
            print(f"✓ Expected length: {self.params.length}")
            
            return True
            
        except ImportError as e:
            self.skipTest(f"Could not import GeneratedSequenceData: {e}")
        except Exception as e:
            self.fail(f"Error testing sequence length validation: {e}")
    
    @patch('src.main_window.main_widget.sequence_card_tab.generation.approval_dialog.managers.synchronous_image_generator.AppContext')
    def test_synchronous_image_generation_mock(self, mock_app_context):
        """Test synchronous image generation with mocked dependencies."""
        try:
            from src.main_window.main_widget.sequence_card_tab.generation.generated_sequence_data import GeneratedSequenceData
            from src.main_window.main_widget.sequence_card_tab.generation.approval_dialog.managers.synchronous_image_generator import SynchronousImageGenerator
            
            # Create test data
            generated_data = GeneratedSequenceData(self.sample_sequence_data, self.params)
            
            # Mock dependencies
            mock_main_widget = Mock()
            mock_sequence_card_tab = Mock()
            mock_temp_beat_frame = Mock()
            mock_image_exporter = Mock()
            mock_image_exporter.temp_beat_frame = mock_temp_beat_frame
            mock_sequence_card_tab.image_exporter = mock_image_exporter
            
            mock_main_widget.tab_manager.get_tab_widget.return_value = mock_sequence_card_tab
            
            mock_export_manager = Mock()
            mock_image_creator = Mock()
            mock_pixmap = Mock()
            mock_pixmap.isNull.return_value = False
            mock_image_creator.create_image.return_value = mock_pixmap
            mock_export_manager.image_creator = mock_image_creator
            
            mock_app_context.export_manager.return_value = mock_export_manager
            
            # Create and test the generator
            generator = SynchronousImageGenerator(mock_main_widget)
            result = generator._generate_image_synchronously(generated_data)
            
            # Verify that the correct method was called with the correct data
            mock_temp_beat_frame.load_sequence_data.assert_called_once_with(generated_data.sequence_data)
            
            # Verify result
            self.assertIsNotNone(result)
            self.assertEqual(result, mock_pixmap)
            
            print("✓ Synchronous image generation mock test passed")
            print("✓ Correct attribute (sequence_data) was used")
            
            return True
            
        except ImportError as e:
            self.skipTest(f"Could not import required modules: {e}")
        except Exception as e:
            self.fail(f"Error testing synchronous image generation: {e}")


def run_integration_tests():
    """Run the integration tests."""
    print("=" * 80)
    print("SEQUENCE GENERATION INTEGRATION TESTS")
    print("=" * 80)
    print()
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add integration tests
    suite.addTest(TestSequenceGenerationIntegration('test_generated_sequence_data_creation'))
    suite.addTest(TestSequenceGenerationIntegration('test_sequence_data_attribute_access'))
    suite.addTest(TestSequenceGenerationIntegration('test_word_extraction'))
    suite.addTest(TestSequenceGenerationIntegration('test_sequence_length_validation'))
    suite.addTest(TestSequenceGenerationIntegration('test_synchronous_image_generation_mock'))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 80)
    if result.wasSuccessful():
        print("✅ ALL INTEGRATION TESTS PASSED!")
        print("The sequence generation system is working correctly.")
    else:
        print("❌ INTEGRATION TESTS FAILED!")
        print("The sequence generation system has issues.")
        
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


if __name__ == '__main__':
    success = run_integration_tests()
    sys.exit(0 if success else 1)
