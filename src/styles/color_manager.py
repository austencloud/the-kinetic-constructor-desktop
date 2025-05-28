"""
Color Manager - Handles color palette and transparency management.

Extracted from GlassmorphismStyler to follow Single Responsibility Principle.
"""

import logging
from typing import Dict


class ColorManager:
    """
    Manages color palette, transparency, and color utility functions.
    
    Responsibilities:
    - Color palette management
    - Alpha transparency handling
    - Color utility functions
    - Theme color variations
    """
    
    # Modern color palette
    COLORS = {
        "primary": "#6366f1",  # Indigo
        "primary_light": "#818cf8",  # Light indigo
        "primary_dark": "#4f46e5",  # Dark indigo
        "secondary": "#8b5cf6",  # Purple
        "accent": "#06b6d4",  # Cyan
        "success": "#10b981",  # Emerald
        "warning": "#f59e0b",  # Amber
        "error": "#ef4444",  # Red
        "surface": "#1f2937",  # Dark gray
        "surface_light": "#374151",  # Medium gray
        "surface_lighter": "#4b5563",  # Light gray
        "background": "#111827",  # Very dark gray
        "text_primary": "#f9fafb",  # Almost white
        "text_secondary": "#d1d5db",  # Light gray
        "text_muted": "#9ca3af",  # Medium gray
        "border": "#374151",  # Medium gray
        "border_light": "#4b5563",  # Light gray
    }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.debug("ColorManager initialized")
    
    def get_color(self, color_name: str, alpha: float = 1.0) -> str:
        """
        Get color with optional alpha transparency.
        
        Args:
            color_name: Name of the color from the palette
            alpha: Alpha transparency (0.0 - 1.0)
            
        Returns:
            Color string (hex or rgba)
        """
        if color_name not in self.COLORS:
            self.logger.warning(f"Unknown color: {color_name}")
            return self.COLORS["text_primary"]

        color = self.COLORS[color_name]
        if alpha < 1.0:
            # Convert hex to rgba
            return self._hex_to_rgba(color, alpha)
        return color
    
    def _hex_to_rgba(self, hex_color: str, alpha: float) -> str:
        """
        Convert hex color to rgba with alpha.
        
        Args:
            hex_color: Hex color string (e.g., "#6366f1")
            alpha: Alpha value (0.0 - 1.0)
            
        Returns:
            RGBA color string
        """
        try:
            color = hex_color.lstrip("#")
            r, g, b = tuple(int(color[i : i + 2], 16) for i in (0, 2, 4))
            return f"rgba({r}, {g}, {b}, {alpha})"
        except (ValueError, IndexError) as e:
            self.logger.warning(f"Invalid hex color {hex_color}: {e}")
            return self.COLORS["text_primary"]
    
    def get_color_variant(self, base_color: str, variant: str) -> str:
        """
        Get a variant of a base color (light, dark).
        
        Args:
            base_color: Base color name
            variant: Variant type ('light', 'dark')
            
        Returns:
            Color string for the variant
        """
        variant_key = f"{base_color}_{variant}"
        if variant_key in self.COLORS:
            return self.COLORS[variant_key]
        
        # Fallback to base color if variant doesn't exist
        self.logger.debug(f"Variant {variant_key} not found, using base color {base_color}")
        return self.get_color(base_color)
    
    def get_gradient_colors(self, start_color: str, end_color: str, start_alpha: float = 1.0, end_alpha: float = 1.0) -> tuple:
        """
        Get gradient color pair for CSS gradients.
        
        Args:
            start_color: Starting color name
            end_color: Ending color name
            start_alpha: Alpha for start color
            end_alpha: Alpha for end color
            
        Returns:
            Tuple of (start_color_string, end_color_string)
        """
        start = self.get_color(start_color, start_alpha)
        end = self.get_color(end_color, end_alpha)
        return (start, end)
    
    def get_theme_colors(self) -> Dict[str, str]:
        """
        Get all theme colors for external use.
        
        Returns:
            Dictionary of all available colors
        """
        return self.COLORS.copy()
    
    def is_valid_color(self, color_name: str) -> bool:
        """
        Check if a color name is valid.
        
        Args:
            color_name: Color name to check
            
        Returns:
            True if color exists in palette
        """
        return color_name in self.COLORS
    
    def get_contrast_color(self, background_color: str) -> str:
        """
        Get appropriate text color for given background.
        
        Args:
            background_color: Background color name
            
        Returns:
            Appropriate text color (primary or secondary)
        """
        # Simple logic - can be enhanced with actual contrast calculation
        dark_backgrounds = ["background", "surface", "surface_light", "primary_dark"]
        
        if background_color in dark_backgrounds:
            return self.get_color("text_primary")
        else:
            return self.get_color("text_secondary")
    
    def create_color_scheme(self, primary_color: str) -> Dict[str, str]:
        """
        Create a color scheme based on a primary color.
        
        Args:
            primary_color: Primary color name
            
        Returns:
            Dictionary with related colors
        """
        return {
            "primary": self.get_color(primary_color),
            "primary_light": self.get_color_variant(primary_color, "light"),
            "primary_dark": self.get_color_variant(primary_color, "dark"),
            "text": self.get_contrast_color(primary_color),
            "border": self.get_color("border"),
            "surface": self.get_color("surface"),
        }
