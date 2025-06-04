"""
Image Scaler - Handles image scaling operations with single responsibility.

Extracted from the monolithic ImageProcessor class to follow SRP.
"""

import logging
from typing import TYPE_CHECKING
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import QSize

from ..scaling.scaling_calculator import ScalingCalculator
from ..scaling.quality_enhancer import QualityEnhancer
from ..scaling.aspect_ratio_manager import AspectRatioManager

if TYPE_CHECKING:
    from ..pages.printable_factory import PrintablePageFactory


class ImageScaler:
    """
    Handles image scaling operations using specialized components.
    
    Responsibilities:
    - Coordinate scaling operations
    - Apply appropriate scaling algorithms
    - Handle screen vs export scaling
    - Manage quality enhancement
    """
    
    def __init__(self, page_factory: "PrintablePageFactory"):
        self.page_factory = page_factory
        self.logger = logging.getLogger(__name__)
        
        # Initialize scaling components
        self.scaling_calculator = ScalingCalculator()
        self.quality_enhancer = QualityEnhancer()
        self.aspect_ratio_manager = AspectRatioManager(page_factory)
        
    def scale_for_screen_display(
        self,
        image: QImage,
        image_path: str,
        columns_per_row: int,
        page_scale_factor: float,
        current_page_index: int = -1
    ) -> QPixmap:
        """
        Scale image for screen display with proper margins and quality.
        
        Args:
            image: Source QImage
            image_path: Path to image (for logging)
            columns_per_row: Number of columns per row
            page_scale_factor: Scale factor from page
            current_page_index: Page index for aspect ratio updates
            
        Returns:
            Scaled QPixmap for screen display
        """
        if image.isNull():
            cell_size = self.page_factory.get_cell_size()
            return self.quality_enhancer.create_error_pixmap(cell_size)
            
        try:
            # Get cell size for calculations
            cell_size = self.page_factory.get_cell_size()
            
            # Calculate scaling parameters
            target_width, target_height, margin = self.scaling_calculator.calculate_screen_scaling_params(
                cell_size, columns_per_row, page_scale_factor
            )
            
            # Get original dimensions
            original_width = image.width()
            original_height = image.height()
            
            if original_width <= 0 or original_height <= 0:
                return self.quality_enhancer.create_error_pixmap(cell_size)
                
            # Calculate final dimensions maintaining aspect ratio
            final_width, final_height = self.scaling_calculator.calculate_aspect_ratio_fit(
                original_width, original_height, target_width, target_height
            )
            
            if final_width <= 0 or final_height <= 0:
                return self.quality_enhancer.create_error_pixmap(cell_size)
                
            # Scale image with quality enhancement
            scaled_image = self.quality_enhancer.scale_image_multi_step(
                image, final_width, final_height
            )
            
            # Update page aspect ratio if this is the first image
            self.aspect_ratio_manager.update_page_aspect_ratio(
                original_width, original_height, current_page_index
            )
            
            # Convert to pixmap
            pixmap = QPixmap.fromImage(scaled_image)
            
            self.logger.debug(
                f"Screen scaling: {original_width}x{original_height} -> {final_width}x{final_height}"
            )
            
            return pixmap
            
        except Exception as e:
            self.logger.error(f"Error scaling image for screen: {e}")
            cell_size = self.page_factory.get_cell_size()
            return self.quality_enhancer.create_error_pixmap(cell_size)
            
    def scale_for_export(
        self,
        image: QImage,
        image_path: str,
        export_target_width: int,
        export_target_height: int
    ) -> QPixmap:
        """
        Scale image for high-quality export.
        
        Args:
            image: Source QImage
            image_path: Path to image (for logging)
            export_target_width: Target export width
            export_target_height: Target export height
            
        Returns:
            Scaled QPixmap for export
        """
        if image.isNull():
            return self.quality_enhancer.create_error_pixmap(
                QSize(export_target_width, export_target_height)
            )
            
        try:
            original_width = image.width()
            original_height = image.height()
            
            if original_width <= 0 or original_height <= 0:
                self.logger.error(
                    f"Invalid original dimensions for export: {original_width}x{original_height}"
                )
                return self.quality_enhancer.create_error_pixmap(
                    QSize(export_target_width, export_target_height)
                )
                
            # Calculate export dimensions
            final_width, final_height = self.scaling_calculator.calculate_export_scaling_params(
                original_width, original_height, export_target_width, export_target_height
            )
            
            if final_width <= 0 or final_height <= 0:
                self.logger.warning(f"Calculated export dimensions are zero for {image_path}")
                return self.quality_enhancer.create_error_pixmap(
                    QSize(export_target_width, export_target_height)
                )
                
            # Scale with high quality (export doesn't need multi-step as much)
            scaled_image = self.quality_enhancer.scale_image_high_quality(
                image, final_width, final_height
            )
            
            if scaled_image.isNull():
                self.logger.error(f"Scaling returned null image for export: {image_path}")
                return self.quality_enhancer.create_error_pixmap(
                    QSize(export_target_width, export_target_height)
                )
                
            # Convert to pixmap
            pixmap = QPixmap.fromImage(scaled_image)
            
            self.logger.debug(
                f"Export scaling: {original_width}x{original_height} -> {final_width}x{final_height}"
            )
            
            return pixmap
            
        except Exception as e:
            self.logger.error(f"Error scaling image for export: {e}")
            return self.quality_enhancer.create_error_pixmap(
                QSize(export_target_width, export_target_height)
            )
            
    def create_cache_key(
        self,
        image_path: str,
        columns_per_row: int,
        page_scale_factor: float
    ) -> str:
        """
        Create cache key for scaled images.
        
        Args:
            image_path: Path to image
            columns_per_row: Number of columns
            page_scale_factor: Scale factor
            
        Returns:
            Cache key string
        """
        cell_size = self.page_factory.get_cell_size()
        return self.scaling_calculator.create_cache_key(
            image_path, cell_size, columns_per_row, page_scale_factor
        )
