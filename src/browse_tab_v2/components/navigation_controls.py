"""
Navigation Controls Component

Modern navigation controls for sequence variations with glassmorphism styling
and smooth hover animations.

Features:
- Previous/Next buttons with modern styling
- Variation counter display
- Keyboard navigation support
- Hover animations and feedback
- Disabled state handling
"""

import logging
from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QFrame,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QIcon, QKeySequence
from PyQt6.QtGui import QShortcut

logger = logging.getLogger(__name__)


class ModernNavigationButton(QPushButton):
    """Modern styled navigation button with hover animations."""

    def __init__(self, text: str, icon_text: str = "", parent: QWidget = None):
        super().__init__(text, parent)

        self.icon_text = icon_text
        self.hover_animation: QPropertyAnimation = None

        self._setup_styling()
        self._setup_animations()

    def _setup_styling(self):
        """Apply modern button styling."""
        self.setFixedSize(80, 40)
        self.setStyleSheet(
            """
            ModernNavigationButton {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 20px;
                color: rgba(255, 255, 255, 0.9);
                font-size: 12px;
                font-weight: bold;
                padding: 8px 16px;
            }
            
            ModernNavigationButton:hover {
                background: rgba(255, 255, 255, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.4);
                color: rgba(255, 255, 255, 1.0);
            }
            
            ModernNavigationButton:pressed {
                background: rgba(255, 255, 255, 0.3);
                border: 1px solid rgba(255, 255, 255, 0.5);
            }
            
            ModernNavigationButton:disabled {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                color: rgba(255, 255, 255, 0.3);
            }
        """
        )

    def _setup_animations(self):
        """Setup hover animations."""
        # Hover animations will be handled by the parent animation system
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


class NavigationControls(QWidget):
    """
    Navigation controls for sequence variations.

    Features:
    - Previous/Next buttons
    - Variation counter
    - Keyboard shortcuts
    - Modern glassmorphism styling
    - Smooth animations
    """

    # Signals
    previous_requested = pyqtSignal()
    next_requested = pyqtSignal()
    variation_selected = pyqtSignal(int)  # variation_index

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)

        # State
        self.current_variation = 0
        self.total_variations = 0
        self.is_enabled = False

        # Components
        self.previous_button: ModernNavigationButton = None
        self.next_button: ModernNavigationButton = None
        self.variation_label: QLabel = None

        self._setup_ui()
        self._setup_styling()
        self._setup_keyboard_shortcuts()

        # Initially disabled
        self.set_enabled(False)

        logger.debug("NavigationControls initialized")

    def _setup_ui(self):
        """Setup the navigation controls UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(15)

        # Container frame
        self.container_frame = QFrame()
        self.container_frame.setObjectName("navigationContainer")
        container_layout = QHBoxLayout(self.container_frame)
        container_layout.setContentsMargins(15, 10, 15, 10)
        container_layout.setSpacing(15)

        # Previous button
        self.previous_button = ModernNavigationButton("← Prev", "←")
        self.previous_button.clicked.connect(self._on_previous_clicked)
        container_layout.addWidget(self.previous_button)

        # Variation counter (center)
        self.variation_label = QLabel("No variations")
        self.variation_label.setObjectName("variationLabel")
        font = QFont("Segoe UI", 11, QFont.Weight.Bold)
        self.variation_label.setFont(font)
        self.variation_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.variation_label.setMinimumWidth(120)
        container_layout.addWidget(self.variation_label)

        # Next button
        self.next_button = ModernNavigationButton("Next →", "→")
        self.next_button.clicked.connect(self._on_next_clicked)
        container_layout.addWidget(self.next_button)

        layout.addStretch()
        layout.addWidget(self.container_frame)
        layout.addStretch()

        # Set size policy
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(70)

    def _setup_styling(self):
        """Apply modern glassmorphic styling."""
        self.setStyleSheet(
            """
            QFrame#navigationContainer {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 25px;
            }
            
            QLabel#variationLabel {
                color: rgba(255, 255, 255, 0.9);
                background: transparent;
                border: none;
                padding: 5px 10px;
            }
        """
        )

    def _setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts for navigation."""
        # Left arrow key for previous
        self.previous_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Left), self)
        self.previous_shortcut.activated.connect(self._on_previous_clicked)

        # Right arrow key for next
        self.next_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Right), self)
        self.next_shortcut.activated.connect(self._on_next_clicked)

    def set_variation_info(self, current_index: int, total_count: int):
        """Update variation information."""
        self.current_variation = current_index
        self.total_variations = total_count

        if total_count > 0:
            self.variation_label.setText(
                f"Variation {current_index + 1} of {total_count}"
            )
            self.set_enabled(True)

            # Update button states
            self.previous_button.setEnabled(current_index > 0)
            self.next_button.setEnabled(current_index < total_count - 1)
        else:
            self.variation_label.setText("No variations")
            self.set_enabled(False)

        logger.debug(f"Variation info updated: {current_index + 1}/{total_count}")

    def set_enabled(self, enabled: bool):
        """Enable or disable navigation controls."""
        self.is_enabled = enabled

        if not enabled:
            self.previous_button.setEnabled(False)
            self.next_button.setEnabled(False)
            self.variation_label.setText("No variations")

        # Update shortcuts
        self.previous_shortcut.setEnabled(enabled)
        self.next_shortcut.setEnabled(enabled)

        # Update styling
        self.container_frame.setProperty("enabled", enabled)
        self.container_frame.style().polish(self.container_frame)

    def _on_previous_clicked(self):
        """Handle previous button click."""
        if self.is_enabled and self.current_variation > 0:
            self.previous_requested.emit()
            logger.debug("Previous variation requested")

    def _on_next_clicked(self):
        """Handle next button click."""
        if self.is_enabled and self.current_variation < self.total_variations - 1:
            self.next_requested.emit()
            logger.debug("Next variation requested")

    def get_current_variation(self) -> int:
        """Get current variation index."""
        return self.current_variation

    def get_total_variations(self) -> int:
        """Get total number of variations."""
        return self.total_variations

    def has_previous(self) -> bool:
        """Check if previous variation is available."""
        return self.current_variation > 0

    def has_next(self) -> bool:
        """Check if next variation is available."""
        return self.current_variation < self.total_variations - 1

    def reset(self):
        """Reset navigation controls to initial state."""
        self.current_variation = 0
        self.total_variations = 0
        self.set_enabled(False)
