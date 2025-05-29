from styles.styled_button import StyledButton
from PyQt6.QtGui import QFontMetrics
from PyQt6.QtCore import QEvent


class SidebarButton(StyledButton):
    """A specialized button for the sidebar with dynamic width adjustment."""

    _max_button_width = 0  # Store max width across all buttons

    def __init__(self, section_key: str):
        super().__init__(section_key)
        self.section_key = section_key
        self.clicked.connect(lambda: self.clicked_signal.emit(self.section_key))
        self.update_max_width()

    @classmethod
    def update_max_width(cls, new_width: int = None):
        """Update the global max button width dynamically."""
        if new_width:
            cls._max_button_width = max(cls._max_button_width, new_width)

    @classmethod
    def calculate_max_width(cls, buttons: list["SidebarButton"], sidebar_width: int):
        """Calculate and update the max button width based on all sidebar buttons."""

        if not buttons:
            return

        max_width = 0
        for button in buttons:
            # Dynamically adjust font size based on sidebar width
            font_size = max(10, sidebar_width // 80)
            btn_font = button.font()
            btn_font.setPointSize(font_size)
            button.setFont(btn_font)  # Apply the font update

            # Now measure text width with updated font
            font_metrics = QFontMetrics(btn_font)
            text_width = font_metrics.horizontalAdvance(button.text())

            button_padding = int(sidebar_width // 2.2)  # Extra padding for aesthetics
            max_width = max(max_width, text_width + button_padding)

        cls._max_button_width = max_width  # Store the new max width globally

    def resizeEvent(self, event: QEvent) -> None:
        """Adjust button width dynamically based on the global max width."""
        self.resize_button()

        super().resizeEvent(event)

    def resize_button(self):
        if SidebarButton._max_button_width > 0:
            self.setFixedWidth(SidebarButton._max_button_width)

        # Adjust border-radius dynamically
        self._border_radius = min(self.height(), self.width()) // 2
        self.update_appearance()
