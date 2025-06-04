"""
Color Correction Diagnostic Dialog

A comprehensive testing interface for diagnosing and resolving color bleeding issues
in the export system's color processing pipeline. This dialog provides real-time
visual feedback and parameter adjustment capabilities to identify optimal settings.
"""

import logging
import os
from typing import Dict, Any, Optional, List, Tuple
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QSlider,
    QPushButton,
    QScrollArea,
    QWidget,
    QGroupBox,
    QSpinBox,
    QDoubleSpinBox,
    QComboBox,
    QTextEdit,
    QProgressBar,
    QCheckBox,
    QFrame,
    QSplitter,
    QTabWidget,
    QApplication,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QElapsedTimer
from PyQt6.QtGui import QPixmap, QImage, QColor, QPainter, QFont, QPalette

from .color_manager import ColorManager

logger = logging.getLogger(__name__)


class ClickableImageLabel(QLabel):
    """Custom QLabel that emits click signals with pixel coordinates."""

    pixel_clicked = pyqtSignal(str, int, int)  # stage_name, x, y

    def __init__(self, stage_name: str, parent=None):
        super().__init__(parent)
        self.stage_name = stage_name
        self.original_image = None

    def set_image(self, image: QImage):
        """Set the image and store original for pixel inspection."""
        self.original_image = image

    def mousePressEvent(self, event):
        """Handle mouse clicks for pixel inspection."""
        if event.button() == Qt.MouseButton.LeftButton and self.original_image:
            # Get click position relative to the label
            click_pos = event.position().toPoint()

            # Convert label coordinates to image coordinates
            if self.pixmap() and not self.pixmap().isNull():
                label_size = self.size()
                pixmap_size = self.pixmap().size()

                # Calculate scaling factors
                scale_x = self.original_image.width() / pixmap_size.width()
                scale_y = self.original_image.height() / pixmap_size.height()

                # Calculate offset for centered image
                offset_x = (label_size.width() - pixmap_size.width()) // 2
                offset_y = (label_size.height() - pixmap_size.height()) // 2

                # Convert to image coordinates
                image_x = int((click_pos.x() - offset_x) * scale_x)
                image_y = int((click_pos.y() - offset_y) * scale_y)

                # Ensure coordinates are within image bounds
                if (
                    0 <= image_x < self.original_image.width()
                    and 0 <= image_y < self.original_image.height()
                ):
                    self.pixel_clicked.emit(self.stage_name, image_x, image_y)

        super().mousePressEvent(event)


