from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QScrollArea,
    QWidget,
    QGridLayout,
    QSpinBox,
    QProgressBar,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from typing import List

from ..generation_manager import GeneratedSequenceData
from ..sequence_card import SequenceCard
from .managers import (
    ApprovalDialogDimensionCalculator,
    ApprovalDialogLayoutManager,
    ApprovalDialogImageManager,
    ApprovalDialogStyleManager,
)


class SequenceApprovalDialog(QDialog):
    sequences_approved = pyqtSignal(list)
    sequences_rejected = pyqtSignal(list)
    all_sequences_processed = pyqtSignal()

    def __init__(self, sequences: List[GeneratedSequenceData], parent=None):
        super().__init__(parent)
        self.sequences = sequences
        self.sequence_states = {}
        self.sequence_cards = {}

        self.main_widget = self._find_main_widget(parent)
        self.dimension_calculator = ApprovalDialogDimensionCalculator(
            parent.size() if parent else None, len(sequences)
        )
        self.image_manager = ApprovalDialogImageManager(self.main_widget)

        # Get initial column count from sidebar settings
        self.initial_column_count = self._get_sidebar_column_count()

        self.setWindowTitle(f"Approve Generated Sequences ({len(sequences)} sequences)")
        self.setModal(True)
        self.resize(
            self.dimension_calculator.dialog_width,
            self.dimension_calculator.dialog_height,
        )
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        self.setup_ui()
        ApprovalDialogStyleManager.apply_styling(self)
        self.populate_sequences()
        self.start_image_generation()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header section
        header_layout = QHBoxLayout()

        title_label = QLabel(f"Review {len(self.sequences)} Generated Sequences")
        title_label.setObjectName("titleLabel")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(len(self.sequences))
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.progress_bar.setObjectName("progressBar")
        header_layout.addWidget(self.progress_bar)

        layout.addLayout(header_layout)

        # Controls section
        controls_layout = QHBoxLayout()

        columns_label = QLabel("Columns:")
        columns_label.setObjectName("controlLabel")
        controls_layout.addWidget(columns_label)

        self.columns_spinbox = QSpinBox()
        self.columns_spinbox.setMinimum(2)
        self.columns_spinbox.setMaximum(4)
        self.columns_spinbox.setValue(self.initial_column_count)
        self.columns_spinbox.setObjectName("columnsSpinBox")
        self.columns_spinbox.valueChanged.connect(self.update_grid_layout)
        controls_layout.addWidget(self.columns_spinbox)

        controls_layout.addStretch()

        approve_all_btn = QPushButton("Approve All")
        approve_all_btn.setObjectName("approveAllButton")
        approve_all_btn.clicked.connect(self.approve_all_sequences)
        controls_layout.addWidget(approve_all_btn)

        reject_all_btn = QPushButton("Reject All")
        reject_all_btn.setObjectName("rejectAllButton")
        reject_all_btn.clicked.connect(self.reject_all_sequences)
        controls_layout.addWidget(reject_all_btn)

        layout.addLayout(controls_layout)

        # Scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setMinimumSize(800, 400)
        scroll_area.setMaximumSize(16777215, 16777215)

        self.container_widget = QWidget()
        self.grid_layout = QGridLayout(self.container_widget)
        self.grid_layout.setSpacing(15)
        self.grid_layout.setContentsMargins(15, 15, 15, 15)

        self.layout_manager = ApprovalDialogLayoutManager(
            self.grid_layout, self.dimension_calculator
        )

        scroll_area.setWidget(self.container_widget)
        layout.addWidget(scroll_area, 1)

        # Footer
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("cancelButton")
        cancel_btn.clicked.connect(self.reject)
        footer_layout.addWidget(cancel_btn)

        self.finish_btn = QPushButton("Finish Review")
        self.finish_btn.setObjectName("finishButton")
        self.finish_btn.clicked.connect(self.finish_review)
        footer_layout.addWidget(self.finish_btn)

        layout.addLayout(footer_layout)

    def populate_sequences(self):
        self.update_grid_layout()

    def update_grid_layout(self):
        columns = self.columns_spinbox.value()
        self.sequence_cards = self.layout_manager.update_layout(
            self.sequences, columns, self._create_sequence_card
        )

        for card in self.sequence_cards.values():
            card.status_changed.connect(self._on_card_status_changed)

    def _create_sequence_card(self, sequence_data: GeneratedSequenceData, columns: int):
        card_width, card_height, image_width, image_height = (
            self.dimension_calculator.calculate_card_dimensions(columns)
        )
        card = SequenceCard(
            sequence_data, card_width, card_height, image_width, image_height
        )
        return card

    def _on_card_status_changed(self, sequence_id: str, status: str):
        self.sequence_states[sequence_id] = status
        if sequence_id in self.sequence_cards:
            self.sequence_cards[sequence_id].update_status(status)

    def approve_all_sequences(self):
        for sequence in self.sequences:
            self._on_card_status_changed(sequence.id, "approved")

    def reject_all_sequences(self):
        for sequence in self.sequences:
            self._on_card_status_changed(sequence.id, "rejected")

    def start_image_generation(self):
        self.image_manager.start_generation(self.sequences, self.sequence_cards)

        def update_progress():
            progress_info = self.image_manager.get_progress()
            loaded = progress_info["images_loaded"]
            total = progress_info["total_images"]
            self.progress_bar.setValue(loaded)
            if loaded >= total:
                self.progress_bar.setVisible(False)

        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(update_progress)
        self.progress_timer.start(100)

    def finish_review(self):
        approved_sequences = []
        rejected_sequences = []

        for sequence in self.sequences:
            state = self.sequence_states.get(sequence.id)
            if state == "approved":
                approved_sequences.append(sequence)
            elif state == "rejected":
                rejected_sequences.append(sequence)

        if approved_sequences:
            self.sequences_approved.emit(approved_sequences)
        if rejected_sequences:
            self.sequences_rejected.emit(rejected_sequences)

        self.all_sequences_processed.emit()
        self.cleanup()
        self.accept()

    def cleanup(self):
        if hasattr(self, "progress_timer"):
            self.progress_timer.stop()
        self.image_manager.cleanup_workers()

    def closeEvent(self, event):
        self.cleanup()
        super().closeEvent(event)

    def _find_main_widget(self, widget):
        current = widget
        while current:
            if hasattr(current, "widget_manager"):
                return current
            current = current.parent()
        return None

    def _get_sidebar_column_count(self):
        """Get the current column count from the sidebar settings."""
        try:
            # Try to get column count from the sequence card tab's sidebar
            if self.main_widget and hasattr(self.main_widget, "tab_manager"):
                tab_manager = self.main_widget.tab_manager
                if hasattr(tab_manager, "get_tab"):
                    sequence_card_tab = tab_manager.get_tab("sequence_card")
                    if sequence_card_tab and hasattr(sequence_card_tab, "nav_sidebar"):
                        sidebar = sequence_card_tab.nav_sidebar
                        if hasattr(sidebar, "column_selector"):
                            return sidebar.column_selector.get_current_count()

            # Fallback: try to get from settings manager
            if self.main_widget and hasattr(self.main_widget, "settings_manager"):
                settings_manager = self.main_widget.settings_manager
                return int(
                    settings_manager.get_setting("sequence_card_tab", "column_count", 3)
                )

            # Final fallback
            return 3
        except Exception as e:
            import logging

            logging.warning(
                f"Could not get sidebar column count: {e}, using default of 3"
            )
            return 3

    def get_approved_sequences(self) -> List[GeneratedSequenceData]:
        return [
            seq
            for seq in self.sequences
            if self.sequence_states.get(seq.id) == "approved"
        ]

    def get_rejected_sequences(self) -> List[GeneratedSequenceData]:
        return [
            seq
            for seq in self.sequences
            if self.sequence_states.get(seq.id) == "rejected"
        ]
