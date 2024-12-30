from typing import TYPE_CHECKING
from PyQt6.QtWidgets import QFrame, QGridLayout, QGraphicsOpacityEffect
from PyQt6.QtCore import Qt

if TYPE_CHECKING:
    from .option_picker_section_widget import OptionPickerSectionWidget


class OptionPickerSectionPictographFrame(QFrame):
    def __init__(self, section: "OptionPickerSectionWidget") -> None:
        super().__init__()
        self.section = section
        self.layout: QGridLayout = QGridLayout(self)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(self.section.scroll_area.spacing)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(1.0)
