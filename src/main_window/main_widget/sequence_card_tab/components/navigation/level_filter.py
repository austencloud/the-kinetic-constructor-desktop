# src/main_window/main_widget/sequence_card_tab/components/navigation/level_filter.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QLabel, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QCursor
from typing import List


class LevelFilterWidget(QWidget):
    """
    Level filter component for sequence card tab.
    
    Provides multi-select checkboxes for filtering sequences by difficulty level.
    Integrates cleanly with existing sidebar design patterns.
    """
    
    level_filter_changed = pyqtSignal(list)  # Emits list of selected levels
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_levels = [1, 2, 3]  # Default: all levels selected
        self.level_checkboxes = {}
        self.setup_ui()
        self.apply_styling()
        
    def setup_ui(self):
        """Setup the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 10, 8, 10)
        layout.setSpacing(8)
        
        # Header label
        self.create_header_label()
        layout.addWidget(self.header_label)
        
        # Checkboxes container
        self.create_checkboxes()
        layout.addWidget(self.checkboxes_frame)
        
    def create_header_label(self):
        """Create the header label for the filter section."""
        self.header_label = QLabel("Difficulty Levels")
        self.header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.header_label.setWordWrap(True)
        self.header_label.setToolTip(
            "Filter sequences by difficulty level:\n"
            "Level 1: Basic sequences (no turns)\n"
            "Level 2: Intermediate (with turns)\n"
            "Level 3: Advanced (non-radial orientations)"
        )
        
        # Font styling to match existing sidebar components
        label_font = QFont()
        label_font.setPointSize(11)
        label_font.setWeight(QFont.Weight.Medium)
        self.header_label.setFont(label_font)
        self.header_label.setObjectName("levelFilterLabel")
        
    def create_checkboxes(self):
        """Create the checkbox container and individual checkboxes."""
        self.checkboxes_frame = QFrame()
        self.checkboxes_frame.setObjectName("levelCheckboxesFrame")
        
        checkboxes_layout = QVBoxLayout(self.checkboxes_frame)
        checkboxes_layout.setContentsMargins(4, 4, 4, 4)
        checkboxes_layout.setSpacing(6)
        
        # Create checkboxes for each level
        level_info = [
            (1, "Level 1 - Basic"),
            (2, "Level 2 - Intermediate"), 
            (3, "Level 3 - Advanced")
        ]
        
        for level, display_text in level_info:
            checkbox = self.create_level_checkbox(level, display_text)
            self.level_checkboxes[level] = checkbox
            checkboxes_layout.addWidget(checkbox)
            
    def create_level_checkbox(self, level: int, display_text: str) -> QCheckBox:
        """Create an individual level checkbox."""
        checkbox = QCheckBox(display_text)
        checkbox.setChecked(True)  # Default: all levels selected
        checkbox.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        checkbox.setObjectName(f"levelCheckbox{level}")
        
        # Connect to change handler
        checkbox.stateChanged.connect(lambda state, lvl=level: self.on_level_toggled(lvl, state))
        
        # Styling
        checkbox_font = QFont()
        checkbox_font.setPointSize(10)
        checkbox.setFont(checkbox_font)
        
        return checkbox
        
    def on_level_toggled(self, level: int, state: int):
        """Handle level checkbox toggle."""
        is_checked = state == Qt.CheckState.Checked.value
        
        if is_checked and level not in self.selected_levels:
            self.selected_levels.append(level)
        elif not is_checked and level in self.selected_levels:
            self.selected_levels.remove(level)
            
        # Sort the selected levels for consistency
        self.selected_levels.sort()
        
        # Emit the change signal
        self.level_filter_changed.emit(self.selected_levels.copy())
        
    def get_selected_levels(self) -> List[int]:
        """Get the currently selected levels."""
        return self.selected_levels.copy()
        
    def set_selected_levels(self, levels: List[int]):
        """Set the selected levels programmatically."""
        # Validate input
        valid_levels = [lvl for lvl in levels if lvl in [1, 2, 3]]
        
        # Update internal state
        self.selected_levels = sorted(valid_levels)
        
        # Update checkbox states
        for level, checkbox in self.level_checkboxes.items():
            checkbox.blockSignals(True)  # Prevent recursive signals
            checkbox.setChecked(level in self.selected_levels)
            checkbox.blockSignals(False)
            
        # Emit change signal
        self.level_filter_changed.emit(self.selected_levels.copy())
        
    def reset_to_all_levels(self):
        """Reset filter to show all levels."""
        self.set_selected_levels([1, 2, 3])
        
    def apply_styling(self):
        """Apply consistent styling to match existing sidebar components."""
        self.setStyleSheet("""
            QWidget#levelFilterWidget {
                background: transparent;
            }
            
            QLabel#levelFilterLabel {
                color: #e1e5e9;
                font-weight: 500;
                padding: 2px;
            }
            
            QFrame#levelCheckboxesFrame {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 6px;
                padding: 4px;
            }
            
            QCheckBox {
                color: #e1e5e9;
                spacing: 8px;
                padding: 4px 8px;
                border-radius: 4px;
            }
            
            QCheckBox:hover {
                background: rgba(255, 255, 255, 0.1);
            }
            
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 3px;
                border: 2px solid #4a5568;
                background: transparent;
            }
            
            QCheckBox::indicator:checked {
                background: #3182ce;
                border-color: #3182ce;
            }
            
            QCheckBox::indicator:checked:hover {
                background: #2c5aa0;
                border-color: #2c5aa0;
            }
            
            QCheckBox::indicator:unchecked:hover {
                border-color: #718096;
            }
        """)
        
        self.setObjectName("levelFilterWidget")
        
    def is_level_selected(self, level: int) -> bool:
        """Check if a specific level is currently selected."""
        return level in self.selected_levels
        
    def get_filter_summary(self) -> str:
        """Get a human-readable summary of the current filter."""
        if len(self.selected_levels) == 3:
            return "All Levels"
        elif len(self.selected_levels) == 0:
            return "No Levels"
        else:
            level_names = {1: "Basic", 2: "Intermediate", 3: "Advanced"}
            selected_names = [level_names[lvl] for lvl in self.selected_levels]
            return f"Levels: {', '.join(selected_names)}"
