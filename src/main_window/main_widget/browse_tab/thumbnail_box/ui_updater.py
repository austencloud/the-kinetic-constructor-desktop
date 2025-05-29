from typing import TYPE_CHECKING
from PyQt6.QtCore import QTimer
from .thumbnail_box import ThumbnailBox

if TYPE_CHECKING:
    from main_window.main_widget.browse_tab.browse_tab import BrowseTab


class ThumbnailBoxUIUpdater:
    """Handles updating and styling of thumbnails."""

    def __init__(self, browse_tab: "BrowseTab"):
        self.browse_tab = browse_tab
        self.font_color_updater = self._get_font_color_updater()
        self._pending_updates = []
        self._update_timer = QTimer()
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(self._process_pending_updates)

    def update_thumbnail_image(self, thumbnail_box: "ThumbnailBox"):
        """Updates the thumbnail image of a given thumbnail box (synchronous)."""
        thumbnail_box.image_label.update_thumbnail(thumbnail_box.state.current_index)

    def update_thumbnail_image_async(self, thumbnail_box: "ThumbnailBox"):
        """Updates the thumbnail image asynchronously to prevent UI blocking."""
        # Add to pending updates queue
        self._pending_updates.append((thumbnail_box, thumbnail_box.state.current_index))

        # Start timer to process updates in batches (prevents overwhelming the UI)
        if not self._update_timer.isActive():
            self._update_timer.start(10)  # Process every 10ms

    def _process_pending_updates(self):
        """Process a batch of pending thumbnail updates with cache integration."""
        if not self._pending_updates:
            return

        # Process up to 3 thumbnails per batch to maintain responsiveness
        batch_size = min(3, len(self._pending_updates))

        for _ in range(batch_size):
            if self._pending_updates:
                thumbnail_box, index = self._pending_updates.pop(0)

                # Set word and variation for cache key generation
                if hasattr(thumbnail_box.image_label, "set_word_and_variation"):
                    thumbnail_box.image_label.set_word_and_variation(
                        thumbnail_box.word, index
                    )

                # Update thumbnail asynchronously
                thumbnail_box.image_label.update_thumbnail_async(index)

        # If more updates pending, schedule next batch
        if self._pending_updates:
            self._update_timer.start(10)

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
        tb.header.setStyleSheet(f"color: {font_color};")
        tb.header.favorite_button.star_icon_empty_path = star_icon_path
        tb.header.favorite_button.update_favorite_icon(
            tb.favorites_manager.favorite_status
        )
        tb.variation_number_label.setStyleSheet(f"color: {font_color};")

    def _get_font_color_updater(self):
        """Get the font color updater using the new MVVM architecture with graceful fallbacks."""
        try:
            # Try to get font_color_updater through the new coordinator pattern
            return self.browse_tab.main_widget.get_widget("font_color_updater")
        except AttributeError:
            # Fallback: try through widget_manager for backward compatibility
            try:
                return self.browse_tab.main_widget.widget_manager.get_widget(
                    "font_color_updater"
                )
            except AttributeError:
                # Final fallback: try direct access for legacy compatibility
                try:
                    if hasattr(self.browse_tab.main_widget, "font_color_updater"):
                        return self.browse_tab.main_widget.font_color_updater
                except AttributeError:
                    pass

        # Ultimate fallback: create a minimal font color updater with static method access
        class FallbackFontColorUpdater:
            @staticmethod
            def get_font_color(bg_type: str) -> str:
                return (
                    "black"
                    if bg_type in ["Rainbow", "AuroraBorealis", "Aurora"]
                    else "white"
                )

        return FallbackFontColorUpdater()
