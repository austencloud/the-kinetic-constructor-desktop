from PyQt6.QtWidgets import QDialog, QLabel, QVBoxLayout, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class BrowseTabDeleteConfirmationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Delete Variation")
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
        self.setFixedSize(300, 150)
        self.setModal(True)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Create and style the label
        label = QLabel("Are you sure you want to delete this variation?")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setWordWrap(True)
        label_font = QFont("Georgia", 11, QFont.Weight.Bold)
        label.setFont(label_font)

        # Create and style the buttons
        button_layout = QHBoxLayout()

        yes_button = QPushButton("Yes")
        yes_button.setFixedSize(100, 40)
        yes_button.clicked.connect(self.accept)
        yes_button.setStyleSheet(
            """
            QPushButton {
                background-color: #d9534f;
                color: white;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #c9302c;
            }
            """
        )

        no_button = QPushButton("No")
        no_button.setFixedSize(100, 40)
        no_button.clicked.connect(self.reject)
        no_button.setStyleSheet(
            """
            QPushButton {
                background-color: #5bc0de;
                color: white;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #31b0d5;
            }
            """
        )

        button_layout.addWidget(yes_button)
        button_layout.addWidget(no_button)

        # Add widgets to the layout
        layout.addWidget(label)
        layout.addStretch(1)  # Add stretch to push buttons to the bottom
        layout.addLayout(button_layout)
