"""
Export Test Component for rapid iteration and testing of image export functionality.
This component provides immediate visual feedback and easy access for repeated testing.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QTextEdit,
    QCheckBox,
    QGroupBox,
    QScrollArea,
    QFrame,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPixmap
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from main_window.main_widget.sequence_workbench.sequence_workbench import (
        SequenceWorkbench,
    )


class ExportTestComponent(QWidget):
    """
    A dedicated test component for rapid iteration and testing of export functionality.
    Provides immediate visual feedback and debugging information.
    """

    def __init__(self, sequence_workbench: "SequenceWorkbench"):
        super().__init__()
        self.sequence_workbench = sequence_workbench
        self.main_widget = sequence_workbench.main_widget

        # Apply glassmorphism styling
        self.setStyleSheet(
            """
            QWidget {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
            QPushButton {
                background: rgba(255, 255, 255, 0.15);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 8px;
                padding: 8px 16px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.25);
            }
            QPushButton:pressed {
                background: rgba(255, 255, 255, 0.35);
            }
            QLabel {
                color: white;
                font-weight: bold;
            }
            QTextEdit {
                background: rgba(0, 0, 0, 0.3);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                color: white;
                padding: 8px;
            }
            QCheckBox {
                color: white;
                font-weight: bold;
            }
            QGroupBox {
                color: white;
                font-weight: bold;
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """
        )

        self.setup_ui()
        self.setup_connections()

    def setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # Title
        title = QLabel("Image Export Test Component")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(title)

        # Test buttons section
        test_group = QGroupBox("Export Tests")
        test_layout = QVBoxLayout(test_group)

        button_layout = QHBoxLayout()

        self.test_current_btn = QPushButton("Test Current Sequence")
        self.test_current_btn.setToolTip("Export the current sequence with debugging")
        button_layout.addWidget(self.test_current_btn)

        self.test_start_only_btn = QPushButton("Test Start Position Only")
        self.test_start_only_btn.setToolTip("Export only the start position")
        button_layout.addWidget(self.test_start_only_btn)

        self.analyze_sequence_btn = QPushButton("Analyze Sequence Data")
        self.analyze_sequence_btn.setToolTip("Analyze the current sequence structure")
        button_layout.addWidget(self.analyze_sequence_btn)

        test_layout.addLayout(button_layout)
        layout.addWidget(test_group)

        # Options section
        options_group = QGroupBox("Export Options")
        options_layout = QVBoxLayout(options_group)

        self.include_start_pos_cb = QCheckBox("Include Start Position")
        self.include_start_pos_cb.setChecked(True)
        options_layout.addWidget(self.include_start_pos_cb)

        self.add_beat_numbers_cb = QCheckBox("Add Beat Numbers")
        self.add_beat_numbers_cb.setChecked(True)
        options_layout.addWidget(self.add_beat_numbers_cb)

        layout.addWidget(options_group)

        # Debug output section
        debug_group = QGroupBox("Debug Output")
        debug_layout = QVBoxLayout(debug_group)

        self.debug_output = QTextEdit()
        self.debug_output.setMaximumHeight(200)
        self.debug_output.setPlainText("Ready for testing...")
        debug_layout.addWidget(self.debug_output)

        clear_btn = QPushButton("Clear Debug Output")
        clear_btn.clicked.connect(self.debug_output.clear)
        debug_layout.addWidget(clear_btn)

        layout.addWidget(debug_group)

        # Status section
        self.status_label = QLabel("Status: Ready")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

    def setup_connections(self):
        """Setup signal connections."""
        self.test_current_btn.clicked.connect(self.test_current_sequence)
        self.test_start_only_btn.clicked.connect(self.test_start_position_only)
        self.analyze_sequence_btn.clicked.connect(self.analyze_sequence_data)

    def log_debug(self, message: str):
        """Add a debug message to the output."""
        self.debug_output.append(f"[{QTimer().remainingTime()}] {message}")
        self.debug_output.ensureCursorVisible()

    def update_status(self, message: str):
        """Update the status label."""
        self.status_label.setText(f"Status: {message}")

    def test_current_sequence(self):
        """Test exporting the current sequence with debugging."""
        self.update_status("Testing current sequence...")
        self.log_debug("=== Testing Current Sequence Export ===")

        try:
            # Get the current sequence
            json_manager = self.main_widget.app_context.json_manager
            sequence = json_manager.loader_saver.load_current_sequence()

            self.log_debug(f"Loaded sequence with {len(sequence)} entries")

            # Analyze sequence structure
            for i, entry in enumerate(sequence):
                if isinstance(entry, dict):
                    keys = list(entry.keys())
                    self.log_debug(
                        f"  Entry {i}: {keys[:5]}{'...' if len(keys) > 5 else ''}"
                    )
                else:
                    self.log_debug(f"  Entry {i}: {type(entry)}")

            # Get export manager
            export_manager = self.sequence_workbench.beat_frame.image_export_manager

            # Set options based on checkboxes
            settings_manager = self.main_widget.app_context.settings_manager
            settings_manager.image_export.set_image_export_setting(
                "include_start_position", self.include_start_pos_cb.isChecked()
            )
            settings_manager.image_export.set_image_export_setting(
                "add_beat_numbers", self.add_beat_numbers_cb.isChecked()
            )

            # Perform export
            export_manager.export_image_directly(sequence)

            self.log_debug("Export completed successfully")
            self.update_status("Export completed")

        except Exception as e:
            self.log_debug(f"Error during export: {str(e)}")
            self.update_status(f"Error: {str(e)}")

    def test_start_position_only(self):
        """Test exporting only the start position."""
        self.update_status("Testing start position only...")
        self.log_debug("=== Testing Start Position Only Export ===")

        try:
            # Force include start position and create minimal sequence
            settings_manager = self.main_widget.app_context.settings_manager
            settings_manager.image_export.set_image_export_setting(
                "include_start_position", True
            )

            # Get current sequence but only use metadata and start position
            json_manager = self.main_widget.app_context.json_manager
            full_sequence = json_manager.loader_saver.load_current_sequence()

            if len(full_sequence) >= 2:
                # Create sequence with only metadata and start position
                minimal_sequence = full_sequence[:2]
                self.log_debug(
                    f"Created minimal sequence with {len(minimal_sequence)} entries"
                )

                export_manager = self.sequence_workbench.beat_frame.image_export_manager
                export_manager.export_image_directly(minimal_sequence)

                self.log_debug("Start position export completed")
                self.update_status("Start position export completed")
            else:
                self.log_debug("Insufficient sequence data for start position")
                self.update_status("No start position available")

        except Exception as e:
            self.log_debug(f"Error during start position export: {str(e)}")
            self.update_status(f"Error: {str(e)}")

    def analyze_sequence_data(self):
        """Analyze the current sequence data structure."""
        self.update_status("Analyzing sequence data...")
        self.log_debug("=== Sequence Data Analysis ===")

        try:
            json_manager = self.main_widget.app_context.json_manager
            sequence = json_manager.loader_saver.load_current_sequence()

            self.log_debug(f"Total sequence length: {len(sequence)}")

            if len(sequence) > 0:
                self.log_debug(f"Entry 0 (metadata): {list(sequence[0].keys())}")

            if len(sequence) > 1:
                entry1_keys = list(sequence[1].keys())
                has_start_pos = "sequence_start_position" in sequence[1]
                self.log_debug(
                    f"Entry 1 (start pos): {entry1_keys}, has_start_pos={has_start_pos}"
                )

            beats_count = len(sequence) - 2 if len(sequence) > 2 else 0
            self.log_debug(f"Beat entries (from index 2): {beats_count}")

            if beats_count > 0:
                for i in range(2, min(len(sequence), 7)):  # Show first 5 beats
                    entry = sequence[i]
                    is_placeholder = entry.get("is_placeholder", False)
                    has_letter = "letter" in entry
                    self.log_debug(
                        f"  Beat {i-2}: placeholder={is_placeholder}, has_letter={has_letter}"
                    )

            self.update_status("Analysis completed")

        except Exception as e:
            self.log_debug(f"Error during analysis: {str(e)}")
            self.update_status(f"Analysis error: {str(e)}")
