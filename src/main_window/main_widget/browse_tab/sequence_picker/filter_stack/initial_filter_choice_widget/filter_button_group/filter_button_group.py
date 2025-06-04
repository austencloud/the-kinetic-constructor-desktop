from typing import TYPE_CHECKING
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy
from PyQt6.QtGui import QFont, QResizeEvent
from PyQt6.QtCore import Qt, QTimer, QSize

from main_window.main_widget.browse_tab.sequence_picker.filter_stack.initial_filter_choice_widget.filter_button_group.filter_button import (
    FilterButton,
)

if TYPE_CHECKING:
    from ..initial_filter_choice_widget import InitialFilterChoiceWidget


class FilterButtonGroup(QWidget):
    """A modern 2025 filter button group with responsive design and glass-morphism effects."""

    def __init__(
        self,
        label: str,
        description: str,
        handler: callable,
        filter_choice_widget: "InitialFilterChoiceWidget",
    ):
        super().__init__()
        self.main_widget = filter_choice_widget.main_widget
        self.settings_manager = self.main_widget.settings_manager
        self.filter_choice_widget = filter_choice_widget
        self.original_handler = handler

        # Modern responsive sizing
        self._setup_responsive_sizing()

        self.button = FilterButton(label)
        # INSTANT SWITCHING: Override with instant response handler
        self.button.clicked.connect(self._instant_click_handler)

        # Enhanced responsiveness with proper timing
        QTimer.singleShot(50, self._ensure_modern_responsiveness)

        self.description_label = QLabel(description)
        self._setup_modern_layout()
        self._apply_modern_styling()

    def _setup_responsive_sizing(self):
        """Setup modern responsive sizing policies."""
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self.setMinimumSize(QSize(120, 80))
        self.setMaximumSize(QSize(200, 120))

    def _setup_modern_layout(self):
        """Setup modern layout with proper spacing and alignment."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Button with responsive sizing
        layout.addWidget(self.button, 0, Qt.AlignmentFlag.AlignCenter)

        # Description label with modern typography
        self.description_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.description_label.setWordWrap(True)
        layout.addWidget(self.description_label, 0, Qt.AlignmentFlag.AlignCenter)

        self.setLayout(layout)

    def _apply_modern_styling(self):
        """Apply PyQt6-compatible modern styling to the button group."""
        # Modern container styling (PyQt6-compatible)
        self.setStyleSheet(
            """
            FilterButtonGroup {
                background: rgba(255, 255, 255, 0.05);
                border-radius: 16px;
                border: 1px solid rgba(255, 255, 255, 0.1);
                margin: 4px;
                padding: 8px;
            }
        """
        )

    def resizeEvent(self, event: QResizeEvent) -> None:
        """Modern responsive resize handling with proper scaling."""
        if not self.main_widget:
            super().resizeEvent(event)
            return

        # Calculate responsive dimensions based on container size
        container_width = (
            self.filter_choice_widget.width()
            if hasattr(self.filter_choice_widget, "width")
            else 800
        )
        container_height = (
            self.filter_choice_widget.height()
            if hasattr(self.filter_choice_widget, "height")
            else 600
        )

        # Modern responsive button sizing (percentage-based)
        button_width = max(100, min(180, container_width // 6))
        button_height = max(40, min(60, container_height // 12))

        # Set button size with modern proportions
        self.button.setFixedSize(button_width, button_height)

        # Modern typography scaling
        self._update_modern_typography(container_width)

        super().resizeEvent(event)

    def _update_modern_typography(self, container_width: int):
        """Update typography with modern responsive scaling."""
        # Button font with proper scaling
        button_font = QFont("Segoe UI, Arial, sans-serif")
        button_font_size = max(10, min(16, container_width // 60))
        button_font.setPointSize(button_font_size)
        button_font.setWeight(QFont.Weight.Medium)
        self.button.setFont(button_font)

        # Description label with modern typography
        desc_font_size = max(8, min(12, container_width // 80))
        color = self._get_modern_text_color()

        self.description_label.setStyleSheet(
            f"""
            QLabel {{
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: {desc_font_size}px;
                font-weight: 400;
                color: {color};
                line-height: 1.4;
                margin-top: 4px;
            }}
        """
        )

    def _get_modern_text_color(self) -> str:
        """Get modern text color with proper contrast."""
        try:
            return self.settings_manager.global_settings.get_current_font_color()
        except:
            return "rgba(255, 255, 255, 0.9)"  # Modern high-contrast fallback

    def _ensure_modern_responsiveness(self):
        """Ensure modern responsiveness with enhanced activation."""
        try:
            # Enhanced button activation
            self.button.setEnabled(True)
            self.button.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
            self.button.update()

            # Ensure proper focus policies
            self.button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

            # Force layout update
            self.updateGeometry()

        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.debug(f"Error in modern responsiveness setup: {e}")

    def _instant_click_handler(self):
        """Handle button clicks with INSTANT visual feedback."""
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import QTimer

        try:
            # INSTANT: Provide immediate visual feedback
            self._show_instant_feedback()

            # INSTANT: Process events for immediate UI update
            QApplication.processEvents()

            # INSTANT: Disable animations temporarily
            self._disable_animations_temporarily()

            # INSTANT: Execute the handler immediately for visual changes
            if hasattr(self.original_handler, "func") and hasattr(
                self.original_handler, "args"
            ):
                # This is a partial function - check if it's show_section
                if (
                    hasattr(self.original_handler.func, "__name__")
                    and "show_section" in self.original_handler.func.__name__
                ):
                    # Section switching - do it instantly
                    self._instant_section_switch()
                else:
                    # Filter application - do it instantly with background loading
                    self._instant_filter_application()
            else:
                # Direct handler call
                self._instant_direct_handler()

            print(f"✅ Filter button '{self.button.text()}' switched INSTANTLY")

        except Exception as e:
            print(f"❌ Error in instant filter button click: {e}")
            # Fallback to original handler if instant fails
            try:
                self.original_handler()
            except Exception as fallback_error:
                print(f"❌ Fallback handler also failed: {fallback_error}")

    def _show_instant_feedback(self):
        """Show immediate visual feedback for button click."""
        try:
            # Flash button to show it was clicked
            self.button.setStyleSheet(
                """
                FilterButton {
                    background: rgba(0, 120, 255, 0.3);
                    border: 2px solid rgba(0, 120, 255, 0.8);
                }
            """
            )

            # Reset after short delay
            QTimer.singleShot(150, self._reset_button_style)

        except Exception as e:
            print(f"Error showing instant feedback: {e}")

    def _reset_button_style(self):
        """Reset button style after feedback."""
        try:
            self.button.setStyleSheet("")  # Reset to default
        except Exception as e:
            print(f"Error resetting button style: {e}")

    def _disable_animations_temporarily(self):
        """Temporarily disable animations for instant switching."""
        try:
            fade_manager = getattr(self.main_widget, "fade_manager", None)
            if fade_manager and hasattr(fade_manager, "set_fades_enabled"):
                fade_manager.set_fades_enabled(False)
                # Re-enable after instant switch
                QTimer.singleShot(200, lambda: fade_manager.set_fades_enabled(True))
        except Exception as e:
            print(f"Error disabling animations: {e}")

    def _instant_section_switch(self):
        """Handle instant section switching."""
        from PyQt6.QtWidgets import QApplication

        try:
            # Extract section name from partial function
            if hasattr(self.original_handler, "args") and self.original_handler.args:
                section_name = self.original_handler.args[0]

                # Get filter stack
                filter_stack = self.filter_choice_widget.filter_selector

                # INSTANT: Switch immediately without fade
                if hasattr(filter_stack, "show_section"):
                    # Direct section switching
                    filter_stack.show_section(section_name)

                # INSTANT: Force immediate visual update
                QApplication.processEvents()

                print(f"✅ Section '{section_name}' switched instantly")

        except Exception as e:
            print(f"Error in instant section switch: {e}")
            # Fallback to original handler
            self.original_handler()

    def _instant_filter_application(self):
        """Handle instant filter application with background loading."""
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import QTimer

        try:
            # Extract filter criteria from partial function
            if hasattr(self.original_handler, "args") and self.original_handler.args:
                filter_criteria = self.original_handler.args[0]

                # Get browse tab components
                browse_tab = self.filter_choice_widget.browse_tab
                filter_controller = browse_tab.filter_controller

                # INSTANT: Switch to sequence picker view immediately
                self._instant_switch_to_sequence_picker()

                # INSTANT: Show loading state
                self._show_filter_loading_state(filter_criteria)

                # INSTANT: Process events for immediate visual update
                QApplication.processEvents()

                # BACKGROUND: Apply filter after visual switch
                QTimer.singleShot(
                    1, lambda: self._apply_filter_background(filter_criteria)
                )

                print(
                    f"✅ Filter '{filter_criteria}' applied instantly with background loading"
                )

        except Exception as e:
            print(f"Error in instant filter application: {e}")
            # Fallback to original handler
            self.original_handler()

    def _instant_direct_handler(self):
        """Handle direct handler calls instantly."""
        from PyQt6.QtWidgets import QApplication

        try:
            # Execute handler immediately
            self.original_handler()

            # Process events for immediate update
            QApplication.processEvents()

        except Exception as e:
            print(f"Error in direct handler: {e}")
            raise

    def _instant_switch_to_sequence_picker(self):
        """Instantly switch to sequence picker view."""
        try:
            browse_tab = self.filter_choice_widget.browse_tab

            # Switch internal stack to sequence picker
            if hasattr(browse_tab, "internal_left_stack"):
                sequence_picker_index = 1  # Sequence picker is typically at index 1
                browse_tab.internal_left_stack.setCurrentIndex(sequence_picker_index)

            # Update browse settings
            browse_tab.browse_settings.set_current_section("sequence_picker")

        except Exception as e:
            print(f"Error switching to sequence picker: {e}")

    def _show_filter_loading_state(self, filter_criteria):
        """Show loading state for filter application."""
        try:
            browse_tab = self.filter_choice_widget.browse_tab

            if hasattr(browse_tab, "sequence_picker") and hasattr(
                browse_tab.sequence_picker, "control_panel"
            ):
                control_panel = browse_tab.sequence_picker.control_panel

                # Show loading message
                if hasattr(control_panel, "currently_displaying_label"):
                    control_panel.currently_displaying_label.setText(
                        f"Loading {filter_criteria}..."
                    )

                # Clear current sequences
                if hasattr(browse_tab.sequence_picker, "scroll_widget"):
                    browse_tab.sequence_picker.scroll_widget.clear_layout()

        except Exception as e:
            print(f"Error showing loading state: {e}")

    def _apply_filter_background(self, filter_criteria):
        """Apply filter in background after instant visual switch."""
        try:
            browse_tab = self.filter_choice_widget.browse_tab
            filter_controller = browse_tab.filter_controller

            # Apply filter without fade (since we already switched)
            filter_controller.apply_filter(filter_criteria, fade=False)

        except Exception as e:
            print(f"Error applying filter in background: {e}")
