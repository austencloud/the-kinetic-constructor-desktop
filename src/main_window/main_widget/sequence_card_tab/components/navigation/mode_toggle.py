# src/main_window/main_widget/sequence_card_tab/components/navigation/mode_toggle.py
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QLabel, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QCursor
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from main_window.main_widget.sequence_card_tab.core.mode_manager import SequenceCardMode

from main_window.main_widget.sequence_card_tab.core.mode_manager import SequenceCardMode


class ModeToggleWidget(QWidget):
    """
    Modern toggle widget for switching between Dictionary and Generation modes.
    
    Features a clean, professional design with smooth animations and clear
    visual feedback for the current mode.
    """
    
    mode_change_requested = pyqtSignal(object)  # Emits SequenceCardMode
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_mode = SequenceCardMode.DICTIONARY
        self.buttons = {}
        self.setup_ui()
        self.apply_styling()
        
    def setup_ui(self):
        """Setup the UI components."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(0)
        
        # Create container frame
        self.container_frame = QFrame()
        self.container_frame.setObjectName("modeToggleContainer")
        container_layout = QHBoxLayout(self.container_frame)
        container_layout.setContentsMargins(2, 2, 2, 2)
        container_layout.setSpacing(0)
        
        # Dictionary mode button
        self.dict_button = self.create_mode_button(
            "Dictionary", 
            SequenceCardMode.DICTIONARY,
            "Browse saved sequences"
        )
        container_layout.addWidget(self.dict_button)
        
        # Generation mode button
        self.gen_button = self.create_mode_button(
            "Generation", 
            SequenceCardMode.GENERATION,
            "Create new sequences"
        )
        container_layout.addWidget(self.gen_button)
        
        layout.addWidget(self.container_frame)
        
        # Set initial state
        self.update_button_states()
        
    def create_mode_button(self, text: str, mode: SequenceCardMode, tooltip: str) -> QPushButton:
        """Create a mode toggle button."""
        button = QPushButton(text)
        button.setCheckable(True)
        button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        button.setToolTip(tooltip)
        button.setObjectName(f"modeButton{mode.value.title()}")
        
        # Store mode reference
        self.buttons[mode] = button
        
        # Connect click handler
        button.clicked.connect(lambda checked, m=mode: self.on_mode_button_clicked(m))
        
        # Font styling
        button_font = QFont()
        button_font.setPointSize(10)
        button_font.setWeight(QFont.Weight.Medium)
        button.setFont(button_font)
        
        return button
        
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
            button.blockSignals(True)  # Prevent recursive signals
            button.setChecked(mode == self.current_mode)
            button.blockSignals(False)
            
    def set_mode_enabled(self, mode: SequenceCardMode, enabled: bool):
        """Enable or disable a specific mode button."""
        if mode in self.buttons:
            button = self.buttons[mode]
            button.setEnabled(enabled)
            
            # Update tooltip for disabled state
            if not enabled:
                if mode == SequenceCardMode.GENERATION:
                    button.setToolTip("Generation mode requires the Generate tab to be available")
                else:
                    button.setToolTip("This mode is currently unavailable")
            else:
                # Restore original tooltip
                if mode == SequenceCardMode.DICTIONARY:
                    button.setToolTip("Browse saved sequences")
                elif mode == SequenceCardMode.GENERATION:
                    button.setToolTip("Create new sequences")
                    
    def get_current_mode(self) -> SequenceCardMode:
        """Get the currently selected mode."""
        return self.current_mode
        
    def apply_styling(self):
        """Apply modern styling to the toggle widget."""
        self.setStyleSheet("""
            QWidget#modeToggleWidget {
                background: transparent;
            }
            
            QFrame#modeToggleContainer {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: 2px;
            }
            
            QPushButton[objectName^="modeButton"] {
                background: transparent;
                border: none;
                color: #e1e5e9;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: 500;
                min-width: 80px;
            }
            
            QPushButton[objectName^="modeButton"]:hover {
                background: rgba(255, 255, 255, 0.1);
            }
            
            QPushButton[objectName^="modeButton"]:checked {
                background: #3182ce;
                color: white;
                font-weight: 600;
            }
            
            QPushButton[objectName^="modeButton"]:checked:hover {
                background: #2c5aa0;
            }
            
            QPushButton[objectName^="modeButton"]:disabled {
                color: #718096;
                background: transparent;
            }
            
            QPushButton[objectName^="modeButton"]:disabled:hover {
                background: transparent;
            }
        """)
        
        self.setObjectName("modeToggleWidget")
        
    def get_mode_summary(self) -> str:
        """Get a summary of the current mode for display."""
        if self.current_mode == SequenceCardMode.DICTIONARY:
            return "Dictionary Mode - Browsing saved sequences"
        elif self.current_mode == SequenceCardMode.GENERATION:
            return "Generation Mode - Creating new sequences"
        else:
            return "Unknown Mode"
