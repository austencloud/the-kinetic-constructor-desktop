from typing import TYPE_CHECKING
from PyQt6.QtWidgets import (
    QCheckBox,
)
from PyQt6.QtCore import QEvent


if TYPE_CHECKING:
    from main_window.main_widget.settings_dialog.beat_layout_tab.beat_layout_options_panel import (
        BeatLayoutOptionsPanel,
    )


class GrowSequenceCheckbox(QCheckBox):
    """Custom QCheckBox for the 'grow sequence' option."""

    def __init__(self, options_panel: "BeatLayoutOptionsPanel"):
        super().__init__("Grow sequence")
        self.options_panel = options_panel
        self.settings_manager = options_panel.settings_manager
        self.sequence_widget = options_panel.sequence_widget

        grow_sequence = self.settings_manager.sequence_layout.get_layout_setting(
            "grow_sequence"
        )
        if grow_sequence == "true":
            grow_sequence = True
        elif grow_sequence == "false":
            grow_sequence = False
        self.setChecked(grow_sequence)

    def toggle_grow_sequence(self):
        """Handle the toggling of the 'grow sequence' checkbox."""
        is_grow_sequence_checked = self.options_panel.grow_sequence_checkbox.isChecked()
        self.options_panel.settings_manager.sequence_layout.set_layout_setting(
            "grow_sequence", is_grow_sequence_checked
        )

        self.options_panel.beats_label.setEnabled(not is_grow_sequence_checked)
        self.options_panel.beats_combo_box.setEnabled(not is_grow_sequence_checked)
        self.options_panel.layout_label.setEnabled(not is_grow_sequence_checked)
        self.options_panel.layout_combo_box.setEnabled(not is_grow_sequence_checked)

        color = "grey" if is_grow_sequence_checked else "black"
        self.options_panel.beats_label.setStyleSheet(f"color: {color};")
        self.options_panel.layout_label.setStyleSheet(f"color: {color};")

        if not is_grow_sequence_checked:
            num_beats = (
                self.options_panel.sequence_widget.beat_frame.get.next_available_beat()
                or 0
            )
            self.options_panel.beats_combo_box.setCurrentText(str(num_beats))
            self.options_panel._setup_layout_options()
            layout_option = (
                self.options_panel.get_layout_option_from_current_sequence_beat_frame_layout()
            )
            self.options_panel.layout_combo_box.setCurrentText(layout_option)

        self.options_panel.tab.beat_frame.update_preview()

    def resizeEvent(self, event: QEvent):
        """Handle the resize event to adjust the font size and checkbox size."""
        font = self.font()
        font_size = self.sequence_widget.main_widget.width() // 120
        font.setPointSize(font_size)
        self.setFont(font)
        self.setStyleSheet(
            f"QCheckBox::indicator {{ width: {font_size}px; height: {font_size}px; }}"
        )
        super().resizeEvent(event)
