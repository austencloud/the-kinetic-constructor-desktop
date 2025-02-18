from typing import TYPE_CHECKING
from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt

if TYPE_CHECKING:
    from .layout_controls_widget import LayoutControlsWidget


class DefaultLayoutLabel(QLabel):
    def __init__(self, control_widget: "LayoutControlsWidget"):
        super().__init__(control_widget)
        layout_settings = (
            control_widget.layout_tab.main_widget.settings_manager.sequence_layout
        )
        current_layout = control_widget.layout_tab.beat_frame.current_layout
        self.setText(
            f"Default: {current_layout[0]} x {current_layout[1]}",
        )
        self.control_widget = control_widget
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = self.font()
        font.setBold(True)
        self.setFont(font)

    def resizeEvent(self, event):
        font = self.font()
        font.setPointSize(self.control_widget.layout_tab.width() // 50)
        self.setFont(font)
