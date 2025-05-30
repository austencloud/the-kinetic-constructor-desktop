"""
Effect Manager - Handles visual effects like blur and shadows.

Extracted from GlassmorphismStyler to follow Single Responsibility Principle.
"""

import logging
from PyQt6.QtWidgets import QWidget, QGraphicsBlurEffect, QGraphicsDropShadowEffect
from PyQt6.QtGui import QColor


class EffectManager:
    """
    Manages visual effects for glassmorphism design.
    
    Responsibilities:
    - Graphics effects (blur, shadow)
    - Effect application and management
    - Effect parameter handling
    - Visual enhancement utilities
    """
    
    # Effect presets
    BLUR_PRESETS = {
        "subtle": 5,
        "medium": 10,
        "strong": 15,
        "intense": 20,
    }
    
    SHADOW_PRESETS = {
        "subtle": {"offset_x": 0, "offset_y": 2, "blur_radius": 4},
        "medium": {"offset_x": 0, "offset_y": 4, "blur_radius": 8},
        "strong": {"offset_x": 0, "offset_y": 8, "blur_radius": 16},
        "card": {"offset_x": 0, "offset_y": 4, "blur_radius": 12},
        "dialog": {"offset_x": 0, "offset_y": 12, "blur_radius": 32},
    }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.debug("EffectManager initialized")
    
    def add_blur_effect(self, widget: QWidget, blur_radius: int = 10) -> bool:
        """
        Add blur effect to a widget.
        
        Args:
            widget: Widget to apply effect to
            blur_radius: Blur radius in pixels
            
        Returns:
            True if effect was applied successfully
        """
        try:
            blur_effect = QGraphicsBlurEffect()
            blur_effect.setBlurRadius(blur_radius)
            widget.setGraphicsEffect(blur_effect)
            self.logger.debug(f"Applied blur effect (radius: {blur_radius}) to {widget.objectName()}")
            return True
        except Exception as e:
            self.logger.warning(f"Could not apply blur effect: {e}")
            return False
    
    def add_blur_effect_preset(self, widget: QWidget, preset: str = "medium") -> bool:
        """
        Add blur effect using preset.
        
        Args:
            widget: Widget to apply effect to
            preset: Preset name from BLUR_PRESETS
            
        Returns:
            True if effect was applied successfully
        """
        if preset not in self.BLUR_PRESETS:
            self.logger.warning(f"Unknown blur preset: {preset}, using medium")
            preset = "medium"
        
        blur_radius = self.BLUR_PRESETS[preset]
        return self.add_blur_effect(widget, blur_radius)
    
    def add_shadow_effect(
        self,
        widget: QWidget,
        offset_x: int = 0,
        offset_y: int = 4,
        blur_radius: int = 12,
        color: str = None,
        opacity: float = 0.3,
    ) -> bool:
        """
        Add drop shadow effect to a widget.
        
        Args:
            widget: Widget to apply effect to
            offset_x: Horizontal shadow offset
            offset_y: Vertical shadow offset
            blur_radius: Shadow blur radius
            color: Shadow color (hex string)
            opacity: Shadow opacity (0.0 - 1.0)
            
        Returns:
            True if effect was applied successfully
        """
        try:
            shadow_effect = QGraphicsDropShadowEffect()
            shadow_effect.setOffset(offset_x, offset_y)
            shadow_effect.setBlurRadius(blur_radius)

            if color:
                shadow_color = QColor(color)
            else:
                shadow_color = QColor(0, 0, 0)  # Black
            
            # Apply opacity
            shadow_color.setAlphaF(opacity)
            shadow_effect.setColor(shadow_color)
            
            widget.setGraphicsEffect(shadow_effect)
            self.logger.debug(f"Applied shadow effect to {widget.objectName()}")
            return True
        except Exception as e:
            self.logger.warning(f"Could not apply shadow effect: {e}")
            return False
    
    def add_shadow_effect_preset(self, widget: QWidget, preset: str = "medium") -> bool:
        """
        Add shadow effect using preset.
        
        Args:
            widget: Widget to apply effect to
            preset: Preset name from SHADOW_PRESETS
            
        Returns:
            True if effect was applied successfully
        """
        if preset not in self.SHADOW_PRESETS:
            self.logger.warning(f"Unknown shadow preset: {preset}, using medium")
            preset = "medium"
        
        shadow_config = self.SHADOW_PRESETS[preset]
        return self.add_shadow_effect(
            widget,
            shadow_config["offset_x"],
            shadow_config["offset_y"],
            shadow_config["blur_radius"]
        )
    
    def add_card_shadow(self, widget: QWidget) -> bool:
        """
        Add card-style shadow effect.
        
        Args:
            widget: Widget to apply effect to
            
        Returns:
            True if effect was applied successfully
        """
        return self.add_shadow_effect_preset(widget, "card")
    
    def add_dialog_shadow(self, widget: QWidget) -> bool:
        """
        Add dialog-style shadow effect.
        
        Args:
            widget: Widget to apply effect to
            
        Returns:
            True if effect was applied successfully
        """
        return self.add_shadow_effect_preset(widget, "dialog")
    
    def remove_effects(self, widget: QWidget) -> bool:
        """
        Remove all graphics effects from a widget.
        
        Args:
            widget: Widget to remove effects from
            
        Returns:
            True if effects were removed successfully
        """
        try:
            widget.setGraphicsEffect(None)
            self.logger.debug(f"Removed effects from {widget.objectName()}")
            return True
        except Exception as e:
            self.logger.warning(f"Could not remove effects: {e}")
            return False
    
    def create_glow_effect(self, widget: QWidget, color: str = "#6366f1", intensity: int = 10) -> bool:
        """
        Create a glow effect using colored shadow.
        
        Args:
            widget: Widget to apply effect to
            color: Glow color (hex string)
            intensity: Glow intensity (blur radius)
            
        Returns:
            True if effect was applied successfully
        """
        return self.add_shadow_effect(
            widget,
            offset_x=0,
            offset_y=0,
            blur_radius=intensity,
            color=color,
            opacity=0.6
        )
    
    def get_available_presets(self) -> dict:
        """
        Get all available effect presets.
        
        Returns:
            Dictionary with blur and shadow presets
        """
        return {
            "blur": list(self.BLUR_PRESETS.keys()),
            "shadow": list(self.SHADOW_PRESETS.keys())
        }
