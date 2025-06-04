import logging
from typing import TYPE_CHECKING
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox
from PyQt6.QtCore import pyqtSignal

if TYPE_CHECKING:
    from ..generation_manager import GenerationParams


class ParameterControlsManager(QWidget):
    level_changed = pyqtSignal(str)
    parameter_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.create_parameter_controls()

    def create_parameter_controls(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        self._create_start_position_control(layout)
        self._create_length_control(layout)
        self._create_level_control(layout)
        self._create_intensity_control(layout)
        self._create_mode_control(layout)
        self._create_cap_type_control(layout)
        self._create_rotation_type_control(layout)
        self._create_continuity_control(layout)

        # Set up visibility logic for CAP controls
        self._update_cap_controls_visibility()

    def _create_start_position_control(self, layout):
        start_pos_layout = QHBoxLayout()
        start_pos_layout.addWidget(QLabel("Start Position:"))
        self.start_pos_combo = QComboBox()
        self.start_pos_combo.addItems(["Any", "Alpha1", "Beta5", "Gamma11"])
        self.start_pos_combo.setCurrentText("Any")
        self.start_pos_combo.setObjectName("startPosCombo")
        self.start_pos_combo.currentTextChanged.connect(self.parameter_changed.emit)
        start_pos_layout.addWidget(self.start_pos_combo)
        start_pos_layout.addStretch()
        layout.addLayout(start_pos_layout)

    def _create_length_control(self, layout):
        length_layout = QHBoxLayout()
        length_layout.addWidget(QLabel("Length:"))
        self.length_combo = QComboBox()
        self.length_combo.addItems(["4", "8", "16", "20", "24", "32"])
        self.length_combo.setCurrentText("16")
        self.length_combo.setObjectName("lengthCombo")
        self.length_combo.currentTextChanged.connect(self.parameter_changed.emit)
        length_layout.addWidget(self.length_combo)
        length_layout.addStretch()
        layout.addLayout(length_layout)

    def _create_level_control(self, layout):
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
        self.level_combo.currentTextChanged.connect(self._on_level_changed)
        self.level_combo.currentTextChanged.connect(self.parameter_changed.emit)
        level_layout.addWidget(self.level_combo)
        level_layout.addStretch()
        layout.addLayout(level_layout)

    def _create_intensity_control(self, layout):
        intensity_layout = QHBoxLayout()
        intensity_layout.addWidget(QLabel("Turn Intensity:"))
        self.intensity_combo = QComboBox()
        self.intensity_combo.addItems(["1", "2", "3"])
        self.intensity_combo.setObjectName("intensityCombo")
        self.intensity_combo.currentTextChanged.connect(self.parameter_changed.emit)
        intensity_layout.addWidget(self.intensity_combo)
        intensity_layout.addStretch()
        layout.addLayout(intensity_layout)

    def _create_mode_control(self, layout):
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Mode:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Freeform", "Circular"])
        self.mode_combo.setObjectName("modeCombo")
        self.mode_combo.currentTextChanged.connect(self.parameter_changed.emit)
        self.mode_combo.currentTextChanged.connect(self._update_cap_controls_visibility)
        mode_layout.addWidget(self.mode_combo)
        mode_layout.addStretch()
        layout.addLayout(mode_layout)

    def _create_cap_type_control(self, layout):
        """Create CAP type selection control (visible only in circular mode)."""
        self.cap_type_layout = QHBoxLayout()
        self.cap_type_layout.addWidget(QLabel("CAP Type:"))
        self.cap_type_combo = QComboBox()
        self.cap_type_combo.addItems(
            [
                "Strict Rotated",
                "Strict Mirrored",
                "Strict Swapped",
                "Strict Complementary",
                "Mirrored Swapped",
                "Swapped Complementary",
                "Rotated Complementary",
                "Mirrored Complementary",
                "Rotated Swapped",
                "Mirrored Rotated",
                "Mirrored Complementary Rotated",
            ]
        )
        self.cap_type_combo.setCurrentText("Strict Rotated")
        self.cap_type_combo.setObjectName("capTypeCombo")
        self.cap_type_combo.currentTextChanged.connect(self.parameter_changed.emit)
        self.cap_type_combo.currentTextChanged.connect(
            self._update_rotation_type_visibility
        )
        self.cap_type_layout.addWidget(self.cap_type_combo)
        self.cap_type_layout.addStretch()
        layout.addLayout(self.cap_type_layout)

    def _create_rotation_type_control(self, layout):
        """Create rotation type selection control (visible only when CAP type is strict_rotated)."""
        self.rotation_type_layout = QHBoxLayout()
        self.rotation_type_layout.addWidget(QLabel("Rotation Type:"))
        self.rotation_type_combo = QComboBox()
        self.rotation_type_combo.addItems(["Halved", "Quartered"])
        self.rotation_type_combo.setCurrentText("Halved")
        self.rotation_type_combo.setObjectName("rotationTypeCombo")
        self.rotation_type_combo.currentTextChanged.connect(self.parameter_changed.emit)
        self.rotation_type_layout.addWidget(self.rotation_type_combo)
        self.rotation_type_layout.addStretch()
        layout.addLayout(self.rotation_type_layout)

    def _create_continuity_control(self, layout):
        continuity_layout = QHBoxLayout()
        continuity_layout.addWidget(QLabel("Prop Continuity:"))
        self.continuity_combo = QComboBox()
        self.continuity_combo.addItems(["Continuous", "Random"])
        self.continuity_combo.setObjectName("continuityCombo")
        self.continuity_combo.currentTextChanged.connect(self.parameter_changed.emit)
        continuity_layout.addWidget(self.continuity_combo)
        continuity_layout.addStretch()
        layout.addLayout(continuity_layout)

    def _on_level_changed(self, level_text: str):
        level_num = int(level_text.split(" - ")[0])

        self.intensity_combo.clear()
        if level_num == 1:
            self.intensity_combo.addItems(["N/A"])
            self.intensity_combo.setEnabled(False)
        elif level_num == 2:
            self.intensity_combo.addItems(["1", "2", "3"])
            self.intensity_combo.setEnabled(True)
        elif level_num == 3:
            self.intensity_combo.addItems(["0.5", "1", "1.5", "2", "2.5", "3"])
            self.intensity_combo.setEnabled(True)

        self.level_changed.emit(level_text)

    def _update_cap_controls_visibility(self):
        """Update visibility of CAP-related controls based on generation mode."""
        is_circular = self.mode_combo.currentText().lower() == "circular"

        # Show/hide CAP type control based on mode
        for i in range(self.cap_type_layout.count()):
            widget = self.cap_type_layout.itemAt(i).widget()
            if widget:
                widget.setVisible(is_circular)

        # Update rotation type visibility based on both mode and CAP type
        self._update_rotation_type_visibility()

    def _update_rotation_type_visibility(self):
        """Update visibility of rotation type control based on CAP type selection."""
        is_circular = self.mode_combo.currentText().lower() == "circular"
        is_strict_rotated = self.cap_type_combo.currentText() == "Strict Rotated"
        show_rotation_type = is_circular and is_strict_rotated

        # Show/hide rotation type control
        for i in range(self.rotation_type_layout.count()):
            widget = self.rotation_type_layout.itemAt(i).widget()
            if widget:
                widget.setVisible(show_rotation_type)

    def _cap_type_to_internal(self, display_text: str) -> str:
        """Convert display text to internal CAP type string."""
        mapping = {
            "Strict Rotated": "strict_rotated",
            "Strict Mirrored": "strict_mirrored",
            "Strict Swapped": "strict_swapped",
            "Strict Complementary": "strict_complementary",
            "Mirrored Swapped": "mirrored_swapped",
            "Swapped Complementary": "swapped_complementary",
            "Rotated Complementary": "rotated_complementary",
            "Mirrored Complementary": "mirrored_complementary",
            "Rotated Swapped": "rotated_swapped",
            "Mirrored Rotated": "mirrored_rotated",
            "Mirrored Complementary Rotated": "mirrored_complementary_rotated",
        }
        return mapping.get(display_text, "strict_rotated")

    def get_generation_parameters(self) -> "GenerationParams":
        from ..generation_manager import GenerationParams

        level_text = self.level_combo.currentText()
        level = int(level_text.split(" - ")[0])

        if level == 1:
            turn_intensity = 0
        else:
            intensity_text = self.intensity_combo.currentText()
            turn_intensity = 0 if intensity_text == "N/A" else float(intensity_text)

        start_pos_text = self.start_pos_combo.currentText()
        start_position = None if start_pos_text == "Any" else start_pos_text.lower()

        # Get CAP type and rotation type from controls
        cap_type = self._cap_type_to_internal(self.cap_type_combo.currentText())
        rotation_type = self.rotation_type_combo.currentText().lower()

        return GenerationParams(
            length=int(self.length_combo.currentText()),
            level=level,
            turn_intensity=turn_intensity,
            prop_continuity=self.continuity_combo.currentText().lower(),
            generation_mode=self.mode_combo.currentText().lower(),
            rotation_type=rotation_type,
            CAP_type=cap_type,
            start_position=start_position,
        )

    def load_values(self, values: dict):
        self.start_pos_combo.setCurrentText(values.get("start_position", "Any"))
        self.length_combo.setCurrentText(values.get("length", "16"))
        self.level_combo.setCurrentText(values.get("level", "1 - Basic (No turns)"))
        self.intensity_combo.setCurrentText(values.get("turn_intensity", "1"))
        self.mode_combo.setCurrentText(values.get("generation_mode", "Freeform"))
        self.continuity_combo.setCurrentText(
            values.get("prop_continuity", "Continuous")
        )

    def get_current_values(self) -> dict:
        return {
            "start_position": self.start_pos_combo.currentText(),
            "length": self.length_combo.currentText(),
            "level": self.level_combo.currentText(),
            "turn_intensity": self.intensity_combo.currentText(),
            "generation_mode": self.mode_combo.currentText(),
            "prop_continuity": self.continuity_combo.currentText(),
        }
