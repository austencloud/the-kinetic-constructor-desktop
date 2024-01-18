from typing import TYPE_CHECKING
from constants import COLOR
from utilities.TypeChecking.TypeChecking import Colors
from widgets.header_widget import HeaderWidget
from .base_attr_box import AttrBox
from .attr_box_widgets.turns_widget.color_turns_widget import ColorTurnsWidget

if TYPE_CHECKING:
    from ..attr_panel.color_attr_panel import ColorAttrPanel


class ColorAttrBox(AttrBox):
    def __init__(self, attr_panel: "ColorAttrPanel", color: Colors) -> None:
        super().__init__(attr_panel, None)
        self.color = color
        self.attribute_type = COLOR
        self._setup_widgets()

    def _setup_widgets(self) -> None:
        self.header_widget = HeaderWidget(self)
        self.turns_widget = ColorTurnsWidget(self)
        self.vbox_layout.addWidget(self.header_widget, 1)
        self.vbox_layout.addWidget(self.turns_widget, 2)
