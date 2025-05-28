"""
Viewport Manager - Grid-aware viewport calculations for lazy loading.

Manages viewport calculations specifically for grid layouts with:
- Row-based loading zones
- Grid-aware visibility detection
- Configurable buffer zones
- Smooth scrolling optimization
"""

import logging
from typing import Optional
from PyQt6.QtCore import QRect
from PyQt6.QtWidgets import QWidget, QScrollArea


class ViewportManager:
    """
    Manages viewport calculations for grid-based lazy loading.
    
    Features:
    - Grid-aware row calculations
    - Configurable loading buffer (rows ahead/behind)
    - Unload zone for memory management
    - Optimized visibility detection
    """
    
    def __init__(self, scroll_area: QScrollArea, grid_columns: int = 3, buffer_rows: int = 7):
        """
        Initialize the viewport manager.
        
        Args:
            scroll_area: The scroll area to monitor
            grid_columns: Number of columns in the grid
            buffer_rows: Number of rows to load ahead/behind viewport
        """
        self.scroll_area = scroll_area
        self.grid_columns = grid_columns
        self.buffer_rows = buffer_rows
        
        # Extended unload zone (further than loading zone)
        self.unload_buffer_rows = buffer_rows * 2
        
        # Cache for performance
        self._cached_viewport_rect: Optional[QRect] = None
        self._cached_scroll_value: Optional[int] = None
        
        logging.debug(f"ViewportManager initialized: {grid_columns} columns, {buffer_rows} buffer rows")
    
    def is_widget_visible(self, widget: QWidget) -> bool:
        """Check if a widget is currently visible in the viewport."""
        if not widget or not self.scroll_area:
            return False
        
        try:
            viewport_rect = self._get_current_viewport_rect()
            widget_rect = self._get_widget_rect_in_scroll_area(widget)
            
            return viewport_rect.intersects(widget_rect)
            
        except Exception as e:
            logging.debug(f"Error checking widget visibility: {e}")
            return True  # Default to visible if we can't determine
    
    def is_widget_in_loading_zone(self, widget: QWidget) -> bool:
        """Check if a widget is in the loading zone (viewport + buffer)."""
        if not widget or not self.scroll_area:
            return False
        
        try:
            loading_zone_rect = self._get_loading_zone_rect()
            widget_rect = self._get_widget_rect_in_scroll_area(widget)
            
            return loading_zone_rect.intersects(widget_rect)
            
        except Exception as e:
            logging.debug(f"Error checking loading zone: {e}")
            return True  # Default to in zone if we can't determine
    
    def is_widget_in_unload_zone(self, widget: QWidget) -> bool:
        """Check if a widget is in the unload zone (extended buffer for memory management)."""
        if not widget or not self.scroll_area:
            return False
        
        try:
            unload_zone_rect = self._get_unload_zone_rect()
            widget_rect = self._get_widget_rect_in_scroll_area(widget)
            
            return unload_zone_rect.intersects(widget_rect)
            
        except Exception as e:
            logging.debug(f"Error checking unload zone: {e}")
            return True  # Default to in zone if we can't determine
    
    def get_visible_row_range(self) -> tuple[int, int]:
        """Get the range of visible rows in the grid."""
        try:
            viewport_rect = self._get_current_viewport_rect()
            
            # Estimate row height from first widget if available
            row_height = self._estimate_row_height()
            if row_height <= 0:
                return (0, 0)
            
            # Calculate visible row range
            start_row = max(0, viewport_rect.top() // row_height)
            end_row = (viewport_rect.bottom() // row_height) + 1
            
            return (start_row, end_row)
            
        except Exception as e:
            logging.debug(f"Error calculating visible row range: {e}")
            return (0, 10)  # Fallback range
    
    def get_loading_row_range(self) -> tuple[int, int]:
        """Get the range of rows that should be loaded (visible + buffer)."""
        try:
            start_row, end_row = self.get_visible_row_range()
            
            # Extend range with buffer
            buffered_start = max(0, start_row - self.buffer_rows)
            buffered_end = end_row + self.buffer_rows
            
            return (buffered_start, buffered_end)
            
        except Exception as e:
            logging.debug(f"Error calculating loading row range: {e}")
            return (0, 15)  # Fallback range
    
    def _get_current_viewport_rect(self) -> QRect:
        """Get the current viewport rectangle in scroll area coordinates."""
        if not self.scroll_area:
            return QRect()
        
        # Check cache
        current_scroll_value = self.scroll_area.verticalScrollBar().value()
        if (self._cached_viewport_rect and 
            self._cached_scroll_value == current_scroll_value):
            return self._cached_viewport_rect
        
        # Calculate viewport rect
        viewport = self.scroll_area.viewport()
        scroll_value = current_scroll_value
        
        viewport_rect = QRect(
            0,
            scroll_value,
            viewport.width(),
            viewport.height()
        )
        
        # Cache the result
        self._cached_viewport_rect = viewport_rect
        self._cached_scroll_value = current_scroll_value
        
        return viewport_rect
    
    def _get_loading_zone_rect(self) -> QRect:
        """Get the loading zone rectangle (viewport + buffer)."""
        viewport_rect = self._get_current_viewport_rect()
        
        # Estimate row height for buffer calculation
        row_height = self._estimate_row_height()
        buffer_pixels = self.buffer_rows * row_height
        
        # Extend viewport with buffer
        loading_rect = QRect(
            viewport_rect.x(),
            max(0, viewport_rect.y() - buffer_pixels),
            viewport_rect.width(),
            viewport_rect.height() + (2 * buffer_pixels)
        )
        
        return loading_rect
    
    def _get_unload_zone_rect(self) -> QRect:
        """Get the unload zone rectangle (extended buffer for memory management)."""
        viewport_rect = self._get_current_viewport_rect()
        
        # Estimate row height for buffer calculation
        row_height = self._estimate_row_height()
        unload_buffer_pixels = self.unload_buffer_rows * row_height
        
        # Extend viewport with larger buffer
        unload_rect = QRect(
            viewport_rect.x(),
            max(0, viewport_rect.y() - unload_buffer_pixels),
            viewport_rect.width(),
            viewport_rect.height() + (2 * unload_buffer_pixels)
        )
        
        return unload_rect
    
    def _get_widget_rect_in_scroll_area(self, widget: QWidget) -> QRect:
        """Get widget rectangle in scroll area coordinates."""
        if not widget or not self.scroll_area or not self.scroll_area.widget():
            return QRect()
        
        try:
            # Get widget position relative to scroll area content
            scroll_content = self.scroll_area.widget()
            widget_pos = widget.mapTo(scroll_content, widget.rect().topLeft())
            
            widget_rect = QRect(
                widget_pos.x(),
                widget_pos.y(),
                widget.width(),
                widget.height()
            )
            
            return widget_rect
            
        except Exception as e:
            logging.debug(f"Error getting widget rect: {e}")
            return QRect()
    
    def _estimate_row_height(self) -> int:
        """Estimate the height of a grid row."""
        try:
            if not self.scroll_area or not self.scroll_area.widget():
                return 200  # Fallback height
            
            scroll_content = self.scroll_area.widget()
            
            # Try to find the first child widget to estimate row height
            children = scroll_content.findChildren(QWidget)
            if children:
                # Use the height of the first widget as row height estimate
                first_widget = children[0]
                if first_widget.height() > 0:
                    # Add some spacing for grid layout
                    return first_widget.height() + 10
            
            # Fallback to reasonable default
            return 200
            
        except Exception as e:
            logging.debug(f"Error estimating row height: {e}")
            return 200
    
    def invalidate_cache(self) -> None:
        """Invalidate cached viewport calculations."""
        self._cached_viewport_rect = None
        self._cached_scroll_value = None
    
    def update_grid_config(self, columns: int, buffer_rows: int) -> None:
        """Update grid configuration."""
        self.grid_columns = columns
        self.buffer_rows = buffer_rows
        self.unload_buffer_rows = buffer_rows * 2
        self.invalidate_cache()
        
        logging.debug(f"Grid config updated: {columns} columns, {buffer_rows} buffer rows")
    
    def get_stats(self) -> dict:
        """Get viewport manager statistics."""
        try:
            visible_start, visible_end = self.get_visible_row_range()
            loading_start, loading_end = self.get_loading_row_range()
            
            return {
                'grid_columns': self.grid_columns,
                'buffer_rows': self.buffer_rows,
                'unload_buffer_rows': self.unload_buffer_rows,
                'visible_rows': (visible_start, visible_end),
                'loading_rows': (loading_start, loading_end),
                'estimated_row_height': self._estimate_row_height(),
                'viewport_cached': self._cached_viewport_rect is not None
            }
        except Exception as e:
            logging.debug(f"Error getting viewport stats: {e}")
            return {
                'grid_columns': self.grid_columns,
                'buffer_rows': self.buffer_rows,
                'error': str(e)
            }
