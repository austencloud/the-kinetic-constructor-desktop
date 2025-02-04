from typing import TYPE_CHECKING
from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt


if TYPE_CHECKING:
    from main_window.main_widget.learn_tab.base_classes.base_lesson_widget.base_lesson_widget import BaseLessonWidget

class LessonProgressLabel(QLabel):
    def __init__(self, lesson_widget: "BaseLessonWidget"):
        super().__init__(lesson_widget)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lesson_widget = lesson_widget
        
    def update_progress(self, current_question, total_questions):
        self.setText(f"{current_question}/{total_questions}")

    def resizeEvent(self,event):
        font_size = self.lesson_widget.main_widget.width() // 75
        font = self.lesson_widget.progress_label.font()
        font.setPointSize(font_size)
        self.lesson_widget.progress_label.setFont(font)
