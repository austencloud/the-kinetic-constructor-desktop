from PyQt6.QtWidgets import (
    QLabel,
    QVBoxLayout,
    QPushButton,
    QSizePolicy,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from typing import TYPE_CHECKING, List, Union
from constants import (
    BLUE,
    CLOCKWISE,
    COUNTER_CLOCKWISE,
    DASH,
    HEX_BLUE,
    HEX_RED,
    ICON_DIR,
    NO_ROT,
    OPP,
    RED,
    SAME,
    STATIC,
)
from utilities.TypeChecking.TypeChecking import VtgDirections
from widgets.buttons.vtg_dir_button import VtgDirButton
from .base_attr_box_widget import AttrBoxWidget

if TYPE_CHECKING:
    from widgets.filter_frame.attr_box.color_attr_box import ColorAttrBox
    from widgets.filter_frame.attr_box.motion_type_attr_box import MotionTypeAttrBox


class VtgDirWidget(AttrBoxWidget):
    def __init__(self, attr_box) -> None:
        super().__init__(attr_box)
        self.attr_box: Union["ColorAttrBox", "MotionTypeAttrBox"] = attr_box
        self.setup_ui()

    def _setup_layout(self) -> None:
        self.layout: QVBoxLayout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.main_vbox_layout = QVBoxLayout()
        self.main_vbox_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

    def setup_ui(self) -> None:
        self._setup_layout()
        self.vtg_dir_buttons = self._setup_vtg_dir_buttons()
        self.setup_rot_dir_section()

    def _setup_vtg_dir_buttons(self) -> List[QPushButton]:
        self.same_button: VtgDirButton = self.create_vtg_dir_button(
            f"{ICON_DIR}same_direction.png", lambda: self._set_prop_rot_dir(SAME)
        )
        self.opp_button: VtgDirButton = self.create_vtg_dir_button(
            f"{ICON_DIR}opp_direction.png",
            lambda: self._set_prop_rot_dir(OPP),
        )

        self.same_button.unpress()
        self.opp_button.unpress()
        self.same_button.setCheckable(True)
        self.opp_button.setCheckable(True)

        buttons = [self.same_button, self.opp_button]
        return buttons

    def _set_default_vtg_dir(self):
        has_turns = any(
            motion.turns > 0
            for pictograph in self.attr_box.attr_panel.parent_tab.scroll_area.pictographs.values()
            for motion in pictograph.motions.values()
            if motion.motion_type == DASH
        )
        self._set_prop_rot_dir(CLOCKWISE if has_turns else None)

    def _set_prop_rot_dir(self, prop_rot_dir: VtgDirections) -> None:
        for (
            pictograph
        ) in self.attr_box.attr_panel.parent_tab.scroll_area.pictographs.values():
            for motion in pictograph.motions.values():
                if motion.motion_type in [DASH, STATIC]:
                    if motion.color == self.attr_box.color:
                        pictograph_dict = {
                            f"{motion.color}_prop_rot_dir": prop_rot_dir,
                        }
                        motion.scene.state_updater.update_pictograph(pictograph_dict)
        if prop_rot_dir:
            if prop_rot_dir == SAME:
                self.same_button.press()
                self.opp_button.unpress()
            elif prop_rot_dir == OPP:
                self.same_button.unpress()
                self.opp_button.press()
        else:
            self.same_button.unpress()
            self.opp_button.unpress()

    def _create_button(self, icon_path, action) -> QPushButton:
        button = QPushButton("", self)
        button.setIcon(QIcon(icon_path))
        button.setIconSize(button.size())
        button.clicked.connect(action)
        button.setContentsMargins(0, 0, 0, 0)
        return button

    def setup_rot_dir_section(self) -> None:
        rot_dir_layout = QVBoxLayout()
        rot_dir_label = QLabel("Dash/Static\nRot Dir:", self)
        rot_dir_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        rot_dir_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        rot_dir_layout.addWidget(rot_dir_label)
        rot_dir_layout.addWidget(self.same_button)
        rot_dir_layout.addWidget(self.opp_button)
        self.layout.addLayout(rot_dir_layout)

    ### EVENT HANDLERS ###

    def update_button_size(self) -> None:
        button_size = self.width() // 5
        for vtg_dir_button in self.vtg_dir_buttons:
            vtg_dir_button.setMinimumSize(button_size, button_size)
            vtg_dir_button.setMaximumSize(button_size, button_size)
            vtg_dir_button.setIconSize(vtg_dir_button.size() * 0.9)

    def resize_prop_rot_dir_widget(self) -> None:
        self.update_button_size()

    def _setup_header_label(self) -> QLabel:
        text = "Left" if self.attr_box.color == BLUE else "Right"
        color_hex = HEX_RED if self.attr_box.color == RED else HEX_BLUE
        label = QLabel(text, self)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet(f"color: {color_hex}; font-weight: bold;")
        return label

    def _get_current_prop_rot_dir(self) -> str:
        return (
            CLOCKWISE
            if self.same_button.isChecked()
            else COUNTER_CLOCKWISE
            if self.opp_button.isChecked()
            else NO_ROT
        )
