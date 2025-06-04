from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QComboBox,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCursor


class GenerationActionManager(QWidget):
    generate_requested = pyqtSignal(object, int)
    clear_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.create_action_controls()

    def create_action_controls(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        self._create_batch_size_control(layout)
        self._create_generate_button(layout)
        self._create_clear_button(layout)

    def _create_batch_size_control(self, layout):
        batch_layout = QHBoxLayout()
        batch_layout.addWidget(QLabel("Generate:"))
        self.batch_size_combo = QComboBox()
        self.batch_size_combo.addItems(["5", "10", "15", "30"])
        self.batch_size_combo.setCurrentText("10")
        self.batch_size_combo.setObjectName("batchSizeCombo")
        batch_layout.addWidget(self.batch_size_combo)
        batch_layout.addWidget(QLabel("sequences"))
        batch_layout.addStretch()
        layout.addLayout(batch_layout)

    def _create_generate_button(self, layout):
        self.generate_button = QPushButton("Generate Sequences")
        self.generate_button.setObjectName("generateButton")
        self.generate_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.generate_button.clicked.connect(self._on_generate_clicked)
        layout.addWidget(self.generate_button)

    def _create_clear_button(self, layout):
        self.clear_button = QPushButton("Clear Generated")
        self.clear_button.setObjectName("clearButton")
        self.clear_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.clear_button.clicked.connect(self.clear_requested.emit)
        layout.addWidget(self.clear_button)

    def _on_generate_clicked(self):
        params = self.get_generation_parameters()
        batch_size = int(self.batch_size_combo.currentText())
        self.generate_requested.emit(params, batch_size)

    def set_generation_enabled(self, enabled: bool):
        self.generate_button.setEnabled(enabled)
        if enabled:
            self.generate_button.setText("Generate Sequences")
        else:
            self.generate_button.setText("Generating...")

    def get_batch_size(self) -> int:
        return int(self.batch_size_combo.currentText())

    def load_batch_size(self, batch_size: str):
        self.batch_size_combo.setCurrentText(batch_size)

    def get_current_batch_size(self) -> str:
        return self.batch_size_combo.currentText()

    def set_parameter_provider(self, provider):
        self.parameter_provider = provider

    def get_generation_parameters(self):
        if hasattr(self, "parameter_provider") and self.parameter_provider:
            return self.parameter_provider.get_generation_parameters()
        return None
