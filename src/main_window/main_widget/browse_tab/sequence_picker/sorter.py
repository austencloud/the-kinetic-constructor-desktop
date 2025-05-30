from datetime import datetime
from typing import TYPE_CHECKING
from main_window.main_widget.browse_tab.thumbnail_box.factory import (
    ThumbnailBoxFactory,
)

if TYPE_CHECKING:
    from main_window.main_widget.browse_tab.sequence_picker.sequence_picker import (
        SequencePicker,
    )


class SequencePickerSorter:
    num_columns: int = 3

    def __init__(self, sequence_picker: "SequencePicker"):
        self.sequence_picker = sequence_picker
        self.browse_tab = sequence_picker.browse_tab
        self.main_widget = self.browse_tab.main_widget
        self.scroll_widget = self.sequence_picker.scroll_widget

    def sort_and_display_currently_filtered_sequences_by_method(
        self, sort_method: str
    ) -> None:
        self.section_manager = self.sequence_picker.section_manager
        self.scroll_widget.clear_layout()
        self.browse_tab.sequence_picker.sections = {}

        sort_key = self.get_sort_key(sort_method)
        self.sort_sequences(sort_key, sort_method)
        self.group_sequences_by_section(sort_method)
        sorted_sections = self.section_manager.get_sorted_sections(
            sort_method, self.browse_tab.sequence_picker.sections.keys()
        )
        self.update_ui(sorted_sections, sort_method)

    def get_sort_key(self, sort_method: str) -> callable:
        sort_key_mapping = {
            "sequence_length": lambda seq_item: (
                seq_item[2] if seq_item[2] is not None else float("inf")
            ),
            "date_added": lambda seq_item: self.section_manager.get_date_added(
                seq_item[1]
            )
            or datetime.min,
            "level": lambda seq_item: seq_item[2],
        }
        return sort_key_mapping.get(sort_method, lambda seq_item: seq_item[0])

    def sort_sequences(self, sort_key, sort_method: str):
        self.browse_tab.sequence_picker.currently_displayed_sequences.sort(
            key=sort_key, reverse=(sort_method == "date_added")
        )

    def group_sequences_by_section(self, sort_method: str):
        for (
            word,
            thumbnails,
            seq_length,
        ) in self.browse_tab.sequence_picker.currently_displayed_sequences:
            section = self.section_manager.get_section_from_word(
                word, sort_method, seq_length, thumbnails
            )
            self.browse_tab.sequence_picker.sections.setdefault(section, []).append(
                (word, thumbnails)
            )

        if sort_method == "level":
            for level in ["1", "2", "3"]:
                if level not in self.browse_tab.sequence_picker.sections:
                    self.browse_tab.sequence_picker.sections[level] = []

    def _sort_only(self, sort_method: str):
        self.section_manager = self.sequence_picker.section_manager
        self.scroll_widget.clear_layout()
        self.browse_tab.sequence_picker.sections = {}

        sort_key = self.get_sort_key(sort_method)
        self.sort_sequences(sort_key, sort_method)
        self.group_sequences_by_section(sort_method)

    def display_sorted_sections(self, skip_scaling: bool = False):
        sort_method = (
            self.sequence_picker.control_panel.sort_widget.settings_manager.browse_settings.get_sort_method()
        )
        sorted_sections = self.sequence_picker.section_manager.get_sorted_sections(
            sort_method, self.browse_tab.sequence_picker.sections.keys()
        )
        self.update_ui(sorted_sections, sort_method, skip_scaling=skip_scaling)

    def update_ui(
        self, sorted_sections: list[str], sort_method: str, skip_scaling: bool = False
    ):
        self.sequence_picker.nav_sidebar.update_sidebar(sorted_sections, sort_method)
        self.sequence_picker.control_panel.sort_widget.sort_buttons_bar.highlight_button(
            sort_method
        )
        current_section = None
        row_index = 0

        for section in sorted_sections:
            if sort_method == "date_added" and section == "Unknown":
                continue

            row_index = self.add_section_headers(
                row_index, section, sort_method, current_section
            )
            if sort_method == "date_added":
                current_section = section

            column_index = 0
            for word, thumbnails in self.browse_tab.sequence_picker.sections[section]:
                self.add_thumbnail_box(
                    row_index,
                    column_index,
                    word,
                    thumbnails,
                    hidden=False,
                    skip_image=skip_scaling,
                )
                column_index = (column_index + 1) % self.num_columns
                if column_index == 0:
                    row_index += 1
        self.sequence_picker.control_panel.count_label.setText(
            f"Number of words: {len(self.browse_tab.sequence_picker.currently_displayed_sequences)}"
        )
        if not self.browse_tab.sequence_viewer.state.matching_thumbnail_box:
            word = (
                self.browse_tab.sequence_viewer.thumbnail_box.header.word_label.text()
            )
            self.browse_tab.sequence_viewer.set_current_thumbnail_box(word)

    def add_section_headers(
        self, row_index: int, section: str, sort_method: str, current_section: str
    ):
        if sort_method == "date_added":
            day, month, year = section.split("-")
            formatted_day = f"{int(day)}-{int(month)}"

            if year != current_section:
                row_index += 1
                self.sequence_picker.section_manager.add_header(
                    row_index, self.num_columns, year
                )
                row_index += 1
                current_section = year

            row_index += 1
            self.sequence_picker.section_manager.add_header(
                row_index, self.num_columns, formatted_day
            )
            row_index += 1
        elif sort_method == "level":
            row_index += 1
            header_title = f"Level {section}"
            self.sequence_picker.section_manager.add_header(
                row_index, self.num_columns, header_title
            )
            row_index += 1
        else:
            row_index += 1
            self.sequence_picker.section_manager.add_header(
                row_index, self.num_columns, section
            )
            row_index += 1
        return row_index

    def add_thumbnail_box(
        self,
        row_index: int,
        column_index: int,
        word: str,
        thumbnails: list[str],
        hidden: bool,
        skip_image: bool = False,
    ):
        if word not in self.scroll_widget.thumbnail_boxes:
            # Use modern integrated thumbnail box for enhanced display
            thumbnail_box = ThumbnailBoxFactory.create_integrated_thumbnail_box(
                self.browse_tab, word, thumbnails
            )
            self.scroll_widget.thumbnail_boxes[word] = thumbnail_box
        else:
            thumbnail_box = self.scroll_widget.thumbnail_boxes[word]

        if hidden:
            thumbnail_box.hide()

        self.scroll_widget.grid_layout.addWidget(thumbnail_box, row_index, column_index)

        if not hidden:
            thumbnail_box.show()

    def reload_currently_displayed_filtered_sequences(self):
        sort_method = (
            self.sequence_picker.control_panel.sort_widget.settings_manager.browse_settings.get_sort_method()
        )
        self.sort_and_display_currently_filtered_sequences_by_method(sort_method)
        self.update_ui(
            self.section_manager.get_sorted_sections(
                sort_method, self.browse_tab.sequence_picker.sections.keys()
            ),
            sort_method,
        )
