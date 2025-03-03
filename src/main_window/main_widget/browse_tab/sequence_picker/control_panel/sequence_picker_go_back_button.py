from typing import TYPE_CHECKING

from main_window.main_widget.tab_indices import LeftStackIndex
from styles.base_styled_button import BaseStyledButton

if TYPE_CHECKING:
    from ..sequence_picker import SequencePicker


class SequencePickerGoBackButton(BaseStyledButton):
    """A go-back button that returns to the initial filter selection."""

    def __init__(self, sequence_picker: "SequencePicker"):
        super().__init__("Go Back")
        self.sequence_picker = sequence_picker
        self.browse_tab = self.sequence_picker.browse_tab
        self.main_widget = self.sequence_picker.main_widget
        self.clicked.connect(self.switch_to_initial_filter_selection)

    def switch_to_initial_filter_selection(self):
        """Switch to the initial selection page in the stacked layout."""
        self.main_widget.fade_manager.stack_fader.fade_stack(
            self.main_widget.left_stack, LeftStackIndex.FILTER_SELECTOR, 300
        )
        self.browse_tab.browse_settings.set_browse_left_stack_index(
            LeftStackIndex.FILTER_SELECTOR.value
        )
        self.browse_tab.browse_settings.set_current_section("filter_selector")
        self.browse_tab.browse_settings.set_current_filter(None)

    def resizeEvent(self, event) -> None:
        """Handle resizing to update styles dynamically."""
        self._border_radius = min(self.height(), self.width()) // 2
        self.update_appearance()
        self.setFixedWidth(int(self.sequence_picker.control_panel.width() // 10))
        self.setFixedHeight(int(self.sequence_picker.height() // 16))
        super().resizeEvent(event)
