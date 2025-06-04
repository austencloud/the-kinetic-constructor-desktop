"""
Sequence Viewer Component - Clean Architecture Implementation.

Handles sequence detail display and operations with single responsibility.
Provides sequence image display, metadata presentation, and action controls.

Features:
- Large sequence image display with navigation
- Sequence metadata and information display
- Action buttons (edit, save, delete, fullscreen)
- Variation navigation for multi-variation sequences
- Responsive layout for 1/3 width panel
- Glassmorphism styling integration

Performance Targets:
- <100ms sequence display
- <50ms variation switching
- Smooth image transitions
- Responsive layout updates
"""

import logging
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QScrollArea,
    QSizePolicy,
)
from PyQt6.QtCore import pyqtSignal, QTimer, QElapsedTimer, QSize
from PyQt6.QtGui import QPixmap, QFont
from PyQt6.QtCore import Qt

from ..core.interfaces import SequenceModel, BrowseTabConfig

logger = logging.getLogger(__name__)


class SequenceViewer(QWidget):
    """
    Sequence viewer component for detailed sequence display.

    Single Responsibility: Display sequence details and provide action controls

    Features:
    - Large sequence image display with navigation
    - Sequence metadata and information display
    - Action controls (edit, save, delete, fullscreen)
    - Variation navigation for sequences with multiple variations
    - Responsive layout for right panel (1/3 width)
    """

    # Signals for component communication
    edit_requested = pyqtSignal(str)  # sequence_id
    save_requested = pyqtSignal(str)  # sequence_id
    delete_requested = pyqtSignal(str)  # sequence_id
    fullscreen_requested = pyqtSignal(str)  # image_path
    variation_changed = pyqtSignal(str, int)  # sequence_id, variation_index

    def __init__(self, config: BrowseTabConfig = None, parent: QWidget = None):
        super().__init__(parent)

        self.config = config or BrowseTabConfig()

        # State management
        self._current_sequence: Optional[SequenceModel] = None
        self._current_variation_index = 0
        self._available_variations = []

        # Performance tracking
        self._performance_timer = QElapsedTimer()

        # UI components
        self.image_display = None
        self.title_label = None
        self.metadata_container = None
        self.action_buttons = {}
        self.variation_controls = None
        self.scroll_area = None

        self._setup_ui()
        self._setup_styling()

        logger.debug("SequenceViewer component initialized")

    def _setup_ui(self):
        """Setup the sequence viewer UI layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Create scroll area for content
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        # Content widget
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(5, 5, 5, 5)
        content_layout.setSpacing(15)

        # Header section
        self._create_header_section(content_layout)

        # Image display section
        self._create_image_section(content_layout)

        # Variation controls section
        self._create_variation_section(content_layout)

        # Metadata section
        self._create_metadata_section(content_layout)

        # Action buttons section
        self._create_action_section(content_layout)

        # Add stretch to push content to top
        content_layout.addStretch()

        # Set content widget to scroll area
        self.scroll_area.setWidget(content_widget)
        layout.addWidget(self.scroll_area)

        # Set size policy
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def _create_header_section(self, layout):
        """Create header section with title."""
        header_container = QWidget()
        header_layout = QVBoxLayout(header_container)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(5)

        # Section title
        section_title = QLabel("Sequence Viewer")
        section_title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        section_title.setStyleSheet("color: white;")
        header_layout.addWidget(section_title)

        # Sequence title
        self.title_label = QLabel("No sequence selected")
        self.title_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: rgba(255, 255, 255, 0.9);")
        self.title_label.setWordWrap(True)
        header_layout.addWidget(self.title_label)

        layout.addWidget(header_container)

    def _create_image_section(self, layout):
        """Create image display section."""
        image_container = QFrame()
        image_container.setMinimumHeight(200)
        image_container.setStyleSheet(
            """
            QFrame {
                background: rgba(255, 255, 255, 0.05);
                border-radius: 12px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
        """
        )

        image_layout = QVBoxLayout(image_container)
        image_layout.setContentsMargins(10, 10, 10, 10)

        # Image display label
        self.image_display = QLabel("No image to display")
        self.image_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_display.setMinimumHeight(180)
        self.image_display.setStyleSheet(
            """
            QLabel {
                background: rgba(255, 255, 255, 0.02);
                border-radius: 8px;
                color: rgba(255, 255, 255, 0.6);
                font-size: 14px;
            }
        """
        )
        self.image_display.setScaledContents(False)
        image_layout.addWidget(self.image_display)

        # Fullscreen button
        fullscreen_button = QPushButton("⛶ Fullscreen")
        fullscreen_button.setStyleSheet(
            """
            QPushButton {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                padding: 6px;
                color: white;
                font-size: 12px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.2);
            }
        """
        )
        fullscreen_button.clicked.connect(self._request_fullscreen)
        image_layout.addWidget(fullscreen_button)

        layout.addWidget(image_container)

    def _create_variation_section(self, layout):
        """Create variation navigation section."""
        self.variation_controls = QWidget()
        variation_layout = QHBoxLayout(self.variation_controls)
        variation_layout.setContentsMargins(0, 0, 0, 0)
        variation_layout.setSpacing(5)

        # Previous variation button
        prev_button = QPushButton("◀")
        prev_button.setFixedSize(30, 30)
        prev_button.clicked.connect(self._previous_variation)
        variation_layout.addWidget(prev_button)

        # Variation info label
        self.variation_label = QLabel("Variation 1 of 1")
        self.variation_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.variation_label.setStyleSheet("color: white; font-size: 12px;")
        variation_layout.addWidget(self.variation_label, 1)

        # Next variation button
        next_button = QPushButton("▶")
        next_button.setFixedSize(30, 30)
        next_button.clicked.connect(self._next_variation)
        variation_layout.addWidget(next_button)

        # Style variation buttons
        button_style = """
            QPushButton {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 15px;
                color: white;
                font-size: 14px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.2);
            }
            QPushButton:disabled {
                background: rgba(255, 255, 255, 0.05);
                color: rgba(255, 255, 255, 0.3);
            }
        """
        prev_button.setStyleSheet(button_style)
        next_button.setStyleSheet(button_style)

        # Store button references
        self.prev_variation_button = prev_button
        self.next_variation_button = next_button

        # Initially hidden
        self.variation_controls.hide()

        layout.addWidget(self.variation_controls)

    def _create_metadata_section(self, layout):
        """Create metadata display section."""
        metadata_frame = QFrame()
        metadata_frame.setStyleSheet(
            """
            QFrame {
                background: rgba(255, 255, 255, 0.05);
                border-radius: 12px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
        """
        )

        self.metadata_container = QVBoxLayout(metadata_frame)
        self.metadata_container.setContentsMargins(15, 15, 15, 15)
        self.metadata_container.setSpacing(8)

        # Metadata title
        metadata_title = QLabel("Sequence Information")
        metadata_title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        metadata_title.setStyleSheet("color: white;")
        self.metadata_container.addWidget(metadata_title)

        # Placeholder for metadata
        no_metadata_label = QLabel("No sequence selected")
        no_metadata_label.setStyleSheet(
            "color: rgba(255, 255, 255, 0.6); font-size: 12px;"
        )
        self.metadata_container.addWidget(no_metadata_label)

        layout.addWidget(metadata_frame)

    def _create_action_section(self, layout):
        """Create action buttons section."""
        action_container = QWidget()
        action_layout = QVBoxLayout(action_container)
        action_layout.setContentsMargins(0, 0, 0, 0)
        action_layout.setSpacing(8)

        # Action buttons
        button_configs = [
            ("edit", "✏️ Edit Sequence", self._request_edit),
            ("save", "💾 Save Sequence", self._request_save),
            ("delete", "🗑️ Delete Sequence", self._request_delete),
        ]

        for button_id, text, handler in button_configs:
            button = QPushButton(text)
            button.setMinimumHeight(35)
            button.setStyleSheet(
                """
                QPushButton {
                    background: rgba(255, 255, 255, 0.1);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    border-radius: 8px;
                    padding: 8px;
                    color: white;
                    font-size: 12px;
                    text-align: left;
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.2);
                }
                QPushButton:disabled {
                    background: rgba(255, 255, 255, 0.05);
                    color: rgba(255, 255, 255, 0.3);
                }
            """
            )
            button.clicked.connect(handler)
            button.setEnabled(False)  # Initially disabled

            self.action_buttons[button_id] = button
            action_layout.addWidget(button)

        layout.addWidget(action_container)

    def _setup_styling(self):
        """Apply glassmorphism styling to the sequence viewer."""
        try:
            self.setStyleSheet(
                """
                SequenceViewer {
                    background: rgba(255, 255, 255, 0.05);
                    border-radius: 15px;
                    border: 1px solid rgba(255, 255, 255, 0.1);
                }
                QScrollArea {
                    background: transparent;
                    border: none;
                }
                QScrollBar:vertical {
                    background: rgba(255, 255, 255, 0.1);
                    width: 8px;
                    border-radius: 4px;
                }
                QScrollBar::handle:vertical {
                    background: rgba(255, 255, 255, 0.3);
                    border-radius: 4px;
                    min-height: 20px;
                }
            """
            )

            logger.debug("Sequence viewer styling applied")

        except Exception as e:
            logger.warning(f"Failed to apply sequence viewer styling: {e}")

    def _update_metadata_display(self):
        """Update the metadata display with current sequence information."""
        # Clear existing metadata
        for i in reversed(range(1, self.metadata_container.count())):
            child = self.metadata_container.itemAt(i).widget()
            if child:
                child.deleteLater()

        if not self._current_sequence:
            no_data_label = QLabel("No sequence selected")
            no_data_label.setStyleSheet(
                "color: rgba(255, 255, 255, 0.6); font-size: 12px;"
            )
            self.metadata_container.addWidget(no_data_label)
            return

        # Add sequence metadata
        metadata_items = [
            ("Name", self._current_sequence.name or "Untitled"),
            ("ID", self._current_sequence.id or "Unknown"),
        ]

        # Add optional metadata
        if (
            hasattr(self._current_sequence, "difficulty")
            and self._current_sequence.difficulty
        ):
            metadata_items.append(
                ("Difficulty", str(self._current_sequence.difficulty))
            )

        if hasattr(self._current_sequence, "length") and self._current_sequence.length:
            metadata_items.append(("Length", str(self._current_sequence.length)))

        if hasattr(self._current_sequence, "author") and self._current_sequence.author:
            metadata_items.append(("Author", self._current_sequence.author))

        if (
            hasattr(self._current_sequence, "date_created")
            and self._current_sequence.date_created
        ):
            metadata_items.append(("Created", str(self._current_sequence.date_created)))

        # Create metadata labels
        for label, value in metadata_items:
            metadata_row = QWidget()
            row_layout = QHBoxLayout(metadata_row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(10)

            label_widget = QLabel(f"{label}:")
            label_widget.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            label_widget.setStyleSheet("color: rgba(255, 255, 255, 0.8);")
            label_widget.setMinimumWidth(80)

            value_widget = QLabel(str(value))
            value_widget.setStyleSheet("color: rgba(255, 255, 255, 0.9);")
            value_widget.setWordWrap(True)

            row_layout.addWidget(label_widget)
            row_layout.addWidget(value_widget, 1)

            self.metadata_container.addWidget(metadata_row)

    def _load_sequence_image(self):
        """Load and display the sequence image."""
        if not self._current_sequence:
            self.image_display.setText("No sequence selected")
            self.image_display.setPixmap(QPixmap())
            return

        self._performance_timer.start()

        try:
            # Get image path for current variation
            if (
                hasattr(self._current_sequence, "thumbnails")
                and self._current_sequence.thumbnails
                and self._current_variation_index
                < len(self._current_sequence.thumbnails)
            ):

                image_path = self._current_sequence.thumbnails[
                    self._current_variation_index
                ]

                # Load and scale image
                pixmap = QPixmap(image_path)
                if not pixmap.isNull():
                    # Scale to fit display area while maintaining aspect ratio
                    scaled_pixmap = pixmap.scaled(
                        self.image_display.size(),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                    self.image_display.setPixmap(scaled_pixmap)
                    self.image_display.setText("")
                else:
                    self.image_display.setText("Failed to load image")
                    self.image_display.setPixmap(QPixmap())
            else:
                self.image_display.setText("No image available")
                self.image_display.setPixmap(QPixmap())

            elapsed = self._performance_timer.elapsed()
            logger.debug(f"Sequence image loaded in {elapsed}ms")

            # Performance target: <100ms sequence display
            if elapsed > 100:
                logger.warning(
                    f"Sequence image loading exceeded 100ms target: {elapsed}ms"
                )

        except Exception as e:
            logger.error(f"Failed to load sequence image: {e}")
            self.image_display.setText("Error loading image")
            self.image_display.setPixmap(QPixmap())

    def _update_variation_controls(self):
        """Update variation navigation controls."""
        if not self._current_sequence:
            self.variation_controls.hide()
            return

        # Check if sequence has multiple variations
        variation_count = 1
        if (
            hasattr(self._current_sequence, "thumbnails")
            and self._current_sequence.thumbnails
        ):
            variation_count = len(self._current_sequence.thumbnails)

        if variation_count > 1:
            self.variation_controls.show()
            self.variation_label.setText(
                f"Variation {self._current_variation_index + 1} of {variation_count}"
            )

            # Update button states
            self.prev_variation_button.setEnabled(self._current_variation_index > 0)
            self.next_variation_button.setEnabled(
                self._current_variation_index < variation_count - 1
            )
        else:
            self.variation_controls.hide()

    def _update_action_buttons(self):
        """Update action button states."""
        has_sequence = self._current_sequence is not None

        for button in self.action_buttons.values():
            button.setEnabled(has_sequence)

    # Event handlers
    def _previous_variation(self):
        """Navigate to previous variation."""
        if self._current_variation_index > 0:
            self._current_variation_index -= 1
            self._load_sequence_image()
            self._update_variation_controls()

            if self._current_sequence:
                self.variation_changed.emit(
                    self._current_sequence.id, self._current_variation_index
                )

    def _next_variation(self):
        """Navigate to next variation."""
        max_variations = 1
        if (
            hasattr(self._current_sequence, "thumbnails")
            and self._current_sequence.thumbnails
        ):
            max_variations = len(self._current_sequence.thumbnails)

        if self._current_variation_index < max_variations - 1:
            self._current_variation_index += 1
            self._load_sequence_image()
            self._update_variation_controls()

            if self._current_sequence:
                self.variation_changed.emit(
                    self._current_sequence.id, self._current_variation_index
                )

    def _request_edit(self):
        """Request sequence editing."""
        if self._current_sequence:
            self.edit_requested.emit(self._current_sequence.id)

    def _request_save(self):
        """Request sequence saving."""
        if self._current_sequence:
            self.save_requested.emit(self._current_sequence.id)

    def _request_delete(self):
        """Request sequence deletion."""
        if self._current_sequence:
            self.delete_requested.emit(self._current_sequence.id)

    def _request_fullscreen(self):
        """Request fullscreen image display."""
        if (
            self._current_sequence
            and hasattr(self._current_sequence, "thumbnails")
            and self._current_sequence.thumbnails
            and self._current_variation_index < len(self._current_sequence.thumbnails)
        ):

            image_path = self._current_sequence.thumbnails[
                self._current_variation_index
            ]
            self.fullscreen_requested.emit(image_path)

    # Public interface methods
    def display_sequence(self, sequence: SequenceModel, variation_index: int = 0):
        """Display a sequence in the viewer."""
        self._performance_timer.start()

        self._current_sequence = sequence
        self._current_variation_index = variation_index

        # Update UI components
        self.title_label.setText(sequence.name or "Untitled Sequence")
        self._update_metadata_display()
        self._load_sequence_image()
        self._update_variation_controls()
        self._update_action_buttons()

        elapsed = self._performance_timer.elapsed()
        logger.debug(f"Sequence displayed in {elapsed}ms: {sequence.name}")

        # Performance target: <100ms sequence display
        if elapsed > 100:
            logger.warning(f"Sequence display exceeded 100ms target: {elapsed}ms")

    def clear_display(self):
        """Clear the sequence display."""
        self._current_sequence = None
        self._current_variation_index = 0

        self.title_label.setText("No sequence selected")
        self.image_display.setText("No image to display")
        self.image_display.setPixmap(QPixmap())
        self.variation_controls.hide()
        self._update_metadata_display()
        self._update_action_buttons()

    def get_current_sequence(self) -> Optional[SequenceModel]:
        """Get the currently displayed sequence."""
        return self._current_sequence

    def get_current_variation_index(self) -> int:
        """Get the current variation index."""
        return self._current_variation_index

    def cleanup(self):
        """Cleanup resources."""
        try:
            self.clear_display()
            logger.debug("SequenceViewer cleanup completed")
        except Exception as e:
            logger.error(f"SequenceViewer cleanup failed: {e}")
