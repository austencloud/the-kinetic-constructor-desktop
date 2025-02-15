from typing import TYPE_CHECKING
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QHBoxLayout
from PyQt6.QtCore import Qt
from .section_widget.option_picker_section_group_widget import OptionPickerSectionGroupWidget
from .section_widget.option_picker_section_widget import OptionPickerSectionWidget
from Enums.Enums import LetterType

if TYPE_CHECKING:
    from ..option_picker import OptionPicker


class OptionScroll(QScrollArea):
    spacing = 3
    layout: QVBoxLayout
    container: QWidget
    sections: dict["LetterType", "OptionPickerSectionWidget"] = {}

    def __init__(self, option_picker: "OptionPicker") -> None:
        super().__init__(option_picker)
        self.option_picker = option_picker
        self.construct_tab = option_picker.construct_tab

        self._setup_layout()
        self._initialize_sections()

    def _initialize_sections(self) -> None:
        """Create and add sections to the layout. Handles groupable sections automatically."""
        groupable_sections = []
        for letter_type in LetterType:
            section = OptionPickerSectionWidget(letter_type, self)
            self.sections[letter_type] = section
            section.setup_components()

            if section.is_groupable:
                groupable_sections.append(section)
            else:
                self.layout.addWidget(section)

        if groupable_sections:
            group_widget = OptionPickerSectionGroupWidget(self)
            for section in groupable_sections:
                group_widget.add_section_widget(section)

            group_layout = QHBoxLayout()
            group_layout.addStretch()
            group_layout.addWidget(group_widget)
            group_layout.addStretch()
            self.layout.addLayout(group_layout, 3)

    def _setup_layout(self):
        self.setWidgetResizable(True)
        self.setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet("background-color: transparent; border: none;")

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.container = QWidget()
        self.container.setAutoFillBackground(True)
        self.container.setStyleSheet("background: transparent;")
        self.container.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.container.setLayout(self.layout)
        self.setWidget(self.container)

        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.viewport().setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
