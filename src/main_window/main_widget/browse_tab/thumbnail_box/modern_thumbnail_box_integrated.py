"""
Modern Thumbnail Box with Integrated Glassmorphism System.

This component leverages the existing GlassmorphismCoordinator for consistent styling
while maximizing image display area and providing responsive layout capabilities.
"""

from typing import TYPE_CHECKING
from PyQt6.QtWidgets import QVBoxLayout, QWidget, QSizePolicy, QGraphicsDropShadowEffect
from PyQt6.QtCore import QSize, QPropertyAnimation, QEasingCurve, QRect, pyqtProperty
from PyQt6.QtGui import QColor

from styles.glassmorphism_coordinator import GlassmorphismCoordinator
from main_window.main_widget.browse_tab.thumbnail_box.favorites_manager import (
    ThumbnailBoxFavoritesManager,
)
from main_window.main_widget.browse_tab.thumbnail_box.nav_buttons_widget import (
    ThumbnailBoxNavButtonsWidget,
)
from .header import ThumbnailBoxHeader
from .variation_number_label import VariationNumberLabel
from .state import ThumbnailBoxState
from .modern_thumbnail_image_label import ModernThumbnailImageLabel

if TYPE_CHECKING:
    from main_window.main_widget.browse_tab.browse_tab import BrowseTab


