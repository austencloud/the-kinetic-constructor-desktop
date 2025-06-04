"""
Processing Size Diagnostic Tool

Compares different processing sizes to find the optimal balance between
image quality and color vibrancy for printed output.
"""

import logging
import os
import time
from typing import Dict, List, Tuple, Any
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QSpinBox, QProgressBar, QTextEdit, QGroupBox, QComboBox, QCheckBox,
    QTabWidget, QWidget, QScrollArea, QFrame, QSplitter
)
from PyQt6.QtGui import QImage, QPixmap, QColor, QFont
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QElapsedTimer

from .color_manager import ColorManager
from .export_config import ExportConfig

logger = logging.getLogger(__name__)


class ProcessingSizeComparisonWorker(QThread):
    """Worker thread for comparing different processing sizes."""
    
    progress_updated = pyqtSignal(int, str)
    comparison_completed = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, test_image: QImage, processing_sizes: List[int]):
        super().__init__()
        self.test_image = test_image
        self.processing_sizes = processing_sizes
        self.should_stop = False
        
    def stop(self):
        self.should_stop = True
        
    def run(self):
        """Run the processing size comparison."""
        try:
            results = {}
            total_tests = len(self.processing_sizes)
            
            for i, size in enumerate(self.processing_sizes):
                if self.should_stop:
                    return
                    
                self.progress_updated.emit(
                    int((i / total_tests) * 100),
                    f"Testing {size}px processing size..."
                )
                
                # Test this processing size
                result = self._test_processing_size(size)
                results[size] = result
                
                # Small delay to keep UI responsive
                time.sleep(0.1)
                
            self.comparison_completed.emit(results)
            
        except Exception as e:
            logger.error(f"Error in processing size comparison: {e}")
            self.error_occurred.emit(str(e))
            
    def _test_processing_size(self, size: int) -> Dict[str, Any]:
        """Test a specific processing size and return quality metrics."""
        timer = QElapsedTimer()
        timer.start()
        
        # Create color manager with standard settings
        color_settings = {
            "preserve_color_profile": True,
            "gamma_correction": 1.0,
            "color_correction": {
                "#ED1C24": "#FF1C24",  # Standard red correction
            },
            "use_high_bit_depth": True,
        }
        color_manager = ColorManager(color_settings)
        
        # Process image at this size
        target_width = size
        target_height = int(size * self.test_image.height() / self.test_image.width())
        
        processed_image = color_manager.process_image_with_target_size(
            self.test_image, target_width, target_height
        )
        
        processing_time = timer.elapsed()
        
        # Analyze the processed image
        analysis = self._analyze_image_quality(processed_image, size)
        analysis['processing_time'] = processing_time
        analysis['processing_size'] = size
        
        return analysis
        
    def _analyze_image_quality(self, image: QImage, size: int) -> Dict[str, Any]:
        """Analyze image quality metrics."""
        if image.isNull():
            return {
                'error': 'Failed to process image',
                'red_vibrancy': 0,
                'sharpness_score': 0,
                'file_size_estimate': 0
            }
            
        # Sample pixels for analysis
        width, height = image.width(), image.height()
        red_pixels = []
        total_pixels = 0
        edge_transitions = 0
        
        # Sample every 10th pixel for performance
        step = max(1, min(width, height) // 50)
        
        for y in range(0, height, step):
            for x in range(0, width, step):
                pixel = image.pixel(x, y)
                color = QColor(pixel)
                r, g, b = color.red(), color.green(), color.blue()
                
                total_pixels += 1
                
                # Detect red pixels (red > 150 and red > green+blue)
                if r > 150 and r > g + 50 and r > b + 50:
                    red_pixels.append((r, g, b))
                    
                # Simple edge detection for sharpness
                if x < width - step and y < height - step:
                    next_pixel = image.pixel(x + step, y)
                    next_color = QColor(next_pixel)
                    
                    # Calculate color difference
                    diff = abs(r - next_color.red()) + abs(g - next_color.green()) + abs(b - next_color.blue())
                    if diff > 30:  # Threshold for edge detection
                        edge_transitions += 1
        
        # Calculate metrics
        red_vibrancy = 0
        if red_pixels:
            avg_red = sum(r for r, g, b in red_pixels) / len(red_pixels)
            avg_saturation = sum(r - max(g, b) for r, g, b in red_pixels) / len(red_pixels)
            red_vibrancy = (avg_red + avg_saturation) / 2
            
        sharpness_score = (edge_transitions / total_pixels) * 1000 if total_pixels > 0 else 0
        
        # Estimate file size (rough approximation)
        file_size_estimate = width * height * 3  # RGB bytes
        
        return {
            'red_vibrancy': round(red_vibrancy, 2),
            'sharpness_score': round(sharpness_score, 2),
            'file_size_estimate': file_size_estimate,
            'red_pixel_count': len(red_pixels),
            'total_pixels_sampled': total_pixels,
            'dimensions': f"{width}x{height}"
        }


class ProcessingSizeDiagnosticDialog(QDialog):
    """Dialog for diagnosing optimal processing size."""
    
    def __init__(self, parent=None, app_context=None):
        super().__init__(parent)
        self.app_context = app_context
        self.current_worker = None
        self.test_results = {}
        
        self._setup_dialog()
        self._create_ui()
        self._load_test_image()
        
        logger.info("Processing Size Diagnostic Dialog initialized")
        
    def _setup_dialog(self):
        """Configure dialog properties."""
        self.setWindowTitle("Processing Size Diagnostic - Quality vs Color Vibrancy")
        self.setModal(True)
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        
    def _create_ui(self):
        """Create the main user interface."""
        layout = QVBoxLayout(self)
        
        # Create tab widget for different views
        self.tab_widget = QTabWidget()
        
        # Tab 1: Comparison Setup
        self.setup_tab = self._create_setup_tab()
        self.tab_widget.addTab(self.setup_tab, "Test Setup")
        
        # Tab 2: Results Analysis
        self.results_tab = self._create_results_tab()
        self.tab_widget.addTab(self.results_tab, "Results Analysis")
        
        # Tab 3: Recommendations
        self.recommendations_tab = self._create_recommendations_tab()
        self.tab_widget.addTab(self.recommendations_tab, "Recommendations")
        
        layout.addWidget(self.tab_widget)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.run_test_btn = QPushButton("Run Diagnostic Test")
        self.run_test_btn.clicked.connect(self._run_diagnostic_test)
        button_layout.addWidget(self.run_test_btn)
        
        self.export_results_btn = QPushButton("Export Results")
        self.export_results_btn.clicked.connect(self._export_results)
        self.export_results_btn.setEnabled(False)
        button_layout.addWidget(self.export_results_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
    def _create_setup_tab(self) -> QWidget:
        """Create the test setup tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Test configuration
        config_group = QGroupBox("Test Configuration")
        config_layout = QGridLayout(config_group)
        
        # Processing sizes to test
        config_layout.addWidget(QLabel("Processing Sizes to Test:"), 0, 0)
        self.sizes_text = QTextEdit()
        self.sizes_text.setPlainText("400, 500, 600, 700, 800, 900, 1000, 1100, 1200")
        self.sizes_text.setMaximumHeight(60)
        config_layout.addWidget(self.sizes_text, 0, 1)
        
        # Test image selection
        config_layout.addWidget(QLabel("Test Image:"), 1, 0)
        self.image_combo = QComboBox()
        self.image_combo.addItems([
            "Generated Test Image (Red Elements)",
            "Dictionary Sequence (if available)",
            "Custom Test Pattern"
        ])
        config_layout.addWidget(self.image_combo, 1, 1)
        
        layout.addWidget(config_group)
        
        # Progress tracking
        progress_group = QGroupBox("Test Progress")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_bar = QProgressBar()
        progress_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Ready to run diagnostic test")
        progress_layout.addWidget(self.status_label)
        
        layout.addWidget(progress_group)
        
        layout.addStretch()
        return widget
