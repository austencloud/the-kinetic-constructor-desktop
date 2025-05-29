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
        self._create_continuity_control(layout)

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
        mode_layout.addWidget(self.mode_combo)
        mode_layout.addStretch()
        layout.addLayout(mode_layout)

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

        return GenerationParams(
            length=int(self.length_combo.currentText()),
            level=level,
            turn_intensity=turn_intensity,
            prop_continuity=self.continuity_combo.currentText().lower(),
            generation_mode=self.mode_combo.currentText().lower(),
            rotation_type="halved",
            CAP_type="strict_rotated",
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
