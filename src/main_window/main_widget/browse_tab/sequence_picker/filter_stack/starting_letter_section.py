from typing import TYPE_CHECKING
from PyQt6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QWidget,
)
from PyQt6.QtCore import Qt, QEvent, QObject
from PyQt6.QtGui import QFontMetrics

from data.constants import LETTER
from styles.styled_button import StyledButton
from .filter_section_base import FilterSectionBase

if TYPE_CHECKING:
    from .sequence_picker_filter_stack import SequencePickerFilterStack


class StartingLetterSection(FilterSectionBase):
    SECTIONS: list[list[list[str]]] = [
        [
            ["A", "B", "C", "D", "E", "F"],
            ["G", "H", "I", "J", "K", "L"],
            ["M", "N", "O", "P", "Q", "R"],
            ["S", "T", "U", "V"],
        ],
        [["W", "X", "Y", "Z"], ["Σ", "Δ", "θ", "Ω"]],
        [["W-", "X-", "Y-", "Z-"], ["Σ-", "Δ-", "θ-", "Ω-"]],
        [["Φ", "Ψ", "Λ"]],
        [["Φ-", "Ψ-", "Λ-"]],
        [["α", "β", "Γ"]],
    ]

    def __init__(self, initial_selection_widget: "SequencePickerFilterStack"):
        super().__init__(initial_selection_widget, "Select by starting letter:")
        self.main_widget = initial_selection_widget.browse_tab.main_widget
        self.buttons: dict[str, StyledButton] = {}
        self.sequence_tally: dict[str, int] = {}
        self.sequence_tally_label = QLabel("")
        self.add_buttons()

    def add_buttons(self):
        self.initialized = True
        self.header_label.show()
        layout: QVBoxLayout = self.layout()
        self.create_letter_buttons(layout)
        layout.addStretch(1)
        self.sequence_tally = self._get_starting_letter_sequence_counts()
        self.sequence_tally_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.sequence_tally_label)

        layout.addStretch(1)
        # self.resize_starting_letter_section()

    def create_letter_buttons(self, layout: QVBoxLayout):
        for section in self.SECTIONS:
            for row in section:
                button_row_layout = QHBoxLayout()
                button_row_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                for letter in row:
                    button = self.create_letter_button(letter)
                    button_row_layout.addWidget(button)
                layout.addLayout(button_row_layout)

    def create_letter_button(self, letter: str) -> StyledButton:
        """Create a BaseStyledButton for a given letter."""
        button = StyledButton(letter)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.buttons[letter] = button
        button.setProperty(LETTER, letter)
        button.installEventFilter(self)

        # INSTANT SWITCHING: Use instant handler instead of direct filter application
        instant_handler = self.create_instant_button_handler(
            lambda l=letter: self.browse_tab.filter_controller.apply_filter(
                {"starting_letter": l}
            ),
            f"Starting Letter: {letter}",
        )
        button.clicked.connect(instant_handler)

        return button

    def _get_starting_letter_sequence_counts(self) -> dict[str, int]:
        """Tally up how many sequences start with each letter."""
        letter_counts = {letter: 0 for letter in self.buttons.keys()}
        base_words = self.get_sorted_base_words("sequence_length")

        for word, _, _ in base_words:
            first_letter = self.extract_first_letter(word)
            if first_letter in letter_counts:
                letter_counts[first_letter] += 1

        return letter_counts

    @staticmethod
    def extract_first_letter(word: str) -> str:
        """Extract the first letter or symbol from the word."""
        if len(word) > 1 and word[1] == "-":
            return word[:2]
        return word[0]

    def _word_starts_with_letter(self, word: str, letter: str) -> bool:
        """Check if the word starts with the given letter."""
        if len(letter) == 1:
            return word.startswith(letter) and (len(word) == 1 or word[1] != "-")
        return word.startswith(letter)

    def resizeEvent(self, event):
        self.resize_buttons()
        self.resize_widget_font(self.header_label, 100)
        self.resize_widget_font(self.sequence_tally_label, 100)
        self.sequence_tally_label.setFixedHeight(self.calculate_label_height())

    def resize_widget_font(self, widget: QWidget, factor: int):
        font = widget.font()
        font.setPointSize(max(10, self.main_widget.width() // factor))
        widget.setFont(font)

    def resize_buttons(self):
        width = self.main_widget.width() // 20
        height = self.main_widget.height() // 20
        font_size = max(10, self.main_widget.width() // 100)
        for button in self.buttons.values():
            font = button.font()
            font.setPointSize(font_size)
            button.setFont(font)
            button.setFixedSize(width, height)

    def calculate_label_height(self) -> int:
        """Calculate and return the height needed for the label."""
        font = self.sequence_tally_label.font()
        font.setPointSize(max(10, self.main_widget.width() // 100))
        font_metrics = QFontMetrics(font)
        return int(font_metrics.height() * 2.1)

    def eventFilter(self, obj: QObject, event: QEvent):
        if event.type() == QEvent.Type.Enter:
            letter = obj.property(LETTER)
            count = self.sequence_tally.get(letter, 0)
            sequence_text = "sequence" if count == 1 else "sequences"
            self.sequence_tally_label.setText(f"{letter}:\n{count} {sequence_text}")
        elif event.type() == QEvent.Type.Leave:
            self.sequence_tally_label.clear()
        return super().eventFilter(obj, event)
