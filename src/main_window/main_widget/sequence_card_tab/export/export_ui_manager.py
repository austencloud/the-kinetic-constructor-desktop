# src/main_window/main_widget/sequence_card_tab/export/export_ui_manager.py
import os
import logging
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from PyQt6.QtWidgets import (
    QFileDialog,
    QMessageBox,
    QProgressDialog,
    QApplication,
)
from PyQt6.QtCore import Qt

from utils.path_helpers import get_user_editable_resource_path, get_win32_photos_path
from .export_folder_naming_service import ExportFolderNamingService, SequenceCardMode

if TYPE_CHECKING:
    from ..tab import SequenceCardTab


class ExportUIManager:
    """
    Manages UI interactions for sequence card page exports.

    This class handles:
    1. File dialogs for selecting export directories
    2. Progress dialogs for showing export progress
    3. Message boxes for error and success notifications
    4. Cancellation handling
    """

    def __init__(self, sequence_card_tab: "SequenceCardTab"):
        self.sequence_card_tab = sequence_card_tab
        self.logger = logging.getLogger(__name__)
        self.progress_dialog: Optional[QProgressDialog] = None
        self.cancel_requested = False
        self.folder_naming_service = ExportFolderNamingService()

    def get_export_directory(self) -> Optional[str]:
        """
        Show a file dialog to select an export directory.

        Returns:
            Optional[str]: Selected directory path or None if cancelled
        """
        self.logger.debug("Showing export directory dialog")

        # Try to get the last used export directory from settings
        try:
            import json

            settings_path = get_user_editable_resource_path("export_settings.json")
            default_dir = None

            if os.path.exists(settings_path):
                with open(settings_path, "r") as f:
                    settings = json.load(f)
                    default_dir = os.path.join(
                        get_win32_photos_path(), "TKA Sequence Cards"
                    )

            # If no saved directory or it doesn't exist, use My Pictures/TKA Sequence Cards
            if not default_dir or not os.path.exists(default_dir):
                os.makedirs(default_dir, exist_ok=True)

        except Exception as e:
            self.logger.warning(f"Could not load export settings: {e}")
            # Fallback to a basic default
            default_dir = os.path.expanduser("~/Pictures")

        # Show the directory selection dialog
        export_dir = QFileDialog.getExistingDirectory(
            self.sequence_card_tab,
            "Select Export Directory",
            default_dir,
            QFileDialog.Option.ShowDirsOnly,
        )

        if not export_dir:
            self.logger.debug("Export directory selection cancelled")
            return None

        # Save the selected directory for next time
        try:
            settings = {"last_export_directory": export_dir}
            with open(settings_path, "w") as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            self.logger.warning(f"Could not save export settings: {e}")

        self.logger.info(f"Selected export directory: {export_dir}")
        return export_dir

    def create_export_subdirectory(
        self,
        export_dir: str,
        selected_length: Optional[int] = None,
        selected_levels: Optional[List[int]] = None,
        sequence_count: Optional[int] = None,
    ) -> str:
        """
        Create a descriptively named subdirectory for this export.

        Args:
            export_dir: Base export directory
            selected_length: Selected sequence length (None for all lengths)
            selected_levels: Selected difficulty levels (None for all levels)
            sequence_count: Total number of sequences being exported

        Returns:
            str: Path to the created subdirectory
        """
        # Determine the export mode from the current tab state
        mode = self._determine_export_mode()

        # Get generated sequence batch info if applicable
        generated_batch_info = (
            self._get_generated_batch_info()
            if mode == SequenceCardMode.GENERATION
            else None
        )

        # Generate the descriptive folder name
        folder_name = self.folder_naming_service.generate_folder_name(
            selected_length=selected_length,
            selected_levels=selected_levels,
            mode=mode,
            sequence_count=sequence_count,
            generated_batch_info=generated_batch_info,
        )

        # Create the full path
        export_subdir = os.path.join(export_dir, folder_name)

        # Ensure the folder name doesn't exceed file system limits
        if len(export_subdir) > 260:  # Windows path limit
            # Fallback to shorter name
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            length_text = (
                f"{selected_length}-count"
                if selected_length and selected_length > 0
                else "all"
            )
            fallback_name = f"sequence_cards_{length_text}_{timestamp}"
            export_subdir = os.path.join(export_dir, fallback_name)
            self.logger.warning(f"Path too long, using fallback name: {fallback_name}")

        # Create the subdirectory
        os.makedirs(export_subdir, exist_ok=True)
        self.logger.info(f"Created export subdirectory: {export_subdir}")

        return export_subdir

    def _determine_export_mode(self) -> SequenceCardMode:
        """
        Determine the current export mode based on the sequence card tab state.

        Returns:
            SequenceCardMode: The current mode (dictionary, generation, or mixed)
        """
        try:
            # Check if the tab has a mode manager
            if (
                hasattr(self.sequence_card_tab, "mode_manager")
                and self.sequence_card_tab.mode_manager
            ):
                current_mode = self.sequence_card_tab.mode_manager.current_mode

                # Convert to our naming service enum
                if hasattr(current_mode, "value"):
                    mode_value = current_mode.value
                elif hasattr(current_mode, "name"):
                    mode_value = current_mode.name.lower()
                else:
                    mode_value = str(current_mode).lower()

                if "dictionary" in mode_value:
                    return SequenceCardMode.DICTIONARY
                elif "generation" in mode_value:
                    return SequenceCardMode.GENERATION
                else:
                    return SequenceCardMode.MIXED

            # Fallback: try to determine mode from displayed sequences
            return self._infer_mode_from_sequences()

        except Exception as e:
            self.logger.warning(f"Could not determine export mode: {e}")
            return SequenceCardMode.MIXED

    def _infer_mode_from_sequences(self) -> SequenceCardMode:
        """
        Infer the export mode by analyzing the currently displayed sequences.

        Returns:
            SequenceCardMode: Inferred mode based on sequence types
        """
        try:
            # Check if we have access to the displayed sequences
            if hasattr(self.sequence_card_tab, "printable_displayer"):
                displayer = self.sequence_card_tab.printable_displayer

                if hasattr(displayer, "manager") and hasattr(
                    displayer.manager, "sequence_processor"
                ):
                    processor = displayer.manager.sequence_processor

                    # Check the last used mode in the processor if available
                    if hasattr(processor, "_last_used_mode"):
                        return processor._last_used_mode

            # Check if there's a generated sequence store with active sequences
            if (
                hasattr(self.sequence_card_tab, "generated_sequence_store")
                and self.sequence_card_tab.generated_sequence_store
                and self.sequence_card_tab.generated_sequence_store.get_sequence_count()
                > 0
            ):
                return SequenceCardMode.GENERATION

            # Default to dictionary mode
            return SequenceCardMode.DICTIONARY

        except Exception as e:
            self.logger.warning(f"Could not infer mode from sequences: {e}")
            return SequenceCardMode.MIXED

    def _get_generated_batch_info(self) -> Optional[dict]:
        """
        Get batch information for generated sequences if available.

        Returns:
            Optional[dict]: Batch information or None if not available
        """
        try:
            if (
                hasattr(self.sequence_card_tab, "generated_sequence_store")
                and self.sequence_card_tab.generated_sequence_store
            ):

                store = self.sequence_card_tab.generated_sequence_store

                # Get summary of the current store
                summary = (
                    store.get_store_summary()
                    if hasattr(store, "get_store_summary")
                    else {}
                )

                # Get all sequences to analyze batch patterns
                sequences = (
                    store.get_all_sequences()
                    if hasattr(store, "get_all_sequences")
                    else []
                )

                if sequences:
                    # Try to determine batch information from the most recent sequences
                    latest_sequence = sequences[-1] if sequences else None

                    batch_info = {
                        "generation_mode": "freeform",  # Default
                        "total_sequences": len(sequences),
                        "generation_timestamp": datetime.now().isoformat(),
                    }

                    # Extract information from the latest sequence if available
                    if latest_sequence and hasattr(latest_sequence, "params"):
                        params = latest_sequence.params
                        if hasattr(params, "generation_mode"):
                            batch_info["generation_mode"] = params.generation_mode

                    # Try to create a batch identifier based on the generation time
                    # Use the current time as a simple batch identifier
                    batch_info["batch_id"] = datetime.now().strftime("%H%M")

                    return batch_info

            return None

        except Exception as e:
            self.logger.warning(f"Could not get generated batch info: {e}")
            return None

    def create_progress_dialog(
        self, total_items: int, item_type: str = "images"
    ) -> QProgressDialog:
        """
        Create a modern glassmorphism-styled progress dialog for the export process.

        Args:
            total_items: Total number of items to process (images, not pages)
            item_type: Type of items being processed (e.g., "images", "pages")

        Returns:
            QProgressDialog: The created progress dialog with modern styling
        """
        self.logger.debug(f"Creating progress dialog for {total_items} {item_type}")

        # Reset cancellation flag
        self.cancel_requested = False

        # Create the progress dialog with modern styling
        progress = QProgressDialog(
            f"Preparing to process {item_type}...",  # labelText
            "Cancel",  # cancelButtonText
            0,  # minimum
            total_items,  # maximum
            self.sequence_card_tab,  # parent
        )

        # Configure dialog properties
        progress.setWindowTitle("Exporting Sequence Card Pages")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)  # Show immediately
        progress.setAutoClose(True)
        progress.setAutoReset(True)

        # Make dialog draggable and closeable
        progress.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowCloseButtonHint
        )

        # Set responsive dimensions
        self._apply_responsive_dialog_size(progress)

        # Apply modern glassmorphism styling
        self._apply_glassmorphism_styling(progress)

        # Set progress format for fine-grained tracking
        progress.setLabelText(f"Processing {item_type} %v of %m...")

        # Connect the cancel button
        progress.canceled.connect(self.handle_cancel_request)

        # Store the progress dialog
        self.progress_dialog = progress

        return progress

    def _apply_responsive_dialog_size(self, dialog: QProgressDialog) -> None:
        """Apply responsive sizing to dialog based on parent window."""
        try:
            # Get parent window dimensions
            if self.sequence_card_tab and hasattr(self.sequence_card_tab, "width"):
                parent_width = self.sequence_card_tab.width()
                parent_height = self.sequence_card_tab.height()
            else:
                parent_width = 800
                parent_height = 600

            # Calculate responsive dialog size (2:1 width-to-height ratio)
            dialog_width = max(400, min(800, parent_width * 0.6))
            dialog_height = max(200, min(300, dialog_width * 0.4))

            dialog.setMinimumSize(int(dialog_width), int(dialog_height))
            dialog.resize(int(dialog_width), int(dialog_height))

            # Center on parent
            if self.sequence_card_tab:
                parent_rect = self.sequence_card_tab.geometry()
                dialog.move(
                    parent_rect.center().x() - dialog.width() // 2,
                    parent_rect.center().y() - dialog.height() // 2,
                )

        except Exception as e:
            self.logger.warning(f"Failed to apply responsive sizing: {e}")
            # Fallback to fixed size
            dialog.setMinimumSize(400, 200)
            dialog.resize(500, 250)

    def _apply_glassmorphism_styling(self, dialog: QProgressDialog) -> None:
        """Apply modern glassmorphism styling to the dialog."""
        try:
            # Calculate responsive font sizes
            dialog_width = dialog.width()
            title_font_size = max(14, min(18, dialog_width // 35))
            text_font_size = max(11, min(14, dialog_width // 45))

            # Modern glassmorphism styling
            glassmorphism_style = f"""
            QProgressDialog {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(52, 73, 94, 0.9),
                    stop:1 rgba(44, 62, 80, 0.9));
                border: 2px solid rgba(255, 255, 255, 0.3);
                border-radius: 20px;
                color: #ffffff;
                font-size: {text_font_size}px;
                font-weight: 500;
            }}

            QProgressDialog QLabel {{
                color: #ffffff;
                font-size: {text_font_size}px;
                font-weight: 500;
                padding: 10px;
                background: transparent;
                border: none;
            }}

            QProgressDialog QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(74, 144, 226, 0.9),
                    stop:1 rgba(52, 152, 219, 0.9));
                border: 1px solid rgba(255, 255, 255, 0.4);
                border-radius: 12px;
                color: #ffffff;
                font-size: {text_font_size}px;
                font-weight: 600;
                padding: 8px 16px;
                min-width: 80px;
                min-height: 32px;
            }}

            QProgressDialog QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(93, 173, 226, 0.9),
                    stop:1 rgba(74, 144, 226, 0.9));
                border: 1px solid rgba(255, 255, 255, 0.6);
            }}

            QProgressDialog QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(41, 128, 185, 0.9),
                    stop:1 rgba(52, 152, 219, 0.9));
                border: 1px solid rgba(255, 255, 255, 0.3);
            }}

            QProgressBar {{
                border: none;
                border-radius: 10px;
                text-align: center;
                background: rgba(255, 255, 255, 0.2);
                color: #ffffff;
                font-size: {text_font_size}px;
                font-weight: 600;
                min-height: 20px;
                margin: 5px;
            }}

            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(46, 204, 113, 0.9),
                    stop:0.5 rgba(52, 152, 219, 0.9),
                    stop:1 rgba(155, 89, 182, 0.9));
                border-radius: 10px;
                margin: 1px;
            }}
            """

            dialog.setStyleSheet(glassmorphism_style)

            # Apply shadow effect (if supported by the platform)
            try:
                from PyQt6.QtWidgets import QGraphicsDropShadowEffect
                from PyQt6.QtGui import QColor

                shadow = QGraphicsDropShadowEffect()
                shadow.setBlurRadius(32)
                shadow.setColor(QColor(0, 0, 0, 77))  # 30% opacity
                shadow.setOffset(0, 8)
                dialog.setGraphicsEffect(shadow)

            except ImportError:
                # Shadow effects not available, continue without them
                pass

        except Exception as e:
            self.logger.warning(f"Failed to apply glassmorphism styling: {e}")

    def _apply_message_box_styling(self, msg_box: QMessageBox, msg_type: str) -> None:
        """Apply modern glassmorphism styling to message boxes."""
        try:
            # Set responsive size
            msg_box.setMinimumSize(350, 150)
            msg_box.resize(450, 200)

            # Color scheme based on message type
            if msg_type == "error":
                accent_color = "rgba(231, 76, 60, 0.9)"
                accent_hover = "rgba(192, 57, 43, 0.9)"
            elif msg_type == "warning":
                accent_color = "rgba(243, 156, 18, 0.9)"
                accent_hover = "rgba(211, 84, 0, 0.9)"
            else:  # info
                accent_color = "rgba(52, 152, 219, 0.9)"
                accent_hover = "rgba(41, 128, 185, 0.9)"

            # Calculate responsive font size
            dialog_width = msg_box.width()
            text_font_size = max(11, min(14, dialog_width // 40))

            glassmorphism_style = f"""
            QMessageBox {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(52, 73, 94, 0.9),
                    stop:1 rgba(44, 62, 80, 0.9));
                border: 2px solid rgba(255, 255, 255, 0.3);
                border-radius: 20px;
                color: #ffffff;
                font-size: {text_font_size}px;
                font-weight: 500;
            }}

            QMessageBox QLabel {{
                color: #ffffff;
                font-size: {text_font_size}px;
                font-weight: 500;
                padding: 15px;
                background: transparent;
                border: none;
                min-height: 60px;
            }}

            QMessageBox QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {accent_color},
                    stop:1 {accent_color});
                border: 1px solid rgba(255, 255, 255, 0.4);
                border-radius: 12px;
                color: #ffffff;
                font-size: {text_font_size}px;
                font-weight: 600;
                padding: 8px 20px;
                min-width: 80px;
                min-height: 32px;
                margin: 5px;
            }}

            QMessageBox QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {accent_hover},
                    stop:1 {accent_hover});
                border: 1px solid rgba(255, 255, 255, 0.6);
            }}

            QMessageBox QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(44, 62, 80, 0.9),
                    stop:1 rgba(52, 73, 94, 0.9));
                border: 1px solid rgba(255, 255, 255, 0.3);
            }}
            """

            msg_box.setStyleSheet(glassmorphism_style)

            # Apply shadow effect
            try:
                from PyQt6.QtWidgets import QGraphicsDropShadowEffect
                from PyQt6.QtGui import QColor

                shadow = QGraphicsDropShadowEffect()
                shadow.setBlurRadius(24)
                shadow.setColor(QColor(0, 0, 0, 64))  # 25% opacity
                shadow.setOffset(0, 6)
                msg_box.setGraphicsEffect(shadow)

            except ImportError:
                pass

        except Exception as e:
            self.logger.warning(f"Failed to apply message box styling: {e}")

    def handle_cancel_request(self) -> None:
        """Handle a cancellation request from the progress dialog."""
        self.logger.info("Export cancelled by user")
        self.cancel_requested = True

    def update_progress(self, value: int, message: str) -> None:
        """
        Update the progress dialog.

        Args:
            value: Current progress value
            message: Progress message to display
        """
        if self.progress_dialog:
            self.progress_dialog.setValue(value)
            self.progress_dialog.setLabelText(message)
            QApplication.processEvents()

    def show_error_message(self, title: str, message: str) -> None:
        """
        Show a modern styled error message box.

        Args:
            title: Error title
            message: Error message
        """
        self.logger.error(f"Error: {message}")
        msg_box = QMessageBox(self.sequence_card_tab)
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        self._apply_message_box_styling(msg_box, "error")
        msg_box.exec()

    def show_warning_message(self, title: str, message: str) -> None:
        """
        Show a modern styled warning message box.

        Args:
            title: Warning title
            message: Warning message
        """
        self.logger.warning(f"Warning: {message}")
        msg_box = QMessageBox(self.sequence_card_tab)
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        self._apply_message_box_styling(msg_box, "warning")
        msg_box.exec()

    def show_info_message(self, title: str, message: str) -> None:
        """
        Show a modern styled information message box.

        Args:
            title: Info title
            message: Info message
        """
        self.logger.info(f"Info: {message}")
        msg_box = QMessageBox(self.sequence_card_tab)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        self._apply_message_box_styling(msg_box, "info")
        msg_box.exec()

    def show_export_complete_message(self, export_dir: str, page_count: int) -> None:
        """
        Show a message indicating that the export is complete.

        Args:
            export_dir: Directory where the pages were exported
            page_count: Number of pages exported
        """
        self.logger.info(
            f"Export complete: {page_count} pages exported to {export_dir}"
        )
        QMessageBox.information(
            self.sequence_card_tab,
            "Export Complete",
            f"Successfully exported {page_count} sequence card pages to:\n{export_dir}",
        )
