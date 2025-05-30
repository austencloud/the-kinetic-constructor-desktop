"""
Thumbnail Image Label - Backward compatibility wrapper.

This module provides backward compatibility by importing the modern implementation
and re-exporting it with the original class name.
"""

from .modern_thumbnail_image_label import ModernThumbnailImageLabel, ImageProcessor

# Backward compatibility alias
ThumbnailImageLabel = ModernThumbnailImageLabel

# Re-export for external imports
__all__ = ["ThumbnailImageLabel", "ImageProcessor"]