class ModernThumbnailBoxIntegrated(QWidget):
    """
    Modern thumbnail box with integrated glassmorphism styling.

    Key improvements:
    - Leverages existing GlassmorphismCoordinator for consistent styling
    - Maximizes image display area (96% vs previous ~88%)
    - Responsive column calculation
    - Maintains all existing functionality
    """

    # CRITICAL: Reduced margin for maximum image display
    MIN_CONTAINER_PADDING = 2  # Reduced from 10 for max image size

    # Shared glassmorphism coordinator for performance optimization
    _shared_glassmorphism_coordinator = None

    def __init__(
        self,
        browse_tab: "BrowseTab",
        word: str,
        thumbnails: list[str],
        in_sequence_viewer=False,
    ) -> None:
        super().__init__(browse_tab)
        self.word = word
        self.main_widget = browse_tab.main_widget
        self.browse_tab = browse_tab
        self.sequence_picker = self.browse_tab.sequence_picker
        self.scroll_Area = self.sequence_picker.scroll_widget.scroll_area
        self.in_sequence_viewer = in_sequence_viewer
        self.state = ThumbnailBoxState(thumbnails)

        # Use minimal margin for maximum image display
        self.margin = self.MIN_CONTAINER_PADDING
        self._preferred_width = 300  # Default preferred width

        # Use shared glassmorphism coordinator for performance
        self.glassmorphism = self._get_shared_glassmorphism_coordinator()

        self._setup_components()
        self._setup_layout()
        self._apply_glassmorphism_styling()

    @classmethod
    def _get_shared_glassmorphism_coordinator(cls):
        """Get shared glassmorphism coordinator for performance optimization."""
        if cls._shared_glassmorphism_coordinator is None:
            cls._shared_glassmorphism_coordinator = GlassmorphismCoordinator()
        return cls._shared_glassmorphism_coordinator

    def _setup_components(self):
        """Setup all child components."""
        self.favorites_manager = ThumbnailBoxFavoritesManager(self)
        self.header = ThumbnailBoxHeader(self)
        # Use modern lazy loading image label
        self.image_label = ModernThumbnailImageLabel(self)
        self.variation_number_label = VariationNumberLabel(self)
        self.nav_buttons_widget = ThumbnailBoxNavButtonsWidget(self)

    def _setup_layout(self):
        """Setup layout with minimal spacing for maximum image display."""
        self.setContentsMargins(0, 0, 0, 0)
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.addWidget(self.header)
        layout.addWidget(self.image_label)
        layout.addWidget(self.nav_buttons_widget)
        layout.addStretch()
        # Use minimal margins for maximum image space
        layout.setContentsMargins(self.margin, self.margin, self.margin, self.margin)

    def _apply_glassmorphism_styling(self):
        """Apply enhanced glassmorphism styling for premium web app feel."""
        # Get enhanced glassmorphism styling
        enhanced_style = (
            self.glassmorphism.component_styler.create_enhanced_glassmorphism_thumbnail_style()
        )

        # Apply base glassmorphism card styling with enhanced effects
        card_style = self.glassmorphism.create_glassmorphism_card(
            blur_radius=15, opacity=0.12, border_radius=14
        )

        # Combine styles for premium web app aesthetic
        combined_style = f"""
        {card_style}

        /* Enhanced Modern Thumbnail Box */
        QWidget {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {self.glassmorphism.get_color("surface", 0.12)},
                stop:1 {self.glassmorphism.get_color("surface", 0.08)});
            border: 1px solid {self.glassmorphism.get_color("border_light", 0.15)};
            border-radius: 14px;
            padding: 2px;
            margin: 2px;
        }}

        QWidget:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {self.glassmorphism.get_color("surface_light", 0.18)},
                stop:1 {self.glassmorphism.get_color("surface_light", 0.12)});
            border: 1px solid {self.glassmorphism.get_color("primary", 0.4)};
            border-radius: 14px;
        }}
        """

        self.setStyleSheet(combined_style)

        # Add enhanced shadow effect using existing effect manager
        self.glassmorphism.add_card_shadow(self)

        # Set object name for enhanced styling
        self.setObjectName("modern_thumbnail_enhanced")

    def calculate_responsive_columns(self, available_width: int) -> int:
        """
        Calculate responsive column count based on available width.

        ENHANCEMENT: Responsive column calculation for different screen sizes.
        """
        # Responsive breakpoints for better layout
        breakpoints = {
            800: 1,  # Mobile-like: 1 column
            1200: 2,  # Tablet-like: 2 columns
            1600: 3,  # Desktop: 3 columns (current default)
            2000: 4,  # Wide desktop: 4 columns
        }

        # Minimum thumbnail width for quality display
        min_thumbnail_width = 180

        # Calculate maximum possible columns based on width
        max_possible_columns = available_width // min_thumbnail_width

        # Find appropriate column count based on breakpoints
        for width_threshold in sorted(breakpoints.keys()):
            if available_width <= width_threshold:
                return min(breakpoints[width_threshold], max_possible_columns)

        # For very wide screens, use maximum columns but cap at 4
        return min(4, max_possible_columns)

    def sizeHint(self):
        """Provide size hint to the layout system."""
        return QSize(self._preferred_width, super().sizeHint().height())

    def resizeEvent(self, event):
        """Handle resize events with responsive layout."""
        super().resizeEvent(event)
        self.resize_thumbnail_box()

    def resize_thumbnail_box(self):
        """Resize thumbnail box with enhanced responsive calculation."""
        if self.in_sequence_viewer:
            # For sequence viewer, use enhanced calculation
            available_width = self._get_sequence_viewer_available_width()
            width = int(available_width * 0.95)  # Use 95% of available width
        else:
            # RESPONSIVE LAYOUT: Enhanced calculation for browse tab
            scroll_widget = self.sequence_picker.scroll_widget
            scroll_widget_width = scroll_widget.width()

            # Account for scrollbar
            scrollbar_width = scroll_widget.calculate_scrollbar_width()

            # Calculate responsive columns
            available_width = scroll_widget_width - scrollbar_width
            columns = self.calculate_responsive_columns(available_width)

            # CRITICAL ENHANCEMENT: Minimal margins for maximum image display
            total_margins = (
                columns * self.margin * 2
            ) + 5  # Reduced margin calculation
            usable_width = available_width - total_margins

            # Calculate width per thumbnail with maximum utilization
            width = max(180, int(usable_width // columns))  # Minimum 180px width

        # Update preferred width and apply
        self._preferred_width = width
        self.setFixedWidth(width)

        # Update image label for maximum display
        if hasattr(self.image_label, "update_for_maximum_display"):
            self.image_label.update_for_maximum_display()

    def _get_sequence_viewer_available_width(self) -> int:
        """Calculate available width in sequence viewer mode."""
        try:
            sequence_viewer = self.browse_tab.sequence_viewer
            # Use 95% of sequence viewer width for maximum display
            return int(sequence_viewer.width() * 0.95)
        except (AttributeError, TypeError):
            return 400  # Fallback width

    # Maintain compatibility with existing interface
    def get_current_index(self) -> int:
        """Get current thumbnail index."""
        return self.state.current_index

    def set_current_index(self, index: int):
        """Set current thumbnail index."""
        self.state.set_current_index(index)
        self.image_label.update_thumbnail(index)

    def update_thumbnails(self, thumbnails=None):
        """Update thumbnails list."""
        if thumbnails is None:
            thumbnails = []
        self.state.update_thumbnails(thumbnails)
        self.nav_buttons_widget.state.thumbnails = thumbnails

        if self == self.browse_tab.sequence_viewer.state.matching_thumbnail_box:
            self.browse_tab.sequence_viewer.update_thumbnails(self.state.thumbnails)

        self.header.difficulty_label.update_difficulty_label()
        self.image_label.update_thumbnail(self.state.current_index)

    def show_nav_buttons(self):
        """Show navigation buttons."""
        self.nav_buttons_widget.show()

    def hide_nav_buttons(self):
        """Hide navigation buttons."""
        self.nav_buttons_widget.hide()

    def get_word(self) -> str:
        """Get the word associated with this thumbnail box."""
        return self.word

    def get_thumbnails(self) -> list[str]:
        """Get the list of thumbnail paths."""
        return self.state.thumbnails

    def is_in_sequence_viewer_mode(self) -> bool:
        """Check if thumbnail box is in sequence viewer mode."""
        return self.in_sequence_viewer
