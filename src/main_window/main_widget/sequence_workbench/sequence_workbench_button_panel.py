import json
import os
from typing import TYPE_CHECKING
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QPushButton,
    QFrame,
    QVBoxLayout,
    QApplication,
    QSpacerItem,
    QSizePolicy,
)

from main_window.main_widget.sequence_workbench.workbench_button import WorkbenchButton
from .button_panel_placeholder import ButtonPanelPlaceholder
from utils.path_helpers import get_image_path, get_user_editable_resource_path

if TYPE_CHECKING:
    from .sequence_workbench import SequenceWorkbench


class SequenceWorkbenchButtonPanel(QFrame):
    swap_colors_button: QPushButton
    copy_sequence_button: QPushButton
    colors_swapped = False
    spacers: list[QSpacerItem] = []

    def __init__(self, sequence_workbench: "SequenceWorkbench") -> None:
        super().__init__(sequence_workbench)
        self.sequence_workbench = sequence_workbench
        self.main_widget = self.sequence_workbench.main_widget
        self.beat_frame = self.sequence_workbench.beat_frame
        self.export_manager = self.beat_frame.image_export_manager
        self.indicator_label = self.sequence_workbench.indicator_label

        self.font_size = self.sequence_workbench.width() // 45

        self.top_placeholder = ButtonPanelPlaceholder(self)
        self.bottom_placeholder = ButtonPanelPlaceholder(self)

        self._setup_buttons()
        self._setup_layout()

    def _setup_buttons(self) -> None:
        self.buttons: dict[str, WorkbenchButton] = {}

        button_dict = {
            "add_to_dictionary": {
                "icon": "add_to_dictionary.svg",
                "callback": self.sequence_workbench.add_to_dictionary_ui.add_to_dictionary,
                "tooltip": "Add to Dictionary",
            },
            "save_image": {
                "icon": "save_image.svg",
                "callback": self.export_manager.export_image_directly,
                "tooltip": "Save Image",
            },
            "view_full_screen": {
                "icon": "eye.png",
                "callback": lambda: self.sequence_workbench.full_screen_viewer.view_full_screen(),
                "tooltip": "View Full Screen",
            },
            "mirror_sequence": {
                "icon": "mirror.png",
                "callback": lambda: self.sequence_workbench.mirror_manager.reflect_current_sequence(),
                "tooltip": "Mirror Sequence",
            },
            "swap_colors": {
                "icon": "yinyang1.svg",
                "callback": lambda: self.sequence_workbench.color_swap_manager.swap_current_sequence(),
                "tooltip": "Swap Colors",
            },
            "rotate_sequence": {
                "icon": "rotate.svg",
                "callback": lambda: self.sequence_workbench.rotation_manager.rotate_current_sequence(),
                "tooltip": "Rotate Sequence",
            },
            "copy_sequence": {
                "icon": None,  # No icon path, will use emoji text instead
                "callback": self._copy_sequence_json,
                "tooltip": "Copy Sequence JSON",
                "text": "📋",  # Emoji text to use instead of icon
                "font_size_multiplier": 1.5,  # For adjusting the emoji size
            },
            "delete_beat": {
                "icon": "delete.svg",
                "callback": lambda: self.sequence_workbench.beat_deleter.delete_selected_beat(),
                "tooltip": "Delete Beat",
            },
            "clear_sequence": {
                "icon": "clear.svg",
                "callback": lambda: self.clear_sequence(),
                "tooltip": "Clear Sequence",
            },

        }

        for button_name, button_data in button_dict.items():
            # Handle icon path (None for copy_sequence button)
            icon_path = None
            if button_data["icon"]:
                icon_path = get_image_path(
                    f"icons/sequence_workbench_icons/{button_data['icon']}"
                )

            # Create the button
            button = self._create_button(
                icon_path, button_data["callback"], button_data["tooltip"]
            )

            # Special handling for emoji buttons (copy_sequence and test_export)
            if (
                button_name in ["copy_sequence", "test_export"]
                and "text" in button_data
            ):
                button.setText(button_data["text"])  # Set emoji text
                # Adjust font size for emoji visibility
                font = button.font()
                font.setPointSize(
                    int(self.font_size * button_data["font_size_multiplier"])
                )
                button.setFont(font)

            # Store the button
            setattr(self, f"{button_name}_button", button)
            self.buttons[button_name] = button

    def _copy_sequence_json(self):
        """Copies the content of current_sequence.json to the clipboard and updates indicator."""
        try:
            sequence_file_path = get_user_editable_resource_path(
                "current_sequence.json"
            )
            if os.path.exists(sequence_file_path):
                with open(sequence_file_path, "r", encoding="utf-8") as file:
                    sequence_data = json.load(file)
                json_string = json.dumps(sequence_data, indent=4)
                clipboard = QApplication.clipboard()
                clipboard.setText(json_string)
                self.indicator_label.show_message("Sequence JSON copied to clipboard!")
                self.copy_sequence_button.setToolTip("Sequence JSON copied!")
            else:
                error_message = f"Error: current_sequence.json not found."
                self.indicator_label.show_message(error_message)
                self.copy_sequence_button.setToolTip("Error: File not found.")

        except json.JSONDecodeError as e:
            error_message = f"Error: Invalid JSON in current_sequence.json."
            print(f"{error_message} Details: {e}")
            self.indicator_label.show_message(error_message)
            self.copy_sequence_button.setToolTip(f"Error: Invalid JSON.")
        except Exception as e:
            error_message = f"Error copying sequence JSON."
            print(f"{error_message} Details: {e}")
            self.indicator_label.show_message(error_message)
            self.copy_sequence_button.setToolTip(f"Error: {e}")

    def _show_export_test_component(self):
        """Show the export test component in a new window."""
        from .sequence_beat_frame.image_export_manager.export_test_component import (
            ExportTestComponent,
        )

        # Create and show the test component
        self.export_test_window = ExportTestComponent(self.sequence_workbench)
        self.export_test_window.setWindowTitle("Image Export Test Component")
        self.export_test_window.resize(600, 800)
        self.export_test_window.show()

        self.indicator_label.show_message("Export test component opened")

    def clear_sequence(self):
        sequence_length = len(
            self.main_widget.json_manager.loader_saver.load_current_sequence()
        )
        # collapse the grpah editor
        graph_editor = self.sequence_workbench.graph_editor
        if sequence_length < 2:
            self.indicator_label.show_message("No sequence to clear")
            return
        if graph_editor.is_toggled:
            graph_editor.animator.toggle()
        self.sequence_workbench.indicator_label.show_message("Sequence cleared")
        self.beat_frame.sequence_workbench.beat_deleter.start_position_deleter.delete_all_beats(
            show_indicator=True
        )

    def _create_button(
        self, icon_path: str | None, callback, tooltip: str
    ) -> WorkbenchButton:
        # Allow None for icon_path
        button = WorkbenchButton(icon_path, tooltip, callback)
        return button

    def toggle_swap_colors_icon(self):
        icon_name = "yinyang1.svg" if self.colors_swapped else "yinyang2.svg"
        new_icon_path = get_image_path(f"icons/sequence_workbench_icons/{icon_name}")
        self.colors_swapped = not self.colors_swapped
        new_icon = QIcon(new_icon_path)
        self.swap_colors_button.setIcon(new_icon)
        QApplication.processEvents()

    def _setup_layout(self) -> None:
        self.layout: QVBoxLayout = QVBoxLayout(self)
        self.layout.addWidget(self.top_placeholder)

        # Group 1 (Basic Tools)
        for name in ["add_to_dictionary", "save_image", "view_full_screen"]:
            self.layout.addWidget(self.buttons[name])

        # Add spacing to separate groups
        self.spacer1 = QSpacerItem(
            20,
            self.sequence_workbench.height() // 20,
            QSizePolicy.Policy.Minimum,
            QSizePolicy.Policy.Expanding,
        )
        self.layout.addItem(self.spacer1)
        if not hasattr(self, "spacers"):
            self.spacers = []  # Ensure spacers list exists
        self.spacers.append(self.spacer1)  # Keep track of spacers

        # Group 2 (Transform Tools)
        for name in ["mirror_sequence", "swap_colors", "rotate_sequence"]:
            self.layout.addWidget(self.buttons[name])

        # Add spacing before next group
        self.spacer2 = QSpacerItem(
            20,
            self.sequence_workbench.height() // 20,
            QSizePolicy.Policy.Minimum,
            QSizePolicy.Policy.Expanding,
        )
        self.layout.addItem(self.spacer2)
        self.spacers.append(self.spacer2)  # Keep track of spacers

        # Group 3 (Sequence Management)
        # Order: delete_beat, copy_sequence, test_export, clear_sequence
        for name in ["delete_beat", "copy_sequence", "test_export", "clear_sequence"]:
            if name in self.buttons:  # Check if button exists before adding
                self.layout.addWidget(self.buttons[name])

        self.layout.addWidget(self.bottom_placeholder)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        # Initial spacing setup - Reuse spacer3 if it exists, otherwise create it
        if not hasattr(self, "spacer3"):
            self.spacer3 = QSpacerItem(
                20,
                self.sequence_workbench.height() // 40,
                QSizePolicy.Policy.Minimum,
                QSizePolicy.Policy.Expanding,
            )
            self.layout.addItem(self.spacer3)
            self.spacers.append(self.spacer3)  # Keep track of spacers

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.resize_button_panel()

    def resize_button_panel(self):
        button_size = self.sequence_workbench.main_widget.height() // 20
        # Resize all buttons
        for button_name, button in self.buttons.items():
            # Special handling for emoji button text size during resize
            if button_name in ["copy_sequence", "test_export"]:
                font = button.font()
                # Use the same multiplier as defined in the button_dict
                font.setPointSize(
                    int(button_size * 0.5)  # Use a consistent scaling factor
                )
                button.setFont(font)

            # Update size for all buttons
            button.update_size(button_size)

        self.layout.setSpacing(
            self.sequence_workbench.beat_frame.main_widget.height() // 120
        )

        spacer_size = self.sequence_workbench.beat_frame.main_widget.height() // 20
        # Update all tracked spacers
        if hasattr(self, "spacers"):  # Check if spacers list exists
            for spacer in self.spacers:
                if spacer:  # Check if spacer exists
                    spacer.changeSize(
                        20,
                        spacer_size,
                        QSizePolicy.Policy.Minimum,
                        QSizePolicy.Policy.Expanding,
                    )
        self.layout.update()
