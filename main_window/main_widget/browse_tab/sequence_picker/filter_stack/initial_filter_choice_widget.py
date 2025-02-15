from typing import TYPE_CHECKING, Callable, Union, Any
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QGridLayout,
)
from PyQt6.QtCore import Qt
from functools import partial
from datetime import datetime, timedelta

from main_window.main_widget.browse_tab.sequence_picker.filter_stack.choose_filter_label import (
    ChooseFilterLabel,
)
from main_window.main_widget.browse_tab.sequence_picker.filter_stack.filter_button_group import (
    FilterButtonGroup,
)


if TYPE_CHECKING:
    from .sequence_picker_filter_stack import SequencePickerFilterStack


class InitialFilterChoiceWidget(QWidget):
    """Widget to display filter options for the dictionary browser."""

    FILTER_OPTIONS: dict[str, tuple[str, Union[str, dict[str, Any]]]] = {
        "Starting Letter": (
            "Display sequences that start with a specific letter.",
            "starting_letter",
        ),
        "Contains Letter": (
            "Display sequences that contain specific letters.",
            "contains_letters",
        ),
        "Sequence Length": ("Display sequences by length.", "sequence_length"),
        "Level": ("Display sequences by difficulty level.", "level"),
        "Starting Position": (
            "Display sequences by starting position.",
            "starting_position",
        ),
        "Author": ("Display sequences by author.", "author"),
        "Favorites": ("Display your favorite sequences.", {"favorites": True}),
        "Most Recent": (
            f"Display sequences created since {datetime.now() - timedelta(weeks=1)}.",
            {"most_recent": datetime.now() - timedelta(weeks=1)},
        ),
        "Grid Mode": (
            "Display sequences by grid mode (Box or Diamond).",
            "grid_mode",
        ),
        "Show All": (
            "Display every sequence in the dictionary.",
            {"show_all": True},
        ),
    }

    def __init__(self, filter_stack: "SequencePickerFilterStack"):
        super().__init__(filter_stack)
        self.filter_selector = filter_stack
        self.browse_tab = filter_stack.browse_tab
        self.main_widget = filter_stack.browse_tab.main_widget
        self.button_groups: dict[str, FilterButtonGroup] = {}
        self._setup_ui()

    def _setup_ui(self):
        self.header_label = ChooseFilterLabel(self)
        self._setup_button_groups()
        self._setup_grid_layout()
        self._setup_main_layout()

    def _setup_main_layout(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addStretch(2)
        self.main_layout.addWidget(self.header_label)
        self.main_layout.addStretch(1)
        self.main_layout.addLayout(self.grid_layout)
        self.main_layout.addStretch(1)
        self.main_layout.addWidget(self.button_groups["Show All"])
        self.main_layout.addStretch(2)
        self.setLayout(self.main_layout)

    def _setup_grid_layout(self):
        self.grid_layout = QGridLayout()
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        horizontal_spacing = self.main_widget.width() // 20
        vertical_spacing = self.main_widget.height() // 20
        self.grid_layout.setHorizontalSpacing(horizontal_spacing)
        self.grid_layout.setVerticalSpacing(vertical_spacing)
        index = 0
        for label, _ in self.FILTER_OPTIONS.items():
            if label != "Show All":
                button_group = self.button_groups[label]
                row = index // 3
                col = index % 3
                self.grid_layout.addWidget(button_group, row, col)
                index += 1

    def _setup_button_groups(self):
        """Create button groups for all filter options."""
        for label, (description, handler_arg) in self.FILTER_OPTIONS.items():
            if isinstance(handler_arg, str):
                handler = partial(self.filter_selector.show_section, handler_arg)
            else:
                handler = partial(
                    self.browse_tab.filter_controller.apply_filter, handler_arg
                )
            self.button_groups[label] = FilterButtonGroup(
                label, description, handler, self
            )
        self.description_labels = {
            label: self.button_groups[label].description_label
            for label in self.button_groups
        }