from PyQt6.QtCore import QEvent
from styles.base_styled_button import BaseStyledButton

class SortButton(BaseStyledButton):
    """A specialized button for sort options."""

    def __init__(self, label: str, identifier: str):
        super().__init__(label)
        self.identifier = identifier
        self.clicked.connect(lambda: self.clicked_signal.emit(self.identifier))

    def resizeEvent(self, event: QEvent) -> None:
        """Handle resizing to update styles dynamically."""
        self._border_radius = min(self.height(), self.width()) // 2
        self.update_appearance()
        super().resizeEvent(event)
