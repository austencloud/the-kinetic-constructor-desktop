"""
Test for ExportCoordinator to verify the export coordination functionality.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
from PyQt6.QtWidgets import QApplication
import sys

# Ensure QApplication exists for testing
if not QApplication.instance():
    app = QApplication(sys.argv)

from .export_coordinator import ExportCoordinator


class TestExportCoordinator(unittest.TestCase):
    """Test the ExportCoordinator functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.exporter = Mock()
        self.exporter.metadata_extractor = Mock()
        
        self.coordinator = ExportCoordinator(self.exporter)
    
    def test_initialization(self):
        """Test that the coordinator initializes correctly."""
        self.assertEqual(self.coordinator.exporter, self.exporter)
        self.assertIsNotNone(self.coordinator.image_converter)
        self.assertIsNotNone(self.coordinator.batch_processor)
        self.assertIsNotNone(self.coordinator.cache_manager)
        self.assertIsNotNone(self.coordinator.memory_manager)
        self.assertIsNotNone(self.coordinator.file_operations)
        
        # Verify statistics are initialized
        self.assertEqual(self.coordinator.stats["processed_sequences"], 0)
        self.assertEqual(self.coordinator.stats["regenerated_count"], 0)
        self.assertEqual(self.coordinator.stats["skipped_count"], 0)
        self.assertEqual(self.coordinator.stats["failed_count"], 0)
    
    def test_export_all_images_success(self):
        """Test successful export coordination."""
        # Mock component methods
        self.coordinator._setup_export_environment = Mock(return_value={"test": "config"})
        self.coordinator._discover_sequences = Mock(return_value=[("word1", "seq1.png")])
        self.coordinator._process_sequences_in_batches = Mock()
        self.coordinator._finalize_export = Mock()
        
        result = self.coordinator.export_all_images()
        
        # Verify all phases were called
        self.coordinator._setup_export_environment.assert_called_once()
        self.coordinator._discover_sequences.assert_called_once()
        self.coordinator._process_sequences_in_batches.assert_called_once()
        self.coordinator._finalize_export.assert_called_once()
        
        # Verify result structure
        self.assertTrue(result["success"])
        self.assertIn("statistics", result)
        self.assertIn("message", result)
    
    def test_export_all_images_setup_failure(self):
        """Test export failure during setup."""
        self.coordinator._setup_export_environment = Mock(return_value=None)
        
        result = self.coordinator.export_all_images()
        
        # Verify failure result
        self.assertFalse(result["success"])
        self.assertIn("error", result)
        self.assertEqual(result["error"], "Failed to setup export environment")
    
    def test_export_all_images_no_sequences(self):
        """Test export when no sequences are found."""
        self.coordinator._setup_export_environment = Mock(return_value={"test": "config"})
        self.coordinator._discover_sequences = Mock(return_value=[])
        
        result = self.coordinator.export_all_images()
        
        # Verify failure result
        self.assertFalse(result["success"])
        self.assertIn("error", result)
        self.assertEqual(result["error"], "No sequences found to export")
    
    def test_delegation_methods(self):
        """Test delegation methods for backward compatibility."""
        # Mock component methods
        self.coordinator.image_converter.convert_qimage_to_pil = Mock(return_value="converted_image")
        self.coordinator.cache_manager.needs_regeneration = Mock(return_value=(True, "reason"))
        self.coordinator.memory_manager.get_current_usage = Mock(return_value=1024.0)
        self.coordinator.memory_manager.force_cleanup = Mock()
        self.coordinator.batch_processor.cancel_processing = Mock()
        
        # Test delegation
        from PyQt6.QtGui import QImage
        test_qimage = QImage(100, 100, QImage.Format.Format_ARGB32)
        
        result = self.coordinator.convert_qimage_to_pil(test_qimage, 2000)
        self.assertEqual(result, "converted_image")
        self.coordinator.image_converter.convert_qimage_to_pil.assert_called_with(test_qimage, 2000)
        
        result = self.coordinator.check_regeneration_needed("source", "output")
        self.assertEqual(result, (True, "reason"))
        self.coordinator.cache_manager.needs_regeneration.assert_called_with("source", "output")
        
        result = self.coordinator.get_memory_usage()
        self.assertEqual(result, 1024.0)
        self.coordinator.memory_manager.get_current_usage.assert_called_once()
        
        self.coordinator.force_memory_cleanup()
        self.coordinator.memory_manager.force_cleanup.assert_called_once()
        
        self.coordinator.cancel_export()
        self.coordinator.batch_processor.cancel_processing.assert_called_once()
    
    def test_get_export_statistics(self):
        """Test getting export statistics."""
        self.coordinator.stats["processed_sequences"] = 10
        self.coordinator.stats["regenerated_count"] = 5
        
        stats = self.coordinator.get_export_statistics()
        
        self.assertEqual(stats["processed_sequences"], 10)
        self.assertEqual(stats["regenerated_count"], 5)
    
    def test_get_performance_stats(self):
        """Test getting performance statistics from all components."""
        # Mock component stats
        self.coordinator.memory_manager.get_stats = Mock(return_value={"memory": "stats"})
        self.coordinator.batch_processor.get_stats = Mock(return_value={"batch": "stats"})
        self.coordinator.cache_manager.get_stats = Mock(return_value={"cache": "stats"})
        self.coordinator.file_operations.get_stats = Mock(return_value={"file": "stats"})
        self.coordinator.image_converter.get_stats = Mock(return_value={"converter": "stats"})
        
        stats = self.coordinator.get_performance_stats()
        
        # Verify all component stats are included
        self.assertIn("coordinator_stats", stats)
        self.assertIn("memory_stats", stats)
        self.assertIn("batch_stats", stats)
        self.assertIn("cache_stats", stats)
        self.assertIn("file_stats", stats)
        self.assertIn("converter_stats", stats)
        
        self.assertEqual(stats["memory_stats"], {"memory": "stats"})
        self.assertEqual(stats["batch_stats"], {"batch": "stats"})
    
    def test_create_success_result(self):
        """Test creating success result."""
        self.coordinator.stats["processed_sequences"] = 15
        
        result = self.coordinator._create_success_result()
        
        self.assertTrue(result["success"])
        self.assertEqual(result["statistics"]["processed_sequences"], 15)
        self.assertIn("message", result)
    
    def test_create_error_result(self):
        """Test creating error result."""
        self.coordinator.stats["failed_count"] = 3
        
        result = self.coordinator._create_error_result("Test error")
        
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "Test error")
        self.assertEqual(result["statistics"]["failed_count"], 3)


if __name__ == '__main__':
    unittest.main()
