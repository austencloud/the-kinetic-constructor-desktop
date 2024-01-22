from typing import TYPE_CHECKING
from PyQt6.QtWidgets import QVBoxLayout, QFrame
from PyQt6.QtCore import Qt
from ..codex.action_button_frame import ActionButtonFrame
from ..letter_button_frame.letter_button_frame import LetterButtonFrame

if TYPE_CHECKING:
    from widgets.codex.codex import Codex


class CodexButtonPanel(QFrame):
    def __init__(self, codex: "Codex") -> None:
        super().__init__(codex)
        self.codex = codex
        self.letter_btn_frame = LetterButtonFrame(self)
        self.action_btn_frame = ActionButtonFrame(self)
        self._setup_layout()

    def _setup_layout(self) -> QFrame:
        self.setStyleSheet("QFrame { border: 1px solid black; }")
        self.setContentsMargins(0, 0, 0, 0)
        self.layout: QVBoxLayout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.layout.addWidget(self.letter_btn_frame, 30)
        self.layout.addWidget(self.action_btn_frame, 1)

    def select_all_letters(self) -> None:
        for (
            button_letter,
            button,
        ) in self.letter_btn_frame.button_manager.buttons.items():
            button.setFlat(True)
            button.setStyleSheet(button.get_button_style(pressed=True))

        for (
            button_letter,
            button,
        ) in self.letter_btn_frame.button_manager.buttons.items():
            button.clicked.disconnect()
            button.click()

            self.codex.selected_letters.append(button_letter)
            button.clicked.connect(
                lambda checked, letter=button_letter: self.letter_btn_frame.on_letter_button_clicked(
                    letter
                )
            )

        self.codex.scroll_area.update_pictographs()
