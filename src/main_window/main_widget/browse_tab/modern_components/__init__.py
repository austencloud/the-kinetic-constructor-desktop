"""
Modern Components Package - 2025 Design System for Browse Tab

This package contains all the modern UI components implementing the 2025 design system
for the browse tab, including glassmorphism effects, smooth animations, and responsive layouts.
"""

from .modern_browse_integration import ModernBrowseIntegration
from .themes.modern_theme_manager import ModernThemeManager
from .animations.hover_animations import HoverAnimationManager
from .layouts.modern_grid_layout import ModernResponsiveGrid
from .cards.modern_thumbnail_card import ModernThumbnailCard
from .utils.change_logger import modernization_logger

__all__ = [
    "ModernBrowseIntegration",
    "ModernThemeManager", 
    "HoverAnimationManager",
    "ModernResponsiveGrid",
    "ModernThumbnailCard",
    "modernization_logger"
]

__version__ = "2025.1.0"
__author__ = "Modern UI Team"
__description__ = "2025 Modern Design System Components"
