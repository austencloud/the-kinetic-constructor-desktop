# src/main_window/main_widget/sequence_card_tab/components/navigation/mode_toggle.py
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel, QFrame
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QCursor
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from main_window.main_widget.sequence_card_tab.core.mode_manager import (
        SequenceCardMode,
    )

from main_window.main_widget.sequence_card_tab.core.mode_manager import SequenceCardMode


class ModeToggleWidget(QWidget):
    """
    Modern toggle widget for switching between Dictionary and Generation modes.
    Enhanced with responsive sizing and improved visual hierarchy.
    """

    mode_change_requested = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_mode = SequenceCardMode.DICTIONARY
        self.buttons = {}
        self.parent_widget = parent
        self.setup_ui()
        self.apply_styling()

    def setup_ui(self):
        """Setup the UI components with responsive design."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(0)

        self.container_frame = QFrame()
        self.container_frame.setObjectName("modeToggleContainer")
        container_layout = QHBoxLayout(self.container_frame)
        container_layout.setContentsMargins(2, 2, 2, 2)
        container_layout.setSpacing(0)

        self.dict_button = self.create_mode_button(
            "Dictionary", SequenceCardMode.DICTIONARY, "Browse saved sequences"
        )
        container_layout.addWidget(self.dict_button)

        self.gen_button = self.create_mode_button(
            "Generation",
            SequenceCardMode.GENERATION,
            "Create new sequences and view approved sequences",
        )
        container_layout.addWidget(self.gen_button)

        layout.addWidget(self.container_frame)
        self.update_button_states()

    def create_mode_button(
        self, text: str, mode: SequenceCardMode, tooltip: str
    ) -> QPushButton:
        """Create a mode toggle button with enhanced styling."""
        button = QPushButton(text)
        button.setCheckable(True)
        button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        button.setToolTip(tooltip)
        button.setObjectName(f"modeButton{mode.value.title()}")

        self.buttons[mode] = button
        button.clicked.connect(lambda checked, m=mode: self.on_mode_button_clicked(m))

        # Set initial responsive font
        self._update_button_font(button)
        return button

    def _update_button_font(self, button):
        """Update button font size responsively."""
        try:
            # Get parent widget width for calculation
            if self.parent_widget and hasattr(self.parent_widget, "sequence_car_tab"):
                widget_width = self.parent_widget.sequence_car_tab.width()
            else:
                widget_width = 800  # Fallback

            if widget_width < 100:
                widget_width = 800  # Fallback for invalid width

            # VISUAL HIERARCHY: Mode toggle buttons should be larger and more prominent
            font_size = max(
                12, min(16, widget_width // 45)
            )  # Larger font than other elements

            button_font = QFont()
            button_font.setPointSize(font_size)
            button_font.setWeight(QFont.Weight.Medium)
            button.setFont(button_font)
        except:
            # Fallback
            button_font = QFont()
            button_font.setPointSize(12)
            button_font.setWeight(QFont.Weight.Medium)
            button.setFont(button_font)

    def resizeEvent(self, event):
        """Handle resize events for responsive button sizing."""
        super().resizeEvent(event)

        # Update all button fonts
        for button in self.buttons.values():
            self._update_button_font(button)

        # Update button dimensions
        self._update_button_dimensions()

    def _update_button_dimensions(self):
        """Update button dimensions responsively."""
        try:
            if self.parent_widget and hasattr(self.parent_widget, "sequence_car_tab"):
                widget_width = self.parent_widget.sequence_car_tab.width()
            else:
                widget_width = 800

            if widget_width < 100:
                widget_width = 800

            # Calculate responsive button dimensions
            button_min_width = max(80, widget_width // 12)  # Scale with width
            button_height = max(
                36, min(48, widget_width // 25)
            )  # Taller buttons for prominence
            padding_h = max(16, min(24, widget_width // 50))
            padding_v = max(10, min(16, widget_width // 60))

            # Apply to all buttons
            for button in self.buttons.values():
                button.setMinimumWidth(button_min_width)
                button.setMinimumHeight(button_height)
        except:
            pass  # Fallback to CSS defaults

    def on_mode_button_clicked(self, mode: SequenceCardMode):
        """Handle mode button clicks."""
        if mode != self.current_mode:
            self.mode_change_requested.emit(mode)

    def set_current_mode(self, mode: SequenceCardMode):
        """Set the current mode and update button states."""
        if mode != self.current_mode:
            self.current_mode = mode
            self.update_button_states()

    def update_button_states(self):
        """Update button visual states based on current mode."""
        for mode, button in self.buttons.items():
            button.blockSignals(True)
            button.setChecked(mode == self.current_mode)
            button.blockSignals(False)

    def set_mode_enabled(self, mode: SequenceCardMode, enabled: bool):
        """Enable or disable a specific mode button."""
        if mode in self.buttons:
            button = self.buttons[mode]
            button.setEnabled(enabled)

            if not enabled:
                if mode == SequenceCardMode.GENERATION:
                    button.setToolTip(
                        "Generation mode requires the Generate tab to be available"
                    )
                else:
                    button.setToolTip("This mode is currently unavailable")
            else:
                if mode == SequenceCardMode.DICTIONARY:
                    button.setToolTip("Browse saved sequences")
                elif mode == SequenceCardMode.GENERATION:
                    button.setToolTip(
                        "Create new sequences and view approved sequences"
                    )

    def get_current_mode(self) -> SequenceCardMode:
        """Get the currently selected mode."""
        return self.current_mode

    def apply_styling(self):
        """Apply enhanced responsive styling to the toggle widget."""
        self.setStyleSheet(
            """
            QWidget#modeToggleWidget {
                background: transparent;
            }
            
            QFrame#modeToggleContainer {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 0.15),
                    stop:1 rgba(255, 255, 255, 0.08));
                border: 2px solid rgba(255, 255, 255, 0.25);
                border-radius: 12px;
                padding: 3px;
            }
            
            QPushButton[objectName^="modeButton"] {
                background: transparent;
                border: none;
                color: #e1e5e9;
                padding: 12px 20px;
                border-radius: 10px;
                font-weight: 500;
                min-width: 90px;
                min-height: 40px;
                text-align: center;
            }
            
            QPushButton[objectName^="modeButton"]:hover {
                background: rgba(255, 255, 255, 0.15);
                color: #ffffff;
            }
            
            QPushButton[objectName^="modeButton"]:checked {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4299e1, stop:1 #3182ce);
                color: white;
                font-weight: 700;
                border: 1px solid rgba(255, 255, 255, 0.3);
            }
            
            QPushButton[objectName^="modeButton"]:checked:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #63b3ed, stop:1 #4299e1);
            }
            
            QPushButton[objectName^="modeButton"]:disabled {
                color: #718096;
                background: transparent;
            }
            
            QPushButton[objectName^="modeButton"]:disabled:hover {
                background: transparent;
            }
        """
        )

        self.setObjectName("modeToggleWidget")

    def get_mode_summary(self) -> str:
        """Get a summary of the current mode for display."""
        if self.current_mode == SequenceCardMode.DICTIONARY:
            return "Dictionary Mode - Browsing saved sequences"
        elif self.current_mode == SequenceCardMode.GENERATION:
            return "Generation Mode - Creating and viewing sequences"
        else:
            return "Unknown Mode"
