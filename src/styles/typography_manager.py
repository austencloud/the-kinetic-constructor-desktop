"""
Typography Manager - Handles font management and typography system.

Extracted from GlassmorphismStyler to follow Single Responsibility Principle.
"""

import logging
from typing import Dict, Any
from PyQt6.QtGui import QFont


class TypographyManager:
    """
    Manages typography system including fonts, sizes, and text styling.
    
    Responsibilities:
    - Font configuration and management
    - Typography scale and sizing
    - Font weight and style handling
    - Text styling utilities
    """
    
    # Typography scale
    FONTS = {
        "heading_large": {"size": 24, "weight": "bold"},
        "heading_medium": {"size": 20, "weight": "bold"},
        "heading_small": {"size": 16, "weight": "bold"},
        "body_large": {"size": 14, "weight": "normal"},
        "body_medium": {"size": 12, "weight": "normal"},
        "body_small": {"size": 10, "weight": "normal"},
        "caption": {"size": 9, "weight": "normal"},
    }
    
    # Font families for different contexts
    FONT_FAMILIES = {
        "primary": "Segoe UI, system-ui, sans-serif",
        "monospace": "Consolas, Monaco, 'Courier New', monospace",
        "serif": "Georgia, 'Times New Roman', serif",
    }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.debug("TypographyManager initialized")
    
    def get_font(self, font_type: str, family: str = "primary") -> QFont:
        """
        Get QFont object with specified type and family.
        
        Args:
            font_type: Font type from FONTS dictionary
            family: Font family type
            
        Returns:
            Configured QFont object
        """
        if font_type not in self.FONTS:
            self.logger.warning(f"Unknown font type: {font_type}, using body_medium")
            font_type = "body_medium"

        font_config = self.FONTS[font_type]
        font = QFont()
        
        # Set font family
        if family in self.FONT_FAMILIES:
            font.setFamily(self.FONT_FAMILIES[family])
        
        # Set font size
        font.setPointSize(font_config["size"])

        # Set font weight
        if font_config["weight"] == "bold":
            font.setBold(True)
        elif font_config["weight"] == "normal":
            font.setBold(False)

        return font
    
    def get_font_css(self, font_type: str, family: str = "primary") -> str:
        """
        Get CSS font properties for specified type.
        
        Args:
            font_type: Font type from FONTS dictionary
            family: Font family type
            
        Returns:
            CSS font properties string
        """
        if font_type not in self.FONTS:
            font_type = "body_medium"
            
        font_config = self.FONTS[font_type]
        font_family = self.FONT_FAMILIES.get(family, self.FONT_FAMILIES["primary"])
        
        weight = "600" if font_config["weight"] == "bold" else "400"
        
        return f"""
            font-family: {font_family};
            font-size: {font_config["size"]}px;
            font-weight: {weight};
        """
    
    def get_text_style_css(self, font_type: str, color: str, family: str = "primary") -> str:
        """
        Get complete text styling CSS.
        
        Args:
            font_type: Font type from FONTS dictionary
            color: Text color
            family: Font family type
            
        Returns:
            Complete CSS text styling
        """
        font_css = self.get_font_css(font_type, family)
        return f"""
            {font_css}
            color: {color};
        """
    
    def get_font_size(self, font_type: str) -> int:
        """
        Get font size for specified type.
        
        Args:
            font_type: Font type from FONTS dictionary
            
        Returns:
            Font size in pixels
        """
        if font_type not in self.FONTS:
            font_type = "body_medium"
        return self.FONTS[font_type]["size"]
    
    def get_font_weight(self, font_type: str) -> str:
        """
        Get font weight for specified type.
        
        Args:
            font_type: Font type from FONTS dictionary
            
        Returns:
            Font weight string
        """
        if font_type not in self.FONTS:
            font_type = "body_medium"
        return self.FONTS[font_type]["weight"]
    
    def create_heading_css(self, level: int, color: str) -> str:
        """
        Create CSS for heading levels.
        
        Args:
            level: Heading level (1-3)
            color: Text color
            
        Returns:
            CSS for heading
        """
        heading_types = {
            1: "heading_large",
            2: "heading_medium", 
            3: "heading_small"
        }
        
        font_type = heading_types.get(level, "heading_medium")
        return self.get_text_style_css(font_type, color)
    
    def create_body_text_css(self, size: str, color: str) -> str:
        """
        Create CSS for body text.
        
        Args:
            size: Size variant (large, medium, small)
            color: Text color
            
        Returns:
            CSS for body text
        """
        font_type = f"body_{size}"
        return self.get_text_style_css(font_type, color)
    
    def get_line_height(self, font_type: str) -> float:
        """
        Get recommended line height for font type.
        
        Args:
            font_type: Font type from FONTS dictionary
            
        Returns:
            Line height multiplier
        """
        # Standard line height recommendations
        line_heights = {
            "heading_large": 1.2,
            "heading_medium": 1.3,
            "heading_small": 1.4,
            "body_large": 1.5,
            "body_medium": 1.5,
            "body_small": 1.4,
            "caption": 1.3,
        }
        
        return line_heights.get(font_type, 1.5)
    
    def get_typography_scale(self) -> Dict[str, Any]:
        """
        Get the complete typography scale.
        
        Returns:
            Dictionary with all font configurations
        """
        return self.FONTS.copy()
    
    def is_valid_font_type(self, font_type: str) -> bool:
        """
        Check if font type is valid.
        
        Args:
            font_type: Font type to check
            
        Returns:
            True if font type exists
        """
        return font_type in self.FONTS
