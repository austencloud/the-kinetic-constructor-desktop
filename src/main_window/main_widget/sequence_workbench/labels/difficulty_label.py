from typing import TYPE_CHECKING
from PyQt6.QtWidgets import QToolButton
from PyQt6.QtGui import QPixmap, QImage, QPainter, QFont, QPen, QFontMetrics, QIcon
from PyQt6.QtCore import Qt, QRect, QPoint, QSize
from main_window.main_widget.sequence_workbench.labels.difficulty_level_icon import DifficultyLevelIcon
from main_window.main_widget.sequence_workbench.sequence_beat_frame.image_export_manager.image_creator.difficult_level_gradients import (
    DifficultyLevelGradients,
)
from settings_manager.global_settings.app_context import AppContext

if TYPE_CHECKING:
    from main_window.main_widget.sequence_workbench.sequence_workbench import (
        SequenceWorkbench,
    )


class DifficultyLabel(QToolButton):
    def __init__(self, sequence_workbench: "SequenceWorkbench") -> None:
        """Handles drawing difficulty level labels in the workbench."""
        super().__init__(sequence_workbench)
        self.main_widget = sequence_workbench.main_widget
        self.sequence_workbench = sequence_workbench
        self.gradients = DifficultyLevelGradients()
        self.setToolTip("Difficulty Level")
        self.setCheckable(False)  # Disabled for now, allows future interaction
        self.setStyleSheet("border: none; background: transparent;")  # Clean look

        self.difficulty_level = 1  # Default level
        self.update_icon_size()

    def set_difficulty_level(self, level: int):
        """Sets the difficulty level and updates the display."""
        self.difficulty_level = level
        self.update_icon_size()

    def update_icon_size(self):
        """Updates the size of the icon dynamically based on workbench size."""
        size = max(32, self.sequence_workbench.width() // 18)  # Ensure min size
        self.setIcon(QIcon(DifficultyLevelIcon.get_pixmap(self.difficulty_level, size)))
        self.setIconSize(QSize(size, size))
        self.setFixedSize(size, size)

    def update_difficulty_label(self):
        """Updates the difficulty level indicator when the sequence changes."""
        sequence = AppContext.json_manager().loader_saver.load_current_sequence()
        difficulty_level = (
            self.main_widget.sequence_level_evaluator.get_sequence_difficulty_level(
                sequence
            )
        )
        self.set_difficulty_level(difficulty_level)

    def resizeEvent(self, event):
        """Resizes the difficulty label on parent resize."""
        super().resizeEvent(event)
        self.update_icon_size()
