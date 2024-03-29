from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QPen, QColor
from PyQt6.QtCore import Qt, QUrl
from typing import TYPE_CHECKING, Optional
from widgets.sequence_widget.sequence_beat_frame.beat import BeatView
from PyQt6.QtMultimedia import QMediaPlayer
from PyQt6.QtMultimediaWidgets import QVideoWidget

from widgets.sequence_widget.sequence_beat_frame.start_pos_beat import (
    StartPositionBeatView,
)

if TYPE_CHECKING:
    from widgets.sequence_widget.sequence_beat_frame.sequence_builder_beat_frame import (
        SequenceBuilderBeatFrame,
    )


class SequenceBuilderBeatSelectionManager(QWidget):
    def __init__(self, beat_frame: "SequenceBuilderBeatFrame"):
        super().__init__(beat_frame)
        self.selected_beat: Optional[BeatView | StartPositionBeatView] = None
        self.border_color = QColor("gold")
        self.border_width = 4  # Adjust as needed
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.hide()

    def select_beat(self, beat_view: BeatView):
        if self.selected_beat == beat_view:
            return
        else:
            if self.selected_beat:
                self.selected_beat.deselect()
            self.selected_beat = beat_view
            blue_turns = self.selected_beat.beat.blue_motion.turns
            red_turns = self.selected_beat.beat.red_motion.turns
            self.selected_beat.is_selected = True
            graph_editor = (
                self.selected_beat.beat_frame.main_widget.sequence_widget.sequence_modifier.graph_editor
            )
            graph_editor.update_GE_pictograph(self.selected_beat.beat)

            graph_editor.adjustment_panel.update_turns_panel(blue_turns, red_turns)
            graph_editor.adjustment_panel.update_adjustment_panel()

            if isinstance(beat_view, StartPositionBeatView):
                start_pos_pictograph = beat_view.beat
                blue_start_pos_ori_picker = (
                    graph_editor.adjustment_panel.blue_start_pos_ori_picker
                )
                red_start_pos_ori_picker = (
                    graph_editor.adjustment_panel.red_start_pos_ori_picker
                )

                blue_start_pos_ori_picker.ori_picker_widget.set_initial_orientation(
                    start_pos_pictograph, "blue"
                )
                red_start_pos_ori_picker.ori_picker_widget.set_initial_orientation(
                    start_pos_pictograph, "red"
                )

            self.update()
            self.update_overlay_position()
            self.show()

    def deselect_beat(self):
        if self.selected_beat:
            self.selected_beat.deselect()
        self.selected_beat = None
        self.hide()

    def update_overlay_position(self):
        if self.selected_beat:
            self.setGeometry(self.selected_beat.geometry())
            self.raise_()
            self.update()

    def get_selected_beat(self) -> Optional[BeatView]:
        return self.selected_beat

    def paintEvent(self, event):
        if not self.selected_beat:
            return

        painter = QPainter(self)
        pen = QPen(self.border_color, self.border_width)
        pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
        painter.setPen(pen)

        rect = self.rect().adjusted(
            self.border_width // 2,
            self.border_width // 2,
            -self.border_width // 2,
            -self.border_width // 2,
        )
        painter.drawRect(rect)
