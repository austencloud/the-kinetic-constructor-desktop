from typing import TYPE_CHECKING
from PyQt6.QtCore import Qt, QRectF, QByteArray
from PyQt6.QtGui import (
    QPainter,
    QColor,
    QCursor,
    QBrush,
    QPen,
)
from PyQt6.QtWidgets import QAbstractButton
from PyQt6.QtSvg import QSvgRenderer

from data.constants import BLUE, RED
from styles.styled_button import StyledButton

if TYPE_CHECKING:
    from ..turns_widget import TurnsWidget


class AdjustTurnsButton(StyledButton):
    def __init__(self, svg_path, turns_widget: "TurnsWidget") -> None:
        super().__init__(turns_widget)
        self.svg_path = svg_path
        self.turns_widget = turns_widget
        self.turns_box = self.turns_widget.turns_box
        self.svg_renderer = QSvgRenderer(svg_path)
        self.hovered = False
        self.pressed = False
        self.setMouseTracking(True)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw a translucent white background if hovered
        if self.hovered and self.isEnabled():
            painter.fillRect(self.rect(), QColor(255, 255, 255, 80))

        turns_box_color = self.turns_widget.turns_box.color
        if turns_box_color == RED:
            border_color = "#ED1C24"
        elif turns_box_color == BLUE:
            border_color = "#2E3192"
        else:
            border_color = "black"

        # If hovered, draw a white border. If pressed, use the turns_box color. Otherwise black border.
        if self.isEnabled():
            if self.hovered:
                painter.setPen(QPen(QColor("white"), 4))
            elif self.pressed:
                painter.setPen(QPen(QColor(f"{border_color}"), 5))
            else:
                painter.setPen(QPen(QColor("black"), 2))

        icon_size = int(min(self.width(), self.height()) * 0.9)
        x = (self.width() - icon_size) / 2
        y = (self.height() - icon_size) / 2
        icon_rect = QRectF(x, y, icon_size, icon_size)
        self.svg_renderer.render(painter, icon_rect)
        painter.end()

    def mousePressEvent(self, event):
        self.pressed = True
        self.update()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self.pressed = False
        self.update()
        super().mouseReleaseEvent(event)

    def enterEvent(self, event) -> None:
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.hovered = True
        self.update()

    def leaveEvent(self, event) -> None:
        self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        self.hovered = False
        self.update()

    def setEnabled(self, enabled) -> None:
        super().setEnabled(enabled)
        svgData = QByteArray()
        with open(self.svg_path, "r") as file:
            svgData = QByteArray(file.read().encode("utf-8"))

        if not enabled:
            svgData.replace(b"black", b"gray")

        self.svg_renderer.load(svgData)
        self.update()

    def resizeEvent(self, event) -> None:
        size = int(self.turns_box.graph_editor.height() * 0.3)
        self.setMaximumWidth(size)
        self.setMaximumHeight(size)
        super().resizeEvent(event)
