# src/main_window/main_widget/sequence_card_tab/generation/generation_controls.py
import logging
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QComboBox,
    QSpinBox,
    QFrame,
    QProgressBar,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QCursor
from .generation_manager import GenerationParams
from src.interfaces.settings_manager_interface import ISettingsManager  # Added import


class GenerationControlsPanel(QWidget):
    """
    Control panel for sequence generation parameters and actions.

    Provides an intuitive interface for configuring generation parameters
    and triggering sequence generation in various batch sizes.
    """

    generate_requested = pyqtSignal(object, int)  # GenerationParams, batch_size
    clear_requested = pyqtSignal()

    def __init__(
        self, settings_manager: ISettingsManager | None = None, parent=None
    ):  # Modified signature
        super().__init__(parent)
        self.settings_manager = settings_manager  # Directly assign
        self.setup_ui()
        self.apply_styling()
        self._setup_settings_persistence()

    def setup_ui(self):
        """Setup the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 10, 8, 10)
        layout.setSpacing(12)

        # Header
        self.create_header()
        layout.addWidget(self.header_label)

        # Parameters section
        self.create_parameters_section()
        layout.addWidget(self.parameters_frame)

        # Generation controls section
        self.create_generation_controls()
        layout.addWidget(self.controls_frame)

        # Progress section
        self.create_progress_section()
        layout.addWidget(self.progress_frame)

    def create_header(self):
        """Create the header label."""
        self.header_label = QLabel("Generate Sequences")
        self.header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        header_font = QFont()
        header_font.setPointSize(11)
        header_font.setWeight(QFont.Weight.Medium)
        self.header_label.setFont(header_font)
        self.header_label.setObjectName("generationHeaderLabel")

    def create_parameters_section(self):
        """Create the parameters configuration section."""
        self.parameters_frame = QFrame()
        self.parameters_frame.setObjectName("parametersFrame")

        params_layout = QVBoxLayout(self.parameters_frame)
        params_layout.setContentsMargins(8, 8, 8, 8)
        params_layout.setSpacing(8)

        # Start Position selector
        start_pos_layout = QHBoxLayout()
        start_pos_layout.addWidget(QLabel("Start Position:"))
        self.start_pos_combo = QComboBox()
        self.start_pos_combo.addItems(["Any", "Alpha1", "Beta5", "Gamma11"])
        self.start_pos_combo.setCurrentText("Any")
        self.start_pos_combo.setObjectName("startPosCombo")
        start_pos_layout.addWidget(self.start_pos_combo)
        start_pos_layout.addStretch()
        params_layout.addLayout(start_pos_layout)

        # Length selector
        length_layout = QHBoxLayout()
        length_layout.addWidget(QLabel("Length:"))
        self.length_combo = QComboBox()
        self.length_combo.addItems(["4", "8", "16", "20", "24", "32"])
        self.length_combo.setCurrentText("16")
        self.length_combo.setObjectName("lengthCombo")
        length_layout.addWidget(self.length_combo)
        length_layout.addStretch()
        params_layout.addLayout(length_layout)

        # Level selector
        level_layout = QHBoxLayout()
        level_layout.addWidget(QLabel("Level:"))
        self.level_combo = QComboBox()
        self.level_combo.addItems(
            [
                "1 - Basic (No turns)",
                "2 - Intermediate (With turns)",
                "3 - Advanced (Non-radial)",
            ]
        )
        self.level_combo.setObjectName("levelCombo")
        level_layout.addWidget(self.level_combo)
        level_layout.addStretch()
        params_layout.addLayout(level_layout)

        # Turn intensity (for levels 2 and 3)
        intensity_layout = QHBoxLayout()
        intensity_layout.addWidget(QLabel("Turn Intensity:"))
        self.intensity_combo = QComboBox()
        self.intensity_combo.addItems(["1", "2", "3"])
        self.intensity_combo.setObjectName("intensityCombo")
        intensity_layout.addWidget(self.intensity_combo)
        intensity_layout.addStretch()
        params_layout.addLayout(intensity_layout)

        # Generation mode
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Mode:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Freeform", "Circular"])
        self.mode_combo.setObjectName("modeCombo")
        mode_layout.addWidget(self.mode_combo)
        mode_layout.addStretch()
        params_layout.addLayout(mode_layout)

        # Prop continuity
        continuity_layout = QHBoxLayout()
        continuity_layout.addWidget(QLabel("Prop Continuity:"))
        self.continuity_combo = QComboBox()
        self.continuity_combo.addItems(["Continuous", "Random"])
        self.continuity_combo.setObjectName("continuityCombo")
        continuity_layout.addWidget(self.continuity_combo)
        continuity_layout.addStretch()
        params_layout.addLayout(continuity_layout)

        # Connect level change to update intensity options
        self.level_combo.currentTextChanged.connect(self.on_level_changed)

    def _setup_settings_persistence(self):
        """Setup automatic settings persistence for all controls."""
        try:
            # self.settings_manager is now passed in constructor
            if self.settings_manager:
                # Load saved settings
                self._load_saved_settings()

                # Connect all controls to auto-save
                self.start_pos_combo.currentTextChanged.connect(self._save_settings)
                self.length_combo.currentTextChanged.connect(self._save_settings)
                self.level_combo.currentTextChanged.connect(self._save_settings)
                self.intensity_combo.currentTextChanged.connect(self._save_settings)
                self.mode_combo.currentTextChanged.connect(self._save_settings)
                self.continuity_combo.currentTextChanged.connect(self._save_settings)
                self.batch_size_combo.currentTextChanged.connect(self._save_settings)

                logging.info("Generation controls settings persistence enabled")
            else:
                logging.warning(
                    "Settings manager not provided to GenerationControlsPanel"  # Updated warning
                )
        except Exception as e:
            logging.error(f"Error setting up settings persistence: {e}")

    def _load_saved_settings(self):
        """Load saved settings and apply them to the UI controls."""
        try:
            # Load each setting with appropriate defaults
            start_pos = self.settings_manager.get_setting(
                "generation_controls", "start_position", "Any"
            )
            length = self.settings_manager.get_setting(
                "generation_controls", "length", "16"
            )
            level = self.settings_manager.get_setting(
                "generation_controls", "level", "1 - Basic (No turns)"
            )
            intensity = self.settings_manager.get_setting(
                "generation_controls", "turn_intensity", "1"
            )
            mode = self.settings_manager.get_setting(
                "generation_controls", "generation_mode", "Freeform"
            )
            continuity = self.settings_manager.get_setting(
                "generation_controls", "prop_continuity", "Continuous"
            )
            batch_size = self.settings_manager.get_setting(
                "generation_controls", "batch_size", "5"
            )

            # Apply settings to UI controls
            self.start_pos_combo.setCurrentText(start_pos)
            self.length_combo.setCurrentText(length)
            self.level_combo.setCurrentText(level)
            self.intensity_combo.setCurrentText(intensity)
            self.mode_combo.setCurrentText(mode)
            self.continuity_combo.setCurrentText(continuity)
            self.batch_size_combo.setCurrentText(batch_size)

            logging.info(
                f"Loaded generation controls settings: length={length}, level={level}, mode={mode}"
            )
        except Exception as e:
            logging.error(f"Error loading saved settings: {e}")

    def _save_settings(self):
        """Save current UI settings."""
        if not self.settings_manager:
            return

        try:
            self.settings_manager.set_setting(
                "generation_controls",
                "start_position",
                self.start_pos_combo.currentText(),
            )
            self.settings_manager.set_setting(
                "generation_controls", "length", self.length_combo.currentText()
            )
            self.settings_manager.set_setting(
                "generation_controls", "level", self.level_combo.currentText()
            )
            self.settings_manager.set_setting(
                "generation_controls",
                "turn_intensity",
                self.intensity_combo.currentText(),
            )
            self.settings_manager.set_setting(
                "generation_controls", "generation_mode", self.mode_combo.currentText()
            )
            self.settings_manager.set_setting(
                "generation_controls",
                "prop_continuity",
                self.continuity_combo.currentText(),
            )
            self.settings_manager.set_setting(
                "generation_controls", "batch_size", self.batch_size_combo.currentText()
            )

            logging.debug("Saved generation controls settings")
        except Exception as e:
            logging.error(f"Error saving settings: {e}")

    def create_generation_controls(self):
        """Create the generation control buttons."""
        self.controls_frame = QFrame()
        self.controls_frame.setObjectName("controlsFrame")

        controls_layout = QVBoxLayout(self.controls_frame)
        controls_layout.setContentsMargins(8, 8, 8, 8)
        controls_layout.setSpacing(8)

        # Batch size selector
        batch_layout = QHBoxLayout()
        batch_layout.addWidget(QLabel("Batch Size:"))
        self.batch_size_combo = QComboBox()
        self.batch_size_combo.addItems(["1", "5", "10", "20"])
        self.batch_size_combo.setCurrentText("5")
        self.batch_size_combo.setObjectName("batchSizeCombo")
        batch_layout.addWidget(self.batch_size_combo)
        batch_layout.addStretch()
        controls_layout.addLayout(batch_layout)

        # Generate button
        self.generate_button = QPushButton("Generate Sequences")
        self.generate_button.setObjectName("generateButton")
        self.generate_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.generate_button.clicked.connect(self.on_generate_clicked)
        controls_layout.addWidget(self.generate_button)

        # Clear button
        self.clear_button = QPushButton("Clear Generated")
        self.clear_button.setObjectName("clearButton")
        self.clear_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.clear_button.clicked.connect(self.clear_requested.emit)
        controls_layout.addWidget(self.clear_button)

    def create_progress_section(self):
        """Create the progress indicator section."""
        self.progress_frame = QFrame()
        self.progress_frame.setObjectName("progressFrame")
        self.progress_frame.setVisible(False)  # Hidden by default

        progress_layout = QVBoxLayout(self.progress_frame)
        progress_layout.setContentsMargins(8, 8, 8, 8)
        progress_layout.setSpacing(4)

        self.progress_label = QLabel("Generating sequences...")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        progress_layout.addWidget(self.progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("generationProgressBar")
        progress_layout.addWidget(self.progress_bar)

    def on_level_changed(self, level_text: str):
        """Handle level selection changes to update turn intensity options."""
        level_num = int(level_text.split(" - ")[0])

        self.intensity_combo.clear()
        if level_num == 1:
            # Level 1 doesn't use turns
            self.intensity_combo.addItems(["N/A"])
            self.intensity_combo.setEnabled(False)
        elif level_num == 2:
            # Level 2 uses integer turns
            self.intensity_combo.addItems(["1", "2", "3"])
            self.intensity_combo.setEnabled(True)
        elif level_num == 3:
            # Level 3 uses fractional turns
            self.intensity_combo.addItems(["0.5", "1", "1.5", "2", "2.5", "3"])
            self.intensity_combo.setEnabled(True)

    def on_generate_clicked(self):
        """Handle generate button clicks."""
        params = self.get_generation_parameters()
        batch_size = int(self.batch_size_combo.currentText())
        self.generate_requested.emit(params, batch_size)

    def get_generation_parameters(self) -> GenerationParams:
        """Get the current generation parameters from the UI."""
        level_text = self.level_combo.currentText()
        level = int(level_text.split(" - ")[0])

        # Handle turn intensity based on level
        if level == 1:
            turn_intensity = 0
        else:
            intensity_text = self.intensity_combo.currentText()
            if intensity_text == "N/A":
                turn_intensity = 0
            else:
                turn_intensity = float(intensity_text)

        # Get start position, convert "Any" to None
        start_pos_text = self.start_pos_combo.currentText()
        start_position = None if start_pos_text == "Any" else start_pos_text.lower()

        return GenerationParams(
            length=int(self.length_combo.currentText()),
            level=level,
            turn_intensity=turn_intensity,
            prop_continuity=self.continuity_combo.currentText().lower(),
            generation_mode=self.mode_combo.currentText().lower(),
            rotation_type="halved",  # Default for circular mode
            CAP_type="strict_rotated",  # Default for circular mode
            start_position=start_position,
        )

    def set_generation_enabled(self, enabled: bool):
        """Enable or disable generation controls."""
        self.generate_button.setEnabled(enabled)
        if enabled:
            self.generate_button.setText("Generate Sequences")
        else:
            self.generate_button.setText("Generating...")

    def show_progress(self, current: int, total: int):
        """Show generation progress."""
        self.progress_frame.setVisible(True)
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.progress_label.setText(f"Generating sequences... ({current}/{total})")

    def hide_progress(self):
        """Hide generation progress."""
        self.progress_frame.setVisible(False)

    def apply_styling(self):
        """Apply consistent styling."""
        self.setStyleSheet(
            """
            QWidget#generationControlsPanel {
                background: transparent;
            }
            
            QLabel#generationHeaderLabel {
                color: #e1e5e9;
                font-weight: 500;
                padding: 2px;
            }
            
            QFrame#parametersFrame, QFrame#controlsFrame {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 6px;
                padding: 4px;
            }
            
            QFrame#progressFrame {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 6px;
                padding: 4px;
            }
            
            QLabel {
                color: #e1e5e9;
                font-size: 10px;
                min-width: 80px;
            }
            
            QComboBox {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 4px;
                padding: 4px 8px;
                color: #e1e5e9;
                min-width: 100px;
            }
            
            QComboBox:hover {
                background: rgba(255, 255, 255, 0.15);
                border-color: rgba(255, 255, 255, 0.3);
            }
            
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid #e1e5e9;
                margin-right: 4px;
            }
            
            QPushButton#generateButton {
                background: #3182ce;
                border: none;
                border-radius: 6px;
                color: white;
                font-weight: 600;
                padding: 10px 16px;
                font-size: 11px;
            }
            
            QPushButton#generateButton:hover {
                background: #2c5aa0;
            }
            
            QPushButton#generateButton:disabled {
                background: #4a5568;
                color: #a0aec0;
            }
            
            QPushButton#clearButton {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                color: #e1e5e9;
                font-weight: 500;
                padding: 8px 16px;
                font-size: 10px;
            }
            
            QPushButton#clearButton:hover {
                background: rgba(255, 255, 255, 0.15);
                border-color: rgba(255, 255, 255, 0.3);
            }
            
            QProgressBar {
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 4px;
                background: rgba(255, 255, 255, 0.1);
                text-align: center;
                color: #e1e5e9;
                font-size: 10px;
            }
            
            QProgressBar::chunk {
                background: #3182ce;
                border-radius: 3px;
            }
        """
        )

        self.setObjectName("generationControlsPanel")
