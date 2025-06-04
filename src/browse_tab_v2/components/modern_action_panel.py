"""
Modern Action Panel Component

Action buttons panel with modern glassmorphism styling for sequence operations.
Provides Edit, Save, Delete, and Full Screen functionality.

Features:
- Modern glassmorphic button styling
- Hover animations and feedback
- Icon support with text labels
- Tooltips for accessibility
- Disabled state handling
- Responsive layout
"""

import logging
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QFrame,
    QSizePolicy,
    QToolTip,
)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QTimer
from PyQt6.QtGui import QFont, QIcon, QCursor

logger = logging.getLogger(__name__)


class ModernActionButton(QPushButton):
    """Modern styled action button with glassmorphism effects."""

    def __init__(
        self,
        text: str,
        icon_text: str = "",
        button_type: str = "primary",
        parent: QWidget = None,
    ):
        super().__init__(text, parent)

        self.button_type = button_type
        self.icon_text = icon_text
        self.hover_animation: Optional[QPropertyAnimation] = None

        self._setup_styling()
        self._setup_animations()

    def _setup_styling(self):
        """Apply modern button styling based on type."""
        base_style = """
            ModernActionButton {
                border-radius: 15px;
                font-size: 10px;
                font-weight: bold;
                padding: 8px 12px;
                min-width: 60px;
                min-height: 32px;
                max-width: 80px;
            }
            
            ModernActionButton:disabled {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                color: rgba(255, 255, 255, 0.3);
            }
        """

        if self.button_type == "primary":
            style = (
                base_style
                + """
                ModernActionButton {
                    background: rgba(76, 175, 80, 0.2);
                    border: 1px solid rgba(76, 175, 80, 0.4);
                    color: rgba(255, 255, 255, 0.9);
                }
                
                ModernActionButton:hover {
                    background: rgba(76, 175, 80, 0.3);
                    border: 1px solid rgba(76, 175, 80, 0.6);
                    color: rgba(255, 255, 255, 1.0);
                }
                
                ModernActionButton:pressed {
                    background: rgba(76, 175, 80, 0.4);
                    border: 1px solid rgba(76, 175, 80, 0.7);
                }
            """
            )
        elif self.button_type == "secondary":
            style = (
                base_style
                + """
                ModernActionButton {
                    background: rgba(33, 150, 243, 0.2);
                    border: 1px solid rgba(33, 150, 243, 0.4);
                    color: rgba(255, 255, 255, 0.9);
                }
                
                ModernActionButton:hover {
                    background: rgba(33, 150, 243, 0.3);
                    border: 1px solid rgba(33, 150, 243, 0.6);
                    color: rgba(255, 255, 255, 1.0);
                }
                
                ModernActionButton:pressed {
                    background: rgba(33, 150, 243, 0.4);
                    border: 1px solid rgba(33, 150, 243, 0.7);
                }
            """
            )
        elif self.button_type == "danger":
            style = (
                base_style
                + """
                ModernActionButton {
                    background: rgba(244, 67, 54, 0.2);
                    border: 1px solid rgba(244, 67, 54, 0.4);
                    color: rgba(255, 255, 255, 0.9);
                }
                
                ModernActionButton:hover {
                    background: rgba(244, 67, 54, 0.3);
                    border: 1px solid rgba(244, 67, 54, 0.6);
                    color: rgba(255, 255, 255, 1.0);
                }
                
                ModernActionButton:pressed {
                    background: rgba(244, 67, 54, 0.4);
                    border: 1px solid rgba(244, 67, 54, 0.7);
                }
            """
            )
        else:  # neutral
            style = (
                base_style
                + """
                ModernActionButton {
                    background: rgba(255, 255, 255, 0.1);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    color: rgba(255, 255, 255, 0.9);
                }
                
                ModernActionButton:hover {
                    background: rgba(255, 255, 255, 0.2);
                    border: 1px solid rgba(255, 255, 255, 0.4);
                    color: rgba(255, 255, 255, 1.0);
                }
                
                ModernActionButton:pressed {
                    background: rgba(255, 255, 255, 0.3);
                    border: 1px solid rgba(255, 255, 255, 0.5);
                }
            """
            )

        self.setStyleSheet(style)

    def _setup_animations(self):
        """Setup hover animations."""
        # Animations will be handled by the animation system
        pass

    def enterEvent(self, event):
        """Handle mouse enter for hover effects."""
        super().enterEvent(event)
        if self.isEnabled():
            self.setCursor(Qt.CursorShape.PointingHandCursor)

    def leaveEvent(self, event):
        """Handle mouse leave."""
        super().leaveEvent(event)
        self.setCursor(Qt.CursorShape.ArrowCursor)


