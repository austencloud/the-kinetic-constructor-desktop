from PyQt6.QtCore import pyqtSignal, QObject
from typing import TYPE_CHECKING
from main_window.settings_manager.global_settings.app_context import AppContext

if TYPE_CHECKING:
    from main_window.main_widget.sequence_workbench.graph_editor.graph_editor import GraphEditor
    from objects.arrow.arrow import Arrow


class ArrowSelectionManager(QObject):
    selection_changed = pyqtSignal(object)

    def __init__(self, graph_editor: "GraphEditor") -> None:
        super().__init__()
        self.graph_editor = graph_editor

    def set_selected_arrow(self, arrow: "Arrow") -> None:
        """Update the global selected arrow via AppContext."""
        AppContext.set_selected_arrow(arrow)
        self.selection_changed.emit(arrow)  # Notify listeners

    def clear_selection(self):
        """Clear the global selection via AppContext."""
        AppContext.clear_selected_arrow()
