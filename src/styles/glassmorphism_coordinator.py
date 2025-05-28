"""
Glassmorphism Coordinator - Orchestrates all styling components.

This coordinator replaces the monolithic GlassmorphismStyler with a clean
architecture that follows the Single Responsibility Principle.
"""

import logging
from typing import Optional
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QFont

from .color_manager import ColorManager
from .typography_manager import TypographyManager
from .component_styler import ComponentStyler
from .effect_manager import EffectManager
from .layout_styler import LayoutStyler


class GlassmorphismCoordinator:
    """
    Coordinates all glassmorphism styling operations using focused components.
    
    This coordinator orchestrates:
    - Color management and palette handling
    - Typography system and font management
    - Component styling (buttons, inputs, etc.)
    - Visual effects (blur, shadows)
    - Layout and container styling
    
    Each responsibility is handled by a dedicated component following SRP.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize specialized components
        self.color_manager = ColorManager()
        self.typography_manager = TypographyManager()
        self.component_styler = ComponentStyler(self.color_manager, self.typography_manager)
        self.effect_manager = EffectManager()
        self.layout_styler = LayoutStyler(
            self.color_manager, 
            self.typography_manager, 
            self.component_styler
        )
        
        self.logger.info("GlassmorphismCoordinator initialized with component architecture")
    
    # Color Management Methods
    def get_color(self, color_name: str, alpha: float = 1.0) -> str:
        """Get color with optional alpha transparency."""
        return self.color_manager.get_color(color_name, alpha)
    
    def get_color_variant(self, base_color: str, variant: str) -> str:
        """Get a variant of a base color (light, dark)."""
        return self.color_manager.get_color_variant(base_color, variant)
    
    def get_gradient_colors(self, start_color: str, end_color: str, start_alpha: float = 1.0, end_alpha: float = 1.0) -> tuple:
        """Get gradient color pair for CSS gradients."""
        return self.color_manager.get_gradient_colors(start_color, end_color, start_alpha, end_alpha)
    
    # Typography Methods
    def get_font(self, font_type: str, family: str = "primary") -> QFont:
        """Get QFont object with specified type and family."""
        return self.typography_manager.get_font(font_type, family)
    
    def get_font_css(self, font_type: str, family: str = "primary") -> str:
        """Get CSS font properties for specified type."""
        return self.typography_manager.get_font_css(font_type, family)
    
    def get_text_style_css(self, font_type: str, color: str, family: str = "primary") -> str:
        """Get complete text styling CSS."""
        return self.typography_manager.get_text_style_css(font_type, color, family)
    
    # Component Styling Methods
    def create_modern_button(self, button_type: str = "primary") -> str:
        """Create modern button styling."""
        return self.component_styler.create_modern_button(button_type)
    
    def create_modern_input(self) -> str:
        """Create modern input field styling."""
        return self.component_styler.create_modern_input()
    
    def create_modern_toggle(self) -> str:
        """Create modern toggle switch styling."""
        return self.component_styler.create_modern_toggle()
    
    def create_modern_slider(self) -> str:
        """Create modern slider styling."""
        return self.component_styler.create_modern_slider()
    
    def create_glassmorphism_card(
        self,
        widget: Optional[QWidget] = None,
        blur_radius: int = 10,
        opacity: float = 0.1,
        border_radius: int = 12,
    ) -> str:
        """Create glassmorphism card styling for a widget."""
        return self.component_styler.create_glassmorphism_card(blur_radius, opacity, border_radius)
    
    # Effect Management Methods
    def add_blur_effect(self, widget: QWidget, blur_radius: int = 10) -> bool:
        """Add blur effect to a widget."""
        return self.effect_manager.add_blur_effect(widget, blur_radius)
    
    def add_shadow_effect(
        self,
        widget: QWidget,
        offset_x: int = 0,
        offset_y: int = 4,
        blur_radius: int = 12,
        color: str = None,
    ) -> bool:
        """Add drop shadow effect to a widget."""
        return self.effect_manager.add_shadow_effect(widget, offset_x, offset_y, blur_radius, color)
    
    def add_card_shadow(self, widget: QWidget) -> bool:
        """Add card-style shadow effect."""
        return self.effect_manager.add_card_shadow(widget)
    
    def add_dialog_shadow(self, widget: QWidget) -> bool:
        """Add dialog-style shadow effect."""
        return self.effect_manager.add_dialog_shadow(widget)
    
    def remove_effects(self, widget: QWidget) -> bool:
        """Remove all graphics effects from a widget."""
        return self.effect_manager.remove_effects(widget)
    
    # Layout Styling Methods
    def create_sidebar_style(self) -> str:
        """Create modern glassmorphism sidebar styling."""
        return self.layout_styler.create_sidebar_style()
    
    def create_dialog_style(self) -> str:
        """Create modern dialog styling."""
        return self.layout_styler.create_dialog_style()
    
    def create_unified_tab_content_style(self) -> str:
        """Create comprehensive glassmorphism styling for all tab content."""
        return self.layout_styler.create_unified_tab_content_style()
    
    # Utility Methods
    def get_spacing(self, size: str) -> int:
        """Get spacing value for given size."""
        return self.component_styler.get_spacing(size)
    
    def get_radius(self, size: str) -> int:
        """Get border radius value for given size."""
        return self.component_styler.get_radius(size)
    
    def get_font_size(self, font_type: str) -> int:
        """Get font size for specified type."""
        return self.typography_manager.get_font_size(font_type)
    
    # Comprehensive Styling Methods
    def create_complete_dialog_style(self) -> str:
        """
        Create complete dialog styling combining all components.
        
        Returns:
            Complete CSS stylesheet for dialogs
        """
        dialog_style = self.layout_styler.create_dialog_style()
        tab_content_style = self.layout_styler.create_unified_tab_content_style()
        button_style = self.layout_styler.create_unified_button_style()
        checkbox_style = self.layout_styler.create_unified_checkbox_style()
        scroll_style = self.component_styler.create_scroll_area_style()
        
        return f"""
        {dialog_style}
        {tab_content_style}
        {button_style}
        {checkbox_style}
        {scroll_style}
        """
    
    def create_complete_component_style(self) -> str:
        """
        Create complete component styling for all UI elements.
        
        Returns:
            Complete CSS stylesheet for components
        """
        button_style = self.create_modern_button()
        input_style = self.create_modern_input()
        toggle_style = self.create_modern_toggle()
        slider_style = self.create_modern_slider()
        
        return f"""
        {button_style}
        {input_style}
        {toggle_style}
        {slider_style}
        """
    
    def apply_complete_styling(self, widget: QWidget, include_effects: bool = True) -> None:
        """
        Apply complete glassmorphism styling to a widget.
        
        Args:
            widget: Widget to style
            include_effects: Whether to include visual effects
        """
        # Apply CSS styling
        complete_style = self.create_complete_dialog_style()
        widget.setStyleSheet(complete_style)
        
        # Apply visual effects if requested
        if include_effects:
            self.add_dialog_shadow(widget)
        
        self.logger.debug(f"Applied complete glassmorphism styling to {widget.objectName()}")
    
    def get_performance_stats(self) -> dict:
        """
        Get performance statistics from all components.
        
        Returns:
            Dictionary with component statistics
        """
        return {
            "components_initialized": 5,
            "color_palette_size": len(self.color_manager.COLORS),
            "font_types_available": len(self.typography_manager.FONTS),
            "effect_presets": self.effect_manager.get_available_presets(),
            "coordinator_status": "active"
        }
