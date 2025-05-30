from PyQt6.QtGui import QCursor
from PyQt6.QtCore import Qt

from main_window.main_widget.browse_tab.sequence_picker.nav_sidebar.button.sidebar_button import SidebarButton

from .base_sidebar_section import BaseSidebarSection


class SidebarGenericSection(BaseSidebarSection):
    def create_widgets(self, sections_data):
        # No special header, just a list of buttons
        for section in sections_data:
            button = SidebarButton(str(section))
            button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            button.clicked.connect(
                lambda _, sec=section, btn=button: self.manager.scroll_to_section(
                    sec, btn
                )
            )
            self.add_centered_button(button)
            self._widgets_created.append(button)
            self.manager.buttons.append(button)
