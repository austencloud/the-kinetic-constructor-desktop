from typing import TYPE_CHECKING
from PyQt6.QtGui import (
    QPainter,
    QPen,
    QFont,
    QFontMetrics,
    QImage,
    QBrush,
)
from PyQt6.QtCore import QRect, Qt, QPoint

from main_window.main_widget.sequence_workbench.sequence_beat_frame.image_export_manager.image_creator.difficult_level_gradients import (
    DifficultyLevelGradients,
)


class ImageExportDifficultyLevelDrawer:
    def __init__(self):
        self.gradients = DifficultyLevelGradients()

    def draw_difficulty_level(
        self,
        image: QImage,
        difficulty_level: int,
        additional_height_top: int,
        beat_scale: float = 1.0,
    ):
        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self._calculate_rect(additional_height_top, beat_scale)
        self._setup_painter(painter, rect, difficulty_level, beat_scale)

        self._draw_ellipse(painter, rect)
        self._draw_text(painter, rect, difficulty_level, beat_scale)

        painter.end()

    def _calculate_rect(self, additional_height_top: int, beat_scale: float) -> QRect:
        # Get the border width from the image creator (scaled)
        border_width = int(3 * beat_scale)  # Scale border width with beat_scale

        shape_size = int(additional_height_top * 0.75)
        inset = additional_height_top // 8
        return QRect(inset + border_width, inset + border_width, shape_size, shape_size)

    def _setup_painter(
        self, painter: QPainter, rect: QRect, difficulty_level: int, beat_scale: float
    ):
        # Scale pen width with beat_scale, ensuring minimum width of 1
        pen_width = max(1, int((rect.height() // 50) * beat_scale))
        pen = QPen(Qt.GlobalColor.black, pen_width)
        painter.setPen(pen)

        gradient = self.gradients.get_gradient(rect, difficulty_level)
        painter.setBrush(QBrush(gradient))

    def _draw_ellipse(self, painter: QPainter, rect: QRect):
        painter.drawEllipse(rect)

    def _draw_text(
        self, painter: QPainter, rect: QRect, difficulty_level: int, beat_scale: float
    ):
        font = self._create_font(rect, beat_scale)
        painter.setFont(font)
        metrics = QFontMetrics(font)

        text = str(difficulty_level)
        bounding_rect = self._calculate_text_rect(
            metrics, text, rect, difficulty_level, beat_scale
        )

        painter.setPen(Qt.GlobalColor.black)
        painter.drawText(bounding_rect, Qt.AlignmentFlag.AlignLeft, text)

    def _create_font(self, rect: QRect, beat_scale: float) -> QFont:
        # Scale font size with beat_scale, ensuring minimum readability
        base_font_size = int(rect.height() // 1.75)
        scaled_font_size = max(8, int(base_font_size * beat_scale))  # Minimum 8pt font
        return QFont("Georgia", scaled_font_size, QFont.Weight.Bold)

    def _calculate_text_rect(
        self,
        metrics: QFontMetrics,
        text: str,
        rect: QRect,
        difficulty_level: int,
        beat_scale: float,
    ) -> QRect:
        bounding_rect = metrics.boundingRect(text)
        text_x = rect.center().x() - bounding_rect.width() // 2
        text_y = rect.center().y() - bounding_rect.height() // 2

        # Scale y_offset with beat_scale to maintain proper positioning
        base_y_offset = -25 if difficulty_level == 3 else -15
        scaled_y_offset = int(base_y_offset * beat_scale)
        bounding_rect.moveTopLeft(QPoint(text_x, text_y + scaled_y_offset))

        return bounding_rect
