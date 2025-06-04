from datetime import datetime
import os
from typing import TYPE_CHECKING
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import Qt, QTimer

from main_window.main_widget.metadata_extractor import MetaDataExtractor
from utils.path_helpers import get_data_path

if TYPE_CHECKING:
    from main_window.main_widget.browse_tab.sequence_picker.filter_stack.sequence_picker_filter_stack import (
        SequencePickerFilterStack,
    )


class FilterSectionBase(QWidget):
    def __init__(self, filter_selector: "SequencePickerFilterStack", label_text: str):
        super().__init__(filter_selector)
        self.filter_selector = filter_selector
        self.buttons: dict[str, QPushButton] = {}
        self.sequence_picker = filter_selector.sequence_picker
        self.browse_tab = filter_selector.browse_tab
        self.main_widget = filter_selector.browse_tab.main_widget
        self.metadata_extractor = MetaDataExtractor()
        self._setup_ui(label_text)

        self.initialized = False

    def _setup_ui(self, label_text: str):
        layout = QVBoxLayout(self)

        self.header_label = QLabel(label_text)
        self.header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.header_label)
        layout.addStretch(1)
        self.setLayout(layout)

        self.header_label.hide()

    def get_sorted_base_words(self, sort_order) -> list[tuple[str, list[str], None]]:
        dictionary_dir = get_data_path("dictionary")
        base_words = [
            (
                d,
                self.main_widget.thumbnail_finder.find_thumbnails(
                    os.path.join(dictionary_dir, d)
                ),
                None,
            )
            for d in os.listdir(dictionary_dir)
            if os.path.isdir(os.path.join(dictionary_dir, d)) and "__pycache__" not in d
        ]

        for i, (word, thumbnails, _) in enumerate(base_words):
            sequence_length = self.get_sequence_length_from_thumbnails(thumbnails)

            base_words[i] = (word, thumbnails, sequence_length)

        if sort_order == "sequence_length":
            base_words.sort(key=lambda x: x[2] if x[2] is not None else float("inf"))
        elif sort_order == "date_added":
            base_words.sort(
                key=lambda x: self.filter_selector.sequence_picker.section_manager.get_date_added(
                    x[1]
                )
                or datetime.min,
                reverse=True,
            )
        else:
            base_words.sort(key=lambda x: x[0])
        return base_words

    def get_sequence_length_from_thumbnails(self, thumbnails):
        """Extract the sequence length from the first available thumbnail metadata."""
        for thumbnail in thumbnails:
            length = self.metadata_extractor.get_length(thumbnail)
            if length:
                return length
        return None

    def create_instant_button_handler(self, original_handler, button_context=""):
        """Create an instant response handler for filter section buttons."""

        def instant_handler():
            from PyQt6.QtWidgets import QApplication
            from PyQt6.QtCore import QTimer

            try:
                print(f"🚀 INSTANT: Filter section button clicked - {button_context}")

                # INSTANT: Show immediate visual feedback
                self._show_instant_section_feedback(button_context)

                # INSTANT: Process events for immediate response
                QApplication.processEvents()

                # INSTANT: Disable animations temporarily
                self._disable_section_animations()

                # INSTANT: Switch to sequence picker immediately
                self._instant_switch_to_results_view()

                # INSTANT: Show loading state immediately
                self._show_instant_loading_state(button_context)

                # INSTANT: Force immediate visual update
                QApplication.processEvents()

                # BACKGROUND: Execute actual filter logic
                QTimer.singleShot(
                    1,
                    lambda: self._execute_filter_background(
                        original_handler, button_context
                    ),
                )

                print(f"✅ Section button '{button_context}' responded INSTANTLY")

            except Exception as e:
                print(f"❌ Error in instant section handler: {e}")
                # Fallback to original handler
                try:
                    original_handler()
                except Exception as fallback_error:
                    print(f"❌ Fallback also failed: {fallback_error}")

        return instant_handler

    def _show_instant_section_feedback(self, context):
        """Show immediate visual feedback for section button click."""
        try:
            # Flash effect for clicked button (if we can identify it)
            from PyQt6.QtCore import QTimer

            if context in self.buttons:
                button = self.buttons[context]
                original_style = button.styleSheet()

                # Apply click feedback
                button.setStyleSheet(
                    """
                    StyledButton {
                        background: rgba(0, 120, 255, 0.4);
                        border: 2px solid rgba(0, 120, 255, 1.0);
                    }
                """
                )

                # Reset after feedback
                QTimer.singleShot(200, lambda: button.setStyleSheet(original_style))

        except Exception as e:
            print(f"Error showing section feedback: {e}")

    def _disable_section_animations(self):
        """Temporarily disable animations for instant section switching."""
        try:
            fade_manager = getattr(self.main_widget, "fade_manager", None)
            if fade_manager and hasattr(fade_manager, "set_fades_enabled"):
                fade_manager.set_fades_enabled(False)
                # Re-enable after instant switch
                QTimer.singleShot(300, lambda: fade_manager.set_fades_enabled(True))
        except Exception as e:
            print(f"Error disabling section animations: {e}")

    def _instant_switch_to_results_view(self):
        """Instantly switch to the sequence picker results view."""
        try:
            # Switch browse tab internal stack to sequence picker
            if hasattr(self.browse_tab, "internal_left_stack"):
                sequence_picker_index = 1  # Sequence picker is typically at index 1
                self.browse_tab.internal_left_stack.setCurrentIndex(
                    sequence_picker_index
                )

            # Update browse settings immediately
            self.browse_tab.browse_settings.set_current_section("sequence_picker")

            print("✅ Switched to results view instantly")

        except Exception as e:
            print(f"Error switching to results view: {e}")

    def _show_instant_loading_state(self, context):
        """Show loading state immediately after button click."""
        try:
            if hasattr(self.browse_tab, "sequence_picker") and hasattr(
                self.browse_tab.sequence_picker, "control_panel"
            ):

                control_panel = self.browse_tab.sequence_picker.control_panel

                # Show loading message
                if hasattr(control_panel, "currently_displaying_label"):
                    control_panel.currently_displaying_label.setText(
                        f"Loading {context}..."
                    )

                # Clear current layout immediately
                if hasattr(self.browse_tab.sequence_picker, "scroll_widget"):
                    self.browse_tab.sequence_picker.scroll_widget.clear_layout()

        except Exception as e:
            print(f"Error showing loading state: {e}")

    def _execute_filter_background(self, original_handler, context):
        """Execute the actual filter logic in background."""
        try:
            print(f"🔄 Executing filter for '{context}' in background...")

            # Execute the original handler without fade (visual switch already done)
            original_handler()

            print(f"✅ Background filter execution completed for '{context}'")

        except Exception as e:
            print(f"❌ Error in background filter execution: {e}")
            # Show error state
            self._show_filter_error_state(context, str(e))

    def _show_filter_error_state(self, context, error_msg):
        """Show error state if filter execution fails."""
        try:
            if hasattr(self.browse_tab, "sequence_picker") and hasattr(
                self.browse_tab.sequence_picker, "control_panel"
            ):

                control_panel = self.browse_tab.sequence_picker.control_panel

                if hasattr(control_panel, "currently_displaying_label"):
                    control_panel.currently_displaying_label.setText(
                        f"Error loading {context}: {error_msg}"
                    )

        except Exception as e:
            print(f"Error showing error state: {e}")
