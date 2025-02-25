from typing import TYPE_CHECKING
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
import logging


logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from .codex_control_widget import CodexControlWidget


class CodexColorSwapper:
    def __init__(self, control_widget: "CodexControlWidget"):
        self.codex = control_widget.codex

    def _swap_colors(self, pictograph):

        if not pictograph:
            return
        pictograph["blue_attributes"], pictograph["red_attributes"] = (
            pictograph["red_attributes"],
            pictograph["blue_attributes"],
        )

    def swap_colors_in_codex(self):
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        for pictograph in self.codex.data_manager.pictograph_data.values():
            self._swap_colors(pictograph)
        try:
            for letter_str, view in self.codex.section_manager.codex_views.items():
                scene = view.pictograph
                if scene.state.pictograph_data:
                    # Implement actual color swap logic here
                    scene.managers.updater.update_pictograph(
                        scene.state.pictograph_data
                    )
                    logger.debug(f"Swapped colors for pictograph '{letter_str}'.")
        except Exception as e:
            logger.exception(f"Error during color_swap_all: {e}")
        QApplication.restoreOverrideCursor()
