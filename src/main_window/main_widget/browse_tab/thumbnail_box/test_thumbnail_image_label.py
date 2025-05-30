"""
Test for ThumbnailImageLabel to verify the coordinator delegation functionality.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QSize
from PyQt6.QtGui import QPixmap
import sys

# Ensure QApplication exists for testing
if not QApplication.instance():
    app = QApplication(sys.argv)

from .thumbnail_image_label import ThumbnailImageLabel


class TestThumbnailImageLabel(unittest.TestCase):
    """Test the ThumbnailImageLabel coordinator delegation functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.thumbnail_box = Mock()
        self.thumbnail_box.in_sequence_viewer = False
        self.thumbnail_box.state.thumbnails = ["test1.png", "test2.png", "test3.png"]
        
        # Mock the coordinator
        with patch('src.main_window.main_widget.browse_tab.thumbnail_box.thumbnail_image_label.ThumbnailCoordinator') as mock_coordinator_class:
            self.mock_coordinator = Mock()
            mock_coordinator_class.return_value = self.mock_coordinator
            
            self.label = ThumbnailImageLabel(self.thumbnail_box)
    
    def test_initialization(self):
        """Test that the label initializes correctly with coordinator."""
        self.assertEqual(self.label.thumbnail_box, self.thumbnail_box)
        self.assertIsNotNone(self.label.thumbnail_coordinator)
        self.assertFalse(self.label.selected)
        self.assertIsNone(self.label.current_path)
        
        # Verify UI setup
        self.assertEqual(self.label.objectName(), "thumbnail_image_label")
    
    def test_aspect_ratio_delegation(self):
        """Test that aspect ratio calculation delegates to coordinator."""
        self.mock_coordinator.get_aspect_ratio.return_value = 1.5
        self.label.current_path = "test.png"
        
        result = self.label.aspect_ratio
        
        self.assertEqual(result, 1.5)
        self.mock_coordinator.get_aspect_ratio.assert_called_with("test.png")
    
    def test_original_pixmap_delegation(self):
        """Test that original pixmap access delegates to coordinator."""
        mock_pixmap = Mock()
        self.mock_coordinator.get_original_pixmap.return_value = mock_pixmap
        self.label.current_path = "test.png"
        
        result = self.label._original_pixmap
        
        self.assertEqual(result, mock_pixmap)
        self.mock_coordinator.get_original_pixmap.assert_called_with("test.png")
    
    def test_update_thumbnail_sync_delegation(self):
        """Test that synchronous thumbnail update delegates to coordinator."""
        self.mock_coordinator.update_thumbnail_sync.return_value = {
            "path": "test1.png"
        }
        
        self.label.update_thumbnail(0)
        
        self.assertEqual(self.label.current_path, "test1.png")
        self.assertIsNone(self.label._cached_available_size)
        self.mock_coordinator.update_thumbnail_sync.assert_called_with(self.label, 0)
    
    def test_update_thumbnail_async_delegation(self):
        """Test that asynchronous thumbnail update delegates to coordinator."""
        self.mock_coordinator.update_thumbnail_async.return_value = {
            "path": "test2.png",
            "pending_path": "test2.png",
            "pending_index": 1,
            "start_timer": True
        }
        
        with patch.object(self.label._load_timer, 'start') as mock_start:
            self.label.update_thumbnail_async(1)
        
        self.assertEqual(self.label.current_path, "test2.png")
        self.assertEqual(self.label._pending_path, "test2.png")
        self.assertEqual(self.label._pending_index, 1)
        mock_start.assert_called_with(1)
        self.mock_coordinator.update_thumbnail_async.assert_called_with(self.label, 1)
    
    def test_load_pending_image_delegation(self):
        """Test that pending image loading delegates to coordinator."""
        self.label._pending_path = "pending.png"
        self.label._pending_index = 2
        
        self.mock_coordinator.load_pending_image.return_value = {
            "path": "pending.png"
        }
        
        self.label._load_pending_image()
        
        self.assertEqual(self.label.current_path, "pending.png")
        self.assertIsNone(self.label._pending_path)
        self.assertIsNone(self.label._pending_index)
        self.mock_coordinator.load_pending_image.assert_called_with(
            self.label, "pending.png", 2
        )
    
    def test_calculate_available_space_delegation(self):
        """Test that available space calculation delegates to coordinator."""
        test_size = QSize(200, 150)
        self.mock_coordinator.calculate_available_space.return_value = test_size
        
        result = self.label._calculate_available_space()
        
        self.assertEqual(result, test_size)
        self.assertEqual(self.label._cached_available_size, test_size)
        self.mock_coordinator.calculate_available_space.assert_called_with(self.label)
    
    def test_calculate_available_space_cached(self):
        """Test that cached available space is returned without delegation."""
        cached_size = QSize(300, 200)
        self.label._cached_available_size = cached_size
        
        result = self.label._calculate_available_space()
        
        self.assertEqual(result, cached_size)
        self.mock_coordinator.calculate_available_space.assert_not_called()
    
    def test_ultra_quality_processing_delegation(self):
        """Test that ultra quality processing delegates to coordinator."""
        self.label.current_path = "test.png"
        test_pixmap = QPixmap(100, 100)
        test_size = QSize(200, 150)
        
        self.mock_coordinator.process_ultra_quality_thumbnail.return_value = {
            "pixmap": test_pixmap,
            "available_size": test_size,
            "from_cache": False
        }
        
        with patch.object(self.label, 'setFixedSize') as mock_set_size, \
             patch.object(self.label, 'setPixmap') as mock_set_pixmap:
            
            self.label._resize_pixmap_to_ultra_quality()
        
        mock_set_size.assert_called_with(test_size)
        mock_set_pixmap.assert_called_with(test_pixmap)
        self.mock_coordinator.process_ultra_quality_thumbnail.assert_called_with(
            self.label, "test.png"
        )
    
    def test_ultra_quality_processing_fallback(self):
        """Test fallback when ultra quality processing fails."""
        self.label.current_path = "test.png"
        self.mock_coordinator.process_ultra_quality_thumbnail.return_value = None
        
        with patch.object(self.label, '_resize_pixmap_to_fit_smooth') as mock_fallback:
            self.label._resize_pixmap_to_ultra_quality()
        
        mock_fallback.assert_called_once()
    
    def test_cache_delegation(self):
        """Test that cache operations delegate to coordinator."""
        test_pixmap = QPixmap(100, 100)
        test_size = QSize(200, 150)
        self.label.current_path = "test.png"
        
        # Test get cached thumbnail
        self.mock_coordinator.get_cached_thumbnail.return_value = test_pixmap
        result = self.label._get_cached_thumbnail(test_size)
        self.assertEqual(result, test_pixmap)
        self.mock_coordinator.get_cached_thumbnail.assert_called_with("test.png", test_size)
        
        # Test cache thumbnail
        self.label._cache_thumbnail(test_pixmap, test_size)
        self.mock_coordinator.cache_thumbnail.assert_called_with("test.png", test_pixmap, test_size)
    
    def test_viewport_visibility_delegation(self):
        """Test that viewport visibility check delegates to coordinator."""
        self.mock_coordinator.check_viewport_visibility.return_value = True
        
        result = self.label._check_viewport_visibility()
        
        self.assertTrue(result)
        self.mock_coordinator.check_viewport_visibility.assert_called_with(self.label)
    
    def test_performance_stats_delegation(self):
        """Test that performance stats delegate to coordinator."""
        test_stats = {"cache_hits": 10, "cache_misses": 2}
        self.mock_coordinator.get_performance_stats.return_value = test_stats
        
        result = self.label.get_performance_stats()
        
        self.assertEqual(result, test_stats)
        self.mock_coordinator.get_performance_stats.assert_called_once()
    
    def test_cache_management_delegation(self):
        """Test that cache management methods delegate to coordinator."""
        test_cache_stats = {"total_cached": 50, "cache_size_mb": 25.5}
        self.mock_coordinator.get_cache_stats.return_value = test_cache_stats
        
        # Test clear cache
        self.label.clear_cache()
        self.mock_coordinator.clear_cache.assert_called_once()
        
        # Test get cache stats
        result = self.label.get_cache_stats()
        self.assertEqual(result, test_cache_stats)
        self.mock_coordinator.get_cache_stats.assert_called_once()
    
    def test_selection_state(self):
        """Test selection state management."""
        self.assertFalse(self.label.selected)
        self.assertIsNone(self.label._border_color)
        
        # Test selection
        self.label.set_selected(True)
        self.assertTrue(self.label.selected)
        
        # Test deselection
        self.label.set_selected(False)
        self.assertFalse(self.label.selected)
    
    def test_border_properties(self):
        """Test border-related properties."""
        self.assertEqual(self.label.border_width, 4)
        self.assertFalse(self.label.is_in_sequence_viewer)
        
        # Test sequence viewer mode
        self.thumbnail_box.in_sequence_viewer = True
        self.assertTrue(self.label.is_in_sequence_viewer)
    
    def test_legacy_methods(self):
        """Test that legacy methods work without errors."""
        # These should not raise exceptions
        self.label._ensure_cache_directory()
        self.label._load_cache_metadata()
        self.label._save_cache_metadata()
        self.label._enhance_image_quality()
        
        # Test cache key generation delegation
        test_size = QSize(100, 100)
        self.mock_coordinator.generate_cache_key.return_value = "test_key"
        
        result = self.label._generate_cache_key("test.png", test_size)
        self.assertEqual(result, "test_key")
        self.mock_coordinator.generate_cache_key.assert_called_with("test.png", test_size)


if __name__ == '__main__':
    unittest.main()
