from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QLabel, QSizePolicy
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from .sequence_viewer import SequenceViewer


class SequenceViewerImageLabel(QLabel):
    def __init__(self, sequence_viewer: "SequenceViewer"):
        super().__init__(sequence_viewer)
        self.sequence_viewer = sequence_viewer
        self._original_pixmap: QPixmap | None = None

        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setScaledContents(False)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_pixmap_with_scaling(self, pixmap: QPixmap):
        self._original_pixmap = pixmap
        self.set_pixmap_to_fit()

    def _calculate_available_space(self) -> tuple[int, int]:
        sequence_viewer = self.sequence_viewer
        available_height = int(sequence_viewer.main_widget.height() * 0.65)
        available_width = int(sequence_viewer.main_widget.width() * 1 / 3 * 0.95)

        return available_width, available_height

    def set_pixmap_to_fit(self):
        if not self._original_pixmap:
            return

        available_width, available_height = self._calculate_available_space()

        target_width = available_width
        aspect_ratio = self._original_pixmap.height() / self._original_pixmap.width()

        target_height = int(target_width * aspect_ratio)

        while target_height > available_height and target_width > 0:
            target_width -= 1
            target_height = int(target_width * aspect_ratio) - 1

        target_width = max(1, target_width)
        target_height = max(1, target_height)

        if target_width == available_width - 1:
            target_height = int(target_width * aspect_ratio)
        elif target_height == available_height - 1:
            target_width = int(target_height / aspect_ratio)

        # ULTRA HIGH QUALITY SCALING: Use advanced multi-step scaling for sequence viewer
        scaled_pixmap = self._create_ultra_high_quality_scaled_pixmap(
            target_width, target_height
        )
        self.setFixedHeight(target_height)
        # CRITICAL FIX: Remove the problematic setFixedHeight call on non-existent stacked_widget
        # This was causing layout regression by trying to set fixed height on undefined widget
        # The image label's setFixedHeight is sufficient for proper scaling
        self.setPixmap(scaled_pixmap)

    def update_thumbnail(self, index: int):
        if not self.sequence_viewer.state.thumbnails:
            return

        self.set_pixmap_with_scaling(
            QPixmap(self.sequence_viewer.state.thumbnails[index])
        )
        self.sequence_viewer.variation_number_label.update_index(index)

    def _create_ultra_high_quality_scaled_pixmap(
        self, target_width: int, target_height: int
    ) -> QPixmap:
        """Create ultra high-quality scaled pixmap for sequence viewer using advanced techniques."""
        if not self._original_pixmap:
            return QPixmap()

        original_size = self._original_pixmap.size()
        target_size = QSize(target_width, target_height)

        # Calculate scale factor
        scale_factor = min(
            target_width / original_size.width(), target_height / original_size.height()
        )

        # SEQUENCE VIEWER ULTRA QUALITY: Use multi-step scaling for large images
        if scale_factor < 0.6:
            # Multi-step scaling for better quality when scaling down significantly
            intermediate_factor = 0.75  # Scale to 75% first, then to target
            intermediate_size = QSize(
                int(original_size.width() * intermediate_factor),
                int(original_size.height() * intermediate_factor),
            )

            # Step 1: Scale to intermediate size with high quality
            intermediate_pixmap = self._original_pixmap.scaled(
                intermediate_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

            # Step 2: Scale to final size with high quality
            final_pixmap = intermediate_pixmap.scaled(
                target_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

            return final_pixmap
        else:
            # Single-step high-quality scaling for smaller scale changes
            return self._original_pixmap.scaled(
                target_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
