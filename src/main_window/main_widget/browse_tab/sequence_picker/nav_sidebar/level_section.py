from PyQt6.QtWidgets import QLabel
from PyQt6.QtGui import QCursor
from PyQt6.QtCore import Qt

from main_window.main_widget.browse_tab.sequence_picker.nav_sidebar.button.sidebar_button import (
    SidebarButton,
)


from .base_sidebar_section import BaseSidebarSection


class SidebarLevelSection(BaseSidebarSection):
    def create_widgets(self, sections_data):
        """
        Example: We show "Level" header + a line, then buttons for "1", "2", "3".
        """
        level_label = QLabel("Level")
        self.style_header_label(level_label)
        self.manager.layout.addWidget(level_label)
        self._widgets_created.append(level_label)

        # Create a horizontal line or spacer
        spacer_line = QLabel()
        spacer_line.setFixedHeight(1)  # Ensure it's exactly 1 pixel tall
        spacer_line.setStyleSheet("background-color: white; border: none; margin: 0;")
        self.manager.layout.addWidget(spacer_line)
        self._widgets_created.append(spacer_line)

        for lvl in ["1", "2", "3"]:
            button = SidebarButton(lvl)
            button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            button.clicked.connect(
                lambda _, lv=lvl, b=button: self.manager.scroll_to_section(lv, b)
            )
            self.add_centered_button(button)
            self._widgets_created.append(button)
            self.manager.buttons.append(button)
        self.manager.layout.addStretch(1)
