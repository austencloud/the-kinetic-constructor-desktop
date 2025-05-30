"""
Glassmorphism Styler for modern UI design with translucent backgrounds and blur effects.

Now uses coordinator pattern with focused components for better maintainability.
"""

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QWidget

from styles.glassmorphism_coordinator import GlassmorphismCoordinator

# Import the new coordinator and components


class GlassmorphismStyler:
    """
    Glassmorphism styler - now a lightweight wrapper around GlassmorphismCoordinator.

    This maintains backward compatibility while using the new refactored architecture
    with focused components following the Single Responsibility Principle.
    """

    # Class-level coordinator instance for backward compatibility
    _coordinator = None

    @classmethod
    def _get_coordinator(cls) -> GlassmorphismCoordinator:
        """Get or create the coordinator instance."""
        if cls._coordinator is None:
            cls._coordinator = GlassmorphismCoordinator()
        return cls._coordinator

    # Backward compatibility class attributes
    @classmethod
    def _init_class_attributes(cls):
        """Initialize class attributes from coordinator."""
        coordinator = cls._get_coordinator()
        cls.COLORS = coordinator.color_manager.COLORS
        cls.FONTS = coordinator.typography_manager.FONTS
        cls.SPACING = coordinator.component_styler.SPACING
        cls.RADIUS = coordinator.component_styler.RADIUS

    def __init_subclass__(cls, **kwargs):
        """Initialize class attributes when class is created."""
        super().__init_subclass__(**kwargs)
        cls._init_class_attributes()

    # Initialize class attributes immediately
    COLORS = {}
    FONTS = {}
    SPACING = {}
    RADIUS = {}

    @classmethod
    def get_color(cls, color_name: str, alpha: float = 1.0) -> str:
        """Get color with optional alpha transparency."""
        return cls._get_coordinator().get_color(color_name, alpha)

    @classmethod
    def get_font(cls, font_type: str) -> QFont:
        """Get font with specified type."""
        return cls._get_coordinator().get_font(font_type)

    @classmethod
    def create_glassmorphism_card(
        cls,
        widget: QWidget,
        blur_radius: int = 10,
        opacity: float = 0.1,
        border_radius: int = 12,
    ) -> str:
        """
        Create glassmorphism card styling for a widget.

        Args:
            widget: The widget to style
            blur_radius: Blur effect radius
            opacity: Background opacity (0.0 - 1.0)
            border_radius: Corner radius

        Returns:
            CSS stylesheet string
        """
        return cls._get_coordinator().create_glassmorphism_card(
            widget, blur_radius, opacity, border_radius
        )

    @classmethod
    def create_modern_button(cls, button_type: str = "primary") -> str:
        """Create modern button styling."""
        return cls._get_coordinator().create_modern_button(button_type)

    @classmethod
    def create_modern_input(cls) -> str:
        """Create modern input field styling."""
        return cls._get_coordinator().create_modern_input()

    @classmethod
    def create_modern_toggle(cls) -> str:
        """Create modern toggle switch styling."""
        return cls._get_coordinator().create_modern_toggle()

    @classmethod
    def create_modern_slider(cls) -> str:
        """Create modern slider styling."""
        return cls._get_coordinator().create_modern_slider()

    @classmethod
    def create_sidebar_style(cls) -> str:
        """Create modern glassmorphism sidebar styling."""
        return cls._get_coordinator().create_sidebar_style()

    @classmethod
    def create_dialog_style(cls) -> str:
        """Create modern dialog styling."""
        return cls._get_coordinator().create_dialog_style()

    @classmethod
    def add_blur_effect(cls, widget: QWidget, blur_radius: int = 10):
        """Add blur effect to a widget."""
        return cls._get_coordinator().add_blur_effect(widget, blur_radius)

    @classmethod
    def add_shadow_effect(
        cls,
        widget: QWidget,
        offset_x: int = 0,
        offset_y: int = 4,
        blur_radius: int = 12,
        color: str = None,
    ):
        """Add drop shadow effect to a widget."""
        return cls._get_coordinator().add_shadow_effect(
            widget, offset_x, offset_y, blur_radius, color
        )

    @classmethod
    def create_unified_tab_content_style(cls) -> str:
        """Create comprehensive glassmorphism styling for all tab content."""
        return cls._get_coordinator().create_unified_tab_content_style()


# Initialize class attributes when module is loaded
GlassmorphismStyler._init_class_attributes()
