from PyQt6.QtWidgets import QPushButton
from PyQt6.QtGui import QIcon
from settings.string_constants import BLUE, RED, COLOR, ICON_PATHS
from settings.numerical_constants import BUTTON_SIZE
from typing import TYPE_CHECKING, Dict, Callable, List
from utilities.TypeChecking.TypeChecking import Color

if TYPE_CHECKING:
    from widgets.graph_editor.infobox.infobox import InfoBox
    from widgets.graph_editor.graphboard.graphboard import GraphBoard
    from widgets.graph_editor.infobox.control_panel.control_panel import ControlPanel
from PyQt6.QtWidgets import QVBoxLayout

class InfoBoxButtons:
    def __init__(self, control_panel: 'ControlPanel', graphboard: "GraphBoard") -> None:
        self.graphboard = graphboard
        self.control_panel = control_panel
        self.button_groups: Dict[str, List[QPushButton]] = {BLUE: [], RED: []}
        self.setup_buttons()
        self.setup_button_layout()

    def create_and_set_button(
        self, button_name: str, properties: Dict[str, str | Callable]
    ) -> None:
        icon = properties.get("icon", None)
        button = QPushButton(QIcon(icon), properties.get("text", ""))

        button.clicked.connect(properties["callback"])
        button.setFixedSize(BUTTON_SIZE, BUTTON_SIZE)
        setattr(self, f"{button_name}_button", button)
        button.hide()

        # Add the button to the appropriate color group
        if BLUE in button_name:
            self.button_groups[BLUE].append(button)
        elif RED in button_name:
            self.button_groups[RED].append(button)

    def show_buttons(self, arrow_color: Color) -> None:
        for button in self.button_groups[arrow_color]:
            button.show()

    def setup_buttons(self) -> None:
        self.button_properties = {
            "swap_motion_type_blue": {
                "icon": ICON_PATHS["swap"],
                "callback": lambda: self.graphboard.get_arrow_by_color(
                    BLUE
                ).swap_motion_type(),
            },
            "swap_motion_type_red": {
                "icon": ICON_PATHS["swap"],
                "callback": lambda: self.graphboard.get_arrow_by_color(
                    RED
                ).swap_motion_type(),
            },
            "swap_start_end_blue": {
                "icon": ICON_PATHS["swap"],
                "callback": lambda: self.graphboard.get_arrow_by_color(
                    BLUE
                ).swap_rot_dir(),
            },
            "swap_start_end_red": {
                "icon": ICON_PATHS["swap"],
                "callback": lambda: self.graphboard.get_arrow_by_color(
                    RED
                ).swap_rot_dir(),
            },
            "decrement_turns_blue": {
                "icon": ICON_PATHS["decrement_turns"],
                "callback": lambda: self.graphboard.get_arrow_by_color(
                    BLUE
                ).subtract_turn(),
            },
            "increment_turns_blue": {
                "icon": ICON_PATHS["increment_turns"],
                "callback": lambda: self.graphboard.get_arrow_by_color(BLUE).add_turn(),
            },
            "decrement_turns_red": {
                "icon": ICON_PATHS["decrement_turns"],
                "callback": lambda: self.graphboard.get_arrow_by_color(
                    RED
                ).subtract_turn(),
            },
            "increment_turns_red": {
                "icon": ICON_PATHS["increment_turns"],
                "callback": lambda: self.graphboard.get_arrow_by_color(RED).add_turn(),
            },
        }

        self.create_infobox_buttons()


    def create_infobox_buttons(self) -> None:
        for button_name, properties in self.button_properties.items():
            self.create_and_set_button(button_name, properties)

        self.setup_button_layout()

    def setup_button_layout(self) -> None:
        self.button_layout = QVBoxLayout()  # Create a vertical layout for the buttons
        for button_name in self.button_properties.keys():
            button = getattr(self, f"{button_name}_button")
            self.button_layout.addWidget(button)  # Add each button to the layout