class ModernActionPanel(QWidget):
    """
    Modern action panel with glassmorphism styling.

    Provides action buttons for sequence operations:
    - Edit: Open sequence in workbench
    - Save: Export sequence image
    - Delete: Remove variation
    - Full Screen: View in full screen mode
    """

    # Signals
    edit_requested = pyqtSignal(str)  # sequence_id
    save_requested = pyqtSignal(str)  # sequence_id
    delete_requested = pyqtSignal()  # Will be handled by parent
    fullscreen_requested = pyqtSignal()  # Will be handled by parent

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)

        # State
        self.current_sequence_id: Optional[str] = None
        self.is_enabled = False

        # Components
        self.edit_button: ModernActionButton = None
        self.save_button: ModernActionButton = None
        self.delete_button: ModernActionButton = None
        self.fullscreen_button: ModernActionButton = None

        self._setup_ui()
        self._setup_styling()

        # Initially disabled
        self.set_enabled(False)

        logger.debug("ModernActionPanel initialized")

    def _setup_ui(self):
        """Setup the action panel UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)  # Reduced margins
        layout.setSpacing(6)  # Reduced spacing

        # Title label
        title_label = QLabel("Actions")
        title_label.setObjectName("actionPanelTitle")
        font = QFont("Segoe UI", 11, QFont.Weight.Bold)  # Slightly smaller font
        title_label.setFont(font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Container frame
        self.container_frame = QFrame()
        self.container_frame.setObjectName("actionContainer")
        container_layout = QHBoxLayout(self.container_frame)
        container_layout.setContentsMargins(8, 6, 8, 6)  # Reduced padding
        container_layout.setSpacing(6)  # Reduced spacing between buttons

        # Edit button (primary action)
        self.edit_button = ModernActionButton("✏️ Edit", "✏️", "primary")
        self.edit_button.setToolTip("Edit sequence in workbench")
        self.edit_button.clicked.connect(self._on_edit_clicked)
        container_layout.addWidget(self.edit_button)

        # Save button (secondary action)
        self.save_button = ModernActionButton("💾 Save", "💾", "secondary")
        self.save_button.setToolTip("Export sequence image")
        self.save_button.clicked.connect(self._on_save_clicked)
        container_layout.addWidget(self.save_button)

        # Full screen button (neutral action)
        self.fullscreen_button = ModernActionButton("🔍 View", "🔍", "neutral")
        self.fullscreen_button.setToolTip("View in full screen")
        self.fullscreen_button.clicked.connect(self._on_fullscreen_clicked)
        container_layout.addWidget(self.fullscreen_button)

        # Delete button (danger action)
        self.delete_button = ModernActionButton("🗑️ Delete", "🗑️", "danger")
        self.delete_button.setToolTip("Delete this variation")
        self.delete_button.clicked.connect(self._on_delete_clicked)
        container_layout.addWidget(self.delete_button)

        layout.addWidget(self.container_frame)

        # Set size policy - allow it to be more flexible
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.setMinimumHeight(70)  # Minimum height instead of fixed
        self.setMaximumHeight(90)  # Maximum height to prevent excessive growth

    def _setup_styling(self):
        """Apply modern glassmorphic styling."""
        self.setStyleSheet(
            """
            QLabel#actionPanelTitle {
                color: rgba(255, 255, 255, 0.9);
                background: transparent;
                border: none;
                margin-bottom: 5px;
            }
            
            QFrame#actionContainer {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 20px;
            }
        """
        )

    def set_enabled(self, enabled: bool):
        """Enable or disable action panel."""
        self.is_enabled = enabled

        # Enable/disable all buttons
        self.edit_button.setEnabled(enabled)
        self.save_button.setEnabled(enabled)
        self.delete_button.setEnabled(enabled)
        self.fullscreen_button.setEnabled(enabled)

        # Update container styling
        self.container_frame.setProperty("enabled", enabled)
        self.container_frame.style().polish(self.container_frame)

        logger.debug(f"Action panel {'enabled' if enabled else 'disabled'}")

    def set_sequence_id(self, sequence_id: str):
        """Set current sequence ID for actions."""
        self.current_sequence_id = sequence_id

    def _on_edit_clicked(self):
        """Handle edit button click."""
        if self.is_enabled and self.current_sequence_id:
            self.edit_requested.emit(self.current_sequence_id)
            logger.info(f"Edit requested for sequence: {self.current_sequence_id}")

    def _on_save_clicked(self):
        """Handle save button click."""
        if self.is_enabled and self.current_sequence_id:
            self.save_requested.emit(self.current_sequence_id)
            logger.info(f"Save requested for sequence: {self.current_sequence_id}")

    def _on_delete_clicked(self):
        """Handle delete button click."""
        if self.is_enabled:
            # Show confirmation dialog would be handled by parent
            self.delete_requested.emit()
            logger.info("Delete requested")

    def _on_fullscreen_clicked(self):
        """Handle fullscreen button click."""
        if self.is_enabled:
            self.fullscreen_requested.emit()
            logger.info("Fullscreen requested")

    def get_enabled_actions(self) -> list:
        """Get list of currently enabled actions."""
        actions = []
        if self.edit_button.isEnabled():
            actions.append("edit")
        if self.save_button.isEnabled():
            actions.append("save")
        if self.delete_button.isEnabled():
            actions.append("delete")
        if self.fullscreen_button.isEnabled():
            actions.append("fullscreen")
        return actions

    def set_button_enabled(self, action: str, enabled: bool):
        """Enable/disable specific action button."""
        if action == "edit":
            self.edit_button.setEnabled(enabled)
        elif action == "save":
            self.save_button.setEnabled(enabled)
        elif action == "delete":
            self.delete_button.setEnabled(enabled)
        elif action == "fullscreen":
            self.fullscreen_button.setEnabled(enabled)

    def reset(self):
        """Reset action panel to initial state."""
        self.current_sequence_id = None
        self.set_enabled(False)
