from typing import TYPE_CHECKING
from PyQt6.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from Enums.letters import LetterType

from main_window.main_widget.generate_tab.freeform.letter_type_button_widget import LetterTypeButtonWidget
from main_window.settings_manager.global_settings.app_context import AppContext

if TYPE_CHECKING:
    from main_window.main_widget.generate_tab.generate_tab import GenerateTab


class LetterTypePickerWidget(QWidget):
    def __init__(self, generate_tab: "GenerateTab"):
        super().__init__(generate_tab)
        self.generate_tab = generate_tab
        self.settings = generate_tab.settings

        self.filter_label = QLabel("Filter by type:")
        self.filter_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.letter_types_layout = QHBoxLayout()
        self.letter_types_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.buttons: list[LetterTypeButtonWidget] = []
        for i, letter_type in enumerate(LetterType, start=1):
            button = LetterTypeButtonWidget(self, letter_type, i)
            button.clicked.connect(self._on_letter_type_clicked)
            self.letter_types_layout.addWidget(button)
            self.buttons.append(button)

        main_layout = QVBoxLayout(self)
        mode_layout = QHBoxLayout()
        mode_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mode_layout.addWidget(self.filter_label)
        main_layout.addLayout(mode_layout)
        main_layout.addLayout(self.letter_types_layout)

    def _on_letter_type_clicked(self, letter_type: LetterType):
        selected_count = sum(button.is_selected for button in self.buttons)
        if selected_count == 0:
            for letter_type, button in zip(LetterType, self.buttons):
                if letter_type == letter_type:
                    button.is_selected = True
                    button.update_colors()

        chosen = [
            letter_type.description
            for letter_type, button in zip(LetterType, self.buttons)
            if button.is_selected
        ]
        self.settings.set_setting(
            "selected_letter_types",
            chosen,
        )

    def _set_buttons_visible(self, visible: bool):
        for button in self.buttons:
            button.setVisible(visible)

    def set_selected_types(self, selected_types: list[str]) -> None:
        self._set_buttons_visible(selected_types is not None)
        if selected_types:
            any_selected = False
            for letter_type, button in zip(LetterType, self.buttons):
                is_selected = letter_type.description in selected_types
                button.is_selected = is_selected
                button.update_colors()
                if is_selected:
                    any_selected = True
            if not any_selected:
                self._select_all_letter_types()
        else:
            self._select_all_letter_types()

    def _select_all_letter_types(self):
        descriptions = [letter_type.description for letter_type in LetterType]
        for button in self.buttons:
            button.is_selected = True
            button.update_colors()
        self.settings.set_setting(
            "selected_letter_types",
            descriptions,
        )

    def get_selected_letter_types(self) -> list[LetterType]:
        return [
            letter_type for letter_type, w in zip(LetterType, self.buttons) if w.is_selected
        ]

    def resizeEvent(self, event):
        super().resizeEvent(event)
        font_size = self.generate_tab.main_widget.height() // 50
        self.filter_label.setFont(QFont("Georgia", font_size))
        self.layout().setSpacing(font_size)
        width = self.generate_tab.width() // 16
        for button in self.buttons:
            button.setFixedSize(width, width)
            font = button.label.font()
            font.setBold(True)
            font.setPointSize(font_size)
            button.label.setFont(font)

        font = self.filter_label.font()
        font.setPointSize(font_size)
        self.filter_label.setFont(font)
        global_settings = AppContext.settings_manager().global_settings
        color = self.generate_tab.main_widget.font_color_updater.get_font_color(
            global_settings.get_background_type()
        )
        existing_style = self.filter_label.styleSheet()
        new_style = f"{existing_style} color: {color};"
        self.filter_label.setStyleSheet(new_style)
