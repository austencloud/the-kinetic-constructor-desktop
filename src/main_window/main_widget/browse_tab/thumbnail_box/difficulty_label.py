from PyQt6.QtWidgets import QToolButton
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QSize
from typing import TYPE_CHECKING

from main_window.main_widget.metadata_extractor import MetaDataExtractor
from main_window.main_widget.sequence_workbench.labels.difficulty_level_icon import (
    DifficultyLevelIcon,
)

if TYPE_CHECKING:
    from .thumbnail_box import ThumbnailBox


class ThumbnailBoxDifficultyLabel(QToolButton):
    def __init__(self, thumbnail_box: "ThumbnailBox"):
        """Handles drawing difficulty level labels in the thumbnail box."""
        super().__init__(thumbnail_box)
        self.thumbnail_box = thumbnail_box
        self.main_widget = thumbnail_box.main_widget
        self.metadata_extractor = MetaDataExtractor()
        self.setToolTip("Difficulty Level")
        self.setCheckable(False)
        self.setStyleSheet("border: none; background: transparent;")  # Clean look

        self.difficulty_level = 1  # Default level
        self.update_difficulty_label()  # Fetch from metadata

    def update_difficulty_label(self):
        """Fetches the difficulty level from the **current** thumbnail's metadata."""
        current_thumbnail = self.thumbnail_box.state.get_current_thumbnail()
        if not current_thumbnail:
            self.hide()
            return

        metadata = self.metadata_extractor.get_full_metadata(current_thumbnail)
        sequence = metadata.get("sequence", [])
        if not sequence:
            self.hide()
            return

        difficulty_level = (
            self.main_widget.sequence_level_evaluator.get_sequence_difficulty_level(
                sequence
            )
        )

        if difficulty_level in ("", None):
            self.hide()
        else:
            self.show()
            self.set_difficulty_level(difficulty_level)

    def set_difficulty_level(self, level: int):
        """Sets the difficulty level and updates the display."""
        self.difficulty_level = level
        self.update_icon()

    def update_icon(self):
        """Updates the size of the icon dynamically based on intended thumbnail box size."""
        # DIFFICULTY LABEL SIZING FIX: Use intended final layout dimensions
        intended_width = self._get_intended_thumbnail_width()
        size = max(24, intended_width // 12)  # Ensure min size
        self.setIcon(QIcon(DifficultyLevelIcon.get_pixmap(self.difficulty_level, size)))
        self.setIconSize(QSize(size, size))
        self.setFixedSize(size, size)

    def _get_intended_thumbnail_width(self):
        """Calculate the intended final width for thumbnail boxes in the 3-column grid."""
        try:
            if self.thumbnail_box.in_sequence_viewer:
                # For sequence viewer, use current thumbnail box width
                return self.thumbnail_box.width()

            # For browse tab, calculate intended width based on final layout
            scroll_widget = self.thumbnail_box.sequence_picker.scroll_widget
            scroll_widget_width = scroll_widget.width()

            # Use the same calculation as thumbnail_box.resize_thumbnail_box()
            scrollbar_width = scroll_widget.calculate_scrollbar_width()

            # Account for ALL horizontal spacing elements
            total_margins = (
                3 * self.thumbnail_box.margin * 2
            ) + 10  # 3 boxes * 20px margins + 10px buffer

            # Calculate usable width for thumbnails
            usable_width = scroll_widget_width - scrollbar_width - total_margins

            # Divide by 3 for 3 columns, ensuring minimum width
            intended_width = max(150, int(usable_width // 3))

            return intended_width

        except (AttributeError, TypeError, ZeroDivisionError):
            # Fallback to current width if calculation fails
            return max(150, self.thumbnail_box.width())

    def resizeEvent(self, event):
        """Resizes the difficulty label when the thumbnail box resizes."""
        super().resizeEvent(event)
        self.update_icon()
