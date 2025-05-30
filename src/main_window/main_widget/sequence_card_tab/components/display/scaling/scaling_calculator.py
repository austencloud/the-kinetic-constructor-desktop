"""
Scaling Calculator - Handles scaling calculations with single responsibility.

Extracted from the monolithic ImageProcessor class to follow SRP.
"""

import logging
from typing import Tuple
from PyQt6.QtCore import QSize


class ScalingCalculator:
    """
    Handles scaling calculations and dimension management.

    Responsibilities:
    - Calculate target dimensions
    - Manage aspect ratios
    - Handle margin calculations
    - Column-based adjustments
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def calculate_screen_scaling_params(
        self, cell_size: QSize, columns_per_row: int, page_scale_factor: float
    ) -> Tuple[int, int, int]:
        """
        Calculate scaling parameters for screen display.

        Args:
            cell_size: Available cell size
            columns_per_row: Number of columns per row
            page_scale_factor: Scale factor from page

        Returns:
            Tuple of (target_width, target_height, margin)
        """
        # Column-based adjustments
        column_adjustment = self._get_column_adjustment(columns_per_row)
        margin_percent = self._get_margin_percent(columns_per_row)

        # Calculate margin
        margin = min(
            15, max(3, int(min(cell_size.width(), cell_size.height()) * margin_percent))
        )

        # Calculate available space
        available_width = cell_size.width() - (margin * 2)
        available_height = cell_size.height() - (margin * 2)

        # Apply scaling factors
        target_width = int(available_width * page_scale_factor * column_adjustment)
        target_height = int(available_height * page_scale_factor * column_adjustment)

        return target_width, target_height, margin

    def calculate_export_scaling_params(
        self,
        original_width: int,
        original_height: int,
        export_target_width: int,
        export_target_height: int,
    ) -> Tuple[int, int]:
        """
        Calculate scaling parameters for export.

        Args:
            original_width: Original image width
            original_height: Original image height
            export_target_width: Target export width
            export_target_height: Target export height

        Returns:
            Tuple of (final_width, final_height)
        """
        if original_width <= 0 or original_height <= 0:
            self.logger.error(
                f"Invalid original dimensions: {original_width}x{original_height}"
            )
            return 0, 0

        # Calculate scaling factors
        width_scale = export_target_width / original_width if original_width > 0 else 0
        height_scale = (
            export_target_height / original_height if original_height > 0 else 0
        )

        # Determine the limiting dimension
        if width_scale > 0 and height_scale > 0:
            scale = min(width_scale, height_scale)
        elif width_scale > 0:
            scale = width_scale
        elif height_scale > 0:
            scale = height_scale
        else:
            self.logger.warning("Cannot determine scale - using original size")
            return original_width, original_height

        if scale > 0:
            final_width = int(original_width * scale)
            final_height = int(original_height * scale)
        else:
            final_width = 0
            final_height = 0

        # Ensure positive dimensions
        final_width = max(0, final_width)
        final_height = max(0, final_height)

        return final_width, final_height

    def calculate_aspect_ratio_fit(
        self,
        original_width: int,
        original_height: int,
        target_width: int,
        target_height: int,
    ) -> Tuple[int, int]:
        """
        Calculate dimensions that fit within target while maintaining aspect ratio.

        Args:
            original_width: Original image width
            original_height: Original image height
            target_width: Target width constraint
            target_height: Target height constraint

        Returns:
            Tuple of (fitted_width, fitted_height)
        """
        if original_width <= 0 or original_height <= 0:
            return 0, 0

        aspect_ratio = original_height / original_width

        if target_width * aspect_ratio <= target_height:
            # Width is the limiting factor
            fitted_width = target_width
            fitted_height = int(target_width * aspect_ratio)
        else:
            # Height is the limiting factor
            fitted_height = target_height
            fitted_width = int(target_height / aspect_ratio)

        # Ensure positive dimensions
        fitted_width = max(0, fitted_width)
        fitted_height = max(0, fitted_height)

        return fitted_width, fitted_height

    def _get_column_adjustment(self, columns_per_row: int) -> float:
        """Get column-based adjustment factor."""
        if columns_per_row == 3:
            return 0.98
        elif columns_per_row == 4:
            return 0.95
        else:
            return 1.0

    def _get_margin_percent(self, columns_per_row: int) -> float:
        """Get margin percentage based on column count."""
        if columns_per_row == 3:
            return 0.04
        elif columns_per_row == 4:
            return 0.03
        else:
            return 0.05

    def create_cache_key(
        self,
        image_path: str,
        cell_size: QSize,
        columns_per_row: int,
        page_scale_factor: float,
    ) -> str:
        """
        Create optimized cache key for scaled images based on display size.

        This method creates cache keys that prioritize image display dimensions
        over source path, allowing the same image at the same size to be reused
        across different sequence length filters.

        Args:
            image_path: Path to image
            cell_size: Cell size
            columns_per_row: Number of columns
            page_scale_factor: Scale factor

        Returns:
            Cache key string optimized for size-based reuse
        """
        # Calculate the actual display dimensions
        target_width, target_height, _ = self.calculate_screen_scaling_params(
            cell_size, columns_per_row, page_scale_factor
        )

        # Create a content-based identifier for the image
        image_content_id = self._create_image_content_id(image_path)

        # Create cache key based on content + display size (not path)
        key_parts = (
            image_content_id,
            target_width,
            target_height,
            f"{page_scale_factor:.4f}",
        )
        return "_".join(map(str, key_parts))

    def _create_image_content_id(self, image_path: str) -> str:
        """
        Create a content-based identifier for an image.

        This uses file size and modification time to create a unique identifier
        that's independent of the file path, allowing the same image content
        to be recognized regardless of how it's accessed.

        Args:
            image_path: Path to the image file

        Returns:
            Content-based identifier string
        """
        import os
        import hashlib

        try:
            # Get file stats for content identification
            stat = os.stat(image_path)
            file_size = stat.st_size
            mtime = stat.st_mtime

            # Use filename (without path) + size + mtime for content ID
            filename = os.path.basename(image_path)
            content_data = f"{filename}_{file_size}_{mtime}"

            # Create a short hash for the cache key
            return hashlib.md5(content_data.encode()).hexdigest()[:12]

        except OSError:
            # Fallback to path-based hash if file stats unavailable
            return hashlib.md5(image_path.encode()).hexdigest()[:12]
