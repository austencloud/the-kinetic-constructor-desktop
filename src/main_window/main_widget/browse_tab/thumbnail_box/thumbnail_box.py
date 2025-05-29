from typing import TYPE_CHECKING
from PyQt6.QtWidgets import QVBoxLayout, QWidget

from main_window.main_widget.browse_tab.thumbnail_box.favorites_manager import (
    ThumbnailBoxFavoritesManager,
)
from main_window.main_widget.browse_tab.thumbnail_box.nav_buttons_widget import (
    ThumbnailBoxNavButtonsWidget,
)
from main_window.main_widget.browse_tab.thumbnail_box.thumbnail_image_label import (
    ThumbnailImageLabel,
)

from .header import ThumbnailBoxHeader
from .variation_number_label import VariationNumberLabel
from .state import ThumbnailBoxState

if TYPE_CHECKING:
    from main_window.main_widget.browse_tab.browse_tab import BrowseTab


class ThumbnailBox(QWidget):
    margin = 10

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
        self.margin = 10  # Default margin
        self._preferred_width = 300  # Default preferred width

        self._setup_components()
        self._setup_layout()

    def _setup_components(self):
        self.favorites_manager = ThumbnailBoxFavoritesManager(self)
        self.header = ThumbnailBoxHeader(self)
        self.image_label = ThumbnailImageLabel(self)
        self.variation_number_label = VariationNumberLabel(self)
        self.nav_buttons_widget = ThumbnailBoxNavButtonsWidget(self)

    def _setup_layout(self):
        self.setContentsMargins(0, 0, 0, 0)
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.addWidget(self.header)
        layout.addWidget(self.image_label)
        layout.addWidget(self.nav_buttons_widget)
        layout.addStretch()
        layout.setContentsMargins(self.margin, self.margin, self.margin, self.margin)

    def sizeHint(self):
        """Provide size hint to the layout system instead of forcing fixed width."""
        from PyQt6.QtCore import QSize

        return QSize(self._preferred_width, super().sizeHint().height())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.resize_thumbnail_box()

    def resize_thumbnail_box(self):
        if self.in_sequence_viewer:
            # For sequence viewer, use the right stack's allocated width (1/3 ratio)
            available_width = self._get_sequence_viewer_available_width()
            # Use most of the available width, leaving some margin
            width = int(available_width * 0.95)

            # CRITICAL FIX: Don't call updateGeometry() for sequence viewer thumbnail boxes
            # This prevents the layout system from expanding the right stack beyond 1/3 width
            self._preferred_width = width
            # Instead of updateGeometry(), just update the image label directly
            if hasattr(self, "image_label"):
                self.image_label.update_thumbnail(self.state.current_index)
        else:
            nav_bar = self.sequence_picker.nav_sidebar
            if nav_bar.width() < 20:
                nav_bar.resize_sidebar()
            scrollbar_width = (
                self.sequence_picker.scroll_widget.calculate_scrollbar_width()
            )

            # RESPONSIVE LAYOUT FIX: Calculate available width more accurately
            # Get the actual scroll widget width (which already excludes the nav sidebar)
            scroll_widget = self.sequence_picker.scroll_widget
            scroll_widget_width = scroll_widget.width()

            # Account for scrollbar and margins
            scrollbar_width = scroll_widget.calculate_scrollbar_width()

            # HORIZONTAL OVERFLOW FIX: Account for ALL horizontal spacing elements
            # Each thumbnail box has 10px margin on left and right (20px total per box)
            # With 3 columns, that's 3 * 20px = 60px total for margins
            # Plus small buffer for any layout spacing
            total_margins = (
                3 * self.margin * 2
            ) + 10  # 3 boxes * 20px margins + 10px buffer

            # Calculate usable width for thumbnails (subtract scrollbar and all margins)
            usable_width = scroll_widget_width - scrollbar_width - total_margins

            # Divide by 3 for 3 columns, ensuring minimum width
            width = max(150, int(usable_width // 3))  # Minimum 150px per thumbnail

            # SMART FIX: Use size hint instead of fixed width to avoid forcing parent expansion
            self._preferred_width = width
            self.updateGeometry()  # Notify layout system of size hint change

    def _get_browse_tab_available_width(self) -> int:
        """Get the actual available width for the Browse Tab's left panel."""
        try:
            # Use the actual sequence picker width instead of calculating ratios
            # This respects the layout system's stretch factors
            sequence_picker = self.browse_tab.sequence_picker
            return sequence_picker.width()
        except (AttributeError, TypeError):
            # Emergency fallback
            return 800  # Reasonable default

    def _get_sequence_viewer_available_width(self) -> int:
        """Get the actual available width for the sequence viewer (right panel)."""
        try:
            # Use the actual sequence viewer width instead of calculating ratios
            # This respects the layout system's stretch factors
            sequence_viewer = self.browse_tab.sequence_viewer
            return sequence_viewer.width()
        except (AttributeError, TypeError):
            # Emergency fallback
            return 400  # Reasonable default width

    def update_thumbnails(self, thumbnails=None):
        if thumbnails is None:
            thumbnails = []
        self.state.update_thumbnails(thumbnails)
        self.nav_buttons_widget.state.thumbnails = thumbnails

        if self == self.browse_tab.sequence_viewer.state.matching_thumbnail_box:
            self.browse_tab.sequence_viewer.update_thumbnails(self.state.thumbnails)

        self.header.difficulty_label.update_difficulty_label()
        self.image_label.update_thumbnail(self.state.current_index)
