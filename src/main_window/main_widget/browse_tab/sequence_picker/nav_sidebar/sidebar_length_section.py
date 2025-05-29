from PyQt6.QtWidgets import QLabel
from PyQt6.QtGui import QCursor
from PyQt6.QtCore import Qt

from main_window.main_widget.browse_tab.sequence_picker.nav_sidebar.button.sidebar_button import (
    SidebarButton,
)

from .base_sidebar_section import BaseSidebarSection


class SidebarLengthSection(BaseSidebarSection):
    def create_widgets(self, sections_data):
        """sections_data is a list of 'section' strings with lengths."""
        # Create a header
        length_label = QLabel("Length")
        self.style_header_label(length_label)
        self.manager.layout.addWidget(length_label)
        self._widgets_created.append(length_label)

        # Create a horizontal line or spacer
        spacer_line = QLabel()
        spacer_line.setFixedHeight(1)  # Ensure it's exactly 1 pixel tall
        spacer_line.setStyleSheet("background-color: white; border: none; margin: 0;")
        self.manager.layout.addWidget(spacer_line)
        self._widgets_created.append(spacer_line)


        # Create a button for each length
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
            self.manager.buttons.append(button)  # So the manager can style it

        self.manager.layout.addStretch()
