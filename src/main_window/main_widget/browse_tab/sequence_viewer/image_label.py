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
        """Calculate available space with proper width/height constraint logic."""
        sequence_viewer = self.sequence_viewer

        # CRITICAL FIX: Implement proper width expansion with height limits
        # Goal: Expand to fill entire width by default, but constrain height to prevent window expansion

        # Get the actual sequence viewer dimensions
        viewer_width = sequence_viewer.width()
        viewer_height = sequence_viewer.height()

        # Use most of the available width (95% to leave some margin)
        available_width = int(viewer_width * 0.95)

        # Set height constraint to prevent window expansion
        # Use 65% of viewer height as maximum, but also set an absolute maximum
        max_height_from_viewer = int(viewer_height * 0.65)
        absolute_max_height = 600  # Prevent excessive height that would expand window
        available_height = min(max_height_from_viewer, absolute_max_height)

        # Ensure minimum dimensions for usability
        available_width = max(300, available_width)
        available_height = max(200, available_height)

        return available_width, available_height

    def set_pixmap_to_fit(self):
        """Set pixmap with proper width expansion and height constraint logic."""
        if not self._original_pixmap:
            return

        available_width, available_height = self._calculate_available_space()

        # CRITICAL FIX: Implement width-first sizing with height constraint
        # Start with full available width
        target_width = available_width
        aspect_ratio = self._original_pixmap.height() / self._original_pixmap.width()
        target_height = int(target_width * aspect_ratio)

        # If height exceeds constraint, scale down to fit height limit
        if target_height > available_height:
            target_height = available_height
            target_width = int(target_height / aspect_ratio)

        # Ensure minimum dimensions
        target_width = max(100, target_width)
        target_height = max(75, target_height)

        # ULTRA HIGH QUALITY SCALING: Use advanced multi-step scaling for sequence viewer
        scaled_pixmap = self._create_ultra_high_quality_scaled_pixmap(
            target_width, target_height
        )

        # Set the image size properly
        self.setFixedSize(target_width, target_height)
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
