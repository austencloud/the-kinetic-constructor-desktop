from typing import TYPE_CHECKING
from PyQt6.QtWidgets import QWidget, QVBoxLayout

from base_widgets.pictograph.elements.views.visibility_pictograph_view import (
    VisibilityPictographView,
)

from .pictograph.visibility_pictograph import VisibilityPictograph
from .visibility_toggler import VisibilityToggler
from .buttons_widget.visibility_buttons_widget import VisibilityButtonsWidget
from PyQt6.QtCore import Qt

if TYPE_CHECKING:
    from main_window.main_widget.settings_dialog.settings_dialog import SettingsDialog


class VisibilityTab(QWidget):
    def __init__(self, settings_dialog: "SettingsDialog"):
        super().__init__()
        self.main_widget = settings_dialog.main_widget
        self.settings = self.main_widget.settings_manager.visibility
        self.dialog = settings_dialog
        self._setup_components()
        self._setup_layout()

    def _setup_components(self):
        self.toggler = VisibilityToggler(self)
        self.pictograph = VisibilityPictograph(self)
        self.pictograph_view = VisibilityPictographView(self, self.pictograph)
        self.buttons_widget = VisibilityButtonsWidget(self)

    def _setup_layout(self):
        layout = QVBoxLayout(self)
        layout.addWidget(
            self.pictograph_view, stretch=3, alignment=Qt.AlignmentFlag.AlignCenter
        )
        layout.addWidget(self.buttons_widget, 1)
        self.setLayout(layout)
