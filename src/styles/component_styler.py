"""
Component Styler - Handles styling for individual UI components.

Extracted from GlassmorphismStyler to follow Single Responsibility Principle.
"""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .color_manager import ColorManager
    from .typography_manager import TypographyManager


class ComponentStyler:
    """
    Handles styling for individual UI components.

    Responsibilities:
    - Individual component styling (buttons, inputs, toggles)
    - Component-specific CSS generation
    - Hover and focus state management
    - Component interaction styling
    """

    # Spacing scale
    SPACING = {
        "xs": 4,
        "sm": 8,
        "md": 16,
        "lg": 24,
        "xl": 32,
        "xxl": 48,
    }

    # Border radius scale
    RADIUS = {
        "sm": 4,
        "md": 8,
        "lg": 12,
        "xl": 16,
        "full": 9999,
    }

    def __init__(
        self, color_manager: "ColorManager", typography_manager: "TypographyManager"
    ):
        self.color_manager = color_manager
        self.typography_manager = typography_manager
        self.logger = logging.getLogger(__name__)
        self.logger.debug("ComponentStyler initialized")

    def create_modern_button(self, button_type: str = "primary") -> str:
        """
        Create modern button styling.

        Args:
            button_type: 'primary', 'secondary', 'success', 'warning', 'error'

        Returns:
            CSS stylesheet string for buttons
        """
        base_color = self.color_manager.get_color(button_type)
        hover_color = self.color_manager.get_color_variant(button_type, "light")
        pressed_color = self.color_manager.get_color_variant(button_type, "dark")
        text_color = self.color_manager.get_color("text_primary")
        disabled_bg = self.color_manager.get_color("surface_light")
        disabled_text = self.color_manager.get_color("text_muted")

        font_size = self.typography_manager.get_font_size("body_medium")

        return f"""
        QPushButton {{
            background-color: {base_color};
            color: {text_color};
            border: none;
            border-radius: {self.RADIUS['md']}px;
            padding: {self.SPACING['sm']}px {self.SPACING['md']}px;
            font-size: {font_size}px;
            font-weight: 500;
            min-height: 32px;
        }}

        QPushButton:hover {{
            background-color: {hover_color};
            border: 1px solid {self.color_manager.get_color('primary_light', 0.5)};
        }}

        QPushButton:pressed {{
            background-color: {pressed_color};
            border: 1px solid {self.color_manager.get_color('primary_dark', 0.7)};
        }}

        QPushButton:disabled {{
            background-color: {disabled_bg};
            color: {disabled_text};
        }}
        """

    def create_modern_input(self) -> str:
        """
        Create modern input field styling.

        Returns:
            CSS stylesheet string for input fields
        """
        bg_color = self.color_manager.get_color("surface", 0.5)
        border_color = self.color_manager.get_color("border")
        focus_border = self.color_manager.get_color("primary")
        hover_border = self.color_manager.get_color("border_light")
        text_color = self.color_manager.get_color("text_primary")
        font_size = self.typography_manager.get_font_size("body_medium")

        return f"""
        QLineEdit, QTextEdit, QComboBox {{
            background-color: {bg_color};
            border: 1px solid {border_color};
            border-radius: {self.RADIUS['md']}px;
            padding: {self.SPACING['sm']}px {self.SPACING['md']}px;
            color: {text_color};
            font-size: {font_size}px;
            min-height: 32px;
        }}

        QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{
            border-color: {focus_border};
            background-color: {self.color_manager.get_color('surface', 0.7)};
        }}

        QLineEdit:hover, QTextEdit:hover, QComboBox:hover {{
            border-color: {hover_border};
        }}
        """

    def create_modern_toggle(self) -> str:
        """
        Create modern toggle switch styling.

        Returns:
            CSS stylesheet string for toggle switches
        """
        text_color = self.color_manager.get_color("text_primary")
        bg_color = self.color_manager.get_color("surface_light")
        border_color = self.color_manager.get_color("border")
        checked_color = self.color_manager.get_color("primary")
        hover_border = self.color_manager.get_color("border_light")
        font_size = self.typography_manager.get_font_size("body_medium")

        return f"""
        QCheckBox {{
            color: {text_color};
            font-size: {font_size}px;
            spacing: {self.SPACING['sm']}px;
        }}

        QCheckBox::indicator {{
            width: 48px;
            height: 24px;
            border-radius: 12px;
            background-color: {bg_color};
            border: 1px solid {border_color};
        }}

        QCheckBox::indicator:checked {{
            background-color: {checked_color};
            border-color: {checked_color};
        }}

        QCheckBox::indicator:hover {{
            border-color: {hover_border};
        }}
        """

    def create_modern_slider(self) -> str:
        """
        Create modern slider styling.

        Returns:
            CSS stylesheet string for sliders
        """
        groove_color = self.color_manager.get_color("surface_light")
        handle_color = self.color_manager.get_color("primary")
        handle_hover = self.color_manager.get_color("primary_light")
        track_color = self.color_manager.get_color("primary")

        return f"""
        QSlider::groove:horizontal {{
            height: 6px;
            background-color: {groove_color};
            border-radius: 3px;
        }}

        QSlider::handle:horizontal {{
            background-color: {handle_color};
            border: 2px solid {handle_color};
            width: 20px;
            height: 20px;
            border-radius: 10px;
            margin: -7px 0;
        }}

        QSlider::handle:horizontal:hover {{
            background-color: {handle_hover};
            border-color: {handle_hover};
        }}

        QSlider::sub-page:horizontal {{
            background-color: {track_color};
            border-radius: 3px;
        }}
        """

    def create_glassmorphism_card(
        self,
        blur_radius: int = 10,
        opacity: float = 0.1,
        border_radius: int = 12,
    ) -> str:
        """
        Create glassmorphism card styling.

        Args:
            blur_radius: Blur effect radius (not used in CSS, for reference)
            opacity: Background opacity (0.0 - 1.0)
            border_radius: Corner radius

        Returns:
            CSS stylesheet string for glassmorphism cards
        """
        bg_color = self.color_manager.get_color("surface", opacity)
        border_color = self.color_manager.get_color("border_light", 0.3)
        hover_bg = self.color_manager.get_color("surface_light", opacity + 0.05)
        hover_border = self.color_manager.get_color("border_light", 0.5)

        return f"""
        QWidget {{
            background-color: {bg_color};
            border: 1px solid {border_color};
            border-radius: {border_radius}px;
            padding: {self.SPACING['md']}px;
        }}

        QWidget:hover {{
            background-color: {hover_bg};
            border-color: {hover_border};
        }}
        """

    def create_tab_widget_style(self) -> str:
        """
        Create modern tab widget styling.

        Returns:
            CSS stylesheet string for tab widgets
        """
        bg_color = self.color_manager.get_color("surface", 0.1)
        border_color = self.color_manager.get_color("border", 0.3)

        return f"""
        QTabWidget::pane {{
            background-color: {bg_color};
            border: 1px solid {border_color};
            border-radius: {self.RADIUS['lg']}px;
            padding: {self.SPACING['lg']}px;
        }}
        """

    def create_scroll_area_style(self) -> str:
        """
        Create modern scroll area styling.

        Returns:
            CSS stylesheet string for scroll areas
        """
        scrollbar_bg = self.color_manager.get_color("surface")
        handle_color = self.color_manager.get_color("surface_light")
        handle_hover = self.color_manager.get_color("surface_lighter")

        return f"""
        QScrollArea {{
            background-color: transparent;
            border: none;
        }}

        QScrollBar:vertical {{
            background-color: {scrollbar_bg};
            width: 12px;
            border-radius: 6px;
        }}

        QScrollBar::handle:vertical {{
            background-color: {handle_color};
            border-radius: 6px;
            min-height: 20px;
        }}

        QScrollBar::handle:vertical:hover {{
            background-color: {handle_hover};
        }}
        """

    def get_spacing(self, size: str) -> int:
        """
        Get spacing value for given size.

        Args:
            size: Spacing size key

        Returns:
            Spacing value in pixels
        """
        return self.SPACING.get(size, self.SPACING["md"])

    def get_radius(self, size: str) -> int:
        """
        Get border radius value for given size.

        Args:
            size: Radius size key

        Returns:
            Radius value in pixels
        """
        return self.RADIUS.get(size, self.RADIUS["md"])

    def create_thumbnail_system_style(self) -> str:
        """Create complete thumbnail styling using existing glassmorphism system."""
        bg_color = self.color_manager.get_color("surface", 0.05)
        border_color = self.color_manager.get_color("border_light", 0.1)
        hover_bg = self.color_manager.get_color("surface_light", 0.08)
        hover_border = self.color_manager.get_color("primary", 0.6)
        text_color = self.color_manager.get_color("text_primary")

        return f"""
        /* Modern Thumbnail Container */
        .modern-thumbnail-container {{
            background-color: {bg_color};
            border: 1px solid {border_color};
            border-radius: {self.RADIUS['lg']}px;
            padding: {self.SPACING['xs']}px;
            margin: {self.SPACING['xs']}px;
            transition: all 0.2s ease;
        }}

        .modern-thumbnail-container:hover {{
            background-color: {hover_bg};
            border-color: {hover_border};
        }}

        /* Thumbnail Header */
        .modern-thumbnail-header {{
            color: {text_color};
            font-size: 12px;
            font-weight: 500;
            margin-bottom: {self.SPACING['xs']}px;
        }}

        /* Image Container - Maximized Display */
        .modern-thumbnail-image {{
            border-radius: {self.RADIUS['md']}px;
            overflow: hidden;
        }}
        """

    def create_enhanced_glassmorphism_thumbnail_style(self) -> str:
        """Create enhanced glassmorphism styling for premium web app feel."""
        # Enhanced color palette with transparency
        bg_primary = self.color_manager.get_color("surface", 0.12)
        bg_hover = self.color_manager.get_color("surface_light", 0.18)
        border_primary = self.color_manager.get_color("border_light", 0.15)
        border_hover = self.color_manager.get_color("primary", 0.4)
        border_glow = self.color_manager.get_color("primary", 0.2)
        text_color = self.color_manager.get_color("text_primary")
        shadow_color = self.color_manager.get_color("background", 0.1)

        return f"""
        /* Enhanced Glassmorphism Thumbnail Container */
        QWidget[class="modern-thumbnail-enhanced"] {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {bg_primary},
                stop:1 {self.color_manager.get_color("surface", 0.08)});
            border: 1px solid {border_primary};
            border-radius: {self.RADIUS['lg']}px;
            padding: {self.SPACING['xs']}px;
            margin: {self.SPACING['xs']}px;
        }}

        QWidget[class="modern-thumbnail-enhanced"]:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {bg_hover},
                stop:1 {self.color_manager.get_color("surface_light", 0.12)});
            border: 1px solid {border_hover};
            border-radius: {self.RADIUS['lg']}px;
        }}

        /* Enhanced Image Container */
        QLabel[class="modern-thumbnail-image-enhanced"] {{
            border-radius: {self.RADIUS['md']}px;
            background: transparent;
            border: 1px solid {self.color_manager.get_color("border_light", 0.05)};
        }}

        QLabel[class="modern-thumbnail-image-enhanced"]:hover {{
            border: 1px solid {border_glow};
        }}
        """
