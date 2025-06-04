"""
Empty State Widget - Modern No Content Display

This component provides elegant empty states for various scenarios in the browse tab:
- No sequences found (filter results)
- Empty dataset (no sequences loaded)
- Search results (no matches)
- Network/loading errors

Features:
- Modern glassmorphic design
- Contextual messages and suggestions
- Action buttons for common solutions
- Responsive layout
- Accessibility support
"""

import logging
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap, QPainter, QColor

logger = logging.getLogger(__name__)


class EmptyStateWidget(QWidget):
    """
    Modern empty state widget with glassmorphic design.
    
    Provides contextual empty states for different scenarios:
    - No filter matches
    - Empty dataset
    - Search results
    - Error states
    """

    # Signals for user actions
    clear_filters_requested = pyqtSignal()
    refresh_requested = pyqtSignal()
    browse_all_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        """Setup the empty state UI."""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Icon area
        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setFixedSize(120, 120)
        self._setup_icon_style()
        layout.addWidget(self.icon_label)

        # Title
        self.title_label = QLabel()
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setWordWrap(True)
        self._setup_title_style()
        layout.addWidget(self.title_label)

        # Message
        self.message_label = QLabel()
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message_label.setWordWrap(True)
        self._setup_message_style()
        layout.addWidget(self.message_label)

        # Action buttons container
        self.actions_layout = QHBoxLayout()
        self.actions_layout.setSpacing(15)
        self.actions_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addLayout(self.actions_layout)

        # Spacer to center content
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # Widget styling
        self.setStyleSheet(
            """
            EmptyStateWidget {
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 16px;
                backdrop-filter: blur(12px);
            }
        """
        )

    def _setup_icon_style(self):
        """Setup icon area styling."""
        self.icon_label.setStyleSheet(
            """
            QLabel {
                background: qradial-gradient(circle,
                    rgba(255, 255, 255, 0.15) 0%,
                    rgba(255, 255, 255, 0.05) 70%,
                    rgba(255, 255, 255, 0.02) 100%);
                border: 2px solid rgba(255, 255, 255, 0.2);
                border-radius: 60px;
                color: rgba(255, 255, 255, 0.7);
                font-size: 48px;
                font-weight: bold;
                backdrop-filter: blur(8px);
            }
        """
        )

    def _setup_title_style(self):
        """Setup title styling."""
        font = QFont()
        font.setPointSize(18)
        font.setBold(True)
        self.title_label.setFont(font)
        
        self.title_label.setStyleSheet(
            """
            QLabel {
                color: rgba(255, 255, 255, 0.9);
                background: transparent;
                padding: 10px;
            }
        """
        )

    def _setup_message_style(self):
        """Setup message styling."""
        font = QFont()
        font.setPointSize(12)
        self.message_label.setFont(font)
        
        self.message_label.setStyleSheet(
            """
            QLabel {
                color: rgba(255, 255, 255, 0.7);
                background: transparent;
                padding: 5px 20px;
                line-height: 1.4;
            }
        """
        )

    def _create_action_button(self, text: str, primary: bool = False) -> QPushButton:
        """Create a styled action button."""
        button = QPushButton(text)
        
        if primary:
            button.setStyleSheet(
                """
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(76, 175, 80, 0.8),
                        stop:1 rgba(56, 142, 60, 0.8));
                    border: 2px solid rgba(76, 175, 80, 0.6);
                    border-radius: 8px;
                    color: white;
                    font-weight: bold;
                    padding: 12px 24px;
                    backdrop-filter: blur(10px);
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(76, 175, 80, 0.9),
                        stop:1 rgba(56, 142, 60, 0.9));
                    border: 2px solid rgba(76, 175, 80, 0.8);
                }
                QPushButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(56, 142, 60, 0.9),
                        stop:1 rgba(46, 125, 50, 0.9));
                }
            """
            )
        else:
            button.setStyleSheet(
                """
                QPushButton {
                    background: rgba(255, 255, 255, 0.1);
                    border: 2px solid rgba(255, 255, 255, 0.2);
                    border-radius: 8px;
                    color: rgba(255, 255, 255, 0.8);
                    font-weight: bold;
                    padding: 12px 24px;
                    backdrop-filter: blur(10px);
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.15);
                    border: 2px solid rgba(255, 255, 255, 0.3);
                    color: rgba(255, 255, 255, 0.9);
                }
                QPushButton:pressed {
                    background: rgba(255, 255, 255, 0.08);
                    border: 2px solid rgba(255, 255, 255, 0.15);
                }
            """
            )
        
        return button

    def show_no_filter_matches(self, filter_count: int = 0):
        """Show empty state for no filter matches."""
        self.icon_label.setText("🔍")
        self.title_label.setText("No Sequences Found")
        
        if filter_count > 0:
            self.message_label.setText(
                f"No sequences match your current filters.\n"
                f"Try adjusting your {filter_count} active filter{'s' if filter_count != 1 else ''} "
                f"or browse all sequences."
            )
        else:
            self.message_label.setText(
                "No sequences match your search criteria.\n"
                "Try different search terms or browse all sequences."
            )

        # Clear existing buttons
        self._clear_actions()

        # Add action buttons
        clear_btn = self._create_action_button("Clear Filters", primary=True)
        clear_btn.clicked.connect(self.clear_filters_requested.emit)
        self.actions_layout.addWidget(clear_btn)

        browse_btn = self._create_action_button("Browse All")
        browse_btn.clicked.connect(self.browse_all_requested.emit)
        self.actions_layout.addWidget(browse_btn)

    def show_empty_dataset(self):
        """Show empty state for completely empty dataset."""
        self.icon_label.setText("📚")
        self.title_label.setText("No Sequences Available")
        self.message_label.setText(
            "There are no sequences in your collection yet.\n"
            "Sequences will appear here once they are loaded or created."
        )

        # Clear existing buttons
        self._clear_actions()

        # Add refresh button
        refresh_btn = self._create_action_button("Refresh", primary=True)
        refresh_btn.clicked.connect(self.refresh_requested.emit)
        self.actions_layout.addWidget(refresh_btn)

    def show_search_no_results(self, search_term: str):
        """Show empty state for search with no results."""
        self.icon_label.setText("🔎")
        self.title_label.setText("No Search Results")
        self.message_label.setText(
            f"No sequences found for '{search_term}'.\n"
            f"Try different keywords or check your spelling."
        )

        # Clear existing buttons
        self._clear_actions()

        # Add action buttons
        clear_btn = self._create_action_button("Clear Search", primary=True)
        clear_btn.clicked.connect(self.clear_filters_requested.emit)
        self.actions_layout.addWidget(clear_btn)

        browse_btn = self._create_action_button("Browse All")
        browse_btn.clicked.connect(self.browse_all_requested.emit)
        self.actions_layout.addWidget(browse_btn)

    def show_loading_error(self, error_message: str = ""):
        """Show empty state for loading errors."""
        self.icon_label.setText("⚠️")
        self.title_label.setText("Loading Error")
        
        if error_message:
            self.message_label.setText(
                f"Failed to load sequences:\n{error_message}\n\n"
                f"Please try refreshing or check your connection."
            )
        else:
            self.message_label.setText(
                "Failed to load sequences.\n"
                "Please try refreshing or check your connection."
            )

        # Clear existing buttons
        self._clear_actions()

        # Add refresh button
        refresh_btn = self._create_action_button("Try Again", primary=True)
        refresh_btn.clicked.connect(self.refresh_requested.emit)
        self.actions_layout.addWidget(refresh_btn)

    def _clear_actions(self):
        """Clear all action buttons."""
        while self.actions_layout.count():
            child = self.actions_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def sizeHint(self) -> QSize:
        """Provide reasonable size hint."""
        return QSize(600, 400)

    def minimumSizeHint(self) -> QSize:
        """Provide minimum size hint."""
        return QSize(400, 300)
