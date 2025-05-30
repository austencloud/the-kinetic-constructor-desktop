"""
Styling components for glassmorphism design system using coordinator pattern.

This package contains the refactored components that were extracted from
the monolithic GlassmorphismStyler class to follow the Single Responsibility Principle.
"""

from styles.glassmorphism_coordinator import GlassmorphismCoordinator
from styles.color_manager import ColorManager
from styles.typography_manager import TypographyManager
from styles.component_styler import ComponentStyler
from styles.effect_manager import EffectManager
from styles.layout_styler import LayoutStyler

__all__ = [
    "GlassmorphismCoordinator",
    "ColorManager",
    "TypographyManager",
    "ComponentStyler",
    "EffectManager",
    "LayoutStyler",
]
