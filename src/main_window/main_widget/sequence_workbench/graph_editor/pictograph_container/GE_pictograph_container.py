from typing import TYPE_CHECKING
import logging
from PyQt6.QtWidgets import QWidget, QVBoxLayout

from base_widgets.pictograph.elements.views.GE_pictograph_view import GE_PictographView
from main_window.main_widget.sequence_workbench.graph_editor.GE_pictograph import (
    GE_Pictograph,
)


if TYPE_CHECKING:
    from main_window.main_widget.sequence_workbench.sequence_beat_frame.beat import Beat
    from ..graph_editor import GraphEditor


class GraphEditorPictographContainer(QWidget):
    def __init__(self, graph_editor: "GraphEditor") -> None:
        super().__init__(graph_editor)
        self.graph_editor = graph_editor
        self.setup_pictograph()

        self.layout: QVBoxLayout = QVBoxLayout(self)
        self.layout.addWidget(self.GE_view)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

    def setup_pictograph(self):
        self.GE_pictograph = GE_Pictograph(self)
        self.GE_view = GE_PictographView(self, self.GE_pictograph)

    def update_pictograph(self, reference_beat: "Beat" = None) -> None:
        selected_beat_view = (
            self.graph_editor.sequence_workbench.beat_frame.get.currently_selected_beat_view()
        )
        if not selected_beat_view:
            return
        if not reference_beat:
            reference_beat = selected_beat_view.beat

        view = self.GE_view
        pictograph = view.pictograph

        pictograph.is_blank = False
        view.reference_beat = reference_beat

        # CRITICAL FIX: Add null check for reference_beat.view to prevent NoneType error
        if reference_beat and hasattr(reference_beat, "view") and reference_beat.view:
            view.is_start_pos = reference_beat.view.is_start_pos
        else:
            view.is_start_pos = False
            logging.warning(
                "reference_beat.view is None - setting is_start_pos to False"
            )

        pictograph.state.blue_reversal = reference_beat.state.blue_reversal
        pictograph.state.red_reversal = reference_beat.state.red_reversal

        pictograph.managers.updater.update_pictograph(
            reference_beat.state.pictograph_data
        )

        beat_number_text = reference_beat.beat_number_item.beat_number_int
        if beat_number_text:
            pictograph.beat_number_item.update_beat_number(beat_number_text)
        else:
            pictograph.start_text_item.add_start_text()
        self.graph_editor.pictograph_selected.emit()

    def resizeEvent(self, event):
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.setLayout(self.layout)
