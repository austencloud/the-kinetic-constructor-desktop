"""
Image Loader - Handles image loading and validation with single responsibility.

Extracted from the monolithic ImageProcessor class to follow SRP.
"""

import os
import logging
from typing import Optional
from pathlib import Path
from PyQt6.QtGui import QImage
from PyQt6.QtCore import Qt


class ImageLoader:
    """
    Handles image loading and validation operations.
    
    Responsibilities:
    - File validation (existence, size, format)
    - Image loading with size limits
    - Error handling and logging
    - Format support management
    """
    
    # Configuration constants
    MAX_FILE_SIZE_MB = 100
    MAX_DIMENSION = 4096
    
    VALID_EXTENSIONS = {
        ".png", ".jpg", ".jpeg", ".bmp", 
        ".gif", ".tiff", ".webp"
    }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def load_image(self, image_path: str) -> Optional[QImage]:
        """
        Load image with validation and size limits.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            QImage if successful, None otherwise
        """
        # Pre-validate file before loading
        if not self.validate_image_file(image_path):
            self.logger.error(f"Image validation failed: {image_path}")
            return None
            
        # Load with size limits
        image = self._load_with_size_limit(image_path)
        if image is None or image.isNull():
            self.logger.error(f"Failed to load image: {image_path}")
            return None
            
        return image
        
    def validate_image_file(self, image_path: str) -> bool:
        """
        Validate image file before loading to prevent crashes and performance issues.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            True if image is safe to load, False otherwise
        """
        try:
            path = Path(image_path)
            
            # Check if file exists
            if not path.exists():
                self.logger.warning(f"Image file does not exist: {image_path}")
                return False
                
            # Check file size (reject files larger than MAX_FILE_SIZE_MB)
            file_size = path.stat().st_size
            max_size = self.MAX_FILE_SIZE_MB * 1024 * 1024
            if file_size > max_size:
                self.logger.warning(
                    f"Image file too large: {file_size / (1024*1024):.1f}MB > {self.MAX_FILE_SIZE_MB}MB"
                )
                return False
                
            # Check file extension
            if path.suffix.lower() not in self.VALID_EXTENSIONS:
                self.logger.warning(f"Unsupported image format: {path.suffix}")
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating image file {image_path}: {e}")
            return False
            
    def _load_with_size_limit(self, image_path: str) -> Optional[QImage]:
        """
        Load image with automatic downscaling if too large.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            QImage if successful, None otherwise
        """
        try:
            # Load the image
            image = QImage(image_path)
            if image.isNull():
                return None
                
            # Check dimensions and downscale if necessary
            if image.width() > self.MAX_DIMENSION or image.height() > self.MAX_DIMENSION:
                self.logger.info(
                    f"Downscaling large image {os.path.basename(image_path)}: "
                    f"{image.width()}x{image.height()} -> max {self.MAX_DIMENSION}"
                )
                
                # Calculate new size maintaining aspect ratio
                if image.width() > image.height():
                    new_width = self.MAX_DIMENSION
                    new_height = int((self.MAX_DIMENSION * image.height()) / image.width())
                else:
                    new_height = self.MAX_DIMENSION
                    new_width = int((self.MAX_DIMENSION * image.width()) / image.height())
                    
                # Scale down using high quality
                image = image.scaled(
                    new_width,
                    new_height,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                
                self.logger.debug(f"Image downscaled to: {image.width()}x{image.height()}")
                
            return image
            
        except Exception as e:
            self.logger.error(f"Error loading image with size limit {image_path}: {e}")
            return None
