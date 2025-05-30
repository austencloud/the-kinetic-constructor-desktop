from PyQt6.QtWidgets import QLabel
from PyQt6.QtGui import QCursor
from PyQt6.QtCore import Qt

from main_window.main_widget.browse_tab.sequence_picker.nav_sidebar.button.sidebar_button import (
    SidebarButton,
)

from .base_sidebar_section import BaseSidebarSection


class SidebarLetterSection(BaseSidebarSection):
    def create_widgets(self, sections_data):
        letter_label = QLabel("Letter")
        self.style_header_label(letter_label)
        self.manager.layout.addWidget(letter_label)
        self._widgets_created.append(letter_label)

        # Create a horizontal line or spacer
        spacer_line = QLabel()
        spacer_line.setFixedHeight(1)  # Ensure it's exactly 1 pixel tall
        spacer_line.setStyleSheet("background-color: white; border: none; margin: 0;")
        self.manager.layout.addWidget(spacer_line)
        self._widgets_created.append(spacer_line)

        for section in sections_data:
            button = SidebarButton(str(section))
            button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            button.clicked.connect(
                lambda _, sec=section, button=button: self.manager.scroll_to_section(
                    sec, button
                )
            )
            self.add_centered_button(button)
            self._widgets_created.append(button)
            self.manager.buttons.append(button)
        self.manager.layout.addStretch(1)
