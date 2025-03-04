from typing import TYPE_CHECKING
from PyQt6.QtWidgets import QApplication
from .thumbnail_box import ThumbnailBox
from settings_manager.global_settings.app_context import AppContext

if TYPE_CHECKING:
    from main_window.main_widget.browse_tab.browse_tab import BrowseTab


class ThumbnailBoxUIUpdater:
    """Handles updating and styling of thumbnails."""

    def __init__(self, browse_tab: "BrowseTab"):
        self.browse_tab = browse_tab
        self.font_color_updater = browse_tab.main_widget.font_color_updater

    def update_thumbnail_image(self, thumbnail_box: "ThumbnailBox"):
        """Updates the thumbnail image of a given thumbnail box."""
        thumbnail_box.image_label.update_thumbnail(thumbnail_box.state.current_index)

    def apply_thumbnail_styling(self, background_type):
        """Applies styling (font color, star icon) to all thumbnails."""
        font_color = self.font_color_updater.get_font_color(background_type)
        star_icon_path = (
            "star_empty_white.png" if font_color == "white" else "star_empty_black.png"
        )

        for (
            tb
        ) in self.browse_tab.sequence_picker.scroll_widget.thumbnail_boxes.values():
            self._apply_single_thumbnail_style(tb, font_color, star_icon_path)

    def _apply_single_thumbnail_style(
        self, tb: "ThumbnailBox", font_color, star_icon_path
    ):
        """Applies styling to a single thumbnail box."""
        tb.word_label.setStyleSheet(f"color: {font_color};")
        tb.word_label.star_icon_empty_path = star_icon_path
        tb.word_label.reload_favorite_icon()
        tb.variation_number_label.setStyleSheet(f"color: {font_color};")
