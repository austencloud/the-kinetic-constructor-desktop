"""
Thumbnail Image Label - Backward compatibility wrapper.

This module provides backward compatibility by importing the component-based implementation
and re-exporting it with the original class name.
"""

from .thumbnail_image_label_modern import ThumbnailImageLabelModern, ImageProcessor

# Backward compatibility alias
ThumbnailImageLabel = ThumbnailImageLabelModern

# Re-export for external imports
__all__ = ["ThumbnailImageLabel", "ImageProcessor"]
