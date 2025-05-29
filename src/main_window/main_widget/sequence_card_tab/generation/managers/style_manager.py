from PyQt6.QtWidgets import QWidget


class StyleManager:
    @staticmethod
    def apply_generation_controls_styling(widget: QWidget):
        widget.setStyleSheet(
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
        widget.setObjectName("generationControlsPanel")
