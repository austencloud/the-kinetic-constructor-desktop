from datetime import datetime
from typing import TYPE_CHECKING, Union

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

from data.constants import GRID_MODE
from main_window.main_widget.tab_indices import LeftStackIndex
from utils.path_helpers import get_data_path

if TYPE_CHECKING:
    from main_window.main_widget.browse_tab.browse_tab import BrowseTab


class BrowseTabFilterController:
    def __init__(self, browse_tab: "BrowseTab"):
        self.browse_tab = browse_tab
        self.filter_manager = browse_tab.filter_manager
        self.ui_updater = browse_tab.ui_updater
        self.fade_manager = browse_tab.main_widget.fade_manager
        self.metadata_extractor = browse_tab.metadata_extractor

    def apply_filter(self, filter_criteria: Union[str, dict], fade=True):
        tab_name = (
            self.browse_tab.browse_settings.settings_manager.global_settings.get_current_tab()
        )
        description = self._get_filter_description(filter_criteria)
        self.browse_tab.browse_settings.set_current_filter(filter_criteria)
        widgets_to_fade = [
            self.browse_tab.sequence_picker.filter_stack,
            self.browse_tab.sequence_picker,
        ]
        if tab_name == "browse" and fade:
            self.fade_manager.widget_fader.fade_and_update(
                widgets_to_fade,
                (
                    lambda: self._apply_filter_after_fade(filter_criteria, description),
                    lambda: self.browse_tab.ui_updater.resize_thumbnails_top_to_bottom(),
                ),
            )

        else:
            self._apply_filter_after_fade(filter_criteria, description)
            self.browse_tab.ui_updater.resize_thumbnails_top_to_bottom()

        self.browse_tab.browse_settings.set_current_section("sequence_picker")


    def _apply_filter_after_fade(self, filter_criteria, description: str):
        self._prepare_ui_for_filtering(description)
        if isinstance(filter_criteria, str):
            results = self._handle_string_filter(filter_criteria)
        elif isinstance(filter_criteria, dict):
            results = self._handle_dict_filter(filter_criteria)
        else:
            raise ValueError(
                f"Invalid filter type: {type(filter_criteria)} (must be str or dict)."
            )
        self.browse_tab.sequence_picker.currently_displayed_sequences = results
        if not self.browse_tab.sequence_picker.initialized:
            skip_scaling = False
        else:
            skip_scaling = True
        self.ui_updater.update_and_display_ui(len(results), skip_scaling)
        if (
            self.browse_tab.browse_settings.settings_manager.global_settings.get_current_tab()
            == "browse"
        ):
            self.browse_tab.main_widget.left_stack.setCurrentWidget(
                self.browse_tab.sequence_picker
            )
        self.browse_tab.browse_settings.set_browse_left_stack_index(
            LeftStackIndex.SEQUENCE_PICKER.value
        )

    def _prepare_ui_for_filtering(self, description: str):
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        control_panel = self.browse_tab.sequence_picker.control_panel
        control_panel.currently_displaying_label.setText(f"Displaying {description}")
        control_panel.count_label.setText("")
        self.browse_tab.sequence_picker.scroll_widget.clear_layout()

    def _handle_string_filter(self, filter_name: str):
        fm = self.filter_manager
        if filter_name == "favorites":
            return fm.filter_favorites()
        elif filter_name == "all":
            return fm.filter_all_sequences()
        elif filter_name == "most_recent":
            return fm.filter_most_recent(datetime.now())
        elif filter_name.startswith("tag:"):
            tag = filter_name.split("tag:")[1].strip()
            return fm.filter_by_tag(tag)
        else:
            raise ValueError(f"Unknown string filter: {filter_name}")

    def _handle_dict_filter(self, criteria: dict):
        if len(criteria) != 1:
            raise ValueError(
                "Dictionary filter must contain exactly one key-value pair."
            )
        (filter_key, filter_value) = next(iter(criteria.items()))
        dispatch_map = {
            "starting_letter": self._dict_filter_starting_letter,
            "contains_letters": self._dict_filter_contains_letters,
            "length": self._dict_filter_length,
            "level": self._dict_filter_level,
            "author": self._dict_filter_author,
            "starting_position": self._dict_filter_starting_pos,
            "favorites": self._dict_filter_favorites,
            "most_recent": self._dict_filter_most_recent,
            "difficulty": self._dict_filter_difficulty,
            "grid_mode": self._dict_filter_grid_mode,
            "show_all": self._dict_filter_show_all,
        }
        if filter_key not in dispatch_map:
            raise ValueError(f"Unknown dictionary filter key: {filter_key}")
        return dispatch_map[filter_key](filter_value)

    def _dict_filter_starting_letter(self, letter):
        base_words = self._base_words()
        fm = self.filter_manager
        return [
            (word, thumbs, fm._get_sequence_length(thumbs[0]))
            for word, thumbs in base_words
            if word.startswith(letter)
        ]

    def _dict_filter_difficulty(self, _unused):
        return self.filter_manager.filter_by_difficulty()

    def _dict_filter_contains_letters(self, letters):
        base_words = self._base_words()
        fm = self.filter_manager
        return [
            (word, thumbs, fm._get_sequence_length(thumbs[0]))
            for word, thumbs in base_words
            if any(char in word for char in letters)
        ]

    def _dict_filter_length(self, length_value):
        base_words = self._base_words()
        fm = self.filter_manager
        try:
            target_length = int(length_value)
        except ValueError:
            raise ValueError(f"Invalid length '{length_value}'; expected integer.")
        return [
            (word, thumbs, fm._get_sequence_length(thumbs[0]))
            for word, thumbs in base_words
            if fm._get_sequence_length(thumbs[0]) == target_length
        ]

    def _dict_filter_level(self, level_value):
        base_words = self._base_words()
        filter_manager = self.filter_manager

        results = []
        for word, thumbs in base_words:
            # If thumbs is empty or None, skip it
            if not thumbs:
                continue

            # Otherwise, safe to do thumbs[0]
            if self.metadata_extractor.get_level(thumbs[0]) == level_value:
                seq_length = filter_manager._get_sequence_length(thumbs[0])
                results.append((word, thumbs, seq_length))

        return results

    def _dict_filter_author(self, author_value):
        base_words = self._base_words()
        fm = self.filter_manager
        return [
            (w, t, fm._get_sequence_length(t[0]))
            for w, t in base_words
            if self.metadata_extractor.get_author(t[0]) == author_value
        ]

    def _dict_filter_starting_pos(self, pos_value):
        base_words = self._base_words()
        fm = self.filter_manager
        result = []
        for w, t in base_words:
            if self.metadata_extractor.get_start_pos(t[0]) == pos_value.lower():
                result.append((w, t, fm._get_sequence_length(t[0])))
        return result

    def _dict_filter_favorites(self, _unused):
        return self.filter_manager.filter_favorites()

    def _dict_filter_most_recent(self, _unused):
        return self.filter_manager.filter_most_recent()

    def _dict_filter_grid_mode(self, grid_mode_value):
        base_words = self._base_words()
        fm = self.filter_manager
        return [
            (w, t, fm._get_sequence_length(t[0]))
            for w, t in base_words
            if self.metadata_extractor.get_grid_mode(t[0]) == grid_mode_value
        ]

    def _dict_filter_show_all(self, _unused):
        return self.filter_manager.filter_all_sequences()

    def _base_words(self) -> list[tuple[str, list[str]]]:
        all_words = self.browse_tab.get.base_words()
        base_words = []
        for w, thumbs in all_words:
            if thumbs:  # only store if thumbs is non-empty
                base_words.append((w, thumbs))
        return base_words

    def _get_filter_description(self, filter_criteria: Union[str, dict]) -> str:
        if isinstance(filter_criteria, str):
            if filter_criteria == "all":
                return "all sequences"
            elif filter_criteria.startswith("tag:"):
                tag_name = filter_criteria.split("tag:")[1].strip()
                return f"sequences with tag '{tag_name}'"
            return filter_criteria.replace("_", " ").capitalize()
        return self._description_for_dict_filter(filter_criteria)

    def _description_for_dict_filter(self, filter_criteria: dict) -> str:
        if len(filter_criteria) != 1:
            return "Unknown Filter"
        key, value = list(filter_criteria.items())[0]
        desc_map = {
            "starting_letter": f"sequences starting with {value}",
            "contains_letters": f"sequences containing {value}",
            "length": f"sequences with length {value}",
            "level": f"sequences with level {value}",
            "author": f"sequences by {value}",
            "starting_position": f"sequences starting at position {value}",
            "favorites": "favorite sequences",
            "most_recent": "most recent sequences",
            GRID_MODE: f"sequences in {value} mode",
            "show_all": "all sequences",
        }
        return desc_map.get(key, "Unknown Filter")
