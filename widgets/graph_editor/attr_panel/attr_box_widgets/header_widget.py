from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
)
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import Qt, QSize
from settings.string_constants import BLUE, BLUE_HEX, RED, RED_HEX, ICON_DIR
from utilities.TypeChecking.TypeChecking import Colors
from typing import TYPE_CHECKING
from objects.motion import Motion
from widgets.graph_editor.attr_panel.attr_box_widgets.custom_button import CustomButton

if TYPE_CHECKING:
    from widgets.graph_editor.attr_panel.attr_box import AttrBox
from settings.string_constants import ICON_DIR


class HeaderWidget(QWidget):
    def __init__(self, attr_box: "AttrBox") -> None:
        super().__init__(attr_box)

        self.attr_box = attr_box
        self.color = attr_box.color
        self.pictograph = attr_box.pictograph

        self.motion: Motion = self.attr_box.pictograph.get_motion_by_color(self.color)
        self.clock: QLabel = self._setup_clock()
        self.header_text: QLabel = self._setup_header_label()
        self.rotate_cw_button, self.rotate_ccw_button = self._setup_buttons()

        self._setup_main_layout()
        self.setFixedWidth(self.attr_box.attr_box_width)

    def _setup_main_layout(self) -> QHBoxLayout:
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        main_layout.addWidget(self.clock)
        main_layout.addWidget(self.header_text)
        main_layout.addWidget(self.rotate_ccw_button)
        main_layout.addWidget(self.rotate_cw_button)

        return main_layout

    def _add_black_borders(self):
        self.setStyleSheet("border: 1px solid black;")
        self.clock.setStyleSheet("border: 1px solid black;")
        self.header_text.setStyleSheet("border: 1px solid black;")
        self.rotate_cw_button.setStyleSheet("border: 1px solid black;")
        self.rotate_ccw_button.setStyleSheet("border: 1px solid black;")

    def _setup_clock(self) -> QLabel:
        clock_label = QLabel(self)
        clock_pixmap = QPixmap(f"{ICON_DIR}clock/clockwise.png")
        if clock_pixmap.isNull():
            print("Failed to load the clock icon.")
        else:
            clock_label.setPixmap(
                clock_pixmap.scaled(
                    int(self.attr_box.width() / 3),
                    int(self.attr_box.width() / 3),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        clock_label.setFixedSize(
            int(self.attr_box.width() / 3), int(self.attr_box.width() / 3)
        )
        return clock_label

    def _setup_buttons(self) -> tuple[CustomButton, CustomButton]:
        rotate_ccw_button = self._create_button(f"{ICON_DIR}rotate_ccw.png")
        rotate_cw_button = self._create_button(f"{ICON_DIR}rotate_cw.png")
        if self.motion:
            rotate_ccw_button.clicked.connect(self.motion.arrow.rotate("ccw"))
            rotate_cw_button.clicked.connect(self.motion.arrow.rotate("cw"))
        buttons = (rotate_ccw_button, rotate_cw_button)
        return buttons

    def _setup_header_label(self) -> QLabel:
        header_label = QLabel("Left" if self.color == BLUE else "Right", self)
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        
        color_hex = RED_HEX if self.color == RED else BLUE_HEX
        font_size = int(header_label.height() * 0.8)
        header_label.setStyleSheet(
            f"color: {color_hex}; font-size: {font_size}px; font-weight: bold;"
        )
        return header_label

    def _create_button(self, icon_path: str) -> CustomButton:
        button = CustomButton(self)
        button.setIcon(QIcon(icon_path))
        return button

    def rotate_ccw(self) -> None:
        # Implementation for rotating left
        pass

    def rotate_cw(self) -> None:
        # Implementation for rotating right
        pass

    def update_header_widget_size(self) -> None:
        self.setFixedSize(
            self.attr_box.attr_box_width,
            self.clock.height(),
        )
