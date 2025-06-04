from typing import TYPE_CHECKING, Union
from PyQt6.QtGui import QColor, QPainter, QLinearGradient
from PyQt6.QtWidgets import QWidget
from main_window.main_widget.main_background_widget.backgrounds.base_background import (
    BaseBackground,
)

if TYPE_CHECKING:
    # Note: BrowseTab import removed due to browse_tab restructure
    from typing import Any

    BrowseTab = Any
    from main_window.main_widget.learn_tab.learn_tab import LearnTab
    from main_window.main_widget.write_tab.write_tab import WriteTab


class SnowfallBackground(BaseBackground):
    def __init__(self, widget: Union["BrowseTab", "LearnTab", "WriteTab"]):
        super().__init__(widget)
        self.widget = widget

    def paint_background(self, widget: QWidget, painter: QPainter):
        # Draw a static gradient
        gradient = QLinearGradient(0, 0, 0, widget.height())
        gradient.setColorAt(0, QColor("#0b1d2a"))
        gradient.setColorAt(0.3, QColor("#142030"))
        gradient.setColorAt(0.7, QColor("#325078"))
        gradient.setColorAt(1, QColor("#49708a"))
        painter.fillRect(widget.rect(), gradient)
