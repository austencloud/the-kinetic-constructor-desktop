from typing import TYPE_CHECKING
from PyQt6.QtCore import QTimer
from .thumbnail_box.thumbnail_box import ThumbnailBox

if TYPE_CHECKING:
    from .browse_tab import BrowseTab


class BrowseTabPersistenceManager:
    """
    Manages the persistence and restoration of the browse tab state.
    Now includes background preloading for thumbnails.
    """

    def __init__(self, browse_tab: "BrowseTab") -> None:
        self.browse_tab = browse_tab
        self.preloading_paused = False  # 🆕 Flag to pause/resume background preloading
        self.thumbnail_queue = []  # 🆕 Queue of words to preload

    def apply_saved_browse_state(self):
        """Applies the saved browse state on startup."""
        state = self.browse_tab.state
        sequence_picker = self.browse_tab.sequence_picker
        filter_controller = self.browse_tab.filter_controller

        section_name = state.get_current_section()
        if not section_name:
            sequence_picker.filter_stack.show_filter_choice_widget()
        else:
            sequence_picker.filter_stack.show_section(section_name)

        filter_criteria = state.get_current_filter()
        selected_seq = state.get_selected_sequence()

        if selected_seq:
            word = selected_seq.get("word")
            var_index = selected_seq.get("variation_index", 0)
            self.browse_tab.sequence_viewer.reopen_thumbnail(word, var_index)

        if filter_criteria:
            filter_controller.apply_filter(filter_criteria, fade=False)

        # 🆕 Start background preloading after state is fully restored
        QTimer.singleShot(100, self.start_background_preloading)

    def start_background_preloading(self):
        """Begins preloading all thumbnail boxes asynchronously."""
        print("[INFO] Starting background preloading of thumbnails...")

        # Get all available words from the dictionary
        self.thumbnail_queue = [word for word, _ in self.browse_tab.get.base_words()]

        # Filter out words that already have thumbnail boxes
        existing_words = set(
            self.browse_tab.sequence_picker.scroll_widget.thumbnail_boxes.keys()
        )
        self.thumbnail_queue = [
            word for word in self.thumbnail_queue if word not in existing_words
        ]

        # Start preloading if there are thumbnails to load
        if self.thumbnail_queue:
            self.preload_next_thumbnail()

    def preload_next_thumbnail(self):
        """Preloads the next thumbnail box in the queue."""
        if self.preloading_paused or not self.thumbnail_queue:
            return  # Stop if preloading is paused or finished

        word = self.thumbnail_queue.pop(0)

        # ✅ Find the corresponding thumbnails correctly
        thumbnails = next(
            (thumbs for w, thumbs in self.browse_tab.get.base_words() if w == word), []
        )

        if thumbnails:
            self.add_thumbnail_box(word, thumbnails)

        # Continue preloading with a slight delay to keep UI responsive
        if self.thumbnail_queue:
            QTimer.singleShot(10, self.preload_next_thumbnail)

    def add_thumbnail_box(self, word: str, thumbnails: list[str]):
        """Adds a new thumbnail box to the scroll widget."""
        scroll_widget = self.browse_tab.sequence_picker.scroll_widget
        thumbnail_box = ThumbnailBox(self.browse_tab, word, thumbnails)
        scroll_widget.thumbnail_boxes[word] = thumbnail_box
        scroll_widget.grid_layout.addWidget(thumbnail_box)
        thumbnail_box.update_thumbnails(thumbnails)  # Ensure it loads properly
        thumbnail_box.image_label.update_thumbnail(thumbnail_box.state.current_index)
        thumbnail_box.hide()  # Hide the box until it's fully loaded
        print(f"[LOADED] Preloaded thumbnail box: {word}")

    def pause_preloading(self):
        """Pauses background preloading when user interacts with UI."""
        self.preloading_paused = True
        print("[PAUSED] Preloading paused due to user interaction.")

    def resume_preloading(self):
        """Resumes background preloading when user is idle."""
        if self.preloading_paused:
            self.preloading_paused = False
            print("[RESUMED] Resuming background preloading...")
            self.preload_next_thumbnail()
