from typing import TYPE_CHECKING
from PyQt6.QtGui import QPainter, QFont, QFontMetrics, QImage
from .font_margin_helper import FontMarginHelper

if TYPE_CHECKING:
    from .image_creator import ImageCreator


class WordDrawer:
    def __init__(self, image_creator: "ImageCreator"):
        self.image_creator = image_creator
        self.base_font = QFont("Georgia", 175, QFont.Weight.DemiBold, False)
        self.base_kerning = 20  # Base kerning value (will be scaled dynamically)

    def draw_word(
        self,
        image: QImage,
        word: str,
        num_filled_beats: int,
        additional_height_top: int,
    ) -> None:
        # Calculate kerning dynamically with current beat_scale
        kerning = int(self.base_kerning * self.image_creator.beat_scale)

        base_margin = 50 * self.image_creator.beat_scale
        font, margin = FontMarginHelper.adjust_font_and_margin(
            self.base_font, num_filled_beats, base_margin, self.image_creator.beat_scale
        )

        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        metrics = QFontMetrics(font)
        text_width = metrics.horizontalAdvance(word)
        text_height = metrics.ascent()

        while text_width + 2 * margin > image.width() - (image.width() // 4):
            font_size = font.pointSize() - 1
            if font_size <= 10:
                break
            font = QFont(font.family(), font_size, font.weight(), font.italic())
            metrics = QFontMetrics(font)
            text_width = metrics.horizontalAdvance(word)
            text_height = metrics.ascent()

        self._draw_text(
            painter,
            image,
            word,
            font,
            margin,
            text_height,
            additional_height_top,
            kerning,
        )
        painter.end()

    def _draw_text(
        self,
        painter: QPainter,
        image: QImage,
        text: str,
        font: QFont,
        margin: int,
        text_height: int,
        additional_height_top: int,
        kerning: int,
        text_width: int = None,
    ) -> None:
        painter.setFont(font)
        metrics = QFontMetrics(font)

        if not text_width:
            text_width = metrics.horizontalAdvance(text)

        # Get the border width from the image creator
        border_width = 3  # Same as in ImageCreator._create_image

        # Calculate the vertical position to center the text in the additional height on top
        y = (
            (additional_height_top // 2 + text_height // 2)
            - (text_height // 10)
            + border_width
        )

        x = (image.width() - text_width - kerning * (len(text) - 1)) // 2

        for letter in text:
            painter.drawText(x, y, letter)
            x += metrics.horizontalAdvance(letter) + kerning
