from typing import TYPE_CHECKING
from PyQt6.QtWidgets import QWidget, QHBoxLayout


from main_window.main_widget.sequence_workbench.add_to_dictionary_manager.add_to_dictionary_ui import (
    AddToDictionaryUI,
)
from main_window.main_widget.sequence_workbench.add_to_dictionary_manager.dictionary_service import (
    DictionaryService,
)
from main_window.main_widget.sequence_workbench.labels.sequence_workbench_indicator_label import (
    SequenceWorkbenchIndicatorLabel,
)
from main_window.main_widget.sequence_workbench.sequence_beat_frame.beat_deleter.beat_deleter import (
    BeatDeleter,
)
from main_window.main_widget.sequence_workbench.sequence_beat_frame.sequence_beat_frame import (
    SequenceBeatFrame,
)
from .full_screen_viewer import FullScreenViewer
from .sequence_color_swapper import SequenceColorSwapper
from .sequence_reflector import SequenceReflector
from .sequence_rotater import SequenceRotater
from .sequence_workbench_layout_manager import SequenceWorkbenchLayoutManager
from .sequence_auto_completer.sequence_auto_completer import SequenceAutoCompleter
from .labels.current_word_label import CurrentWordLabel
from .labels.difficulty_label import DifficultyLabel
from .graph_editor.graph_editor import GraphEditor
from .sequence_workbench_button_panel import SequenceWorkbenchButtonPanel
from .sequence_workbench_scroll_area import SequenceWorkbenchScrollArea

if TYPE_CHECKING:
    from main_window.main_widget.main_widget import MainWidget


class SequenceWorkbench(QWidget):
    beat_frame_layout: QHBoxLayout
    indicator_label_layout: QHBoxLayout

    def __init__(self, main_widget: "MainWidget") -> None:
        super().__init__()
        self.main_widget = main_widget
        self.main_widget.splash.updater.update_progress("SequenceWorkbench")
        self.setObjectName("SequenceWorkbench")
        # Managers
        self.dictionary_service = DictionaryService(
            create_sequence_image_callback=lambda sequence, include_start_pos: self.sequence_beat_frame.image_export_manager.image_creator.create_sequence_image(
                sequence, include_start_pos
            ),
            get_current_word_callback=lambda: self.sequence_beat_frame.get.current_word(),
        )

        # Create the “UI” class that uses it:
        self.add_to_dictionary_ui = AddToDictionaryUI(self, self.dictionary_service)

        self.autocompleter = SequenceAutoCompleter(self)

        # Modification Managers
        self.mirror_manager = SequenceReflector(self)
        self.color_swap_manager = SequenceColorSwapper(self)
        self.rotation_manager = SequenceRotater(self)

        # Labels
        self.indicator_label = SequenceWorkbenchIndicatorLabel(self)
        self.current_word_label = CurrentWordLabel(self)
        self.difficulty_label = DifficultyLabel(self)

        # Sections
        self.scroll_area = SequenceWorkbenchScrollArea(self)
        self.sequence_beat_frame = SequenceBeatFrame(self)
        self.button_panel = SequenceWorkbenchButtonPanel(self)
        self.graph_editor = GraphEditor(self)

        # Full Screen Viewer
        self.full_screen_viewer = FullScreenViewer(self)

        # Layout
        self.layout_manager = SequenceWorkbenchLayoutManager(self)
        self.beat_deleter = BeatDeleter(self)



    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.graph_editor.resizeEvent(event)
