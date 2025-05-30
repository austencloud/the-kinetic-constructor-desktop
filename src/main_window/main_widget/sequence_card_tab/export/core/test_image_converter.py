"""
Test for ImageConverter to verify image conversion functionality.
"""

import unittest
from unittest.mock import Mock, patch
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QImage
from PyQt6.QtCore import Qt
import sys

# Ensure QApplication exists for testing
if not QApplication.instance():
    app = QApplication(sys.argv)

from .image_converter import ImageConverter


class TestImageConverter(unittest.TestCase):
    """Test the ImageConverter functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.converter = ImageConverter()
    
    def test_initialization(self):
        """Test that the converter initializes correctly."""
        self.assertIsNotNone(self.converter.logger)
        self.assertEqual(self.converter.stats["conversions_attempted"], 0)
        self.assertEqual(self.converter.stats["conversions_successful"], 0)
        self.assertEqual(self.converter.stats["memory_errors"], 0)
        self.assertEqual(self.converter.stats["fallback_conversions"], 0)
        self.assertEqual(self.converter.stats["downsampling_applied"], 0)
    
    def test_convert_qimage_to_pil_success(self):
        """Test successful QImage to PIL conversion."""
        # Create a test QImage
        qimage = QImage(100, 100, QImage.Format.Format_ARGB32)
        qimage.fill(Qt.GlobalColor.red)
        
        # Mock the numpy conversion to avoid actual conversion
        with patch.object(self.converter, '_convert_with_numpy') as mock_convert:
            mock_convert.return_value = Mock()  # Mock PIL Image
            
            result = self.converter.convert_qimage_to_pil(qimage)
            
            self.assertIsNotNone(result)
            self.assertEqual(self.converter.stats["conversions_attempted"], 1)
            self.assertEqual(self.converter.stats["conversions_successful"], 1)
    
    def test_convert_qimage_to_pil_memory_error(self):
        """Test QImage to PIL conversion with memory error."""
        qimage = QImage(100, 100, QImage.Format.Format_ARGB32)
        
        # Mock numpy conversion to raise MemoryError
        with patch.object(self.converter, '_convert_with_numpy') as mock_convert:
            mock_convert.side_effect = MemoryError("Out of memory")
            
            with patch.object(self.converter, '_handle_memory_error') as mock_handle:
                mock_handle.return_value = Mock()  # Mock PIL Image
                
                result = self.converter.convert_qimage_to_pil(qimage)
                
                self.assertIsNotNone(result)
                self.assertEqual(self.converter.stats["conversions_attempted"], 1)
                self.assertEqual(self.converter.stats["memory_errors"], 1)
                mock_handle.assert_called_once()
    
    def test_apply_downsampling_if_needed(self):
        """Test downsampling logic."""
        # Create large image that needs downsampling
        qimage = QImage(4000, 3000, QImage.Format.Format_ARGB32)
        
        result = self.converter._apply_downsampling_if_needed(qimage, 2000)
        
        # Should be downsampled
        self.assertLessEqual(result.width(), 2000)
        self.assertLessEqual(result.height(), 2000)
        self.assertEqual(self.converter.stats["downsampling_applied"], 1)
    
    def test_apply_downsampling_not_needed(self):
        """Test when downsampling is not needed."""
        # Create small image
        qimage = QImage(500, 400, QImage.Format.Format_ARGB32)
        
        result = self.converter._apply_downsampling_if_needed(qimage, 2000)
        
        # Should not be downsampled
        self.assertEqual(result.width(), 500)
        self.assertEqual(result.height(), 400)
        self.assertEqual(self.converter.stats["downsampling_applied"], 0)
    
    def test_handle_memory_error_progressive_downsampling(self):
        """Test progressive downsampling on memory error."""
        qimage = QImage(100, 100, QImage.Format.Format_ARGB32)
        
        # Mock convert_qimage_to_pil to succeed on second call
        call_count = 0
        def mock_convert(img, max_dim):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise MemoryError("First call fails")
            return Mock()  # Success on second call
        
        with patch.object(self.converter, 'convert_qimage_to_pil', side_effect=mock_convert):
            result = self.converter._handle_memory_error(qimage, 3000)
            
            self.assertIsNotNone(result)
    
    def test_convert_with_buffer_fallback(self):
        """Test buffer conversion fallback method."""
        qimage = QImage(100, 100, QImage.Format.Format_ARGB32)
        qimage.fill(Qt.GlobalColor.blue)
        
        with patch('PIL.Image.open') as mock_open:
            mock_image = Mock()
            mock_image.copy.return_value = Mock()
            mock_open.return_value = mock_image
            
            result = self.converter._convert_with_buffer(qimage)
            
            self.assertIsNotNone(result)
            self.assertEqual(self.converter.stats["fallback_conversions"], 1)
    
    def test_create_error_image(self):
        """Test error image creation."""
        result = self.converter._create_error_image((200, 150))
        
        self.assertIsNotNone(result)
        # Would need PIL Image mock to test actual properties
    
    def test_get_optimal_max_dimension(self):
        """Test optimal dimension calculation."""
        qimage = QImage(1000, 1000, QImage.Format.Format_ARGB32)
        
        result = self.converter.get_optimal_max_dimension(qimage, 5.0)
        
        # Should return a reasonable dimension
        self.assertGreaterEqual(result, 500)
        self.assertLessEqual(result, 4000)
    
    def test_validate_conversion_quality(self):
        """Test conversion quality validation."""
        qimage = QImage(200, 150, QImage.Format.Format_ARGB32)
        
        # Mock PIL Image
        pil_image = Mock()
        pil_image.size = (180, 135)
        pil_image.format = "PNG"
        pil_image.mode = "RGBA"
        
        result = self.converter.validate_conversion_quality(qimage, pil_image)
        
        self.assertEqual(result["original_size"], (200, 150))
        self.assertEqual(result["converted_size"], (180, 135))
        self.assertEqual(result["format"], "PNG")
        self.assertEqual(result["mode"], "RGBA")
    
    def test_get_stats(self):
        """Test statistics retrieval."""
        # Set some test statistics
        self.converter.stats["conversions_attempted"] = 10
        self.converter.stats["conversions_successful"] = 8
        
        stats = self.converter.get_stats()
        
        self.assertEqual(stats["conversions_attempted"], 10)
        self.assertEqual(stats["conversions_successful"], 8)
        self.assertEqual(stats["success_rate_percent"], 80.0)
    
    def test_reset_stats(self):
        """Test statistics reset."""
        # Set some statistics
        self.converter.stats["conversions_attempted"] = 5
        self.converter.stats["conversions_successful"] = 3
        
        self.converter.reset_stats()
        
        # All stats should be reset to 0
        self.assertEqual(self.converter.stats["conversions_attempted"], 0)
        self.assertEqual(self.converter.stats["conversions_successful"], 0)
        self.assertEqual(self.converter.stats["memory_errors"], 0)
        self.assertEqual(self.converter.stats["fallback_conversions"], 0)
        self.assertEqual(self.converter.stats["downsampling_applied"], 0)


if __name__ == '__main__':
    unittest.main()