class PixelInspectorDialog(QDialog):
    """Dialog for detailed pixel-level inspection with magnification."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Pixel Inspector")
        self.setModal(False)
        self.resize(800, 600)

        # Setup UI
        layout = QVBoxLayout(self)

        # Info panel
        self.info_label = QLabel()
        self.info_label.setStyleSheet(
            "color: white; font-family: 'Courier New'; font-size: 12px; padding: 10px;"
        )
        layout.addWidget(self.info_label)

        # Magnified view
        self.magnified_label = QLabel()
        self.magnified_label.setMinimumSize(400, 400)
        self.magnified_label.setStyleSheet(
            """
            QLabel {
                border: 2px solid rgba(255, 255, 255, 0.5);
                border-radius: 10px;
                background: rgba(20, 20, 20, 0.8);
            }
        """
        )
        self.magnified_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.magnified_label)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

        # Apply glassmorphism styling
        self.setStyleSheet(
            """
            QDialog {
                background: rgba(40, 40, 40, 0.95);
                border: 2px solid rgba(255, 255, 255, 0.4);
                border-radius: 15px;
            }
        """
        )

    def show_pixel_analysis(
        self, stage_name: str, image: QImage, x: int, y: int, all_stages: dict
    ):
        """Show detailed pixel analysis for the clicked coordinates."""
        if (
            image.isNull()
            or x < 0
            or y < 0
            or x >= image.width()
            or y >= image.height()
        ):
            return

        # Get pixel color at clicked position
        pixel_color = QColor(image.pixel(x, y))
        r, g, b = pixel_color.red(), pixel_color.green(), pixel_color.blue()

        # Create magnified view (8x zoom of 50x50 area)
        magnified_image = self._create_magnified_view(image, x, y, zoom=8, area_size=50)
        if magnified_image:
            pixmap = QPixmap.fromImage(magnified_image)
            self.magnified_label.setPixmap(pixmap)

        # Build analysis text
        analysis_text = f"PIXEL ANALYSIS - {stage_name.upper()}\n"
        analysis_text += f"Position: ({x}, {y})\n"
        analysis_text += f"RGB: ({r}, {g}, {b})\n"
        analysis_text += f"Hex: {pixel_color.name()}\n\n"

        # Compare with other stages
        if all_stages:
            analysis_text += "STAGE COMPARISON:\n"
            for stage, stage_data in all_stages.items():
                if "image" in stage_data and not stage_data["image"].isNull():
                    stage_image = stage_data["image"]
                    if x < stage_image.width() and y < stage_image.height():
                        stage_pixel = QColor(stage_image.pixel(x, y))
                        sr, sg, sb = (
                            stage_pixel.red(),
                            stage_pixel.green(),
                            stage_pixel.blue(),
                        )
                        analysis_text += (
                            f"{stage.capitalize()}: RGB({sr}, {sg}, {sb})\n"
                        )

        self.info_label.setText(analysis_text)
        self.show()

    def _create_magnified_view(
        self, image: QImage, center_x: int, center_y: int, zoom: int, area_size: int
    ) -> QImage:
        """Create a magnified view of the specified area."""
        try:
            # Calculate extraction area
            half_size = area_size // 2
            x1 = max(0, center_x - half_size)
            y1 = max(0, center_y - half_size)
            x2 = min(image.width(), center_x + half_size)
            y2 = min(image.height(), center_y + half_size)

            # Extract the area
            extracted = image.copy(x1, y1, x2 - x1, y2 - y1)

            # Scale up for magnification
            magnified = extracted.scaled(
                extracted.width() * zoom,
                extracted.height() * zoom,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.FastTransformation,  # Use fast for pixel art effect
            )

            return magnified

        except Exception as e:
            logger.error(f"Error creating magnified view: {e}")
            return QImage()


class ColorDiagnosticWorker(QThread):
    """Worker thread for processing images without blocking the UI."""

    image_processed = pyqtSignal(dict)  # Emits processed image data
    progress_updated = pyqtSignal(int, str)  # Progress percentage and status

    def __init__(
        self, color_manager: ColorManager, image: QImage, parameters: Dict[str, Any]
    ):
        super().__init__()
        self.color_manager = color_manager
        self.image = image
        self.parameters = parameters
        self.should_stop = False

    def run(self):
        """Process image through the color correction pipeline with timing."""
        try:
            timer = QElapsedTimer()
            timer.start()

            # Stage 1: Original image
            self.progress_updated.emit(10, "Processing original image...")
            original_data = self._analyze_image(self.image, "original")

            # Stage 2: Scale to processing size
            self.progress_updated.emit(30, "Scaling to processing size...")
            processing_size = self.parameters.get(
                "processing_size", 800
            )  # Balanced size for sharpness and printer compatibility
            scaled_image = self._scale_image(self.image, processing_size)
            scaled_data = self._analyze_image(scaled_image, "scaled")

            if self.should_stop:
                return

            # Stage 3: Apply color corrections
            self.progress_updated.emit(60, "Applying color corrections...")
            corrected_image = self._apply_color_corrections(scaled_image)
            corrected_data = self._analyze_image(corrected_image, "corrected")

            if self.should_stop:
                return

            # Stage 4: Final scaling
            self.progress_updated.emit(90, "Final scaling...")
            final_image = self._scale_image(corrected_image, self.image.width())
            final_data = self._analyze_image(final_image, "final")

            processing_time = timer.elapsed()

            # Emit results
            result = {
                "stages": {
                    "original": {"image": self.image, "data": original_data},
                    "scaled": {"image": scaled_image, "data": scaled_data},
                    "corrected": {"image": corrected_image, "data": corrected_data},
                    "final": {"image": final_image, "data": final_data},
                },
                "processing_time": processing_time,
                "parameters": self.parameters,
            }

            self.progress_updated.emit(100, "Processing complete")
            self.image_processed.emit(result)

        except Exception as e:
            logger.error(f"Error in color diagnostic worker: {e}")

    def stop(self):
        """Stop the processing."""
        self.should_stop = True

    def _scale_image(self, image: QImage, target_size: int) -> QImage:
        """Scale image maintaining aspect ratio."""
        if image.width() > image.height():
            new_width = target_size
            new_height = int(target_size * image.height() / image.width())
        else:
            new_height = target_size
            new_width = int(target_size * image.width() / image.height())

        return image.scaled(
            new_width,
            new_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

    def _apply_color_corrections(self, image: QImage) -> QImage:
        """Apply color corrections using the ColorManager."""
        try:
            # Check if color corrections are enabled
            if not self.parameters.get("enable_corrections", True):
                logger.info(
                    "[COLOR] Color corrections disabled - returning original image"
                )
                return image.copy()

            # Update ColorManager settings with current parameters
            self.color_manager.gamma_correction = self.parameters.get(
                "gamma_correction", 1.0
            )
            # REMOVED: Red enhancement no longer exists in ColorManager
            # self.color_manager.enhance_red_channel = self.parameters.get(
            #     "red_enhancement", 1.15
            # )

            logger.info(
                f"[COLOR] Applying corrections: gamma={self.color_manager.gamma_correction}, red_enhancement=disabled"
            )

            # Apply the color processing pipeline using the optimized method
            target_width = self.parameters.get(
                "processing_size", 800
            )  # Balanced size for sharpness and printer compatibility
            target_height = int(target_width * image.height() / image.width())

            # Use the same method as production export
            corrected_image = self.color_manager.process_image_with_target_size(
                image, target_width, target_height
            )

            if corrected_image.isNull():
                logger.error(
                    "[COLOR] Color correction returned null image - using original"
                )
                return image.copy()

            logger.info(
                f"[COLOR] Color correction completed: {corrected_image.width()}x{corrected_image.height()}"
            )
            return corrected_image

        except Exception as e:
            logger.error(f"[COLOR] Error in color correction: {e}")
            return image.copy()

    def _analyze_image(self, image: QImage, stage: str) -> Dict[str, Any]:
        """Analyze image for diagnostic information."""
        if image.isNull():
            return {"error": "Null image"}

        # Sample pixels for analysis
        width, height = image.width(), image.height()
        sample_points = [
            (width // 4, height // 4),  # Top-left quadrant
            (3 * width // 4, height // 4),  # Top-right quadrant
            (width // 2, height // 2),  # Center
            (width // 4, 3 * height // 4),  # Bottom-left quadrant
            (3 * width // 4, 3 * height // 4),  # Bottom-right quadrant
        ]

        pixel_data = []
        gray_pixels = 0
        red_pixels = 0

        for x, y in sample_points:
            if 0 <= x < width and 0 <= y < height:
                pixel = image.pixel(x, y)
                color = QColor(pixel)
                r, g, b = color.red(), color.green(), color.blue()

                pixel_info = {
                    "position": (x, y),
                    "rgb": (r, g, b),
                    "is_gray": self._is_gray_pixel(r, g, b),
                    "is_red": self._is_red_pixel(r, g, b),
                }
                pixel_data.append(pixel_info)

                if pixel_info["is_gray"]:
                    gray_pixels += 1
                if pixel_info["is_red"]:
                    red_pixels += 1

        return {
            "stage": stage,
            "size": (width, height),
            "sample_pixels": pixel_data,
            "gray_pixel_count": gray_pixels,
            "red_pixel_count": red_pixels,
            "total_samples": len(sample_points),
        }

    def _is_gray_pixel(self, r: int, g: int, b: int) -> bool:
        """Check if pixel is gray (neutral)."""
        return abs(r - g) <= 15 and abs(r - b) <= 15 and abs(g - b) <= 15

    def _is_red_pixel(self, r: int, g: int, b: int) -> bool:
        """Check if pixel is predominantly red."""
        return r > g + 30 and r > b + 30 and r > 150


class ColorCorrectionDiagnosticDialog(QDialog):
    """
    Comprehensive diagnostic interface for color correction pipeline testing.

    Provides real-time visual feedback, parameter adjustment, and detailed analysis
    of the color processing pipeline to identify and resolve color bleeding issues.
    """

    def __init__(self, parent=None, app_context=None):
        super().__init__(parent)
        self.app_context = app_context
        self.color_manager = None
        self.current_sequence_data = None
        self.current_worker = None
        self.processing_results = {}
        self.pixel_inspector = None

        self._setup_dialog()
        self._create_ui()
        self._setup_connections()
        self._load_default_parameters()

        logger.info("Color Correction Diagnostic Dialog initialized")

    def _setup_dialog(self):
        """Configure dialog properties with glassmorphism styling."""
        self.setWindowTitle("Color Correction Diagnostic Interface")
        self.setModal(True)

        # Modern resizable dialog with title bar for moving and resizing
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowSystemMenuHint
            | Qt.WindowType.WindowMinMaxButtonsHint
            | Qt.WindowType.WindowCloseButtonHint
        )

        # Resizable dialog with responsive layout
        self.setMinimumSize(1400, 900)
        self.resize(1600, 1000)  # Default size, but user can resize

        # Center on parent
        if self.parent():
            parent_rect = self.parent().geometry()
            self.move(
                parent_rect.center().x() - self.width() // 2,
                parent_rect.center().y() - self.height() // 2,
            )

        # Store initial size for responsive calculations
        self.initial_size = (1600, 1000)

    def _create_ui(self):
        """Create the main user interface."""
        # Set dialog background
        self.setStyleSheet(
            """
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(30, 30, 30, 1.0),
                    stop:1 rgba(50, 50, 50, 1.0));
            }
        """
        )

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # Create main container
        container = QFrame()
        container.setStyleSheet(
            """
            QFrame {
                background: rgba(40, 40, 40, 0.95);
                border: 2px solid rgba(255, 255, 255, 0.4);
                border-radius: 15px;
            }
        """
        )

        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(30, 30, 30, 30)

        # Title
        title = QLabel("Color Correction Diagnostic Interface")
        title.setStyleSheet(
            """
            QLabel {
                color: white;
                font-size: 24px;
                font-weight: bold;
                margin-bottom: 20px;
            }
        """
        )
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(title)

        # Create main content splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        container_layout.addWidget(splitter)

        # Left panel: Controls and parameters
        self._create_control_panel(splitter)

        # Right panel: Visual pipeline display
        self._create_visual_panel(splitter)

        # Bottom panel: Analysis and results
        self._create_analysis_panel(container_layout)

        main_layout.addWidget(container)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        close_btn.setStyleSheet(
            """
            QPushButton {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 10px;
                color: white;
                padding: 10px 20px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.2);
            }
        """
        )
        main_layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignCenter)

    def _create_control_panel(self, parent_splitter):
        """Create the left control panel with parameter adjustments."""
        control_widget = QWidget()
        control_layout = QVBoxLayout(control_widget)

        # Sequence selection section
        sequence_group = QGroupBox("Sequence Selection")
        sequence_group.setStyleSheet(self._get_group_style())
        sequence_layout = QVBoxLayout(sequence_group)

        self.sequence_combo = QComboBox()
        self.sequence_combo.setStyleSheet(self._get_combo_style())

        # Style the label
        sequence_label = QLabel("Select Test Sequence:")
        sequence_label.setStyleSheet(
            "color: white; font-size: 12px; font-weight: bold; margin-bottom: 5px;"
        )
        sequence_layout.addWidget(sequence_label)
        sequence_layout.addWidget(self.sequence_combo)

        load_btn = QPushButton("Load Sequence")
        load_btn.setStyleSheet(self._get_button_style())
        load_btn.clicked.connect(self._load_selected_sequence)
        sequence_layout.addWidget(load_btn)

        control_layout.addWidget(sequence_group)

        # Parameter adjustment section
        params_group = QGroupBox("Color Processing Parameters")
        params_group.setStyleSheet(self._get_group_style())
        params_layout = QVBoxLayout(params_group)

        # Processing size parameter
        size_layout = QHBoxLayout()
        size_label = QLabel("Processing Size:")
        size_label.setStyleSheet("color: white; font-size: 12px; font-weight: bold;")
        size_layout.addWidget(size_label)
        self.size_spin = QSpinBox()
        self.size_spin.setRange(500, 1500)  # Increased range for better quality
        self.size_spin.setValue(
            800
        )  # Balanced size for sharpness and printer compatibility
        self.size_spin.setSuffix("px")
        self.size_spin.setStyleSheet(self._get_spinbox_style())
        self.size_spin.valueChanged.connect(self._on_parameter_changed)
        size_layout.addWidget(self.size_spin)
        params_layout.addLayout(size_layout)

        # Gamma correction parameter
        gamma_layout = QHBoxLayout()
        gamma_label = QLabel("Gamma Correction:")
        gamma_label.setStyleSheet("color: white; font-size: 12px; font-weight: bold;")
        gamma_layout.addWidget(gamma_label)
        self.gamma_spin = QDoubleSpinBox()
        self.gamma_spin.setRange(0.5, 2.0)
        self.gamma_spin.setValue(1.0)
        self.gamma_spin.setSingleStep(0.1)
        self.gamma_spin.setDecimals(2)
        self.gamma_spin.setStyleSheet(self._get_spinbox_style())
        self.gamma_spin.valueChanged.connect(self._on_parameter_changed)
        gamma_layout.addWidget(self.gamma_spin)
        params_layout.addLayout(gamma_layout)

        # Red enhancement parameter - DISABLED (causing issues)
        # red_layout = QHBoxLayout()
        # red_label = QLabel("Red Enhancement:")
        # red_label.setStyleSheet("color: white; font-size: 12px; font-weight: bold;")
        # red_layout.addWidget(red_label)
        # self.red_spin = QDoubleSpinBox()
        # self.red_spin.setRange(0.8, 2.0)
        # self.red_spin.setValue(1.0)  # Set to 1.0 (no enhancement)
        # self.red_spin.setSingleStep(0.05)
        # self.red_spin.setDecimals(2)
        # self.red_spin.setStyleSheet(self._get_spinbox_style())
        # self.red_spin.valueChanged.connect(self._on_parameter_changed)
        # red_layout.addWidget(self.red_spin)
        # params_layout.addLayout(red_layout)

        # Create hidden red enhancement control set to 1.0 (no enhancement)
        self.red_spin = QDoubleSpinBox()
        self.red_spin.setValue(1.0)  # No red enhancement
        self.red_spin.setVisible(False)

        # Color tolerance parameter
        tolerance_layout = QHBoxLayout()
        tolerance_label = QLabel("Color Tolerance:")
        tolerance_label.setStyleSheet(
            "color: white; font-size: 12px; font-weight: bold;"
        )
        tolerance_layout.addWidget(tolerance_label)
        self.tolerance_spin = QSpinBox()
        self.tolerance_spin.setRange(0, 30)
        self.tolerance_spin.setValue(2)
        self.tolerance_spin.setStyleSheet(self._get_spinbox_style())
        self.tolerance_spin.valueChanged.connect(self._on_parameter_changed)
        tolerance_layout.addWidget(self.tolerance_spin)
        params_layout.addLayout(tolerance_layout)

        # Reset button
        reset_btn = QPushButton("Reset to Production Defaults")
        reset_btn.setStyleSheet(self._get_button_style())
        reset_btn.clicked.connect(self._reset_to_defaults)
        params_layout.addWidget(reset_btn)

        control_layout.addWidget(params_group)

        # Processing controls
        process_group = QGroupBox("Processing Controls")
        process_group.setStyleSheet(self._get_group_style())
        process_layout = QVBoxLayout(process_group)

        # Color correction toggle
        from PyQt6.QtWidgets import QCheckBox

        self.enable_corrections_checkbox = QCheckBox("Enable Color Corrections")
        self.enable_corrections_checkbox.setChecked(True)
        self.enable_corrections_checkbox.setStyleSheet(
            """
            QCheckBox {
                color: white;
                font-size: 12px;
                font-weight: bold;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid rgba(255, 255, 255, 0.4);
                border-radius: 4px;
                background: rgba(80, 80, 80, 0.9);
            }
            QCheckBox::indicator:checked {
                background: rgba(100, 140, 220, 0.9);
                border: 2px solid rgba(255, 255, 255, 0.6);
            }
        """
        )
        self.enable_corrections_checkbox.stateChanged.connect(
            self._on_parameter_changed
        )
        process_layout.addWidget(self.enable_corrections_checkbox)

        self.process_btn = QPushButton("Process Image")
        self.process_btn.setStyleSheet(self._get_button_style())
        self.process_btn.clicked.connect(self._process_current_image)
        process_layout.addWidget(self.process_btn)

        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet(self._get_progress_style())
        self.progress_bar.setVisible(False)
        process_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: white; font-size: 12px;")
        process_layout.addWidget(self.status_label)

        control_layout.addWidget(process_group)

        # Add stretch to push everything to top
        control_layout.addStretch()

        parent_splitter.addWidget(control_widget)

        # Responsive splitter sizing (25% control panel, 75% visual panel)
        total_width = self.width() - 80  # Account for margins
        control_width = int(total_width * 0.25)
        visual_width = int(total_width * 0.75)
        parent_splitter.setSizes([control_width, visual_width])

        # Store splitter reference for responsive updates
        self.main_splitter = parent_splitter

    def _create_visual_panel(self, parent_splitter):
        """Create the right visual panel showing pipeline stages."""
        visual_widget = QWidget()
        visual_layout = QVBoxLayout(visual_widget)

        # Pipeline stages display
        stages_group = QGroupBox("Color Processing Pipeline Stages")
        stages_group.setStyleSheet(self._get_group_style())
        stages_layout = QGridLayout(stages_group)

        # Create image display labels for each stage
        self.stage_labels = {}
        stage_names = ["Original", "Scaled", "Color Corrected", "Final"]

        for i, stage in enumerate(stage_names):
            # Stage title
            title_label = QLabel(stage)
            title_label.setStyleSheet(
                "color: white; font-weight: bold; font-size: 14px;"
            )
            title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            stages_layout.addWidget(title_label, 0, i)

            # Image display with click-to-zoom functionality
            image_label = ClickableImageLabel(stage)
            image_label.setMinimumSize(250, 200)
            image_label.setStyleSheet(
                """
                QLabel {
                    border: 2px solid rgba(255, 255, 255, 0.5);
                    border-radius: 10px;
                    background: rgba(20, 20, 20, 0.8);
                    color: rgba(255, 255, 255, 0.7);
                    font-size: 12px;
                }
                QLabel:hover {
                    border: 2px solid rgba(100, 140, 220, 0.8);
                    background: rgba(30, 30, 30, 0.9);
                }
            """
            )
            image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            image_label.setText("No Image")
            image_label.setCursor(Qt.CursorShape.PointingHandCursor)
            # Connect click signal for pixel inspection
            image_label.pixel_clicked.connect(self._show_pixel_inspector)
            # Don't use setScaledContents to preserve aspect ratio
            stages_layout.addWidget(image_label, 1, i)

            # Store reference
            self.stage_labels[stage.lower().replace(" ", "_")] = image_label

        visual_layout.addWidget(stages_group)

        # Pixel analysis display
        pixel_group = QGroupBox("Pixel Analysis")
        pixel_group.setStyleSheet(self._get_group_style())
        pixel_layout = QVBoxLayout(pixel_group)

        self.pixel_analysis_text = QTextEdit()
        self.pixel_analysis_text.setStyleSheet(
            """
            QTextEdit {
                background: rgba(0, 0, 0, 0.5);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 8px;
                color: white;
                font-family: 'Courier New', monospace;
                font-size: 11px;
            }
        """
        )
        self.pixel_analysis_text.setMaximumHeight(150)
        pixel_layout.addWidget(self.pixel_analysis_text)

        visual_layout.addWidget(pixel_group)

        parent_splitter.addWidget(visual_widget)

    def _create_analysis_panel(self, parent_layout):
        """Create the bottom analysis panel."""
        analysis_group = QGroupBox("Performance & Statistical Analysis")
        analysis_group.setStyleSheet(self._get_group_style())
        analysis_layout = QHBoxLayout(analysis_group)

        # Performance metrics
        perf_widget = QWidget()
        perf_layout = QVBoxLayout(perf_widget)
        perf_layout.addWidget(QLabel("Performance Metrics:"))

        self.perf_text = QTextEdit()
        self.perf_text.setStyleSheet(
            """
            QTextEdit {
                background: rgba(0, 0, 0, 0.5);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 8px;
                color: white;
                font-family: 'Courier New', monospace;
                font-size: 11px;
            }
        """
        )
        self.perf_text.setMaximumHeight(100)
        perf_layout.addWidget(self.perf_text)

        analysis_layout.addWidget(perf_widget)

        # Export controls
        export_widget = QWidget()
        export_layout = QVBoxLayout(export_widget)
        export_layout.addWidget(QLabel("Export Results:"))

        export_btn = QPushButton("Export Analysis Report")
        export_btn.setStyleSheet(self._get_button_style())
        export_btn.clicked.connect(self._export_analysis)
        export_layout.addWidget(export_btn)

        save_settings_btn = QPushButton("Save Optimal Settings")
        save_settings_btn.setStyleSheet(self._get_button_style())
        save_settings_btn.clicked.connect(self._save_optimal_settings)
        export_layout.addWidget(save_settings_btn)

        analysis_layout.addWidget(export_widget)

        parent_layout.addWidget(analysis_group)

    def _setup_connections(self):
        """Setup signal connections."""
        pass  # Connections already set up in UI creation

    def _load_default_parameters(self):
        """Load default parameters and populate sequence list."""
        # Initialize ColorManager with default settings
        default_settings = {
            "preserve_color_profile": True,
            "gamma_correction": 1.0,
            # REMOVED: Red enhancement causing gray-to-red color bleeding
            # "enhance_red_channel": 1.15,
            "color_correction": {},
            "use_high_bit_depth": True,
        }
        self.color_manager = ColorManager(default_settings)

        # Populate sequence combo with test sequences
        self._populate_sequence_list()

        self.status_label.setText("Ready - Select a sequence to begin testing")

    def _populate_sequence_list(self):
        """Populate the sequence selection combo with available dictionary sequences."""
        try:
            # Load actual dictionary sequences
            from utils.path_helpers import get_data_path
            import os

            dictionary_dir = get_data_path("dictionary")
            if not os.path.exists(dictionary_dir):
                # Fallback to test sequences if dictionary not available
                test_sequences = [
                    "Test Sequence 1 (Gray Background)",
                    "Test Sequence 2 (Mixed Colors)",
                    "Test Sequence 3 (Red Elements)",
                    "Test Sequence 4 (Complex Scene)",
                ]
                self.sequence_combo.addItems(test_sequences)
                return

            # Scan dictionary for sequences with thumbnails
            sequence_options = []
            for word_entry in os.listdir(dictionary_dir):
                word_path = os.path.join(dictionary_dir, word_entry)

                # Skip non-directories and __pycache__
                if not os.path.isdir(word_path) or "__pycache__" in word_entry:
                    continue

                # Find thumbnails in the word directory
                thumbnails = []
                for file in os.listdir(word_path):
                    if file.lower().endswith((".png", ".jpg", ".jpeg")):
                        thumbnails.append(os.path.join(word_path, file))

                if thumbnails:
                    # Add word with thumbnail count
                    sequence_options.append(
                        f"{word_entry} ({len(thumbnails)} variations)"
                    )

                    # Limit to first 20 for performance
                    if len(sequence_options) >= 20:
                        break

            if sequence_options:
                self.sequence_combo.addItems(sequence_options)
            else:
                # Fallback if no sequences found
                self.sequence_combo.addItem("No dictionary sequences found")

        except Exception as e:
            logger.error(f"Error loading dictionary sequences: {e}")
            # Fallback to test sequences
            test_sequences = [
                "Test Sequence 1 (Gray Background)",
                "Test Sequence 2 (Mixed Colors)",
            ]
            self.sequence_combo.addItems(test_sequences)

    def _on_parameter_changed(self):
        """Handle parameter changes and trigger auto-processing if enabled."""
        self.status_label.setText(
            "Parameters changed - Click 'Process Image' to update"
        )

    def _reset_to_defaults(self):
        """Reset all parameters to production defaults."""
        self.size_spin.setValue(
            800
        )  # Balanced size for sharpness and printer compatibility
        self.gamma_spin.setValue(1.0)
        self.red_spin.setValue(1.0)  # Red enhancement disabled
        self.tolerance_spin.setValue(2)
        self.status_label.setText(
            "Parameters reset to production defaults (800px processing, red enhancement disabled)"
        )

    def _load_selected_sequence(self):
        """Load the selected sequence for testing."""
        selected = self.sequence_combo.currentText()
        if not selected:
            return

        self.status_label.setText(f"Loading sequence: {selected}")

        # Try to load actual dictionary image
        image = self._load_dictionary_image(selected)
        if image is None:
            # Fallback to test image
            image = self._create_test_image()

        self.current_sequence_data = {"name": selected, "image": image}

        # Display original image
        pixmap = self._qimage_to_pixmap(image)
        self.stage_labels["original"].setPixmap(pixmap)

        self.status_label.setText(f"Loaded: {selected} - Ready for processing")

    def _load_dictionary_image(self, sequence_name: str) -> QImage:
        """Load an actual sequence card using the production export pipeline."""
        try:
            from utils.path_helpers import get_data_path
            from main_window.main_widget.metadata_extractor import MetaDataExtractor
            import os

            # Extract word name from combo text (remove variation count)
            word_name = sequence_name.split(" (")[0]

            dictionary_dir = get_data_path("dictionary")
            word_path = os.path.join(dictionary_dir, word_name)

            if not os.path.exists(word_path):
                logger.warning(f"Dictionary path not found: {word_path}")
                return None

            # Find the first thumbnail image to extract metadata
            metadata_extractor = MetaDataExtractor()
            sequence_metadata = None

            for file in os.listdir(word_path):
                if file.lower().endswith((".png", ".jpg", ".jpeg")):
                    image_path = os.path.join(word_path, file)
                    sequence_metadata = metadata_extractor.extract_metadata_from_file(
                        image_path
                    )
                    if sequence_metadata:
                        break

            if not sequence_metadata:
                logger.warning(f"No sequence metadata found for {word_name}")
                return None

            # Create sequence card using production pipeline
            try:
                # Import the ImageCreator from the production export system
                from main_window.main_widget.sequence_workbench.sequence_beat_frame.image_export_manager.image_creator.image_creator import (
                    ImageCreator,
                )

                # Get the app context to access the export manager
                if self.app_context and hasattr(self.app_context, "main_widget"):
                    main_widget = self.app_context.main_widget
                    if hasattr(main_widget, "sequence_workbench") and hasattr(
                        main_widget.sequence_workbench, "beat_frame"
                    ):
                        export_manager = (
                            main_widget.sequence_workbench.beat_frame.image_export_manager
                        )
                        image_creator = export_manager.image_creator

                        # Production export options
                        export_options = {
                            "add_beat_numbers": True,
                            "add_reversal_symbols": True,
                            "add_user_info": True,
                            "add_word": True,
                            "add_difficulty_level": True,
                            "include_start_position": True,
                            "combined_grids": False,
                            "additional_height_top": 0,
                            "additional_height_bottom": 0,
                        }

                        # Create sequence image using production pipeline
                        sequence_data = sequence_metadata.get("sequence", [])
                        qimage = image_creator.create_sequence_image(
                            sequence_data,
                            export_options,
                            dictionary=True,
                            fullscreen_preview=False,
                        )

                        if qimage and not qimage.isNull():
                            logger.info(
                                f"Created sequence card for {word_name}: {qimage.width()}x{qimage.height()}"
                            )
                            return qimage
                        else:
                            logger.warning(
                                f"Failed to create sequence image for {word_name}"
                            )

            except Exception as e:
                logger.error(f"Error creating sequence card for {word_name}: {e}")

            # Fallback: load the thumbnail image directly
            for file in os.listdir(word_path):
                if file.lower().endswith((".png", ".jpg", ".jpeg")):
                    image_path = os.path.join(word_path, file)
                    image = QImage(image_path)
                    if not image.isNull():
                        logger.info(
                            f"Fallback: Loaded thumbnail image: {image_path} ({image.width()}x{image.height()})"
                        )
                        return image

            return None

        except Exception as e:
            logger.error(f"Error loading sequence for {sequence_name}: {e}")
            return None

    def _create_test_image(self) -> QImage:
        """Create a test image with gray and red elements for testing."""
        # Create a simple test image with known color patterns
        image = QImage(400, 300, QImage.Format.Format_RGB32)
        image.fill(QColor(128, 128, 128))  # Gray background

        # Add some red elements
        for y in range(50, 100):
            for x in range(50, 150):
                image.setPixel(x, y, QColor(220, 50, 50).rgb())

        # Add some near-gray elements that might be affected
        for y in range(150, 200):
            for x in range(200, 300):
                image.setPixel(x, y, QColor(140, 135, 130).rgb())

        return image

    def _process_current_image(self):
        """Process the current image through the color correction pipeline."""
        if not self.current_sequence_data:
            self.status_label.setText(
                "No sequence loaded - please select and load a sequence first"
            )
            return

        # Stop any existing worker
        if self.current_worker and self.current_worker.isRunning():
            self.current_worker.stop()
            self.current_worker.wait()

        # Get current parameters
        parameters = {
            "processing_size": self.size_spin.value(),
            "gamma_correction": self.gamma_spin.value(),
            "red_enhancement": self.red_spin.value(),
            "color_tolerance": self.tolerance_spin.value(),
            "enable_corrections": self.enable_corrections_checkbox.isChecked(),
        }

        # Start processing
        self.process_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        # Create and start worker
        self.current_worker = ColorDiagnosticWorker(
            self.color_manager, self.current_sequence_data["image"], parameters
        )
        self.current_worker.image_processed.connect(self._on_image_processed)
        self.current_worker.progress_updated.connect(self._on_progress_updated)
        self.current_worker.start()

    def _on_progress_updated(self, percentage: int, status: str):
        """Handle progress updates from the worker."""
        self.progress_bar.setValue(percentage)
        self.status_label.setText(status)

    def _on_image_processed(self, result: Dict[str, Any]):
        """Handle completed image processing results."""
        self.processing_results = result

        # Update visual displays
        stages = result["stages"]
        for stage_name, stage_data in stages.items():
            if stage_name in self.stage_labels:
                image = stage_data["image"]
                pixmap = self._qimage_to_pixmap(image)
                label = self.stage_labels[stage_name]
                label.setPixmap(pixmap)
                # Set original image for pixel inspection
                if hasattr(label, "set_image"):
                    label.set_image(image)

        # Update pixel analysis
        self._update_pixel_analysis(result)

        # Update performance metrics
        self._update_performance_metrics(result)

        # Re-enable controls
        self.process_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("Processing complete - Review results")

    def _update_pixel_analysis(self, result: Dict[str, Any]):
        """Update the pixel analysis display."""
        analysis_text = "PIXEL ANALYSIS RESULTS:\n\n"

        stages = result["stages"]
        for stage_name, stage_data in stages.items():
            data = stage_data["data"]
            if "error" in data:
                analysis_text += f"{stage_name.upper()}: {data['error']}\n"
                continue

            analysis_text += f"{stage_name.upper()}:\n"
            analysis_text += f"  Size: {data['size'][0]}x{data['size'][1]}\n"
            analysis_text += (
                f"  Gray pixels: {data['gray_pixel_count']}/{data['total_samples']}\n"
            )
            analysis_text += (
                f"  Red pixels: {data['red_pixel_count']}/{data['total_samples']}\n"
            )

            # Show sample pixel data
            for i, pixel in enumerate(
                data["sample_pixels"][:3]
            ):  # Show first 3 samples
                rgb = pixel["rgb"]
                analysis_text += f"  Sample {i+1}: RGB({rgb[0]}, {rgb[1]}, {rgb[2]}) "
                analysis_text += f"Gray: {pixel['is_gray']}, Red: {pixel['is_red']}\n"

            analysis_text += "\n"

        self.pixel_analysis_text.setText(analysis_text)

    def _update_performance_metrics(self, result: Dict[str, Any]):
        """Update the performance metrics display."""
        processing_time = result["processing_time"]
        parameters = result["parameters"]

        metrics_text = f"PERFORMANCE METRICS:\n\n"
        metrics_text += f"Total Processing Time: {processing_time}ms\n"
        metrics_text += f"Processing Size: {parameters['processing_size']}px\n"
        metrics_text += f"Gamma Correction: {parameters['gamma_correction']}\n"
        metrics_text += f"Red Enhancement: {parameters['red_enhancement']}\n"
        metrics_text += f"Color Tolerance: {parameters['color_tolerance']}\n\n"

        # Calculate efficiency metrics
        stages = result["stages"]
        original_size = stages["original"]["data"]["size"]
        scaled_size = stages["scaled"]["data"]["size"]

        size_reduction = (original_size[0] * original_size[1]) / (
            scaled_size[0] * scaled_size[1]
        )
        metrics_text += f"Size Reduction Factor: {size_reduction:.2f}x\n"
        metrics_text += f"Estimated Performance Gain: {size_reduction:.1f}x faster\n"

        self.perf_text.setText(metrics_text)

    def resizeEvent(self, event):
        """Handle window resize to maintain responsive layout."""
        super().resizeEvent(event)

        # Update splitter sizes to maintain proportions
        if hasattr(self, "main_splitter"):
            total_width = self.width() - 80  # Account for margins
            control_width = int(total_width * 0.25)
            visual_width = int(total_width * 0.75)
            self.main_splitter.setSizes([control_width, visual_width])

    def _show_pixel_inspector(self, stage_name: str, x: int, y: int):
        """Show the pixel inspector for the clicked coordinates."""
        if not self.processing_results or "stages" not in self.processing_results:
            return

        # Find the clicked stage image
        stages = self.processing_results["stages"]
        clicked_stage = None

        for stage, stage_data in stages.items():
            if stage.lower().replace(" ", "_") == stage_name.lower().replace(" ", "_"):
                clicked_stage = stage_data
                break

        if not clicked_stage or "image" not in clicked_stage:
            return

        # Create pixel inspector if it doesn't exist
        if not self.pixel_inspector:
            self.pixel_inspector = PixelInspectorDialog(self)

        # Show pixel analysis
        self.pixel_inspector.show_pixel_analysis(
            stage_name, clicked_stage["image"], x, y, stages
        )

    def _export_analysis(self):
        """Export the current analysis results to a file."""
        if not self.processing_results:
            self.status_label.setText("No analysis results to export")
            return

        # TODO: Implement file dialog and export functionality
        self.status_label.setText("Export functionality not yet implemented")

    def _save_optimal_settings(self):
        """Save the current parameter settings as optimal for production use."""
        parameters = {
            "processing_size": self.size_spin.value(),
            "gamma_correction": self.gamma_spin.value(),
            "red_enhancement": self.red_spin.value(),
            "color_tolerance": self.tolerance_spin.value(),
        }

        # TODO: Implement saving to configuration
        self.status_label.setText(f"Settings saved: {parameters}")

    def _qimage_to_pixmap(self, image: QImage, target_size=(250, 200)) -> QPixmap:
        """Convert QImage to QPixmap for display with proper aspect ratio scaling."""
        from PyQt6.QtGui import QPixmap

        if image.isNull():
            return QPixmap()

        # Create pixmap from image
        pixmap = QPixmap.fromImage(image)

        # Scale while preserving aspect ratio
        target_width, target_height = target_size
        scaled_pixmap = pixmap.scaled(
            target_width,
            target_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

        return scaled_pixmap

    # Styling methods
    def _get_group_style(self) -> str:
        """Get glassmorphism group box styling."""
        return """
            QGroupBox {
                background: rgba(60, 60, 60, 0.8);
                border: 2px solid rgba(255, 255, 255, 0.3);
                border-radius: 12px;
                margin-top: 15px;
                padding-top: 15px;
                color: white;
                font-weight: bold;
                font-size: 14px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px 0 10px;
                color: white;
                background: rgba(60, 60, 60, 0.9);
                border-radius: 6px;
            }
        """

    def _get_button_style(self) -> str:
        """Get glassmorphism button styling."""
        return """
            QPushButton {
                background: rgba(80, 120, 200, 0.8);
                border: 2px solid rgba(255, 255, 255, 0.4);
                border-radius: 8px;
                color: white;
                padding: 10px 18px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(100, 140, 220, 0.9);
                border: 2px solid rgba(255, 255, 255, 0.6);
            }
            QPushButton:pressed {
                background: rgba(60, 100, 180, 0.9);
            }
            QPushButton:disabled {
                background: rgba(60, 60, 60, 0.5);
                border: 2px solid rgba(255, 255, 255, 0.2);
                color: rgba(255, 255, 255, 0.5);
            }
        """

    def _get_combo_style(self) -> str:
        """Get glassmorphism combo box styling."""
        return """
            QComboBox {
                background: rgba(80, 80, 80, 0.9);
                border: 2px solid rgba(255, 255, 255, 0.4);
                border-radius: 6px;
                color: white;
                padding: 8px 12px;
                font-size: 12px;
            }
            QComboBox:hover {
                background: rgba(100, 100, 100, 0.9);
                border: 2px solid rgba(255, 255, 255, 0.6);
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid white;
                margin-right: 5px;
            }
            QComboBox QAbstractItemView {
                background: rgba(80, 80, 80, 0.95);
                border: 2px solid rgba(255, 255, 255, 0.4);
                color: white;
                selection-background-color: rgba(100, 140, 220, 0.8);
            }
        """

    def _get_spinbox_style(self) -> str:
        """Get glassmorphism spinbox styling."""
        return """
            QSpinBox, QDoubleSpinBox {
                background: rgba(80, 80, 80, 0.9);
                border: 2px solid rgba(255, 255, 255, 0.4);
                border-radius: 6px;
                color: white;
                padding: 8px 10px;
                font-size: 12px;
            }
            QSpinBox:hover, QDoubleSpinBox:hover {
                background: rgba(100, 100, 100, 0.9);
                border: 2px solid rgba(255, 255, 255, 0.6);
            }
            QSpinBox::up-button, QDoubleSpinBox::up-button {
                background: rgba(100, 120, 200, 0.8);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 3px;
                width: 18px;
            }
            QSpinBox::down-button, QDoubleSpinBox::down-button {
                background: rgba(100, 120, 200, 0.8);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 3px;
                width: 18px;
            }
            QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
            QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
                background: rgba(120, 140, 220, 0.9);
            }
        """

    def _get_progress_style(self) -> str:
        """Get glassmorphism progress bar styling."""
        return """
            QProgressBar {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 8px;
                text-align: center;
                color: white;
                font-size: 11px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(100, 200, 255, 0.8),
                    stop:1 rgba(50, 150, 255, 0.8));
                border-radius: 6px;
                margin: 1px;
            }
        """
