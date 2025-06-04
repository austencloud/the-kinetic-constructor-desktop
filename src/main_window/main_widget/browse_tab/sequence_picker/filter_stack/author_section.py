# author_section.py (refactored)

import os
from typing import TYPE_CHECKING
from PyQt6.QtWidgets import (
    QVBoxLayout,
    QLabel,
    QGridLayout,
    QSpacerItem,
    QSizePolicy,
)
from PyQt6.QtCore import Qt
from functools import partial

from main_window.main_widget.metadata_extractor import MetaDataExtractor
from styles.styled_button import StyledButton
from utils.path_helpers import get_data_path

from .filter_section_base import FilterSectionBase
from src.settings_manager.global_settings.app_context import AppContext

if TYPE_CHECKING:
    from .sequence_picker_filter_stack import SequencePickerFilterStack


class AuthorSection(FilterSectionBase):
    MAX_COLUMNS = 3

    def __init__(self, initial_selection_widget: "SequencePickerFilterStack"):
        super().__init__(initial_selection_widget, "Select by Author:")
        self.main_widget = initial_selection_widget.browse_tab.main_widget
        self.buttons: dict[str, StyledButton] = {}
        self.tally_labels: dict[str, QLabel] = {}
        self.sequence_counts: dict[str, int] = {}
        self.add_buttons()

    def add_buttons(self):
        """Initialize the UI components for the author selection."""
        self.header_label.show()

        layout: QVBoxLayout = self.layout()

        # Using the new data manager:
        data_manager = AppContext.dictionary_data_manager()
        all_authors = data_manager.get_distinct_authors()

        # Build an author -> count map
        # (like your old _get_sequence_counts_per_author)
        for author in all_authors:
            these_records = data_manager.get_records_by_author(author)
            self.sequence_counts[author] = len(these_records)

        grid_layout = QGridLayout()
        grid_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grid_layout.setHorizontalSpacing(20)
        grid_layout.setVerticalSpacing(20)

        row, col = 0, 0
        for author in sorted(self.sequence_counts.keys()):
            vbox = self._create_author_vbox(author)
            grid_layout.addLayout(vbox, row, col)

            col += 1
            if col >= self.MAX_COLUMNS:
                col = 0
                row += 1

        layout.addLayout(grid_layout)
        layout.addStretch(1)

    def _create_author_vbox(self, author: str) -> QVBoxLayout:
        vbox = QVBoxLayout()
        vbox.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btn = self._create_author_button(author)
        label = self._create_sequence_count_label(author)
        vbox.addWidget(btn)
        vbox.addItem(
            QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        )
        vbox.addWidget(label)
        return vbox

    def _create_author_button(self, author: str) -> StyledButton:
        button = StyledButton(author)
        button.setMinimumSize(120, 30)
        button.setMaximumSize(200, 40)

        # INSTANT SWITCHING: Use instant handler instead of direct connection
        instant_handler = self.create_instant_button_handler(
            lambda: self.handle_author_click(author), f"Author: {author}"
        )
        button.clicked.connect(instant_handler)

        self.buttons[author] = button
        return button

    def _create_sequence_count_label(self, author: str) -> QLabel:
        count = self.sequence_counts.get(author, 0)
        seq_text = "sequence" if count == 1 else "sequences"
        lbl = QLabel(f"{count} {seq_text}")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.tally_labels[author] = lbl
        return lbl

    def handle_author_click(self, author: str):
        """Just pass the filter to your FilterController as you do now."""
        self.browse_tab.filter_controller.apply_filter({"author": author})

    # The rest is mostly the same, except we have no _get_all_sequences_with_authors,
    # no repeated dictionary_dir scanning, etc.

    def _get_all_sequences_with_authors(self) -> list[tuple[str, list[str], str]]:
        """Retrieve and cache all sequences along with their authors."""
        if hasattr(self, "_all_sequences_with_authors"):
            return self._all_sequences_with_authors

        dictionary_dir = get_data_path("dictionary")
        base_words = [
            (
                word,
                self.main_widget.thumbnail_finder.find_thumbnails(
                    os.path.join(dictionary_dir, word)
                ),
            )
            for word in os.listdir(dictionary_dir)
            if os.path.isdir(os.path.join(dictionary_dir, word))
            and "__pycache__" not in word
        ]

        sequences_with_authors = []
        for word, thumbnails in base_words:
            author = self.get_sequence_author(thumbnails)
            if author is not None:
                sequences_with_authors.append((word, thumbnails, author))

        self._all_sequences_with_authors = sequences_with_authors
        return sequences_with_authors

    def _get_sequence_counts_per_author(self) -> dict[str, int]:
        """Compute the number of sequences available for each author."""
        author_counts: dict[str, int] = {}
        sequences_with_authors = self._get_all_sequences_with_authors()
        for _, _, author in sequences_with_authors:
            author_counts[author] = author_counts.get(author, 0) + 1
        return author_counts

    def get_sequences_by_author(self, author: str) -> list[tuple[str, list[str]]]:
        """Retrieve sequences that correspond to a specific author."""
        sequences_with_authors = self._get_all_sequences_with_authors()
        return [
            (word, thumbnails)
            for word, thumbnails, seq_author in sequences_with_authors
            if seq_author == author
        ]

    def get_sequence_author(self, thumbnails: list[str]) -> str:
        """Extract the author from the metadata of the thumbnails."""
        for thumbnail in thumbnails:
            author = MetaDataExtractor().get_author(thumbnail)
            if author:
                return author
        return None

    def get_sequence_length_from_thumbnails(self, thumbnails: list[str]) -> int:
        """Extract the sequence length from the thumbnails' metadata."""
        for thumbnail in thumbnails:
            length = self.metadata_extractor.get_length(thumbnail)
            if length is not None:
                return length
        return 0

    def resizeEvent(self, event):
        """Handle resizing of the author section."""
        self.resize_buttons()
        self.resize_labels()
        super().resizeEvent(event)

    def resize_labels(self):
        """Adjust font sizes of labels during resizing."""
        font_size_label = max(10, self.main_widget.width() // 140)
        font_size_header = max(12, self.main_widget.width() // 100)

        for label in self.tally_labels.values():
            font = label.font()
            font.setPointSize(font_size_label)
            label.setFont(font)

        font = self.header_label.font()
        font.setPointSize(font_size_header)
        self.header_label.setFont(font)

    def resize_buttons(self):
        """Adjust button sizes and fonts during resizing."""
        button_width = max(1, self.main_widget.width() // 6)
        button_height = max(1, self.main_widget.height() // 16)
        font_size_button = max(10, self.main_widget.width() // 100)

        for button in self.buttons.values():
            font = button.font()
            font.setPointSize(font_size_button)
            button.setFont(font)
            button.setFixedSize(button_width, button_height)
