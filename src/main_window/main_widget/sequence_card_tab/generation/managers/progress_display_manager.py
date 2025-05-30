from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar, QFrame
from PyQt6.QtCore import Qt


class ProgressDisplayManager(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.create_progress_ui()
        self.setVisible(False)

    def create_progress_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        self.progress_label = QLabel("Generating sequences...")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("generationProgressBar")
        layout.addWidget(self.progress_bar)

    def show_progress(self, current: int, total: int):
        self.setVisible(True)
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.progress_label.setText(f"Generating sequences... ({current}/{total})")

    def hide_progress(self):
        self.setVisible(False)

    def set_progress_text(self, text: str):
        self.progress_label.setText(text)
