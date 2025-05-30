from typing import TYPE_CHECKING, Tuple
from PyQt6.QtWidgets import (
    QVBoxLayout,
    QLabel,
    QGridLayout,
    QSpacerItem,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, QEvent, QObject
from PyQt6.QtGui import QPixmap, QPainter, QPen
import os
from functools import partial

from styles.styled_button import StyledButton
from utils.path_helpers import get_data_path, get_image_path
from .filter_section_base import FilterSectionBase

if TYPE_CHECKING:
    from .sequence_picker_filter_stack import SequencePickerFilterStack


class StartingPositionSection(FilterSectionBase):
    POSITION_DESCRIPTIONS = {
        "Alpha": "Hands apart.",
        "Beta": "Hands together.",
        "Gamma": "Hands form a right angle.",
    }
    AVAILABLE_POSITIONS = ["Alpha", "Beta", "Gamma"]
    IMAGE_DIR = get_image_path("position_images")

    def __init__(self, initial_selection_widget: "SequencePickerFilterStack"):
        super().__init__(initial_selection_widget, "Select by Starting Position:")
        self.main_widget = initial_selection_widget.browse_tab.main_widget
        self.buttons: dict[str, StyledButton] = {}
        self.description_labels: dict[str, QLabel] = {}
        self.position_images: dict[str, QLabel] = {}
        self.tally_labels: dict[str, QLabel] = {}
        self.original_pixmaps: dict[str, QPixmap] = {}
        self.sequence_counts: dict[str, int] = {}
        self.add_buttons()

    def add_buttons(self):
        """Initialize the UI components for the starting position selection."""
        self.header_label.show()
        layout: QVBoxLayout = self.layout()

        # Calculate the sequence counts per starting position
        self.sequence_counts = self._get_sequence_counts_per_position()

        grid_layout = QGridLayout()
        grid_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grid_layout.setHorizontalSpacing(50)
        grid_layout.setVerticalSpacing(30)

        for col, position in enumerate(self.AVAILABLE_POSITIONS):
            position_vbox = self.create_position_vbox(position)
            grid_layout.addLayout(position_vbox, 0, col)

        layout.addLayout(grid_layout)
        layout.addStretch(1)
        # self.resize_starting_position_section()

    def create_position_vbox(self, position: str) -> QVBoxLayout:
        """Create a vertical box layout containing all components for a position."""
        position_vbox = QVBoxLayout()
        position_vbox.setAlignment(Qt.AlignmentFlag.AlignCenter)

        button = self.create_position_button(position)
        description_label = self.create_description_label(position)
        image_placeholder = self.create_image_placeholder(position)
        sequence_count_label = self.create_sequence_count_label(position)

        position_vbox.addWidget(button)
        position_vbox.addWidget(description_label)
        position_vbox.addItem(
            QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        )
        position_vbox.addWidget(image_placeholder)
        position_vbox.addWidget(sequence_count_label)

        return position_vbox

    def create_position_button(self, position: str) -> StyledButton:
        """Create and configure the position selection button."""
        button = StyledButton(position)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.clicked.connect(partial(self.handle_position_click, position))
        self.buttons[position] = button
        return button

    def create_description_label(self, position: str) -> QLabel:
        """Create a label for the position description."""
        description_label = QLabel(self.POSITION_DESCRIPTIONS.get(position, ""))
        description_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.description_labels[position] = description_label
        return description_label

    def create_image_placeholder(self, position: str) -> QLabel:
        """Create and configure the image placeholder for a position."""
        image_placeholder = QLabel()
        image_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_placeholder.setProperty(
            "position", position
        )  # Associate position with the label
        self.position_images[position] = image_placeholder

        image_path = os.path.join(self.IMAGE_DIR, f"{position.lower()}.png")
        if os.path.exists(image_path):
            original_pixmap = QPixmap(image_path)
            self.original_pixmaps[position] = (
                original_pixmap  # Store the original pixmap
            )

            # Make the image clickable
            image_placeholder.setCursor(Qt.CursorShape.PointingHandCursor)
            image_placeholder.mousePressEvent = partial(
                self.handle_image_click, position
            )
            # Install event filter for hover effect
            image_placeholder.installEventFilter(self)
        else:
            image_placeholder.setText("No Image Available")

        return image_placeholder

    def create_sequence_count_label(self, position: str) -> QLabel:
        """Create a label displaying the sequence count for a position."""
        count = self.sequence_counts.get(position.lower(), 0)
        sequence_text = "sequence" if count == 1 else "sequences"
        sequence_count_label = QLabel(f"{count} {sequence_text}")
        sequence_count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.tally_labels[position] = sequence_count_label
        return sequence_count_label

    def handle_position_click(self, position: str):
        """Handle clicks on position buttons."""
        self.browse_tab.filter_controller.apply_filter({"starting_position": position})

    def handle_image_click(self, position: str, event):
        """Handle clicks on position images."""
        self.handle_position_click(position)

    def _get_all_sequences_with_positions(self) -> list[Tuple[str, list[str], str]]:
        """Retrieve and cache all sequences along with their starting positions."""
        if hasattr(self, "_all_sequences_with_positions"):
            return self._all_sequences_with_positions

        dictionary_dir = get_data_path("dictionary")
        # Fix: Access thumbnail_finder as a service attribute, not through widget manager
        thumbnail_finder = getattr(self.main_widget, "thumbnail_finder", None)

        if thumbnail_finder:
            base_words = [
                (
                    word,
                    thumbnail_finder.find_thumbnails(
                        os.path.join(dictionary_dir, word)
                    ),
                )
                for word in os.listdir(dictionary_dir)
                if os.path.isdir(os.path.join(dictionary_dir, word))
                and "__pycache__" not in word
            ]
        else:
            base_words = []

        sequences_with_positions = []
        for word, thumbnails in base_words:
            position = self.get_sequence_starting_position(thumbnails)
            if position is not None:
                sequences_with_positions.append((word, thumbnails, position))

        self._all_sequences_with_positions = sequences_with_positions
        return sequences_with_positions

    def _get_sequence_counts_per_position(self) -> dict[str, int]:
        """Compute the number of sequences available for each starting position."""
        position_counts: dict[str, int] = {}
        sequences_with_positions = self._get_all_sequences_with_positions()
        for _, _, position in sequences_with_positions:
            position_counts[position] = position_counts.get(position, 0) + 1
        return position_counts

    def get_sequences_that_are_a_specific_position(
        self, position: str
    ) -> list[Tuple[str, list[str]]]:
        """Retrieve sequences that correspond to a specific starting position."""
        sequences_with_positions = self._get_all_sequences_with_positions()
        return [
            (word, thumbnails)
            for word, thumbnails, seq_position in sequences_with_positions
            if seq_position == position.lower()
        ]

    def get_sequence_starting_position(self, thumbnails: list[str]) -> str:
        """Extract the starting position from the metadata of the thumbnails."""
        for thumbnail in thumbnails:
            start_position = self.metadata_extractor.get_start_pos(thumbnail)
            if start_position:
                return start_position
        return None

    def get_sequence_length_from_thumbnails(self, thumbnails: list[str]) -> int:
        """Extract the sequence length from the thumbnails' metadata."""
        for thumbnail in thumbnails:
            length = self.metadata_extractor.get_length(thumbnail)
            if length is not None:
                return length
        return 0

    def apply_hover_effect(self, position: str, label: QLabel):
        """Add a border to the image when hovered."""
        original_pixmap = self.original_pixmaps.get(position)
        if original_pixmap:
            bordered_pixmap = self.add_border_to_pixmap(
                original_pixmap, 4, Qt.GlobalColor.yellow
            )
            scaled_pixmap = self.scale_pixmap(bordered_pixmap)
            label.setPixmap(scaled_pixmap)

    def remove_hover_effect(self, position: str, label: QLabel):
        """Remove the border from the image when not hovered."""
        original_pixmap = self.original_pixmaps.get(position)
        if original_pixmap:
            scaled_pixmap = self.scale_pixmap(original_pixmap)
            label.setPixmap(scaled_pixmap)

    def add_border_to_pixmap(
        self, pixmap: QPixmap, border_width: int, border_color: Qt.GlobalColor
    ) -> QPixmap:
        """Add a border around the pixmap."""
        bordered_pixmap = QPixmap(pixmap.size())
        bordered_pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(bordered_pixmap)
        painter.drawPixmap(0, 0, pixmap)

        pen = QPen(border_color)
        pen.setWidth(border_width)
        painter.setPen(pen)
        painter.drawRect(
            border_width // 2,
            border_width // 2,
            pixmap.width() - border_width,
            pixmap.height() - border_width,
        )
        painter.end()
        return bordered_pixmap

    def scale_images(self):
        """Scale all images to fit the current widget size."""
        for position, label in self.position_images.items():
            original_pixmap = self.original_pixmaps.get(position)
            if original_pixmap:
                scaled_pixmap = self.scale_pixmap(original_pixmap)
                label.setPixmap(scaled_pixmap)

    def scale_pixmap(self, pixmap: QPixmap) -> QPixmap:
        """Scale a pixmap to the desired size."""
        size = max(1, self.main_widget.width() // 6)
        return pixmap.scaled(
            size,
            size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

    def resizeEvent(self, event):
        """Handle resizing of the starting position section."""
        self.scale_images()
        self.resize_buttons()
        self.resize_labels()

    def resize_labels(self):
        """Adjust font sizes of labels during resizing."""
        font_size_description = max(10, self.main_widget.width() // 140)
        font_size_header = max(12, self.main_widget.width() // 100)

        for label in self.description_labels.values():
            font = label.font()
            font.setPointSize(font_size_description)
            label.setFont(font)

        for label in self.tally_labels.values():
            font = label.font()
            font.setPointSize(font_size_description)
            label.setFont(font)

        font = self.header_label.font()
        font.setPointSize(font_size_header)
        self.header_label.setFont(font)

    def resize_buttons(self):
        """Adjust button sizes and fonts during resizing."""
        button_width = max(1, self.main_widget.width() // 5)
        button_height = max(1, self.main_widget.height() // 20)
        font_size_button = max(10, self.main_widget.width() // 100)

        for button in self.buttons.values():
            font = button.font()
            font.setPointSize(font_size_button)
            button.setFont(font)
            button.setFixedSize(button_width, button_height)

    def eventFilter(self, source: QObject, event: QEvent) -> bool:
        """Handle hover events to add or remove borders on images."""
        if isinstance(source, QLabel):
            position = source.property("position")
            if position is not None:
                if event.type() == QEvent.Type.Enter:
                    self.apply_hover_effect(position, source)
                    return True
                elif event.type() == QEvent.Type.Leave:
                    self.remove_hover_effect(position, source)
                    return True
        return super().eventFilter(source, event)
