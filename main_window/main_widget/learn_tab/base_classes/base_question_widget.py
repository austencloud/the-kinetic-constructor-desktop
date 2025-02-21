from typing import TYPE_CHECKING
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QSpacerItem, QSizePolicy
from PyQt6.QtCore import Qt
from base_widgets.pictograph.pictograph_scene import PictographScene
from main_window.main_widget.learn_tab.base_classes.base_lesson_widget.lesson_pictograph_view import (
    LessonPictographView,
)

if TYPE_CHECKING:
    from .base_lesson_widget.base_lesson_widget import BaseLessonWidget


class BaseQuestionWidget(QWidget):
    letter_label: QLabel = None
    pictograph: PictographScene = None

    def __init__(self, lesson_widget: "BaseLessonWidget"):
        super().__init__(lesson_widget)
        self.lesson_widget = lesson_widget
        self.main_widget = lesson_widget.main_widget
        self.question_label: QLabel = None
        self.layout: QVBoxLayout = None
        self.spacer: QSpacerItem = None

    def clear(self) -> None:
        raise NotImplementedError(
            "This function should be implemented by the subclass."
        )

    def _resize_question_widget(self) -> None:
        raise NotImplementedError(
            "This function should be implemented by the subclass."
        )

    def _update_letter_label(self, letter: str) -> None:
        raise NotImplementedError(
            "This function should be implemented by the subclass."
        )

    def update_pictograph(self, pictograph_data) -> None:
        """
        Update the existing pictograph view with new data.
        If no view exists yet, create one.
        """
        if self.pictograph is None:
            # Create the persistent pictograph view if it doesn't exist
            self.pictograph = PictographScene()
            self.pictograph.elements.view = LessonPictographView(self.pictograph)
            self.layout.addWidget(
                self.pictograph.elements.view, alignment=Qt.AlignmentFlag.AlignCenter
            )
        # Update the pictograph’s content in place
        self.pictograph.state.disable_gold_overlay = True
        self.pictograph.managers.updater.update_pictograph(pictograph_data)
        self.pictograph.elements.view.update_borders()
        self.pictograph.elements.tka_glyph.setVisible(False)

    def _resize_question_label(self) -> None:
        question_label_font_size = self.main_widget.width() // 65
        font = self.question_label.font()
        font.setFamily("Georgia")
        font.setPointSize(question_label_font_size)
        self.question_label.setFont(font)

    def _resize_spacer(self) -> None:
        self.spacer.changeSize(
            20,
            self.main_widget.height() // 20,
            QSizePolicy.Policy.Minimum,
            QSizePolicy.Policy.Expanding,
        )
