class ApprovalDialogStyleManager:
    @staticmethod
    def apply_styling(dialog):
        dialog.setStyleSheet(
            """
            QDialog {
                background: #2d3748;
                color: #e1e5e9;
            }

            QLabel#titleLabel {
                color: #e1e5e9;
                font-weight: bold;
                font-size: 16px;
            }

            QLabel#controlLabel {
                color: #e1e5e9;
                font-size: 12px;
                font-weight: 500;
            }

            QSpinBox#columnsSpinBox {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 4px;
                color: #e1e5e9;
                padding: 4px 8px;
                font-size: 12px;
                min-width: 60px;
            }

            QSpinBox#columnsSpinBox:hover {
                background: rgba(255, 255, 255, 0.15);
                border-color: rgba(255, 255, 255, 0.3);
            }

            QProgressBar#progressBar {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 4px;
                text-align: center;
                color: #e1e5e9;
                font-size: 11px;
                min-width: 200px;
                max-height: 20px;
            }

            QProgressBar#progressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4CAF50, stop:1 #66BB6A);
                border-radius: 3px;
            }

            QFrame#sequenceCard {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 12px;
            }

            QFrame#sequenceCard:hover {
                background: rgba(255, 255, 255, 0.15);
                border: 1px solid rgba(255, 255, 255, 0.3);
            }

            QLabel#sequenceImage {
                background: rgba(0, 0, 0, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
            }

            QLabel#sequenceInfo {
                color: #e1e5e9;
                font-size: 11px;
                background: transparent;
                border: none;
                padding: 5px;
            }

            QPushButton#approveButton {
                background: #38a169;
                border: none;
                border-radius: 6px;
                color: white;
                font-weight: 600;
                padding: 8px 16px;
                font-size: 11px;
            }

            QPushButton#approveButton:hover {
                background: #2f855a;
            }

            QPushButton#rejectButton {
                background: #e53e3e;
                border: none;
                border-radius: 6px;
                color: white;
                font-weight: 600;
                padding: 8px 16px;
                font-size: 11px;
            }

            QPushButton#rejectButton:hover {
                background: #c53030;
            }

            QPushButton#approveAllButton {
                background: #38a169;
                border: none;
                border-radius: 6px;
                color: white;
                font-weight: 600;
                padding: 10px 20px;
                font-size: 12px;
            }

            QPushButton#approveAllButton:hover {
                background: #2f855a;
            }

            QPushButton#rejectAllButton {
                background: #e53e3e;
                border: none;
                border-radius: 6px;
                color: white;
                font-weight: 600;
                padding: 10px 20px;
                font-size: 12px;
            }

            QPushButton#rejectAllButton:hover {
                background: #c53030;
            }

            QPushButton#cancelButton, QPushButton#finishButton {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                color: #e1e5e9;
                font-weight: 500;
                padding: 10px 20px;
                font-size: 12px;
            }

            QPushButton#cancelButton:hover, QPushButton#finishButton:hover {
                background: rgba(255, 255, 255, 0.15);
                border-color: rgba(255, 255, 255, 0.3);
            }

            QLabel#statusLabel {
                color: #a0aec0;
                font-size: 10px;
                font-weight: bold;
            }
            """
        )
