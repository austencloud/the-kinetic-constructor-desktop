from PyQt6.QtWidgets import QWidget


class SidebarStyler:
    @staticmethod
    def apply_modern_styling(widget: QWidget):
        widget.setStyleSheet(
            """
            /* Widget container - override default gray background */
            QWidget {
                background: transparent;
            }

            /* Main container */
            SequenceCardNavSidebar {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(71, 85, 105, 0.4), stop:1 rgba(51, 65, 85, 0.6));
                border-radius: 12px;
                border: 1px solid rgba(100, 116, 139, 0.3);
                padding: 10px;
            }

            /* Header styling */
            QFrame#headerFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(71, 85, 105, 0.5), stop:1 rgba(51, 65, 85, 0.7));
                border-radius: 10px;
                border: 1px solid rgba(100, 116, 139, 0.4);
            }

            QLabel#headerTitle {
                color: #f8fafc;
                font-size: 16px;
                font-weight: bold;
                letter-spacing: 0.5px;
            }

            QLabel#headerSubtitle {
                color: #cbd5e1;
                font-size: 12px;
                font-style: italic;
            }

            /* Scroll area */
            QScrollArea#lengthScrollArea {
                background: transparent;
                border: none;
            }

            QScrollArea#lengthScrollArea QScrollBar:vertical {
                background: rgba(15, 23, 42, 0.2);
                width: 8px;
                border-radius: 4px;
                margin: 2px;
            }

            QScrollArea#lengthScrollArea QScrollBar::handle:vertical {
                background: rgba(100, 116, 139, 0.5);
                border-radius: 4px;
                min-height: 20px;
            }

            QScrollArea#lengthScrollArea QScrollBar::handle:vertical:hover {
                background: rgba(100, 116, 139, 0.8);
            }

            QScrollArea#lengthScrollArea QScrollBar::add-line:vertical,
            QScrollArea#lengthScrollArea QScrollBar::sub-line:vertical {
                height: 0px;
            }

            QScrollArea#lengthScrollArea QScrollBar::add-page:vertical,
            QScrollArea#lengthScrollArea QScrollBar::sub-page:vertical {
                background: none;
            }

            /* Length option frames - unselected */
            QFrame[objectName^="lengthFrame_"]:!QFrame[objectName$="_selected"] {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(71, 85, 105, 0.3), stop:1 rgba(51, 65, 85, 0.5));
                border: 1px solid rgba(100, 116, 139, 0.4);
                border-radius: 10px;
                margin: 3px;
            }

            QFrame[objectName^="lengthFrame_"]:hover:!QFrame[objectName$="_selected"] {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(100, 116, 139, 0.4), stop:1 rgba(71, 85, 105, 0.6));
                border: 1px solid rgba(148, 163, 184, 0.5);
            }

            /* Length option frames - selected */
            QFrame[objectName$="_selected"] {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3b82f6, stop:1 #2563eb);
                border: 1px solid #60a5fa;
                border-radius: 10px;
                margin: 3px;
            }

            QFrame[objectName$="_selected"]:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #60a5fa, stop:1 #3b82f6);
                border: 1px solid #93c5fd;
            }

            /* Length labels */
            QLabel#lengthLabel {
                color: #f8fafc;
                font-size: 15px;
                font-weight: 600;
                letter-spacing: 0.5px;
            }

            /* Separator */
            QFrame#separator {
                background-color: #475569;
                max-height: 1px;
                margin: 8px 0px;
            }

            /* Column selector frame */
            QFrame#columnFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(71, 85, 105, 0.3), stop:1 rgba(51, 65, 85, 0.5));
                border-radius: 10px;
                border: 1px solid rgba(100, 116, 139, 0.4);
                margin-top: 8px;
            }

            QLabel#columnLabel {
                color: #f8fafc;
                font-size: 14px;
                font-weight: 600;
                letter-spacing: 0.5px;
            }

            /* Column dropdown */
            QComboBox#columnDropdown {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #475569, stop:1 #334155);
                color: #f8fafc;
                border: 1px solid #64748b;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 13px;
                min-height: 28px;
                selection-background-color: #3b82f6;
            }

            QComboBox#columnDropdown:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #64748b, stop:1 #475569);
                border: 1px solid #94a3b8;
            }

            QComboBox#columnDropdown:focus {
                border: 1px solid #60a5fa;
            }

            QComboBox#columnDropdown::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left-width: 1px;
                border-left-color: #64748b;
                border-left-style: solid;
                border-top-right-radius: 6px;
                border-bottom-right-radius: 6px;
            }

            /* Apply button */
            QPushButton#applyButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3b82f6, stop:1 #2563eb);
                color: #f8fafc;
                border: 1px solid #60a5fa;
                border-radius: 6px;
                padding: 6px 16px;
                font-size: 13px;
                font-weight: bold;
                min-height: 28px;
            }

            QPushButton#applyButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #60a5fa, stop:1 #3b82f6);
                border: 1px solid #93c5fd;
            }

            QPushButton#applyButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2563eb, stop:1 #1d4ed8);
                border: 1px solid #3b82f6;
                padding-top: 7px;
                padding-bottom: 5px;
            }
        """
        )
