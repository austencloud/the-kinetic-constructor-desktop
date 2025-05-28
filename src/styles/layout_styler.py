"""
Layout Styler - Handles complex layout and container styling.

Extracted from GlassmorphismStyler to follow Single Responsibility Principle.
"""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .color_manager import ColorManager
    from .typography_manager import TypographyManager
    from .component_styler import ComponentStyler


class LayoutStyler:
    """
    Handles styling for complex layouts and containers.
    
    Responsibilities:
    - Dialog and container styling
    - Layout-specific CSS generation
    - Unified styling for complex layouts
    - Responsive styling utilities
    """
    
    def __init__(
        self, 
        color_manager: "ColorManager", 
        typography_manager: "TypographyManager",
        component_styler: "ComponentStyler"
    ):
        self.color_manager = color_manager
        self.typography_manager = typography_manager
        self.component_styler = component_styler
        self.logger = logging.getLogger(__name__)
        self.logger.debug("LayoutStyler initialized")
    
    def create_sidebar_style(self) -> str:
        """
        Create modern glassmorphism sidebar styling.
        
        Returns:
            CSS stylesheet string for sidebars
        """
        surface_color = self.color_manager.get_color("surface", 0.4)
        surface_light = self.color_manager.get_color("surface_light", 0.3)
        border_color = self.color_manager.get_color("border", 0.2)
        text_secondary = self.color_manager.get_color("text_secondary")
        text_primary = self.color_manager.get_color("text_primary")
        primary_color = self.color_manager.get_color("primary", 0.3)
        primary_light = self.color_manager.get_color("primary_light", 0.2)
        
        spacing_md = self.component_styler.get_spacing("md")
        spacing_sm = self.component_styler.get_spacing("sm")
        spacing_lg = self.component_styler.get_spacing("lg")
        spacing_xs = self.component_styler.get_spacing("xs")
        
        radius_lg = self.component_styler.get_radius("lg")
        radius_md = self.component_styler.get_radius("md")
        
        font_size = self.typography_manager.get_font_size("body_medium")

        return f"""
        QListWidget {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {surface_color},
                stop:0.5 {surface_light},
                stop:1 {surface_color});
            border: 1px solid {border_color};
            border-radius: {radius_lg}px;
            padding: {spacing_md}px {spacing_sm}px;
            outline: none;
        }}

        QListWidget::item {{
            background-color: transparent;
            color: {text_secondary};
            padding: {spacing_md}px {spacing_lg}px;
            border-radius: {radius_md}px;
            margin: {spacing_xs}px 0;
            font-size: {font_size}px;
            font-weight: 500;
            min-height: 32px;
        }}

        QListWidget::item:selected {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {primary_color},
                stop:1 {primary_light});
            color: {text_primary};
            border: 1px solid {self.color_manager.get_color('primary', 0.4)};
            font-weight: 600;
        }}

        QListWidget::item:hover:!selected {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {self.color_manager.get_color('surface_light', 0.6)},
                stop:1 {self.color_manager.get_color('surface_lighter', 0.4)});
            color: {text_primary};
            border: 1px solid {self.color_manager.get_color('border_light', 0.3)};
        }}

        QListWidget::item:focus {{
            outline: none;
        }}
        """
    
    def create_dialog_style(self) -> str:
        """
        Create modern dialog styling.
        
        Returns:
            CSS stylesheet string for dialogs
        """
        bg_color = self.color_manager.get_color("background")
        text_color = self.color_manager.get_color("text_primary")
        radius_xl = self.component_styler.get_radius("xl")

        return f"""
        QDialog {{
            background-color: {bg_color};
            color: {text_color};
            border-radius: {radius_xl}px;
        }}
        """
    
    def create_unified_tab_content_style(self) -> str:
        """
        Create comprehensive glassmorphism styling for all tab content.
        
        Returns:
            CSS stylesheet string for unified tab content
        """
        # Get colors
        surface_color = self.color_manager.get_color("surface", 0.05)
        surface_light = self.color_manager.get_color("surface_light", 0.03)
        border_color = self.color_manager.get_color("border", 0.15)
        border_light = self.color_manager.get_color("border_light", 0.3)
        text_primary = self.color_manager.get_color("text_primary")
        primary_color = self.color_manager.get_color("primary", 0.8)
        text_muted = self.color_manager.get_color("text_muted")
        
        # Get spacing and radius
        spacing_lg = self.component_styler.get_spacing("lg")
        spacing_md = self.component_styler.get_spacing("md")
        spacing_sm = self.component_styler.get_spacing("sm")
        radius_lg = self.component_styler.get_radius("lg")
        radius_md = self.component_styler.get_radius("md")
        radius_sm = self.component_styler.get_radius("sm")
        
        # Get typography
        heading_size = self.typography_manager.get_font_size("heading_small")
        body_size = self.typography_manager.get_font_size("body_medium")

        return f"""
        /* Base tab content styling */
        QWidget[objectName="tab_content"] {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {surface_color},
                stop:0.5 {surface_light},
                stop:1 {surface_color});
            border: 1px solid {border_color};
            border-radius: {radius_lg}px;
            padding: {spacing_lg}px;
        }}

        /* Group boxes with glassmorphism */
        QGroupBox {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {self.color_manager.get_color('surface', 0.1)},
                stop:1 {self.color_manager.get_color('surface_light', 0.08)});
            border: 1px solid {border_light};
            border-radius: {radius_md}px;
            padding: {spacing_lg}px {spacing_md}px;
            margin-top: {spacing_md}px;
            font-size: {heading_size}px;
            font-weight: 600;
            color: {text_primary};
        }}

        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 {spacing_sm}px;
            background: {primary_color};
            border-radius: {radius_sm}px;
            color: {text_primary};
            font-weight: 600;
            margin-left: {spacing_md}px;
        }}

        /* Modern form elements */
        QLineEdit, QTextEdit, QComboBox, QSpinBox {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {self.color_manager.get_color('surface', 0.6)},
                stop:1 {self.color_manager.get_color('surface_light', 0.4)});
            border: 1px solid {self.color_manager.get_color('border', 0.4)};
            border-radius: {radius_md}px;
            padding: {spacing_sm}px {spacing_md}px;
            color: {text_primary};
            font-size: {body_size}px;
            min-height: 32px;
            selection-background-color: {self.color_manager.get_color('primary', 0.3)};
        }}

        QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus {{
            border: 2px solid {self.color_manager.get_color('primary', 0.8)};
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {self.color_manager.get_color('surface_light', 0.7)},
                stop:1 {self.color_manager.get_color('surface_lighter', 0.5)});
        }}

        QLineEdit:hover, QTextEdit:hover, QComboBox:hover, QSpinBox:hover {{
            border-color: {self.color_manager.get_color('border_light', 0.6)};
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {self.color_manager.get_color('surface_light', 0.6)},
                stop:1 {self.color_manager.get_color('surface_lighter', 0.4)});
        }}
        """
    
    def create_unified_button_style(self) -> str:
        """
        Create unified button styling for layouts.
        
        Returns:
            CSS stylesheet string for unified buttons
        """
        primary_color = self.color_manager.get_color("primary", 0.9)
        primary_dark = self.color_manager.get_color("primary_dark", 0.8)
        primary_light = self.color_manager.get_color("primary_light", 0.9)
        text_primary = self.color_manager.get_color("text_primary")
        surface_light = self.color_manager.get_color("surface_light", 0.3)
        text_muted = self.color_manager.get_color("text_muted")
        
        spacing_sm = self.component_styler.get_spacing("sm")
        spacing_lg = self.component_styler.get_spacing("lg")
        radius_md = self.component_styler.get_radius("md")
        
        body_size = self.typography_manager.get_font_size("body_medium")

        return f"""
        /* Modern buttons */
        QPushButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {primary_color},
                stop:1 {primary_dark});
            color: {text_primary};
            border: 1px solid {self.color_manager.get_color('primary', 0.5)};
            border-radius: {radius_md}px;
            padding: {spacing_sm}px {spacing_lg}px;
            font-size: {body_size}px;
            font-weight: 500;
            min-height: 36px;
            min-width: 80px;
        }}

        QPushButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {primary_light},
                stop:1 {primary_color});
            border: 1px solid {self.color_manager.get_color('primary_light', 0.7)};
            transform: translateY(-1px);
        }}

        QPushButton:pressed {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {self.color_manager.get_color('primary_dark', 0.9)},
                stop:1 {self.color_manager.get_color('primary_dark', 0.7)});
            border: 1px solid {self.color_manager.get_color('primary_dark', 0.8)};
            transform: translateY(1px);
        }}

        QPushButton:disabled {{
            background: {surface_light};
            color: {text_muted};
            border: 1px solid {self.color_manager.get_color('border', 0.2)};
        }}
        """
    
    def create_unified_checkbox_style(self) -> str:
        """
        Create unified checkbox styling for layouts.
        
        Returns:
            CSS stylesheet string for unified checkboxes
        """
        text_primary = self.color_manager.get_color("text_primary")
        surface_color = self.color_manager.get_color("surface", 0.6)
        border_color = self.color_manager.get_color("border", 0.5)
        primary_color = self.color_manager.get_color("primary")
        
        spacing_md = self.component_styler.get_spacing("md")
        spacing_sm = self.component_styler.get_spacing("sm")
        radius_sm = self.component_styler.get_radius("sm")
        
        body_size = self.typography_manager.get_font_size("body_medium")

        return f"""
        /* Modern checkboxes */
        QCheckBox {{
            color: {text_primary};
            font-size: {body_size}px;
            spacing: {spacing_md}px;
            padding: {spacing_sm}px 0;
        }}

        QCheckBox::indicator {{
            width: 20px;
            height: 20px;
            border-radius: {radius_sm}px;
            background: {surface_color};
            border: 2px solid {border_color};
        }}

        QCheckBox::indicator:checked {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {primary_color},
                stop:1 {self.color_manager.get_color('primary_light')});
            border-color: {primary_color};
        }}

        QCheckBox::indicator:hover {{
            border-color: {self.color_manager.get_color('border_light')};
        }}
        """
