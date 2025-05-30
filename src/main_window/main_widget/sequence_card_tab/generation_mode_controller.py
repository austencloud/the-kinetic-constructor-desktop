import logging
from PyQt6.QtWidgets import (
    QApplication,
    QGridLayout,
    QWidget,
    QLabel,
    QFrame,
    QVBoxLayout,
    QPushButton,
    QHBoxLayout,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap


from .generation.generation_controls import GenerationControlsPanel
from .generation.approval_dialog.approval_dialog import SequenceApprovalDialog
from .core.mode_manager import SequenceCardMode
from .ui_manager import SequenceCardUIManager  # Added for type hint
from .generation.generation_manager import GenerationManager  # Added for type hint
from .generation.generated_sequence_store import (
    GeneratedSequenceStore,
)  # Added for type hint

from typing import (
    TYPE_CHECKING,
    List,
    Any,
)  # Added Any for sequence_data, consider a specific type

if TYPE_CHECKING:
    from main_window.main_widget.sequence_workbench.sequence_beat_frame.image_export_manager.image_export_manager import (
        ImageExportManager,
    )
    from .tab import SequenceCardTab
    from .generation.generation_manager import GenerationParams
    from main_window.main_widget.main_widget import (
        MainWidget,
    )  # For self.tab.main_widget
    from main_window.main_widget.sequence_workbench.sequence_workbench import (
        SequenceWorkbench,
    )  # For sequence_workbench

    # Define a type for sequence_data if possible, e.g., a TypedDict or a class
    # from .generation.generation_types import GeneratedSequenceData # Example


class SequenceCardGenerationModeController:
    def __init__(self, tab: "SequenceCardTab"):
        self.tab: "SequenceCardTab" = tab
        self.ui_manager: SequenceCardUIManager = tab.ui_manager
        self.generation_manager: GenerationManager = tab.generation_manager
        self.generated_sequence_store: GeneratedSequenceStore = (
            tab.generated_sequence_store
        )
        self.generation_controls: GenerationControlsPanel | None = None
        self._pending_batch_sequences: List[Any] = []  # Use specific type if available
        self._expected_batch_size: int = 0

    def activate(self) -> None:
        """Activates generation mode."""
        if not self.generation_manager.is_available():
            self.ui_manager.set_header_description(
                "Initializing generation mode dependencies..."
            )
            QApplication.processEvents()  # Update UI immediately
            if not self.generation_manager._refresh_generate_tab_reference():
                self.tab.mode_manager.switch_mode(SequenceCardMode.DICTIONARY)  # Revert
                self.ui_manager.set_header_description(
                    "Generation mode unavailable - Could not initialize required dependencies."
                )
                return

        self.ui_manager.set_header_description("Generate new sequences on-demand")
        if self.tab.nav_sidebar.scroll_area:
            self.tab.nav_sidebar.scroll_area.setVisible(False)
        if self.tab.nav_sidebar.level_filter:
            self.tab.nav_sidebar.level_filter.setVisible(False)

        self._ensure_generation_controls()
        if self.generation_controls:
            self.generation_controls.setVisible(True)

        self.ui_manager.clear_content_area()
        self._display_generated_sequences()

    def deactivate(self) -> None:
        """Deactivates generation mode."""
        if self.generation_controls:
            self.generation_controls.setVisible(False)

    def _ensure_generation_controls(self) -> None:
        if self.generation_controls is None:
            # Pass the settings_manager from the tab to the controls panel
            settings_manager = self.tab.main_widget.app_context.settings_manager
            self.generation_controls = GenerationControlsPanel(
                settings_manager=settings_manager
            )
            self.generation_controls.generate_requested.connect(
                self.on_generate_requested
            )
            self.generation_controls.clear_requested.connect(
                self.on_clear_generated_requested
            )
            sidebar_layout = self.tab.nav_sidebar.layout()
            if sidebar_layout:
                sidebar_layout.insertWidget(
                    sidebar_layout.count() - 1, self.generation_controls
                )

    def on_generate_requested(
        self, params: "GenerationParams", batch_size: int
    ) -> None:
        if self.tab.is_initializing:
            logging.info("Ignoring generation request during initialization")
            return

        logging.info(
            f"Using generation controls parameters directly: {params.__dict__}"
        )

        if batch_size == 1:
            self.generation_manager.generate_single_sequence(params)
        else:
            self._pending_batch_sequences = []
            self._expected_batch_size = batch_size
            self.generation_manager.generate_batch(params, batch_size)

    def on_sequence_generated(
        self, sequence_data: Any
    ) -> None:  # Use specific type if available
        # Ensure _pending_batch_sequences is initialized (it is in __init__)
        self._pending_batch_sequences.append(sequence_data)
        if (
            len(self._pending_batch_sequences) >= self._expected_batch_size
            and self._expected_batch_size > 0
        ):
            dialog = SequenceApprovalDialog(self._pending_batch_sequences, self.tab)
            dialog.sequences_approved.connect(self.on_sequences_approved)
            dialog.sequences_rejected.connect(self.on_sequences_rejected)
            dialog.show()
            self._pending_batch_sequences = []  # Reset after showing dialog
            self._expected_batch_size = 0
        elif (
            self._expected_batch_size == 0
        ):  # Single generation or batch of 1 already handled
            dialog = SequenceApprovalDialog([sequence_data], self.tab)
            dialog.sequences_approved.connect(self.on_sequences_approved)
            dialog.sequences_rejected.connect(self.on_sequences_rejected)
            dialog.show()
            # Reset pending if it was a single sequence that somehow got here
            self._pending_batch_sequences = []

    def on_sequences_approved(
        self, approved_sequences: List[Any]
    ) -> None:  # Use specific type
        for sequence_data in approved_sequences:
            self.generated_sequence_store.add_approved_sequence(sequence_data)
        self._display_generated_sequences()

    def on_sequences_rejected(
        self, rejected_sequences: List[Any]
    ) -> None:  # Use specific type
        # Rejected sequences are simply not added to the store
        pass

    def on_generation_failed(self, error_message: str) -> None:
        self.ui_manager.set_header_description(f"Generation failed: {error_message}")

    def on_generation_progress(self, current: int, total: int) -> None:
        if self.generation_controls:
            self.generation_controls.show_progress(current, total)

    def on_clear_generated_requested(self) -> None:
        self.generated_sequence_store.clear_all_sequences()
        self._display_generated_sequences()

    def _display_generated_sequences(self) -> None:
        count = self.generated_sequence_store.get_sequence_count()
        if count == 0:
            self.ui_manager.set_header_description(
                "No generated sequences. Use the controls to generate some!"
            )
            self.ui_manager.clear_content_area()
        else:
            self.ui_manager.set_header_description(
                f"Showing {count} generated sequences"
            )
            self._render_generated_sequence_cards()

    def _render_generated_sequence_cards(self) -> None:
        try:
            self.ui_manager.clear_content_area()
            sequences = self.generated_sequence_store.get_all_sequences()
            if not sequences:
                return

            container_widget = QWidget()
            grid_layout = QGridLayout(container_widget)
            grid_layout.setSpacing(20)
            grid_layout.setContentsMargins(20, 20, 20, 20)

            columns = min(3, len(sequences))
            # rows = (len(sequences) + columns - 1) // columns # Not strictly needed for adding widgets

            for i, sequence_data in enumerate(sequences):
                row = i // columns
                col = i % columns
                card = self._create_sequence_card(sequence_data)
                grid_layout.addWidget(card, row, col)

            self.tab.content_area.scroll_layout.addWidget(container_widget)
        except Exception as e:
            logging.error(f"Error rendering generated sequence cards: {e}")
            self.ui_manager.set_header_description(
                f"Error displaying sequences: {str(e)}"
            )

    def _create_sequence_card(self, sequence_data: Any) -> QFrame:  # Use specific type
        try:
            card = QFrame()
            card.setFixedSize(280, 350)
            card.setStyleSheet(
                """
                QFrame {
                    background: rgba(255, 255, 255, 0.1);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    border-radius: 12px;
                    padding: 10px;
                }
                QFrame:hover {
                    background: rgba(255, 255, 255, 0.15);
                    border: 1px solid rgba(255, 255, 255, 0.3);
                }
            """
            )
            layout = QVBoxLayout(card)
            layout.setSpacing(10)
            layout.setContentsMargins(15, 15, 15, 15)

            image_label = QLabel()
            image_label.setFixedSize(250, 200)
            image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            image_label.setStyleSheet(
                """
                QLabel {
                    background: rgba(0, 0, 0, 0.2);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 8px;
                }
            """
            )
            pixmap = self._generate_sequence_card_image(sequence_data)
            if pixmap and not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    image_label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                image_label.setPixmap(scaled_pixmap)
            else:
                image_label.setText("Generating...")
                image_label.setStyleSheet(
                    image_label.styleSheet()
                    + """
                    color: #e1e5e9;
                    font-size: 12px;
                """
                )
            layout.addWidget(image_label)

            info_label = QLabel()
            info_label.setText(
                f"<b>{sequence_data.word}</b><br>"
                f"Length: {sequence_data.params.length} beats<br>"
                f"Level: {sequence_data.params.level}<br>"
                f"Mode: {sequence_data.params.generation_mode.title()}"
            )
            info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            info_label.setStyleSheet(
                """
                QLabel {
                    color: #e1e5e9;
                    font-size: 11px;
                    background: transparent;
                    border: none;
                    padding: 5px;
                }
            """
            )
            layout.addWidget(info_label)

            button_layout = QHBoxLayout()
            export_btn = QPushButton("Export")
            export_btn.setFixedSize(60, 25)
            export_btn.setStyleSheet(
                """
                QPushButton {
                    background: rgba(100, 150, 255, 0.8);
                    border: 1px solid rgba(100, 150, 255, 1.0);
                    border-radius: 4px;
                    color: white;
                    font-size: 10px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: rgba(100, 150, 255, 1.0);
                }
            """
            )
            export_btn.clicked.connect(
                lambda: self._export_generated_sequence(sequence_data)
            )

            remove_btn = QPushButton("Remove")
            remove_btn.setFixedSize(60, 25)
            remove_btn.setStyleSheet(
                """
                QPushButton {
                    background: rgba(255, 100, 100, 0.8);
                    border: 1px solid rgba(255, 100, 100, 1.0);
                    border-radius: 4px;
                    color: white;
                    font-size: 10px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: rgba(255, 100, 100, 1.0);
                }
            """
            )
            remove_btn.clicked.connect(
                lambda: self._remove_generated_sequence(sequence_data)
            )

            button_layout.addWidget(export_btn)
            button_layout.addWidget(remove_btn)
            button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addLayout(button_layout)
            return card
        except Exception as e:
            logging.error(f"Error creating sequence card: {e}")
            error_card = QFrame()
            error_card.setFixedSize(280, 350)
            error_layout = QVBoxLayout(error_card)
            error_label = QLabel(f"Error creating card:\n{str(e)}")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            error_layout.addWidget(error_label)
            return error_card

    def _generate_sequence_card_image(
        self, sequence_data: Any
    ) -> QPixmap | None:  # Use specific type
        try:
            main_widget: "MainWidget" = self.tab.main_widget
            sequence_workbench: "SequenceWorkbench" = (
                main_widget.widget_manager.get_widget("sequence_workbench")
            )
            if not sequence_workbench:
                return None
            image_export_manager: "ImageExportManager" = (
                sequence_workbench.beat_frame.image_export_manager
            )
            if not image_export_manager:
                return None

            options = {
                "add_beat_numbers": True,
                "add_reversal_symbols": True,
                "add_user_info": True,
                "add_word": True,
                "add_difficulty_level": True,
                "include_start_position": True,  # Enable start position for approval dialog
                "combined_grids": False,
                "additional_height_top": 0,
                "additional_height_bottom": 0,
            }
            qimage = image_export_manager.image_creator.create_sequence_image(
                sequence_data.sequence_data,
                options,
                dictionary=True,
                fullscreen_preview=False,
            )
            pixmap = QPixmap.fromImage(qimage)
            return pixmap
        except Exception as e:
            logging.error(f"Error generating sequence card image: {e}")
            return None

    def _export_generated_sequence(
        self, sequence_data: Any
    ) -> None:  # Use specific type
        try:
            main_widget: "MainWidget" = self.tab.main_widget
            sequence_workbench: "SequenceWorkbench" = (
                main_widget.widget_manager.get_widget("sequence_workbench")
            )
            if sequence_workbench:
                image_export_manager: "ImageExportManager" = (
                    sequence_workbench.beat_frame.image_export_manager
                )
                if image_export_manager:
                    image_export_manager.export_image_directly(
                        sequence_data.sequence_data
                    )
        except Exception as e:
            logging.error(f"Error exporting generated sequence: {e}")

    def _remove_generated_sequence(
        self, sequence_data: Any
    ) -> None:  # Use specific type
        try:
            self.generated_sequence_store.remove_sequence(sequence_data.id)
            self._display_generated_sequences()
        except Exception as e:
            logging.error(f"Error removing generated sequence: {e}")
