from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QColor
import logging

from .generation_manager import GeneratedSequenceData


class SequenceCard(QFrame):
    status_changed = pyqtSignal(str, str)  # sequence_id, status

    def __init__(
        self,
        sequence_data: GeneratedSequenceData,
        card_width: int,
        card_height: int,
        image_width: int,
        image_height: int,
    ):
        super().__init__()
        self.sequence_data = sequence_data
        self.setObjectName("sequenceCard")
        self.setFixedSize(card_width, card_height)
        self.setup_ui(image_width, image_height)

    def setup_ui(self, image_width: int, image_height: int):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        self.image_label = QLabel()
        self.image_label.setFixedSize(image_width, image_height)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setObjectName("sequenceImage")
        self.image_label.setText("Loading...")
        self.image_label.setStyleSheet(
            """
            QLabel {
                background: rgba(0, 0, 0, 0.3);
                border: 2px dashed rgba(255, 255, 255, 0.3);
                border-radius: 8px;
                color: #e1e5e9;
                font-size: 12px;
                font-weight: bold;
            }
        """
        )
        layout.addWidget(self.image_label)

        info_label = QLabel()
        info_text = (
            f"<b>{self.sequence_data.word}</b><br>"
            f"Length: {self.sequence_data.params.length} beats<br>"
            f"Level: {self.sequence_data.params.level}<br>"
            f"Mode: {self.sequence_data.params.generation_mode.title()}<br>"
            f"Continuity: {self.sequence_data.params.prop_continuity.title()}"
        )
        info_label.setText(info_text)
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setObjectName("sequenceInfo")

        button_layout = QHBoxLayout()

        approve_btn = QPushButton("✓ Approve")
        approve_btn.setObjectName("approveButton")
        approve_btn.clicked.connect(
            lambda: self.status_changed.emit(self.sequence_data.id, "approved")
        )
        button_layout.addWidget(approve_btn)

        reject_btn = QPushButton("✗ Reject")
        reject_btn.setObjectName("rejectButton")
        reject_btn.clicked.connect(
            lambda: self.status_changed.emit(self.sequence_data.id, "rejected")
        )
        button_layout.addWidget(reject_btn)

        layout.addLayout(button_layout)

        self.status_label = QLabel("Pending")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setObjectName("statusLabel")
        layout.addWidget(self.status_label)

    def update_status(self, status: str):
        if status == "approved":
            self.status_label.setText("✓ Approved")
            self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            self.setStyleSheet(
                self.styleSheet()
                + """
                QFrame#sequenceCard {
                    border: 2px solid #4CAF50;
                    background: rgba(76, 175, 80, 0.1);
                }
            """
            )
        elif status == "rejected":
            self.status_label.setText("✗ Rejected")
            self.status_label.setStyleSheet("color: #F44336; font-weight: bold;")
            self.setStyleSheet(
                self.styleSheet()
                + """
                QFrame#sequenceCard {
                    border: 2px solid #F44336;
                    background: rgba(244, 67, 54, 0.1);
                }
            """
            )

    def set_image(self, pixmap: QPixmap):
        """Set image with thread safety and memory management."""
        try:
            logging.info(
                f"SequenceCard {self.sequence_data.id}: set_image called. Pixmap isNull: {pixmap.isNull()}, Size: {pixmap.size()}"
            )

            # Ensure we're on the main thread for UI updates
            from PyQt6.QtCore import QTimer
            from PyQt6.QtWidgets import QApplication

            if QApplication.instance().thread() != self.thread():
                # If called from a worker thread, use QTimer to invoke on main thread
                QTimer.singleShot(0, lambda: self._set_image_main_thread(pixmap))
                return

            self._set_image_main_thread(pixmap)

        except Exception as e:
            logging.error(
                f"SequenceCard {self.sequence_data.id}: Exception in set_image: {e}"
            )
            import traceback

            traceback.print_exc()
            try:
                self.image_label.setText("Error")
            except:
                pass  # Even setting error text failed

    def _set_image_main_thread(self, pixmap: QPixmap):
        """Internal method to set image on main thread with enhanced crash protection."""
        sequence_id = getattr(self.sequence_data, "id", "unknown")

        try:
            # Enhanced validation with detailed logging
            if not pixmap or pixmap.isNull():
                logging.error(
                    f"SequenceCard {sequence_id}: Received null or invalid pixmap"
                )
                self._set_error_state("Invalid Image")
                return

            # Validate widget state before proceeding
            if not self._validate_widget_state():
                logging.error(f"SequenceCard {sequence_id}: Widget validation failed")
                return

            # Get and validate label size with fallbacks
            label_size = self._get_safe_label_size(pixmap)
            if label_size.width() <= 0 or label_size.height() <= 0:
                logging.error(
                    f"SequenceCard {sequence_id}: Could not determine valid label size"
                )
                self._set_error_state("Size Error")
                return

            # Perform safe scaling with memory limits
            scaled_pixmap = self._safe_scale_pixmap(pixmap, label_size, sequence_id)
            if not scaled_pixmap or scaled_pixmap.isNull():
                logging.error(f"SequenceCard {sequence_id}: Scaling failed")
                self._set_error_state("Scaling Error")
                return

            # Final safety check before setting pixmap
            if not self._validate_widget_state():
                logging.error(
                    f"SequenceCard {sequence_id}: Widget became invalid during processing"
                )
                return

            # Set the pixmap with additional safety
            self.image_label.setPixmap(scaled_pixmap)
            self.image_label.setStyleSheet("")

            logging.info(
                f"SequenceCard {sequence_id}: Successfully set image {scaled_pixmap.size()}"
            )

        except Exception as e:
            logging.error(
                f"SequenceCard {sequence_id}: Critical exception in _set_image_main_thread: {e}"
            )
            import traceback

            traceback.print_exc()
            self._set_error_state("Critical Error")

    def set_image_error(self, error_message: str):
        """Set error state with comprehensive error protection"""
        try:
            if not hasattr(self, "image_label") or self.image_label is None:
                logging.warning(
                    f"SequenceCard {getattr(self.sequence_data, 'id', 'unknown')}: No image label available for error state"
                )
                return

            # Truncate long error messages to prevent UI issues
            display_message = (
                error_message[:100] + "..."
                if len(error_message) > 100
                else error_message
            )

            self.image_label.setText(f"Image failed\n{display_message}")
            self.image_label.setStyleSheet(
                """
                QLabel {
                    background: rgba(244, 67, 54, 0.2);
                    border: 2px solid rgba(244, 67, 54, 0.5);
                    border-radius: 8px;
                    color: #F44336;
                    font-size: 10px;
                    font-weight: bold;
                    padding: 5px;
                }
            """
            )
            logging.info(
                f"SequenceCard {getattr(self.sequence_data, 'id', 'unknown')}: Error state set - {display_message}"
            )

        except Exception as e:
            logging.error(
                f"SequenceCard {getattr(self.sequence_data, 'id', 'unknown')}: Failed to set error state: {e}"
            )
            # Last resort - try to set basic text
            try:
                if hasattr(self, "image_label") and self.image_label is not None:
                    self.image_label.setText("Error")
            except:
                pass  # Even basic error text failed

    def _safe_scale_pixmap(
        self, pixmap: QPixmap, target_size, sequence_id: str
    ) -> QPixmap:
        """Safely scale pixmap with memory and error protection."""
        try:
            if not pixmap or pixmap.isNull():
                logging.warning(f"SequenceCard {sequence_id}: Cannot scale null pixmap")
                return QPixmap()

            # Check if scaling is needed
            current_size = pixmap.size()
            if (
                current_size.width() <= target_size.width()
                and current_size.height() <= target_size.height()
            ):
                logging.debug(f"SequenceCard {sequence_id}: No scaling needed")
                return pixmap

            # Perform safe scaling with memory protection
            max_memory_dimension = 2048  # Limit to prevent excessive memory usage

            if (
                pixmap.width() > max_memory_dimension
                or pixmap.height() > max_memory_dimension
            ):
                # Pre-scale to manageable size first
                scale_factor = min(
                    max_memory_dimension / pixmap.width(),
                    max_memory_dimension / pixmap.height(),
                )
                intermediate_size = QSize(
                    int(pixmap.width() * scale_factor),
                    int(pixmap.height() * scale_factor),
                )
                pixmap = pixmap.scaled(
                    intermediate_size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                logging.debug(
                    f"SequenceCard {sequence_id}: Pre-scaled to {intermediate_size}"
                )

            # Final scaling to target size
            scaled_pixmap = pixmap.scaled(
                target_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

            logging.debug(
                f"SequenceCard {sequence_id}: Final scaled to {scaled_pixmap.size()}"
            )
            return scaled_pixmap

        except Exception as e:
            logging.error(f"SequenceCard {sequence_id}: Error scaling pixmap: {e}")
            # Return a minimal error pixmap
            try:
                error_pixmap = QPixmap(target_size)
                error_pixmap.fill(QColor(244, 67, 54, 50))
                return error_pixmap
            except:
                return QPixmap()

    def _validate_widget_state(self) -> bool:
        """Validate that the widget is in a safe state for image operations."""
        try:
            # Check if widget still exists and is valid
            if not hasattr(self, "image_label"):
                logging.warning("Widget missing image_label attribute")
                return False

            if self.image_label is None:
                logging.warning("Image label is None")
                return False

            # Check if widget is still accessible (not deleted)
            try:
                _ = self.image_label.size()
            except RuntimeError as e:
                logging.warning(f"Widget no longer accessible: {e}")
                return False

            # Check if parent widget chain is still valid
            parent = self.parent()
            if parent is None:
                logging.warning("Widget has no parent")
                return False

            return True
        except Exception as e:
            logging.warning(f"Widget state validation failed: {e}")
            return False

    def _get_safe_label_size(self, pixmap: QPixmap):
        """Get a safe label size with multiple fallback strategies."""
        try:
            # Primary: Use actual label size
            if hasattr(self, "image_label") and self.image_label is not None:
                try:
                    label_size = self.image_label.size()
                    if label_size.width() > 0 and label_size.height() > 0:
                        return label_size
                except RuntimeError:
                    pass  # Widget deleted

            # Fallback 1: Use parent widget size
            try:
                if self.parent():
                    parent_size = self.parent().size()
                    margin = 20  # Leave some margin
                    return QSize(
                        max(100, parent_size.width() - margin),
                        max(100, parent_size.height() - margin),
                    )
            except:
                pass

            # Fallback 2: Use pixmap size with reasonable limits
            if pixmap and not pixmap.isNull():
                pixmap_size = pixmap.size()
                max_size = 400  # Reasonable maximum
                return QSize(
                    min(pixmap_size.width(), max_size),
                    min(pixmap_size.height(), max_size),
                )

            # Final fallback: Use default size
            return QSize(300, 200)

        except Exception as e:
            logging.warning(f"Error getting safe label size: {e}")
            return QSize(300, 200)

    def force_error_state(self, message: str = "Generation Failed"):
        """Force the card into error state (used by image manager for fallbacks)"""
        try:
            self.set_image_error(message)
        except Exception as e:
            logging.error(
                f"SequenceCard {getattr(self.sequence_data, 'id', 'unknown')}: Failed to force error state: {e}"
            )

    def is_in_error_state(self) -> bool:
        """Check if the card is currently in an error state"""
        try:
            if hasattr(self, "image_label") and self.image_label is not None:
                text = self.image_label.text()
                return text.startswith("Error") or text.startswith("Image failed")
        except:
            pass
        return False

    def reset_to_loading_state(self):
        """Reset the card to loading state (useful for retries)"""
        try:
            if hasattr(self, "image_label") and self.image_label is not None:
                self.image_label.setText("Loading...")
                self.image_label.setStyleSheet(
                    """
                    QLabel {
                        background: rgba(0, 0, 0, 0.3);
                        border: 2px dashed rgba(255, 255, 255, 0.3);
                        border-radius: 8px;
                        color: #e1e5e9;
                        font-size: 12px;
                        font-weight: bold;
                        padding: 5px;
                    }
                """
                )
        except Exception as e:
            logging.error(
                f"SequenceCard {getattr(self.sequence_data, 'id', 'unknown')}: Failed to reset to loading state: {e}"
            )
