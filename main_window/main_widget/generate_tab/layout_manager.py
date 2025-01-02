from PyQt6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QStackedLayout,
)
from PyQt6.QtCore import Qt
from typing import TYPE_CHECKING

from main_window.main_widget.generate_tab.generate_tab_spacer import GenerateTabSpacer


if TYPE_CHECKING:
    from main_window.main_widget.generate_tab.generate_tab import GenerateTab


class GenerateTabLayoutManager:
    def __init__(self, tab: "GenerateTab"):
        self.tab = tab
        self._setup_spacers()
        self._setup_layout()
        self.tab.freeform_generator_frame.show()

    def _setup_layout(self):
        self.tab.stacked_layout = QStackedLayout()
        self.tab.stacked_layout.addWidget(self.tab.freeform_generator_frame)
        self.tab.stacked_layout.addWidget(self.tab.circular_generator_frame)

        top_hbox = QHBoxLayout()
        top_hbox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top_hbox.addWidget(self.tab.customize_sequence_label)

        generate_button_hbox = QHBoxLayout()
        generate_button_hbox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        generate_button_hbox.addWidget(self.tab.generate_sequence_button)

        self.tab.checkbox_layout = QHBoxLayout()
        self.tab.checkbox_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.tab.checkbox_layout.addWidget(self.tab.overwrite_checkbox)

        self.tab.layout = QVBoxLayout(self.tab)
        self.tab.layout.addLayout(top_hbox)
        self.tab.layout.addWidget(self.tab.spacer_1)
        self.tab.layout.addLayout(self.tab.button_layout)
        self.tab.layout.addLayout(self.tab.stacked_layout)
        self.tab.layout.addWidget(self.tab.spacer_2)
        self.tab.layout.addLayout(generate_button_hbox)
        self.tab.layout.addLayout(self.tab.checkbox_layout)
        self.tab.layout.addWidget(self.tab.spacer_3)
        self.tab.setLayout(self.tab.layout)
        

    def _setup_spacers(self):
        spacers: list[GenerateTabSpacer] = []
        for _ in range(3):
            spacer = GenerateTabSpacer(self.tab)
            spacers.append(spacer)
        self.tab.spacer_1, self.tab.spacer_2, self.tab.spacer_3 = spacers
