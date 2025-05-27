"""
Image Converter - Handles QImage to PIL conversion with memory management.

This component extracts image conversion logic from the main exporter
following the Single Responsibility Principle.
"""

import logging
import io
import numpy as np
from typing import Optional
from PyQt6.QtGui import QImage
from PyQt6.QtCore import QBuffer, Qt
from PIL import Image


class ImageConverter:
    """
    Handles image conversion operations with memory management.
    
    Responsibilities:
    - QImage to PIL Image conversion
    - Memory-efficient image scaling
    - Error handling for out-of-memory situations
    - Progressive downsampling strategies
    - Alternative conversion methods
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Conversion statistics
        self.stats = {
            "conversions_attempted": 0,
            "conversions_successful": 0,
            "memory_errors": 0,
            "fallback_conversions": 0,
            "downsampling_applied": 0
        }
        
        self.logger.info("ImageConverter initialized")
    
    def convert_qimage_to_pil(self, qimage: QImage, max_dimension: int = 3000) -> Image.Image:
        """
        Convert a QImage to a PIL Image with memory-efficient processing.
        
        Args:
            qimage: The QImage to convert
            max_dimension: Maximum width or height for the image
            
        Returns:
            PIL Image object
        """
        self.stats["conversions_attempted"] += 1
        
        try:
            # Apply downsampling if needed
            processed_qimage = self._apply_downsampling_if_needed(qimage, max_dimension)
            
            # Attempt primary conversion method
            pil_image = self._convert_with_numpy(processed_qimage)
            
            self.stats["conversions_successful"] += 1
            return pil_image
            
        except MemoryError as e:
            self.logger.warning(f"Memory error during conversion: {e}")
            self.stats["memory_errors"] += 1
            return self._handle_memory_error(qimage, max_dimension)
        except Exception as e:
            self.logger.error(f"Conversion error: {e}")
            return self._create_error_image()
    
    def _apply_downsampling_if_needed(self, qimage: QImage, max_dimension: int) -> QImage:
        """Apply downsampling if image exceeds maximum dimensions."""
        original_width, original_height = qimage.width(), qimage.height()
        
        # Check if downsampling is needed
        if original_width <= max_dimension and original_height <= max_dimension:
            return qimage
        
        # Calculate scaling factor
        scale_factor = min(
            max_dimension / original_width if original_width > max_dimension else 1.0,
            max_dimension / original_height if original_height > max_dimension else 1.0
        )
        
        # Apply scaling
        new_width = int(original_width * scale_factor)
        new_height = int(original_height * scale_factor)
        
        self.logger.info(
            f"Downsampling image from {original_width}x{original_height} "
            f"to {new_width}x{new_height}"
        )
        
        scaled_image = qimage.scaled(
            new_width,
            new_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        
        self.stats["downsampling_applied"] += 1
        return scaled_image
    
    def _convert_with_numpy(self, qimage: QImage) -> Image.Image:
        """Convert QImage to PIL using numpy (primary method)."""
        # Convert to ARGB32 format
        qimage = qimage.convertToFormat(QImage.Format.Format_ARGB32)
        width, height = qimage.width(), qimage.height()
        
        # Get image data
        ptr = qimage.bits()
        ptr.setsize(height * width * 4)
        
        # Create numpy array with copy=True for memory safety
        arr = np.array(ptr, copy=True).reshape((height, width, 4))
        
        # Convert from ARGB to RGBA
        arr = arr[..., [2, 1, 0, 3]]
        
        # Create PIL image
        pil_image = Image.fromarray(arr, "RGBA")
        
        # Clear the numpy array to free memory
        arr = None
        
        return pil_image
    
    def _handle_memory_error(self, qimage: QImage, max_dimension: int) -> Image.Image:
        """Handle memory errors with progressive downsampling."""
        self.logger.warning("Handling memory error with progressive downsampling")
        
        # Try progressively smaller dimensions
        fallback_dimensions = [2000, 1500, 1000, 500]
        
        for dimension in fallback_dimensions:
            if dimension >= max_dimension:
                continue
                
            try:
                self.logger.info(f"Retrying with max dimension: {dimension}px")
                return self.convert_qimage_to_pil(qimage, dimension)
            except MemoryError:
                continue
        
        # If all else fails, use alternative method
        self.logger.warning("Using alternative conversion method")
        return self._convert_with_buffer(qimage)
    
    def _convert_with_buffer(self, qimage: QImage) -> Image.Image:
        """Alternative conversion method using QBuffer (fallback)."""
        try:
            self.stats["fallback_conversions"] += 1
            
            # Save to a temporary buffer in PNG format
            buffer = QBuffer()
            buffer.open(QBuffer.OpenModeFlag.ReadWrite)
            qimage.save(buffer, "PNG", quality=100)
            buffer.seek(0)
            
            # Load from buffer with PIL
            pil_image = Image.open(io.BytesIO(buffer.data().data()))
            return pil_image.copy()  # Return a copy to ensure buffer can be released
            
        except Exception as e:
            self.logger.error(f"Buffer conversion failed: {e}")
            return self._create_error_image()
    
    def _create_error_image(self, size: tuple = (400, 300)) -> Image.Image:
        """Create an error image when conversion fails."""
        self.logger.warning("Creating error image due to conversion failure")
        return Image.new("RGBA", size, (255, 0, 0, 128))
    
    def get_optimal_max_dimension(self, qimage: QImage, target_file_size_mb: float = 10.0) -> int:
        """
        Calculate optimal maximum dimension based on target file size.
        
        Args:
            qimage: Source QImage
            target_file_size_mb: Target file size in MB
            
        Returns:
            Optimal maximum dimension
        """
        # Estimate bytes per pixel (RGBA = 4 bytes)
        bytes_per_pixel = 4
        target_bytes = target_file_size_mb * 1024 * 1024
        
        # Calculate maximum pixels for target size
        max_pixels = target_bytes / bytes_per_pixel
        
        # Calculate dimension (assuming square for simplicity)
        max_dimension = int(max_pixels ** 0.5)
        
        # Apply reasonable bounds
        max_dimension = max(500, min(max_dimension, 4000))
        
        self.logger.debug(f"Calculated optimal max dimension: {max_dimension}px")
        return max_dimension
    
    def validate_conversion_quality(self, original: QImage, converted: Image.Image) -> dict:
        """
        Validate the quality of the conversion.
        
        Args:
            original: Original QImage
            converted: Converted PIL Image
            
        Returns:
            Dictionary with quality metrics
        """
        return {
            "original_size": (original.width(), original.height()),
            "converted_size": converted.size,
            "size_ratio": (converted.size[0] / original.width(), converted.size[1] / original.height()),
            "format": converted.format,
            "mode": converted.mode
        }
    
    def get_stats(self) -> dict:
        """Get conversion statistics."""
        success_rate = (
            self.stats["conversions_successful"] / max(1, self.stats["conversions_attempted"])
        ) * 100
        
        return {
            **self.stats,
            "success_rate_percent": round(success_rate, 2)
        }
    
    def reset_stats(self) -> None:
        """Reset conversion statistics."""
        self.stats = {
            "conversions_attempted": 0,
            "conversions_successful": 0,
            "memory_errors": 0,
            "fallback_conversions": 0,
            "downsampling_applied": 0
        }
        self.logger.info("Conversion statistics reset")
