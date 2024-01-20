from PyQt6.QtWidgets import QPushButton
from typing import TYPE_CHECKING



if TYPE_CHECKING:
    from widgets.attr_box.attr_box_widgets.turns_widget.turns_widget import TurnsWidget


class PropRotDirButton(QPushButton):
    def __init__(
        self,
        parent_widget: "TurnsWidget",
    ) -> None:
        super().__init__(parent_widget)
        self.parent_widget = parent_widget

    def get_button_style(self, pressed: bool) -> str:
        if pressed:
            return """
                QPushButton {
                    background-color: #ccd9ff;
                    border: 2px solid #555555;
                    border-bottom-color: #888888; /* darker shadow on the bottom */
                    border-right-color: #888888; /* darker shadow on the right */
                    padding: 5px;
                }
            """
        else:
            return """
                QPushButton {
                    background-color: white;
                    border: 1px solid black;
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: #e6f0ff;
                }
            """

    def press(self) -> None:
        self.setStyleSheet(self.get_button_style(pressed=True))

    def unpress(self) -> None:
        self.setStyleSheet(self.get_button_style(pressed=False))
