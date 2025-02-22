from typing import Any, List, Callable
from PyQt6.QtWidgets import QGridLayout, QWidget
from PyQt6.QtCore import Qt
from base_widgets.pictograph.pictograph import Pictograph
from main_window.main_widget.learn_tab.base_classes.base_lesson_widget.lesson_pictograph_view import (
    LessonPictographView,
)
from main_window.main_widget.pictograph_key_generator import PictographKeyGenerator


class PictographAnswersRenderer:
    def __init__(self, columns: int = 2, spacing: int = 30):
        self.layout = QGridLayout()
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.setSpacing(spacing)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.columns = columns
        self.key_generator = PictographKeyGenerator()
        self.pictograph_views: dict[str, LessonPictographView] = {}

    def get_layout(self):
        return self.layout

    def create_answer_options(
        self,
        answers: List[Any],
        check_callback: Callable[[Any, Any], None],
        correct_answer: Any,
    ) -> None:
        self._clear_layout()
        for i, answer in enumerate(answers):
            answer_key = self.key_generator.generate_pictograph_key(answer)
            scene = Pictograph()
            view = LessonPictographView(scene)
            scene.elements.view = view
            scene.managers.updater.update_pictograph(answer)
            scene.elements.view.update_borders()
            scene.elements.tka_glyph.setVisible(False)
            scene.elements.view.set_overlay_color(None)
            view.mousePressEvent = lambda event, a=answer: check_callback(
                a, correct_answer
            )
            row, col = divmod(i, self.columns)
            self.layout.addWidget(view, row, col)
            self.pictograph_views[answer_key] = view

    def update_answer_options(
        self,
        answers: List[Any],
        check_callback: Callable[[Any, Any], None],
        correct_answer: Any,
    ) -> None:
        if len(self.pictograph_views) != len(answers):
            self.create_answer_options (answers, check_callback, correct_answer)
            return

        self.pictograph_views.clear()

        for i, answer in enumerate(answers):
            item = self.layout.itemAt(i)
            view: LessonPictographView = item.widget()
            scene = view.pictograph

            scene.managers.updater.update_pictograph(answer)
            scene.elements.view.update_borders()
            scene.elements.tka_glyph.setVisible(False)
            scene.elements.view.set_overlay_color(None)
            view.setEnabled(True)

            view.mousePressEvent = lambda event, a=answer: check_callback(
                a, correct_answer
            )

            answer_key = self.key_generator.generate_pictograph_key(answer)
            self.pictograph_views[answer_key] = view

    def disable_answer_option(self, answer: Any) -> None:
        answer_key = self.key_generator.generate_pictograph_key(answer)
        if answer_key in self.pictograph_views:
            view: LessonPictographView = self.pictograph_views[answer_key]
            view.setEnabled(False)
            view.set_overlay_color("red")

    def _clear_layout(self):
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.pictograph_views.clear()
