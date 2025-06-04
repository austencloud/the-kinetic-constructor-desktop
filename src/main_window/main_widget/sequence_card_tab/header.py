# src/main_window/main_widget/sequence_card_tab/header.py
from PyQt6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFrame,
    QProgressBar,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from .components.navigation.mode_toggle import ModeToggleWidget
from .core.mode_manager import SequenceCardMode


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from main_window.main_widget.sequence_card_tab.tab import SequenceCardTab


class SequenceCardHeader(QFrame):
    # Signal for mode change requests
    mode_change_requested = pyqtSignal(object)  # Emits SequenceCardMode

    def __init__(self, parent: "SequenceCardTab"):
        super().__init__(parent)
        self.sequence_car_tab = parent
        self.mode_toggle = None
        self._setup_ui()

    def _setup_ui(self):
        self.setObjectName("sequenceCardHeader")
        self.setStyleSheet(
            """
            #sequenceCardHeader {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #34495e, stop:1 #2c3e50);
                border-radius: 10px;
                border: 1px solid #4a5568;
            }
        """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 12, 20, 12)
        layout.setSpacing(6)

        # Create top row with title and mode toggle
        top_row = self._create_top_row()
        layout.addLayout(top_row)

        # Create description label
        self.description_label = self._create_description()
        layout.addWidget(self.description_label)

        # Create progress container
        self.progress_container = self._create_progress()
        layout.addWidget(self.progress_container)

        # Create action buttons
        self.button_layout = self._create_buttons()
        layout.addLayout(self.button_layout)

    def _create_top_row(self):
        """Create the top row with title and mode toggle."""
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(20)

        # Create title
        self.title_label = self._create_title()

        # Create mode toggle
        self.mode_toggle = ModeToggleWidget(self)
        self.mode_toggle.mode_change_requested.connect(self.mode_change_requested.emit)

        # UPDATED: Reduce toggle size while maintaining visual importance through modern styling
        top_layout.addWidget(self.title_label, 3)  # Title gets more space
        top_layout.addStretch(1)  # Spacer
        top_layout.addWidget(
            self.mode_toggle, 1
        )  # Mode toggle gets less space but maintains importance through styling

        return top_layout

    def _create_title(self):
        title_label = QLabel("Sequence Cards")
        title_label.setObjectName("sequenceCardTitle")
        title_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )

        # Dynamic font sizing
        self._update_title_font(title_label)
        title_label.setStyleSheet("color: #ffffff; letter-spacing: 0.5px;")
        return title_label

    def _update_title_font(self, title_label):
        """Update title font size based on widget dimensions."""
        try:
            # Calculate font size based on widget width
            widget_width = (
                self.sequence_car_tab.width()
                if self.sequence_car_tab.width() > 100
                else 800
            )
            font_size = max(
                12, min(18, widget_width // 50)
            )  # Scale with width, bounded

            title_font = QFont()
            title_font.setPointSize(font_size)
            title_font.setWeight(QFont.Weight.Bold)
            title_label.setFont(title_font)
        except:
            # Fallback
            title_font = QFont()
            title_font.setPointSize(14)
            title_font.setWeight(QFont.Weight.Bold)
            title_label.setFont(title_font)

    def _create_description(self):
        description_label = QLabel("Select a sequence length to view cards")
        description_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Make description smaller and less prominent
        self._update_description_font(description_label)
        return description_label

    def _update_description_font(self, description_label):
        """Update description font size dynamically."""
        try:
            widget_width = (
                self.sequence_car_tab.width()
                if self.sequence_car_tab.width() > 100
                else 800
            )
            font_size = max(10, min(13, widget_width // 65))  # Smaller than title

            description_label.setStyleSheet(
                f"""
                color: #bdc3c7;
                font-size: {font_size}px;
                font-style: italic;
            """
            )
        except:
            description_label.setStyleSheet(
                """
                color: #bdc3c7;
                font-size: 12px;
                font-style: italic;
            """
            )

    def resizeEvent(self, event):
        """Handle resize events for responsive typography."""
        super().resizeEvent(event)

        if hasattr(self, "title_label"):
            self._update_title_font(self.title_label)

        if hasattr(self, "description_label"):
            self._update_description_font(self.description_label)

        # Update button sizes
        if hasattr(self, "button_layout"):
            self._update_button_sizes()

    def _update_button_sizes(self):
        """Update action button sizes responsively."""
        try:
            widget_width = (
                self.sequence_car_tab.width()
                if self.sequence_car_tab.width() > 100
                else 800
            )

            # Calculate responsive button dimensions
            button_height = max(28, min(40, widget_width // 40))
            font_size = max(10, min(14, widget_width // 70))
            padding_h = max(12, min(20, widget_width // 60))
            padding_v = max(6, min(12, widget_width // 80))

            button_style = f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3498db, stop:1 #2980b9);
                color: white;
                border: 1px solid #5dade2;
                border-radius: 6px;
                padding: {padding_v}px {padding_h}px;
                font-weight: 600;
                font-size: {font_size}px;
                min-width: {widget_width // 12}px;
                min-height: {button_height}px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5dade2, stop:1 #3498db);
                border: 1px solid #85c1e9;
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2980b9, stop:1 #1f618d);
                border: 1px solid #3498db;
            }}
            """

            # Apply to all action buttons
            for i in range(self.button_layout.count()):
                item = self.button_layout.itemAt(i)
                if item and item.widget() and isinstance(item.widget(), QPushButton):
                    item.widget().setStyleSheet(button_style)
        except:
            pass  # Fallback to existing styles

    def _create_progress(self):
        progress_container = QFrame()
        progress_container.setFixedHeight(20)
        progress_container.setStyleSheet("background: transparent;")
        progress_container_layout = QVBoxLayout(progress_container)
        progress_container_layout.setContentsMargins(0, 0, 0, 0)
        progress_container_layout.setSpacing(0)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p% (%v/%m)")
        self.progress_bar.setFixedHeight(12)
        self.progress_bar.setStyleSheet(
            """
            QProgressBar {
                border: none;
                border-radius: 6px;
                text-align: center;
                background-color: rgba(0, 0, 0, 0.15);
                color: rgba(255, 255, 255, 0.9);
                font-size: 10px;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 6px;
            }
            """
        )

        progress_container_layout.addWidget(self.progress_bar)
        self.progress_bar.hide()
        progress_container.setVisible(False)
        return progress_container

    def _create_buttons(self):
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)

        self.export_page_button = self._create_action_button(
            "Export Page",
            self.sequence_car_tab.page_exporter.export_current_page_as_image,
        )
        self.export_all_button = self._create_action_button(
            "Export All Pages",
            self.sequence_car_tab.page_exporter.export_all_pages_as_images,
        )
        self.export_pdf_button = self._create_action_button(
            "Export as PDF",
            self.sequence_car_tab.page_exporter.export_all_pages_as_pdf,
        )
        self.refresh_button = self._create_action_button(
            "Refresh", self.sequence_car_tab.load_sequences
        )
        self.refresh_cache_button = self._create_action_button(
            "Refresh Cache", self.sequence_car_tab.page_exporter.clear_page_cache
        )

        button_layout.addStretch()
        button_layout.addWidget(self.export_page_button)
        button_layout.addWidget(self.export_all_button)
        button_layout.addWidget(self.export_pdf_button)
        button_layout.addWidget(self.refresh_button)
        button_layout.addWidget(self.refresh_cache_button)
        button_layout.addStretch()

        return button_layout

    def _create_action_button(self, text: str, callback) -> QPushButton:
        button = QPushButton(text)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.clicked.connect(callback)
        # Initial styling - will be updated by _update_button_sizes
        button.setStyleSheet(
            """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3498db, stop:1 #2980b9);
                color: white;
                border: 1px solid #5dade2;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
                font-size: 12px;
                min-width: 100px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5dade2, stop:1 #3498db);
                border: 1px solid #85c1e9;
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2980b9, stop:1 #1f618d);
                border: 1px solid #3498db;
            }
        """
        )
        return button
