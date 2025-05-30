# grid_mode_section.py

from typing import TYPE_CHECKING
from PyQt6.QtWidgets import (
    QVBoxLayout,
    QLabel,
    QGridLayout,
    QSpacerItem,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, QEvent, QObject
from PyQt6.QtGui import QPixmap, QPainter, QPen
from PyQt6.QtSvg import QSvgRenderer

from functools import partial
import os

from data.constants import GRID_MODE
from main_window.main_widget.metadata_extractor import MetaDataExtractor
from styles.styled_button import StyledButton
from utils.path_helpers import get_data_path, get_image_path
from .filter_section_base import FilterSectionBase

if TYPE_CHECKING:
    from main_window.main_widget.browse_tab.sequence_picker.filter_stack.sequence_picker_filter_stack import (
        SequencePickerFilterStack,
    )


class GridModeSection(FilterSectionBase):
    GRID_MODES = ["Box", "Diamond"]
    IMAGE_DIR = get_image_path("grid")

    def __init__(self, initial_selection_widget: "SequencePickerFilterStack"):
        super().__init__(initial_selection_widget, "Select by Grid Mode:")
        self.main_widget = initial_selection_widget.browse_tab.main_widget
        self.buttons: dict[str, StyledButton] = {}
        self.description_labels: dict[str, QLabel] = {}
        self.grid_mode_images: dict[str, QLabel] = {}
        self.original_pixmaps: dict[str, QPixmap] = {}
        self.tally: dict[str, int] = {}
        self.tally_labels: dict[str, QLabel] = {}
        self.spacers: dict[str, QSpacerItem] = {}
        self.add_buttons()

    def add_buttons(self):
        """Initialize the UI components for the grid mode selection."""
        self.header_label.show()
        layout: QVBoxLayout = self.layout()

        self.tally = self._get_sequence_counts_per_grid_mode()

        grid_layout = QGridLayout()
        grid_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grid_layout.setHorizontalSpacing(50)
        grid_layout.setVerticalSpacing(30)

        for col, grid_mode in enumerate(self.GRID_MODES):
            grid_mode_vbox = self.create_grid_mode_vbox(grid_mode)
            grid_layout.addLayout(grid_mode_vbox, 0, col)

        layout.addLayout(grid_layout)
        layout.addStretch(1)

    def create_grid_mode_vbox(self, grid_mode: str) -> QVBoxLayout:
        """Create a vertical box layout containing all components for a grid mode."""
        grid_mode_vbox = QVBoxLayout()
        grid_mode_vbox.setAlignment(Qt.AlignmentFlag.AlignCenter)

        button = self.create_grid_mode_button(grid_mode)
        description_label = self.create_description_label(grid_mode)
        image_placeholder = self.create_image_placeholder(grid_mode)
        sequence_count_label = self.create_sequence_count_label(grid_mode)
        spacer = self.create_spacer(grid_mode)

        grid_mode_vbox.addWidget(button)
        grid_mode_vbox.addWidget(description_label)
        grid_mode_vbox.addItem(spacer)
        grid_mode_vbox.addWidget(image_placeholder)
        grid_mode_vbox.addWidget(sequence_count_label)

        return grid_mode_vbox

    def create_spacer(self, grid_mode) -> QSpacerItem:
        spacer = QSpacerItem(
            20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed
        )
        self.spacers[grid_mode] = spacer
        return spacer

    def create_grid_mode_button(self, grid_mode: str) -> StyledButton:
        """Create and configure the grid mode selection button."""
        button = StyledButton(grid_mode)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.clicked.connect(partial(self.handle_grid_mode_click, grid_mode.lower()))
        self.buttons[grid_mode] = button
        return button

    def create_description_label(self, grid_mode: str) -> QLabel:
        """Create a label for the grid mode description."""
        if grid_mode == "Box":
            description = f"Sequences using diagonal points\nNE, SE, SW, NW"
        elif grid_mode == "Diamond":
            description = f"Sequences using cardinal points\nN, E, S, W"
        description_label = QLabel(description)
        description_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.description_labels[grid_mode] = description_label
        return description_label

    def create_image_placeholder(self, grid_mode: str) -> QLabel:
        """Create and configure the image placeholder for a grid mode."""
        image_placeholder = QLabel()
        image_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_placeholder.setProperty(
            GRID_MODE, grid_mode
        )  # Associate grid mode with the label
        self.grid_mode_images[grid_mode] = image_placeholder

        # Update the path to point to the SVG files
        image_path = os.path.join(self.IMAGE_DIR, f"{grid_mode.lower()}_grid.svg")
        if os.path.exists(image_path):
            # Render the SVG to a QPixmap
            pixmap = self.render_svg_to_pixmap(image_path)
            self.original_pixmaps[grid_mode] = pixmap  # Store the original pixmap

            scaled_pixmap = self.scale_pixmap(pixmap)
            image_placeholder.setPixmap(scaled_pixmap)

            # Make the image clickable
            image_placeholder.setCursor(Qt.CursorShape.PointingHandCursor)
            image_placeholder.mousePressEvent = partial(
                self.handle_image_click, grid_mode.lower()
            )
            # Install event filter for hover effect
            image_placeholder.installEventFilter(self)
        else:
            image_placeholder.setText("No Image Available")

        return image_placeholder

    def render_svg_to_pixmap(self, svg_path: str) -> QPixmap:
        """Render an SVG file to a QPixmap with a white background."""
        svg_renderer = QSvgRenderer(svg_path)
        default_size = svg_renderer.defaultSize()
        pixmap = QPixmap(default_size)
        pixmap.fill(Qt.GlobalColor.white)  # Changed from transparent to white
        painter = QPainter(pixmap)
        svg_renderer.render(painter)
        painter.end()
        return pixmap

    def create_sequence_count_label(self, grid_mode: str) -> QLabel:
        """Create a label displaying the sequence count for a grid mode."""
        count = self.tally.get(grid_mode.lower(), 0)
        sequence_text = "sequence" if count == 1 else "sequences"
        sequence_count_label = QLabel(f"{count} {sequence_text}")
        sequence_count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.tally_labels[grid_mode] = sequence_count_label
        return sequence_count_label

    def handle_grid_mode_click(self, grid_mode: str):
        """Handle clicks on grid mode buttons."""
        self.browse_tab.filter_controller.apply_filter({GRID_MODE: grid_mode})

    def handle_image_click(self, grid_mode: str, event):
        """Handle clicks on grid mode images."""
        self.handle_grid_mode_click(grid_mode)

    def _get_all_sequences_with_grid_modes(self):
        """Retrieve and cache all sequences along with their grid modes."""
        if hasattr(self, "_all_sequences_with_grid_modes"):
            return self._all_sequences_with_grid_modes

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

        sequences_with_grid_modes = []
        for word, thumbnails in base_words:
            grid_mode = self.get_sequence_grid_mode(thumbnails)
            if grid_mode is not None:
                sequences_with_grid_modes.append((word, thumbnails, grid_mode))

        self._all_sequences_with_grid_modes = sequences_with_grid_modes
        return sequences_with_grid_modes

    def _get_sequence_counts_per_grid_mode(self) -> dict[str, int]:
        """Compute the number of sequences available for each grid mode."""
        grid_mode_counts: dict[str, int] = {}
        sequences_with_grid_modes = self._get_all_sequences_with_grid_modes()
        for _, _, grid_mode in sequences_with_grid_modes:
            grid_mode_counts[grid_mode] = grid_mode_counts.get(grid_mode, 0) + 1
        return grid_mode_counts

    def get_sequences_by_grid_mode(self, grid_mode: str):
        """Retrieve sequences that correspond to a specific grid mode."""
        sequences_with_grid_modes = self._get_all_sequences_with_grid_modes()
        return [
            (word, thumbnails)
            for word, thumbnails, seq_grid_mode in sequences_with_grid_modes
            if seq_grid_mode == grid_mode
        ]

    def get_sequence_grid_mode(self, thumbnails: list) -> str:
        """Extract the grid mode from the metadata of the thumbnails."""
        for thumbnail in thumbnails:
            grid_mode = MetaDataExtractor().get_grid_mode(thumbnail)
            if grid_mode:
                return grid_mode
        return None

    def display_only_thumbnails_with_grid_mode(self, grid_mode: str):
        """Display only the thumbnails that match the selected grid mode."""
        self.filter_selector.browse_tab.settings.set_current_filter(
            {GRID_MODE: grid_mode.lower()}
        )
        self.browse_tab.filter_manager.prepare_ui_for_filtering(
            f"{grid_mode.capitalize()} mode sequences."
        )

        sequences = self.get_sequences_by_grid_mode(grid_mode)
        total_sequences = len(sequences)

        self.browse_tab.sequence_picker.currently_displayed_sequences = [
            (word, thumbnails, self.get_sequence_length_from_thumbnails(thumbnails))
            for word, thumbnails in sequences
        ]

        self.browse_tab.ui_updater.update_and_display_ui(total_sequences)

    def get_sequence_length_from_thumbnails(self, thumbnails: list[str]) -> int:
        """Extract the sequence length from the thumbnails' metadata."""
        for thumbnail in thumbnails:
            length = self.metadata_extractor.get_length(thumbnail)
            if length is not None:
                return length
        return 0

    def eventFilter(self, source: QObject, event: QEvent) -> bool:
        """Handle hover events to add or remove borders on images."""
        if isinstance(source, QLabel):
            grid_mode = source.property(GRID_MODE)
            if grid_mode is not None:
                if event.type() == QEvent.Type.Enter:
                    self.apply_hover_effect(grid_mode, source)
                    return True
                elif event.type() == QEvent.Type.Leave:
                    self.remove_hover_effect(grid_mode, source)
                    return True
        return super().eventFilter(source, event)

    def apply_hover_effect(self, grid_mode: str, label: QLabel):
        """Add a border to the image when hovered."""
        original_pixmap = self.original_pixmaps.get(grid_mode)
        if original_pixmap:
            bordered_pixmap = self.add_border_to_pixmap(
                original_pixmap, 4, Qt.GlobalColor.yellow
            )
            scaled_pixmap = self.scale_pixmap(bordered_pixmap)
            label.setPixmap(scaled_pixmap)

    def remove_hover_effect(self, grid_mode: str, label: QLabel):
        """Remove the border from the image when not hovered."""
        original_pixmap = self.original_pixmaps.get(grid_mode)
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
        for grid_mode, label in self.grid_mode_images.items():
            original_pixmap = self.original_pixmaps.get(grid_mode)
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
        """Handle resizing of the grid mode section."""
        self.scale_images()
        self.resize_buttons()
        self.resize_labels()
        self.resize_spacer()

    def resize_spacer(self):
        spacer_height = max(1, self.main_widget.height() // 50)
        for spacer in self.spacers.values():
            spacer.changeSize(20, spacer_height)

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
