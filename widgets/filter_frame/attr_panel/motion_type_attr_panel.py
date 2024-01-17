from constants import ANTI, DASH, PRO, STATIC
from typing import TYPE_CHECKING, List, Union
from utilities.TypeChecking.TypeChecking import MotionTypes
from data.letter_engine_data import motion_type_letter_combinations

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt

from ..attr_box.motion_type_attr_box import MotionTypeAttrBox
from ..attr_panel.base_attr_panel import BaseAttrPanel


if TYPE_CHECKING:
    from ...option_picker_tab.option_picker_tab import OptionPickerTab
    from ...ig_tab.ig_tab import IGTab


class MotionTypeAttrPanel(BaseAttrPanel):
    def __init__(self, parent_tab: Union["IGTab", "OptionPickerTab"]) -> None:
        super().__init__(parent_tab)
        self.parent_tab = parent_tab

        self.placeholder_label = QLabel(
            "Please select a letter to view motion type adjustments.", self
        )
        self.placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.placeholder_label.setFont(QFont("Arial", 14))
        self.placeholder_label.setWordWrap(True)
        self.setup_layouts()
        self.layout.addWidget(self.placeholder_label)

        self.pro_attr_box = MotionTypeAttrBox(self, PRO)
        self.anti_attr_box = MotionTypeAttrBox(self, ANTI)
        self.dash_attr_box = MotionTypeAttrBox(self, DASH)
        self.static_attr_box = MotionTypeAttrBox(self, STATIC)
        self.boxes: List[MotionTypeAttrBox] = [
            self.pro_attr_box,
            self.anti_attr_box,
            self.dash_attr_box,
            self.static_attr_box,
        ]
        for box in self.boxes:
            box.hide()
            self.layout.addWidget(box)

    def add_black_borders(self) -> None:
        self.setStyleSheet(
            f"{self.styleSheet()} border: 1px solid black; border-radius: 0px;"
        )
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.setContentsMargins(0, 0, 0, 0)

    def update_motion_type_widget_visibility(self, selected_letters: List[str]) -> None:
        """Update the visibility of motion type widgets based on selected letters."""
        if not selected_letters:
            self.placeholder_label.show()
            for box in self.boxes:
                box.hide()
                box.turns_widget.turn_display_manager.turns_display.setText("0")
                if hasattr(box.header_widget, "same_button"):
                    box.header_widget.same_button.unpress()
                    box.header_widget.opp_button.unpress()
        else:
            self.hide_placeholder_message()
            motion_types_in_use = set()
            for letter in selected_letters:
                motions = motion_type_letter_combinations.get(letter, ())
                motion_types_in_use.update(motions)

            for box in self.boxes:
                box.setVisible(box.motion_type in motion_types_in_use)
                self.layout.addWidget(box)
                box.resize_ig_motion_type_attr_box()


    def hide_placeholder_message(self) -> None:
        """Hide the placeholder message."""
        self.placeholder_label.hide()

    def get_turns_for_motion_type(self, motion_type: MotionTypes) -> int:
        for box in self.boxes:
            if box.motion_type == motion_type:
                if box.turns_widget.turn_display_manager.turns_display.text() in [
                    "0",
                    "1",
                    "2",
                    "3",
                ]:
                    return int(
                        box.turns_widget.turn_display_manager.turns_display.text()
                    )
                elif box.turns_widget.turn_display_manager.turns_display.text() in [
                    "0.5",
                    "1.5",
                    "2.5",
                ]:
                    return float(
                        box.turns_widget.turn_display_manager.turns_display.text()
                    )

    def resize_attr_panel(self) -> None:
        self.layout.setSpacing(int(self.boxes[0].width() / 5))
        for box in self.boxes:
            box.resize_attr_box()
