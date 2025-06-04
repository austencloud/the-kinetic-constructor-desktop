"""
Modern Theme Manager - 2025 Design System Foundation

MODERNIZATION LOG:
- Date: 2025-01-27
- Changes Made: Created comprehensive 2025 theme system with glassmorphism, gradients, and modern color palettes
- Performance Impact: Centralized theme management for consistent styling
- Breaking Changes: None (new component)
- Migration Notes: Use this for all new modern components
- Visual Changes: Establishes 2025 design foundation with glassmorphism and vibrant gradients
"""

import logging
from typing import Dict, Tuple, Optional
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QColor


class ModernThemeManager(QObject):
    """
    Centralized theme system for 2025 modern UI design.

    Features:
    - Dynamic color schemes (light/dark/auto)
    - Glassmorphic color palettes with proper transparency
    - Gradient definitions for modern visual appeal
    - Animation timing constants for consistent motion
    - Responsive breakpoints for adaptive layouts
    - Typography scale for proper hierarchy
    - Spacing system for consistent layouts
    """

    # Signal emitted when theme changes
    theme_changed = pyqtSignal(str)  # theme_name

    # 2025 Modern Color Palette
    COLORS_2025 = {
        # Primary Brand Colors - Vibrant and Modern
        "primary": "#6366f1",  # Indigo - Main brand color
        "primary_light": "#818cf8",  # Light indigo for hover states
        "primary_dark": "#4f46e5",  # Dark indigo for pressed states
        "primary_glow": "#a5b4fc",  # Glow effect color
        # Secondary Colors - Purple gradient family
        "secondary": "#8b5cf6",  # Purple
        "secondary_light": "#a78bfa",  # Light purple
        "secondary_dark": "#7c3aed",  # Dark purple
        # Accent Colors - Vibrant highlights
        "accent_cyan": "#06b6d4",  # Cyan for highlights
        "accent_emerald": "#10b981",  # Emerald for success
        "accent_amber": "#f59e0b",  # Amber for warnings
        "accent_rose": "#f43f5e",  # Rose for errors/attention
        "accent_violet": "#8b5cf6",  # Violet for special elements
        # Glassmorphism Base Colors
        "glass_white": "#ffffff",  # Pure white for light glass
        "glass_dark": "#000000",  # Pure black for dark glass
        "glass_neutral": "#6b7280",  # Neutral gray for balanced glass
        # Background System - Rich dark theme
        "bg_primary": "#0a0a0a",  # Deep black primary background
        "bg_secondary": "#1a1a1a",  # Dark gray secondary background
        "bg_tertiary": "#2a2a2a",  # Medium gray tertiary background
        "bg_elevated": "#3a3a3a",  # Elevated surface background
        # Surface Colors - For cards and containers
        "surface_glass": "#ffffff",  # Glass surface base (use with alpha)
        "surface_dark": "#1f2937",  # Dark surface
        "surface_medium": "#374151",  # Medium surface
        "surface_light": "#4b5563",  # Light surface
        # Text Colors - High contrast and readable
        "text_primary": "#f9fafb",  # Primary text (almost white)
        "text_secondary": "#d1d5db",  # Secondary text (light gray)
        "text_muted": "#9ca3af",  # Muted text (medium gray)
        "text_disabled": "#6b7280",  # Disabled text (dark gray)
        # Border Colors - Subtle and elegant
        "border_primary": "#374151",  # Primary border
        "border_light": "#4b5563",  # Light border
        "border_glass": "#ffffff",  # Glass border (use with alpha)
        "border_accent": "#6366f1",  # Accent border
    }

    # Glassmorphism Opacity Levels
    GLASS_OPACITY = {
        "subtle": 0.05,  # Very subtle glass effect
        "light": 0.1,  # Light glass effect
        "medium": 0.15,  # Medium glass effect
        "strong": 0.2,  # Strong glass effect
        "intense": 0.25,  # Intense glass effect
    }

    # Border Radius Scale - Rounded modern design
    RADIUS = {
        "xs": 4,  # Extra small - small buttons, inputs
        "sm": 8,  # Small - buttons, small cards
        "md": 12,  # Medium - standard cards, containers
        "lg": 16,  # Large - main cards, panels
        "xl": 20,  # Extra large - hero cards
        "xxl": 24,  # Double extra large - major containers
        "full": 9999,  # Full rounded - pills, circular elements
    }

    # Spacing System - Consistent layout spacing
    SPACING = {
        "xs": 4,  # Extra small spacing
        "sm": 8,  # Small spacing
        "md": 16,  # Medium spacing (base unit)
        "lg": 24,  # Large spacing
        "xl": 32,  # Extra large spacing
        "xxl": 48,  # Double extra large spacing
        "xxxl": 64,  # Triple extra large spacing
    }

    # Animation Timing - Smooth and responsive
    ANIMATION_TIMING = {
        "instant": 0,  # No animation
        "fast": 100,  # Fast transitions (hover feedback)
        "normal": 200,  # Normal transitions (standard UI)
        "slow": 300,  # Slow transitions (major changes)
        "dramatic": 500,  # Dramatic transitions (page changes)
    }

    # Animation Easing - Natural motion curves
    EASING_CURVES = {
        "ease_out": "cubic-bezier(0.25, 0.46, 0.45, 0.94)",
        "ease_in": "cubic-bezier(0.55, 0.055, 0.675, 0.19)",
        "ease_in_out": "cubic-bezier(0.645, 0.045, 0.355, 1)",
        "bounce": "cubic-bezier(0.68, -0.55, 0.265, 1.55)",
        "elastic": "cubic-bezier(0.175, 0.885, 0.32, 1.275)",
    }

    # Typography Scale - Modern hierarchy
    TYPOGRAPHY = {
        "display": {"size": 32, "weight": 700, "line_height": 1.2},  # Hero text
        "h1": {"size": 24, "weight": 600, "line_height": 1.3},  # Main headings
        "h2": {"size": 20, "weight": 500, "line_height": 1.4},  # Section headings
        "h3": {"size": 18, "weight": 500, "line_height": 1.4},  # Subsection headings
        "body_large": {
            "size": 16,
            "weight": 400,
            "line_height": 1.5,
        },  # Large body text
        "body": {"size": 14, "weight": 400, "line_height": 1.5},  # Standard body text
        "body_small": {
            "size": 12,
            "weight": 400,
            "line_height": 1.4,
        },  # Small body text
        "caption": {"size": 11, "weight": 500, "line_height": 1.3},  # Captions, labels
        "micro": {"size": 10, "weight": 500, "line_height": 1.2},  # Micro text
    }

    # Responsive Breakpoints
    BREAKPOINTS = {
        "mobile": 768,  # Mobile devices
        "tablet": 1024,  # Tablet devices
        "desktop": 1440,  # Desktop screens
        "large": 1920,  # Large desktop screens
    }

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self._current_theme = "dark"  # Default to dark theme
        self.logger.info("🎨 ModernThemeManager initialized with 2025 design system")

    def get_color(self, color_name: str, alpha: float = 1.0) -> str:
        """
        Get color with optional alpha transparency.

        Args:
            color_name: Name of the color from the 2025 palette
            alpha: Alpha transparency (0.0 - 1.0)

        Returns:
            Color string (hex or rgba)
        """
        if color_name not in self.COLORS_2025:
            self.logger.warning(f"Unknown color: {color_name}, using text_primary")
            color_name = "text_primary"

        color = self.COLORS_2025[color_name]

        if alpha < 1.0:
            return self._hex_to_rgba(color, alpha)
        return color

    def get_glassmorphism_color(
        self, base_color: str, opacity_level: str = "medium"
    ) -> str:
        """
        Get glassmorphism color with predefined opacity levels.

        Args:
            base_color: Base color name (usually glass_white or glass_dark)
            opacity_level: Opacity level from GLASS_OPACITY

        Returns:
            RGBA color string for glassmorphism effect
        """
        if opacity_level not in self.GLASS_OPACITY:
            opacity_level = "medium"

        opacity = self.GLASS_OPACITY[opacity_level]
        return self.get_color(base_color, opacity)

    def _hex_to_rgba(self, hex_color: str, alpha: float) -> str:
        """Convert hex color to rgba with alpha."""
        try:
            color = hex_color.lstrip("#")
            r, g, b = tuple(int(color[i : i + 2], 16) for i in (0, 2, 4))
            return f"rgba({r}, {g}, {b}, {alpha})"
        except (ValueError, IndexError) as e:
            self.logger.warning(f"Invalid hex color {hex_color}: {e}")
            return self.get_color("text_primary")

    def create_gradient(
        self,
        start_color: str,
        end_color: str,
        direction: str = "vertical",
        start_alpha: float = 1.0,
        end_alpha: float = 1.0,
    ) -> str:
        """
        Create CSS gradient string for modern visual effects.

        Args:
            start_color: Starting color name
            end_color: Ending color name
            direction: Gradient direction ('vertical', 'horizontal', 'diagonal')
            start_alpha: Alpha for start color
            end_alpha: Alpha for end color

        Returns:
            CSS gradient string
        """
        start = self.get_color(start_color, start_alpha)
        end = self.get_color(end_color, end_alpha)

        direction_map = {
            "vertical": "to bottom",
            "horizontal": "to right",
            "diagonal": "to bottom right",
            "radial": "radial-gradient(circle",
        }

        if direction == "radial":
            return f"radial-gradient(circle, {start}, {end})"
        else:
            css_direction = direction_map.get(direction, "to bottom")
            return f"linear-gradient({css_direction}, {start}, {end})"

    def get_spacing(self, size: str) -> int:
        """Get spacing value for consistent layouts."""
        return self.SPACING.get(size, self.SPACING["md"])

    def get_radius(self, size: str) -> int:
        """Get border radius for consistent rounded corners."""
        return self.RADIUS.get(size, self.RADIUS["md"])

    def get_animation_duration(self, speed: str) -> int:
        """Get animation duration in milliseconds."""
        return self.ANIMATION_TIMING.get(speed, self.ANIMATION_TIMING["normal"])

    def get_typography(self, style: str) -> Dict[str, any]:
        """Get typography settings for text hierarchy."""
        return self.TYPOGRAPHY.get(style, self.TYPOGRAPHY["body"])

    def create_glassmorphism_style(
        self,
        opacity_level: str = "medium",
        blur_radius: int = 10,
        border_radius: str = "lg",
    ) -> str:
        """
        Create complete glassmorphism CSS style.

        Args:
            opacity_level: Glass opacity level
            blur_radius: Backdrop blur radius (for reference)
            border_radius: Border radius size

        Returns:
            Complete CSS style string for glassmorphism effect
        """
        bg_color = self.get_glassmorphism_color("glass_white", opacity_level)
        border_color = self.get_glassmorphism_color("glass_white", "subtle")
        radius = self.get_radius(border_radius)

        return f"""
            background-color: {bg_color};
            border: 1px solid {border_color};
            border-radius: {radius}px;
            backdrop-filter: blur({blur_radius}px);
            -webkit-backdrop-filter: blur({blur_radius}px);
        """

    def create_hover_animation_style(
        self, scale: float = 1.05, duration: str = "fast", easing: str = "ease_out"
    ) -> str:
        """
        Create hover animation CSS style.

        Args:
            scale: Scale factor on hover
            duration: Animation duration key
            easing: Easing curve key

        Returns:
            CSS style string for hover animations
        """
        duration_ms = self.get_animation_duration(duration)
        easing_curve = self.EASING_CURVES.get(easing, self.EASING_CURVES["ease_out"])

        return f"""
            transition: transform {duration_ms}ms {easing_curve},
                       box-shadow {duration_ms}ms {easing_curve},
                       border-color {duration_ms}ms {easing_curve};

            &:hover {{
                transform: scale({scale});
                box-shadow: 0 10px 25px {self.get_color("bg_primary", 0.3)},
                           0 0 20px {self.get_color("primary", 0.2)};
                border-color: {self.get_color("primary", 0.6)};
            }}
        """

    def get_responsive_columns(self, container_width: int) -> int:
        """
        Calculate responsive column count based on container width.

        Args:
            container_width: Available container width in pixels

        Returns:
            Optimal number of columns for the given width
        """
        if container_width < self.BREAKPOINTS["mobile"]:
            return 1  # Mobile: single column
        elif container_width < self.BREAKPOINTS["tablet"]:
            return 2  # Tablet: two columns
        elif container_width < self.BREAKPOINTS["desktop"]:
            return 3  # Desktop: three columns
        else:
            return 4  # Large desktop: four columns

    def create_shadow_style(self, elevation: str = "medium") -> str:
        """
        Create modern shadow effects for depth.

        Args:
            elevation: Shadow elevation level

        Returns:
            CSS box-shadow string
        """
        shadows = {
            "subtle": f"0 1px 3px {self.get_color('bg_primary', 0.1)}",
            "medium": f"0 4px 12px {self.get_color('bg_primary', 0.15)}",
            "strong": f"0 8px 25px {self.get_color('bg_primary', 0.2)}",
            "dramatic": f"0 15px 35px {self.get_color('bg_primary', 0.25)}, 0 5px 15px {self.get_color('bg_primary', 0.1)}",
        }

        return shadows.get(elevation, shadows["medium"])

    def switch_theme(self, theme_name: str):
        """Switch to a different theme and emit signal."""
        if theme_name in ["light", "dark", "auto"]:
            self._current_theme = theme_name
            self.theme_changed.emit(theme_name)
            self.logger.info(f"🎨 Theme switched to: {theme_name}")

    @property
    def current_theme(self) -> str:
        """Get current theme name."""
        return self._current_theme
